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

# Temporary route for testing the rate limiter
@app.get("/rate-test")
@limiter.limit("10/minute")
def rate_test(request: Request):
    return {"message": "OK"}

# Main chatbot route
@app.post("/chat")
@limiter.limit("10/minute")
def chat(request: Request, body: ChatRequest):
    try:
        # Get the student's question
        question = body.question

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
            question.lower()
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

        # Find relevant knowledge records
        relevant_items = []

        for item in all_items:

            searchable_text = (
                f"{item['category']} "
                f"{item['topic']} "
                f"{item['keywords'] or ''}"
            ).lower()

            # Give the record one point for every matching word
            score = sum(
                1 for word in question_words
                if word in searchable_text
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

        # Ask OpenAI to answer using Marina's knowledge
        ai_response = client.responses.create(
            model="gpt-5-mini",

            instructions="""
    You are Marina's English-teaching website assistant.

    Answer questions using ONLY the knowledge provided.

    Do not invent courses, books, policies, prices, schedules,
    qualifications, or other information.

    If the answer is not contained in the knowledge,
    say that you don't have that information and suggest
    contacting Marina.

    Keep answers friendly, conversational, and concise.
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