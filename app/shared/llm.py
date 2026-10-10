import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

model_name = "openai/gpt-4.1-mini"
# model_name = "qwen/qwen3.8-27b"

llm = LiteLlm(
    model=f"openrouter/{model_name}",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    api_base="https://openrouter.ai/api/v1",
)
