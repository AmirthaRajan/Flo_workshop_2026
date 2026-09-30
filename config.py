"""Small, environment-based settings for the workshop."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _number(name: str, default: int) -> int:
    """Read a positive integer while keeping configuration errors friendly."""
    value = int(os.getenv(name, default))
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    model_provider: str = os.getenv("MODEL_PROVIDER", "ollama").lower()
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_llm_model: str = os.getenv("OLLAMA_LLM_MODEL", "")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_llm_model: str = os.getenv("OPENAI_LLM_MODEL", "")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "")
    top_k: int = _number("TOP_K", 4)
    chunk_size: int = _number("CHUNK_SIZE", 800)
    chunk_overlap: int = _number("CHUNK_OVERLAP", 100)
    vector_store_path: str = os.getenv("VECTOR_STORE_PATH", "data/vector_store")
    allow_private_urls: bool = _flag("ALLOW_PRIVATE_URLS")

    def __post_init__(self) -> None:
        supported = {"ollama", "openai"}
        if self.model_provider not in supported:
            raise ValueError("MODEL_PROVIDER must be 'ollama' or 'openai'.")
        if self.embedding_provider not in supported:
            raise ValueError("EMBEDDING_PROVIDER must be 'ollama' or 'openai'.")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")


settings = Settings()
