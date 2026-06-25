from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

print("API Key Loaded:", os.getenv("OPENAI_API_KEY")[:15] + "...")

response = client.responses.create(
    model="gpt-5",
    input="Say Hello Vishal"
)

print(response.output_text)