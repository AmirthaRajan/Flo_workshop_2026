"""Streamlit interface for the Project Onboarding RAG workshop."""

import streamlit as st

from config import settings
from loaders import load_file, load_url, save_uploaded_file
from rag import answer_question, create_vector_store, reset_vector_store, split_documents

st.set_page_config(page_title="Project Onboarding Chatbot", page_icon="📚")
st.title("📚 Project Onboarding Chatbot")
st.caption("A small RAG application for the 45-minute workshop")

st.header("1. Configuration")
col1, col2 = st.columns(2)
col1.metric("LLM Provider", settings.model_provider.title())
col2.metric("Embedding Provider", settings.embedding_provider.title())

st.header("2. Knowledge ingestion")
uploaded_files = st.file_uploader(
    "Upload PDF or DOCX files",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)
url = st.text_input("Web or accessible wiki / Confluence URL (optional)")

if st.button("Build / Update Knowledge Base", type="primary"):
    try:
        with st.status("Building knowledge base...") as status:
            status.write("Loading documents...")
            documents = []
            for uploaded_file in uploaded_files:
                documents.extend(load_file(save_uploaded_file(uploaded_file)))
            if url.strip():
                documents.extend(load_url(url.strip()))
            if not documents:
                raise ValueError("Upload a document or enter a URL first.")

            status.write("Creating chunks...")
            chunks = split_documents(documents)
            status.write("Generating embeddings and building vector store...")
            create_vector_store(chunks)
            status.update(label="Knowledge base ready.", state="complete")
        st.success(f"Stored {len(chunks)} searchable chunks.")
    except Exception as error:
        st.error(
            f"Could not build the knowledge base: {error}\n\n"
            "Check your model settings and make sure Ollama is running."
        )

if st.button("Reset Knowledge Base", type="secondary"):
    try:
        reset_vector_store()
        st.success("Knowledge base reset. Build again to load fresh documents.")
    except Exception as error:
        st.error(f"Could not reset the knowledge base: {error}")

st.header("3. Chat")
question = st.text_input(
    "Ask a question about the project",
    placeholder="How do I set up the local development environment?",
)

if st.button("Ask"):
    try:
        with st.spinner("Retrieving context and generating an answer..."):
            answer, retrieved_docs = answer_question(question)

        st.subheader("Answer")
        st.write(answer)

        st.subheader("Sources")
        for number, document in enumerate(retrieved_docs, start=1):
            source = document.metadata.get("source", "Unknown source")
            page = document.metadata.get("page")
            st.write(f"{number}. {source}" + (f" — page {page}" if page else ""))

        with st.expander("Retrieved Context"):
            for number, document in enumerate(retrieved_docs, start=1):
                st.markdown(f"**Chunk {number}**")
                st.write(document.page_content)
    except Exception as error:
        st.error(
            f"Could not answer the question: {error}\n\n"
            "Build the knowledge base and check that the selected model is available."
        )
