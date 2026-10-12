
import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

model_name = os.getenv("MODEL_NAME")
provider = os.getenv("MODEL_PROVIDER")

PROVIDERS = [
    "gemini",
    "openroute",
    "ollama"
]

if not provider or not model_name:
    raise ValueError("Missing provider or model settings, check .env MODEL_PROVIDER and MODEL_NAME values")

if provider not in PROVIDERS:
    raise ValueError(f"Invalid {provider}. Supported providers are {", ".join(PROVIDERS)}")

if provider == "ollama":
    llm = LiteLlm(
        model=f"ollama_chat/{model_name}",
        api_base=os.getenv("OLLAMA_HOST")
        
    )
elif provider == "openroute":
    llm = LiteLlm(
        model=f"openrouter/{model_name}",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        api_base="https://openrouter.ai/api/v1",
    )
else:
    llm = model_name
