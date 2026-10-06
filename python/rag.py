"""The complete, intentionally small RAG workflow."""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings
from providers import get_embeddings, get_llm

FALLBACK_ANSWER = "I could not find that information in the project documentation."


def split_documents(documents: list[Document]) -> list[Document]:
    """Split documents so retrieval can select only the relevant information."""
    # Overlap keeps ideas near a chunk boundary from being separated completely.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return text_splitter.split_documents(documents)


def create_vector_store(chunks: list[Document]) -> FAISS:
    """Convert chunks to vectors and persist the searchable FAISS index."""
    if not chunks:
        raise ValueError("No document text was found to add to the knowledge base.")

    # Embeddings let us compare meaning instead of only matching exact words.
    embeddings = get_embeddings()
    index_file = Path(settings.vector_store_path) / "index.faiss"
    if index_file.exists():
        vector_store = FAISS.load_local(
            settings.vector_store_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        vector_store.add_documents(chunks)
    else:
        vector_store = FAISS.from_documents(chunks, embeddings)

    Path(settings.vector_store_path).mkdir(parents=True, exist_ok=True)
    vector_store.save_local(settings.vector_store_path)
    return vector_store


def load_vector_store() -> FAISS:
    """Open the locally persisted knowledge base."""
    index_file = Path(settings.vector_store_path) / "index.faiss"
    if not index_file.exists():
        raise FileNotFoundError(
            "No knowledge base exists yet. Ingest a document or URL first."
        )

    # FAISS stores document metadata beside the index. Only load this local,
    # workshop-created file; never replace it with an untrusted download.
    return FAISS.load_local(
        settings.vector_store_path,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def build_prompt(context: str, question: str) -> str:
    """Keep the teaching prompt visible and easy to experiment with."""
    return f"""You are a project onboarding assistant.

Answer the user's question using ONLY the provided context.

If the answer cannot be found in the context, say:
"{FALLBACK_ANSWER}"

Context:
{context}

Question:
{question}
"""


def answer_question(question: str) -> tuple[str, list[Document]]:
    """Retrieve context first, then ask the selected LLM for an answer."""
    if not question.strip():
        raise ValueError("Enter a question about the project.")

    vector_store = load_vector_store()
    # Retrieve relevant chunks before asking the LLM, which limits its context.
    retrieved_docs = vector_store.similarity_search(question, k=settings.top_k)
    context = "\n\n---\n\n".join(
        document.page_content for document in retrieved_docs
    )
    response = get_llm().invoke(build_prompt(context, question))
    answer = response.content if hasattr(response, "content") else str(response)
    return answer, retrieved_docs
