
import os

from dotenv import load_dotenv
from google.adk.models import Gemini
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

load_dotenv()

# Sem MODEL_PROVIDER/MODEL_NAME no .env, usa Gemini (basta preencher GEMINI_API_KEY).
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL_NAME = "gemini-3.8-flash"

provider = os.getenv("MODEL_PROVIDER") or DEFAULT_PROVIDER
model_name = os.getenv("MODEL_NAME") or DEFAULT_MODEL_NAME

PROVIDERS = [
    "gemini",
    "openroute",
    "ollama"
]

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
    # Sem retry_options o google-genai nao repete a chamada: um 429/503 passageiro virava 500 na API.
    # Repete com backoff exponencial (codigos padrao: 408, 429, 500, 502, 503, 504).
    llm = Gemini(
        model=model_name,
        retry_options=types.HttpRetryOptions(attempts=6, initial_delay=2, max_delay=30),
    )
