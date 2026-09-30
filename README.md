# Building Your First RAG Application
## Project Onboarding Chatbot

A beginner-friendly, 45-minute hands-on workshop. Build a small chatbot that
answers questions from project PDFs, Word documents, web pages, and accessible
wiki or Confluence pages.

## What we are building

New team members often search many documents before they can run a project or
understand a process. This Streamlit app lets you add project knowledge, ask a
question, and inspect both the answer and the source chunks used to create it.

The app runs locally with either:

- **Ollama** and open-source models (fully offline after models are downloaded)
- **OpenAI** as an optional API provider

## What is RAG?

Retrieval-Augmented Generation (RAG) is like an open-book exam:

> Instead of asking the LLM to remember everything, we first search the
> project's documentation, then give the relevant information to the LLM.

The LLM does not automatically know the project's private documentation. RAG
retrieves relevant project information first and gives that information to the
LLM as context.

## RAG architecture

```text
                ┌───────────────────┐
                │ Knowledge Sources │
                │ PDF / DOCX / Web  │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Document Loading  │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Text Chunking     │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Embeddings        │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Vector Store      │
                │       FAISS       │
                └─────────┬─────────┘
                          │
                    User Question
                          │
                          ▼
                ┌───────────────────┐
                │ Query Embedding   │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Similarity Search │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Retrieved Context │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Prompt + Context  │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ LLM Generation    │
                └─────────┬─────────┘
                          │
                          ▼
                      Final Answer
```

1. **Load documents** from PDF, DOCX, or a URL.
2. **Split documents into chunks** so we do not send every page to the LLM.
3. **Convert chunks into embeddings** (numbers representing meaning).
4. **Store embeddings in FAISS**, a local vector database.
5. **Convert the user's question into an embedding** with the same model.
6. **Retrieve the most relevant chunks** using vector similarity.
7. **Put the retrieved chunks into a prompt** as context.
8. **Ask the LLM to generate the answer** using only that context.

Open `rag.py` to see these steps without an agent framework or hidden chain.

## Learning objectives

By the end, you should understand:

- what embeddings represent and what vector search does
- why chunking and overlap are useful
- how retrieval selects context for an LLM
- why RAG helps with private or project-specific knowledge
- how generation and embedding providers can be switched independently

## Prerequisites

- Python 3.11 or newer
- [Ollama](https://ollama.com/download) for local mode
- an Ollama chat model and embedding model that fit your machine
- optionally, an OpenAI API key for OpenAI mode

No OpenAI account is required. Ollama models vary in size and hardware needs,
so choose compatible models from the Ollama library rather than treating one
model as mandatory.

## Installation

```bash
git clone https://github.com/AmirthaRajan/Flo_workshop_2026.git
cd Flo_workshop_2026
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

Edit `.env` before starting the app.

## Ollama setup (offline mode)

Install Ollama, start it if your operating system does not start it
automatically, and choose suitable models:

```bash
ollama pull <llm-model>
ollama pull <embedding-model>
```

Then configure their exact names:

```env
MODEL_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=<llm-model>
OLLAMA_EMBEDDING_MODEL=<embedding-model>
```

After downloading the models, document ingestion and chat can run without an
internet connection.

## OpenAI setup (optional)

Never commit a real API key. Put it only in your ignored `.env` file:

```env
MODEL_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=<your-key>
OPENAI_LLM_MODEL=<configured-model>
OPENAI_EMBEDDING_MODEL=<configured-model>
```

OpenAI is contacted only for the stage(s) where it is selected.

## Provider switching

`get_embeddings()` and `get_llm()` in `providers.py` are the only provider
selection functions. The RAG pipeline does not change.

| Experiment | `EMBEDDING_PROVIDER` | `MODEL_PROVIDER` |
|---|---|---|
| Fully local | `ollama` | `ollama` |
| Local retrieval, API answer | `ollama` | `openai` |
| API retrieval, local answer | `openai` | `ollama` |
| Fully OpenAI | `openai` | `openai` |

The same embedding model must be used to create and search an index. When
changing the embedding provider or model, delete the contents of
`data/vector_store/` and rebuild it. The generation model can change without
rebuilding.

## Running the application

```bash
streamlit run app.py
```

1. Confirm the two providers shown in **Configuration**.
2. Upload PDF/DOCX files or enter an accessible URL.
3. Select **Build / Update Knowledge Base**. New chunks are added to local
   `data/vector_store/`.
4. Ask a question and inspect **Sources** and **Retrieved Context**.

The simple URL loader works for public documentation and wiki-style pages.
Authenticated/private Confluence pages may require a separate authenticated
integration, which is intentionally outside this workshop. Private network URLs
are blocked by default; for a trusted internal wiki, set
`ALLOW_PRIVATE_URLS=true`. Do not enable this when exposing the app to untrusted
users.

## 45-minute hands-on flow

| Time | Activity |
|---|---|
| 0–5 min | What is RAG? |
| 5–10 min | Follow the architecture from document to answer |
| 10–20 min | Load documents and change chunking settings |
| 20–30 min | Create embeddings and search the FAISS vectors |
| 30–38 min | Retrieve context, inspect the prompt, and call the LLM |
| 38–45 min | Switch Ollama/OpenAI providers and experiment |

## Experiment ideas

- Change `CHUNK_SIZE` from `800`.
- Change `CHUNK_OVERLAP` and observe boundary context.
- Change `TOP_K` and inspect how many chunks are retrieved.
- Switch only the embedding provider or only the LLM provider.
- Try another Ollama model suitable for your machine.
- Ask a question whose answer is not in the documents.
- Edit the visible prompt in `rag.py`.

## Project structure

```text
├── app.py                 # Streamlit UI
├── config.py              # Environment settings
├── loaders.py             # PDF, DOCX, and URL loading
├── providers.py           # Ollama/OpenAI selection
├── rag.py                 # Chunk, embed, retrieve, prompt, answer
├── data/                  # Uploaded files and local FAISS index
├── examples/              # Sample onboarding content
└── tests/                 # Small, provider-free unit tests
```

## Limitations

This teaching demo is not a production enterprise RAG system. It has basic
document parsing and similarity search, local FAISS storage, no authentication,
no advanced reranking, no chat memory, no agents, no hybrid search, no
evaluation framework, and no enterprise Confluence authentication. Re-ingesting
the same source can add duplicate chunks.

Only load a FAISS index created locally by this application; its metadata format
is not safe for untrusted downloaded indexes.

## RAG checklist

- [ ] Load documents
- [ ] Split documents
- [ ] Create embeddings
- [ ] Store vectors
- [ ] Embed user question
- [ ] Retrieve relevant chunks
- [ ] Build context
- [ ] Generate answer
- [ ] Inspect sources