import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

model_name = "openai/gpt-4.1-mini"
# model_name = "qwen/qwen3.8-27b"

llm = LiteLlm(
    # Specify the OpenRouter model using 'openrouter/' prefix
    model=f"openrouter/{model_name}",
    # Explicitly provide the API key from environment variables
    api_key=os.getenv("OPENROUTER_API_KEY"),
    # Explicitly provide the OpenRouter API base URL
    api_base="https://openrouter.ai/api/v1",
)
