from dotenv import load_dotenv
from supabase import create_client
import os

# Load variables from .env
load_dotenv()

# Get Supabase information from .env
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")

# Connect to Supabase
supabase = create_client(supabase_url, supabase_key)

# Read one record from Marina's knowledge base
response = (
    supabase.table("knowledge_items")
    .select("category, topic, content")
    .limit(1)
    .execute()
)

print(response.data)