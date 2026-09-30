"""Choose model providers without changing the rest of the RAG pipeline."""

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import settings


def _required(value: str, variable_name: str) -> str:
    if not value or value.startswith("<"):
        raise ValueError(f"Set {variable_name} in your .env file.")
    return value


def get_embeddings():
    """Return the selected embedding model."""
    if settings.embedding_provider == "ollama":
        model = _required(
            settings.ollama_embedding_model, "OLLAMA_EMBEDDING_MODEL"
        )
        return OllamaEmbeddings(model=model, base_url=settings.ollama_base_url)

    _required(settings.openai_api_key, "OPENAI_API_KEY")
    model = _required(
        settings.openai_embedding_model, "OPENAI_EMBEDDING_MODEL"
    )
    return OpenAIEmbeddings(model=model, api_key=settings.openai_api_key)


def get_llm():
    """Return the selected chat model."""
    if settings.model_provider == "ollama":
        model = _required(settings.ollama_llm_model, "OLLAMA_LLM_MODEL")
        return ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )

    _required(settings.openai_api_key, "OPENAI_API_KEY")
    model = _required(settings.openai_llm_model, "OPENAI_LLM_MODEL")
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
