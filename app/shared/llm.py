
from dotenv import load_dotenv

load_dotenv()

# model_name = "openai/gpt-4.1-mini"
# model_name = "qwen/qwen3.8-27b"

# llm = LiteLlm(
#     model=f"openrouter/{model_name}",
#     api_key=os.getenv("OPENROUTER_API_KEY"),
#     api_base="https://openrouter.ai/api/v1",
# )

# llm = LiteLlm(
#     model="ollama_chat/gemma4:e2b"
# )

llm = "gemini-3.8-flash"
