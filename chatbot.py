from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
import os

# Load environment variables
load_dotenv()

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_PUBLISHABLE_KEY")
)

# Connect to OpenAI
client = OpenAI()

# Ask the user a question
question = input("Ask Marina's chatbot a question: ")

# Get Marina's knowledge from Supabase
response = (
    supabase.table("knowledge_items")
    .select("category, topic, content, keywords")
    .execute()
)

all_items = response.data

# Break the student's question into words
question_words = set(question.lower().split())

# Find knowledge records that match words in the question
relevant_items = []

for item in all_items:
    searchable_text = (
        f"{item['category']} "
        f"{item['topic']} "
        f"{item['keywords'] or ''}"
    ).lower()

    score = sum(
        1 for word in question_words
        if word in searchable_text
    )

    if score > 0:
        relevant_items.append((score, item))

# Put the strongest matches first
relevant_items.sort(key=lambda x: x[0], reverse=True)

# Keep only the 8 best matches
knowledge_items = [
    item for score, item in relevant_items[:8]
]

# Combine the knowledge into text
knowledge_text = "\n\n".join(
    f"Topic: {item['topic']}\n{item['content']}"
    for item in knowledge_items
)

# Give the question + Marina's knowledge to OpenAI
ai_response = client.responses.create(
    model="gpt-5-mini",
    instructions="""
You are Marina's English-teaching website assistant.

Answer questions using ONLY the knowledge provided below.
Do not invent courses, books, policies, prices, schedules,
qualifications, or other information.

If the answer is not contained in the knowledge base,
say that you don't have that information and suggest
contacting Marina.

Keep answers friendly, conversational, and concise.
""",
    input=f"""
MARINA'S KNOWLEDGE BASE:

{knowledge_text}

STUDENT'S QUESTION:
{question}
"""
)

print("\nChatbot:")
print(ai_response.output_text)