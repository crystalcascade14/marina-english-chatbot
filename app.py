from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
import os

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

# Allow webpages to communicate with the API
# "*" is temporary while we develop and test the chatbot.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# Describe what a chatbot request contains
class ChatRequest(BaseModel):
    question: str


# Simple test route
@app.get("/")
def home():
    return {"message": "Marina English Chatbot API is running!"}


# Main chatbot route
@app.post("/chat")
def chat(request: ChatRequest):

    # Get the student's question
    question = request.question

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
