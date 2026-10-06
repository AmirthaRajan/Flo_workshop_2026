"""Choose Ollama models for the RAG pipeline."""

from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import settings


def _required(value: str, variable_name: str) -> str:
    if not value or value.startswith("<"):
        raise ValueError(f"Set {variable_name} in your .env file.")
    return value


def get_embeddings():
    """Return the configured Ollama embedding model."""
    model = _required(settings.ollama_embedding_model, "OLLAMA_EMBEDDING_MODEL")
    return OllamaEmbeddings(model=model, base_url=settings.ollama_base_url)


def get_llm():
    """Return the configured Ollama chat model."""
    model = _required(settings.ollama_llm_model, "OLLAMA_LLM_MODEL")
    return ChatOllama(
        model=model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )
