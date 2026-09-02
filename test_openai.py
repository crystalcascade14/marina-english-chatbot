from dotenv import load_dotenv
from openai import OpenAI

# Load variables from the .env file
load_dotenv()

# Create the OpenAI client
client = OpenAI()

# Send a simple test request
response = client.responses.create(
    model="gpt-5-mini",
    input="Say: The Marina English Chatbot is connected to OpenAI!"
)

print(response.output_text)