# 🐍 Project Onboarding Chatbot — Python Edition

The Python implementation of the workshop RAG application, built with **LangChain**, **FAISS** and **Streamlit**, using **Ollama** for both embeddings and generation.

> 📖 **Start with the [main README](../README.md)**. It explains RAG, the architecture, the tuning parameters, model sizing, Ollama setup and the demo script shared by both editions. This page only covers what is specific to Python.
>
> Prefer Java? See the [Spring + LangChain4j edition](../spring/README.md).

---

## Tech Stack

| Concern | Library |
|---|---|
| UI | Streamlit |
| Document loading | pypdf (PDF), python-docx (DOCX), BeautifulSoup (Confluence MHTML), LangChain `WebBaseLoader` (URLs) |
| Chunking | `langchain-text-splitters` → `RecursiveCharacterTextSplitter` |
| Embeddings & LLM | `langchain-ollama` → `OllamaEmbeddings`, `ChatOllama` |
| Vector store | FAISS (`faiss-cpu`) persisted to `data/vector_store/` |
| Configuration | `python-dotenv` reading `.env` |

---

## Prerequisites

In addition to the [common prerequisites](../README.md#6-common-setup-both-editions):

* **Python 3.11+** available in your terminal (`python --version`).

For common Windows setup issues (path length, activation policy, PATH warnings), see [README-QA.md](README-QA.md).

---

## Setup

Make sure you have completed the [common setup](../README.md#6-common-setup-both-editions) (clone the repo, install Ollama, pull models). Then:

```bash
cd python

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create your local environment file
cp .env.example .env    # Linux / macOS
Copy-Item .env.example .env  # Windows PowerShell
```

### Configure `.env`

Open `python/.env` and set your selected models (all variables are described in the [main README](../README.md#shared-env-settings)):

```env
MODEL_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

TOP_K=4
CHUNK_SIZE=800
CHUNK_OVERLAP=100
VECTOR_STORE_PATH=data/vector_store
ALLOW_PRIVATE_URLS=false
```

---

## Running the Application

From the `python/` folder:

```bash
streamlit run app.py
```

Streamlit opens http://localhost:8501. Follow the [demo walkthrough](../README.md#8-using-the-application-both-editions).

> Run commands from inside `python/`: uploaded files and the FAISS index are stored in `python/data/` relative to the working directory.

---

## Running the Tests

The tests are fast and do not need Ollama:

```bash
python -m pytest -q
```

---

## Codebase Structure

```text
python/
├── app.py                 # Streamlit UI interface & chat interaction
├── config.py              # Environment configuration & parameter validation
├── loaders.py             # Robust loaders for PDF, DOCX, Confluence MHTML & URLs
├── providers.py           # Ollama-only model abstraction layer
├── rag.py                 # Core RAG pipeline: chunking, embedding, FAISS index, prompt assembly
├── requirements.txt       # Pinned Python dependencies
├── .env.example           # Configuration template (copy to .env)
├── data/                  # Local storage for uploaded files and FAISS vector index
├── examples/              # Sample onboarding documentation
├── tests/                 # Fast, provider-independent unit tests
└── README-QA.md           # Windows setup troubleshooting
```

### Python-specific notes

* **FAISS persistence:** FAISS saves `index.faiss` plus an `index.pkl` metadata file. Loading it requires `allow_dangerous_deserialization=True` because the metadata is pickled — only ever load an index you created yourself, never one downloaded from elsewhere.
* **Switching embedding models:** delete `python/data/vector_store/` and rebuild the knowledge base.
