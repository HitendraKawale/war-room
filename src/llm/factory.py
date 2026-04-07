from src.config import settings
from src.llm.base import LLMClient
from src.llm.ollama_client import OllamaClient
from src.llm.openai_client import OpenAIClient


def get_llm_client() -> LLMClient:
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        return OllamaClient()

    if provider == "openai":
        return OpenAIClient()

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
