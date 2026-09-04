from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Load environment variables from .env
load_dotenv()

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_PUBLISHABLE_KEY")
)

# Connect to OpenAI
client = OpenAI()

# Create FastAPI application
app = FastAPI()

# Create rate limiter based on the visitor's IP address
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Handle requests that exceed the rate limit
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

# Allow only Marina's website to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "https://englishwmarina.com",
    "https://www.englishwmarina.com",
    ],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# Describe what a chatbot request contains
class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)
    language: str = "en"

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty")

        return value

# Simple test route
@app.get("/")
def home():
    return {"message": "Marina English Chatbot API is running!"}


# Main chatbot route
@app.post("/chat")
@limiter.limit("10/minute")
def chat(request: Request, body: ChatRequest):
    try:
        # Get the student's question
        question = body.question
        language = body.language

                # Translate Russian questions to English for knowledge retrieval
        search_question = question

        if language == "ru":
            translation_response = client.responses.create(
                model="gpt-5-mini",
                instructions=(
                    "Translate the user's question from Russian to English. "
                    "Return only the English translation. Do not answer the question."
                ),
                input=question
            )
            search_question = translation_response.output_text

        # Get Marina's knowledge from Supabase
        response = (
            supabase.table("knowledge_items")
            .select("category, topic, content, keywords")
            .execute()
        )

        all_items = response.data

        # Common words that are not useful for finding knowledge
        stop_words = {
            "a", "an", "the", "and", "or", "but",
            "i", "you", "your", "we", "they",
            "is", "are", "am", "was", "were",
            "do", "does", "did",
            "what", "which", "who", "where", "when", "why", "how",
            "for", "to", "of", "in", "on", "at", "with",
            "can", "could", "would", "should",
            "have", "has", "had"
        }

        # Remove punctuation from the question
        clean_question = (
            search_question.lower()
            .replace("?", "")
            .replace("!", "")
            .replace(".", "")
            .replace(",", "")
        )

        # Keep only useful words from the question
        question_words = {
            word for word in clean_question.split()
            if word not in stop_words
        }
                # Add related words so natural questions can find the right knowledge
        synonyms = {
            "often": {"frequency", "weekly", "week"},
            "frequently": {"frequency", "weekly", "week"},
            "classes": {"lessons", "lesson"},
            "class": {"lesson", "lessons"},
            "book": {"books", "materials"},
            "books": {"book", "materials"},
            "material": {"materials", "books"},
            "materials": {"material", "books"},
            "cancel": {"cancellation", "reschedule"},
            "cancellation": {"cancel", "reschedule"},
            "reschedule": {"cancellation", "cancel"},
            "trial": {"assessment", "level"},
            "level": {"assessment", "trial"},
        }

        expanded_words = set(question_words)

        for word in question_words:
            expanded_words.update(synonyms.get(word, set()))

        question_words = expanded_words

        # Find relevant knowledge records
        relevant_items = []

        for item in all_items:

            searchable_text = (
                f"{item['category']} "
                f"{item['topic']} "
                f"{item['keywords'] or ''}"
            ).lower()

            # Match complete words instead of parts of words
            searchable_words = set(
                searchable_text
                .replace(",", " ")
                .replace(".", " ")
                .replace(":", " ")
                .replace("/", " ")
                .replace("-", " ")
                .split()
            )

            score = sum(
                1 for word in question_words
                if word in searchable_words
            )

            if score > 0:
                relevant_items.append((score, item))

        # Put the strongest matches first
        relevant_items.sort(
            key=lambda x: x[0],
            reverse=True
        )

        # Keep only the 8 best matches
        knowledge_items = [
            item for score, item in relevant_items[:8]
        ]

        # Convert selected knowledge into text for OpenAI
        knowledge_text = "\n\n".join(
            f"Topic: {item['topic']}\n{item['content']}"
            for item in knowledge_items
        )
        if language == "ru":
            language_instruction = "Answer in Russian."
        else:
            language_instruction = "Answer in English."

        # Ask OpenAI to answer using Marina's knowledge
        ai_response = client.responses.create(
            model="gpt-5-mini",

            instructions=f"""
You are the chatbot for Marina's English-teaching website.

LANGUAGE:
{language_instruction}

Answer the student's specific question using ONLY the provided knowledge.

Keep answers friendly, natural, conversational, and suitable for a website chatbot.

RESPONSE LENGTH:
- For normal questions, aim for about 60-120 words.
- Prefer 1-3 short paragraphs.
- Use a short list only when it makes the answer easier to read.
- If the user explicitly asks for details, a full list, or a comparison, you may give a longer answer.
- Do not dump all related knowledge into the response.

RELEVANCE:
- Answer the student's actual question first.
- Use only the knowledge that is relevant to that question.
- Do not add unrelated details just because they appear in the provided knowledge.
- You may briefly mention a closely related course when it is genuinely useful. Keep cross-promotion to one short sentence and keep the student's original question as the main focus.

ACCURACY:
- Do not invent courses, books, materials, policies, prices, schedules, availability, qualifications, or other information.
- A2 is Marina's minimum entry level, not a General English course she teaches.
- Marina's General English courses are B1, B2, C1, and C2.
- English for IT requires at least B2 General English.
- Do not promise IELTS scores, Cambridge exam results, or progress within a fixed amount of time.

MISSING INFORMATION:
- If the provided knowledge contains the answer, answer it directly.
- Do not tell the student to contact Marina when the answer is already available.
- If the requested information is genuinely missing, say that you don't have that information and suggest contacting Marina.
- Never invent available lesson times.

STYLE:
- Avoid overly formal, academic, or sales-heavy language.
- Avoid repetitive AI-style wording.
- Avoid constructions such as "It's not X, it's Y", "X isn't about... It's about...", and "This isn't just...".
- Do not automatically end every response with an invitation to contact Marina.
- A brief useful follow-up question is allowed when appropriate.
""",

            input=f"""
    MARINA'S KNOWLEDGE:

    {knowledge_text}

    STUDENT'S QUESTION:
    {question}
    """
        )

        # Send the answer back to the website
        return {
            "question": question,
            "answer": ai_response.output_text
        }
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process the request right now."
        )

    