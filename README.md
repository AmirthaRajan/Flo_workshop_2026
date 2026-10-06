# Building Your First RAG Application
## Project Onboarding Chatbot

A step-by-step, interactive guide to building and running a local Retrieval-Augmented Generation (RAG) application that answers questions directly from project PDFs, Word documents, web pages, and accessible internal documentation.

---

## 1. What We Are Building

When new members join a project, they face a common pain point: **information fragmentation**. Architecture diagrams, setup procedures, API specs, and team guidelines are scattered across PDFs, Word documents, and wikis.

This application provides a unified assistant that:
1. **Ingests** private team documents securely on your machine.
2. **Indexes** and creates vector embeddings of those documents.
3. **Retrieves** the most relevant excerpts when you ask a question.
4. **Generates** an accurate, grounded answer backed by verifiable source citations.

It runs **100% locally and offline** using **Ollama**.

---

## 2. What is RAG? (The Open-Book Analogy)

Think of standard LLMs versus RAG like an exam:

* **Standard LLM (Closed-Book Exam):** The model relies solely on knowledge memorized during its training cutoff. It knows nothing about your company's proprietary code, internal repos, or private designs—and may hallucinate plausible-sounding guesses.
* **RAG (Open-Book Exam):** When a user asks a question, the system first retrieves the exact relevant pages from your private knowledge base, places those facts directly into the prompt context, and asks the model to formulate an answer using only those facts.

> **Key Rule:** We do not retrain or fine-tune the model. We search first, inject the relevant facts into the prompt, and let the LLM synthesize the answer.

---

## 3. The Complete RAG Architecture

Follow the data flow from raw documents to final answer:

```text
 ┌────────────────────────────────────────────────────────┐
 │ 1. Ingestion Phase                                     │
 │                                                        │
 │  ┌─────────────────────┐                               │
 │  │  Knowledge Sources  │ (PDF, DOCX / MHTML, Web URL)  │
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │  Document Loaders   │ (Extract plain text & metadata│
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │    Text Chunking    │ (Recursive character split,   │
 │  │                     │  CHUNK_SIZE + CHUNK_OVERLAP)  │
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │  Embedding Model    │ (Converts text chunks into    │
 │  │                     │  high-dimensional vectors)    │
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │ Vector Store (FAISS)│ (Saved locally to disk)       │
 │  └─────────────────────┘                               │
 └────────────────────────────────────────────────────────┘

 ┌────────────────────────────────────────────────────────┐
 │ 2. Query & Generation Phase                            │
 │                                                        │
 │      User Question                                     │
 │             │                                          │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │  Question Embedding │ (Uses the SAME embedding model│
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │  Similarity Search  │ (Cosine/L2 distance in FAISS; │
 │  │                     │  fetches TOP_K chunks)        │
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │  Retrieved Context  │ (Top matching excerpts)       │
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │   Prompt Assembly   │ (Combines System Instructions │
 │  │                     │  + Context + User Question)   │
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │  ┌─────────────────────┐                               │
 │  │   LLM Generation    │ (Synthesizes factual answer)  │
 │  └──────────┬──────────┘                               │
 │             ▼                                          │
 │     Answer & Citations                                 │
 └────────────────────────────────────────────────────────┘
```

### The 8 Steps Behind the Code

1. **Document Loading (`loaders.py`):** Reads files (PDF, DOCX, Confluence MHTML exports) and extracts clean text with source metadata.
2. **Text Chunking (`rag.py`):** Splits long documents into manageable chunks (default: 800 characters) with overlap (100 characters) to avoid splitting sentences or thoughts in half.
3. **Embedding Generation (`providers.py`):** Passes chunks through an embedding model (`nomic-embed-text`) which maps semantic meaning into numbers (vectors).
4. **Vector Storage (`rag.py`):** Indexes the vectors inside a local FAISS index on disk (`data/vector_store`).
5. **Query Embedding:** Converts incoming user questions into vector representations using the identical embedding model.
6. **Vector Search:** Performs fast similarity search against FAISS to retrieve the top $K$ most semantically relevant text chunks.
7. **Prompt Injection:** Injects the retrieved chunks directly into a prompt template alongside the user question.
8. **LLM Generation:** The LLM produces a concise, accurate answer strictly grounded in the provided context.

---

## 4. Key Concepts & Tuning Parameters

When configuring a RAG pipeline, you control three primary knobs in `.env`:

* **`CHUNK_SIZE` (e.g., 800):** How many characters each document chunk contains.
  * *Too small:* Loses context, sentences get fragmented.
  * *Too large:* Retrieves diluted information, exceeds prompt limits, or distracts the LLM.
* **`CHUNK_OVERLAP` (e.g., 100):** The number of characters shared between adjacent chunks. This prevents losing critical context that falls right on a boundary.
* **`TOP_K` (e.g., 4):** How many top matching chunks are retrieved and passed to the LLM.

---

## 5. Hardware Specifications & Ollama Model Sizing

Different team members have different computers (laptops with integrated graphics vs. workstations with dedicated GPUs). Ollama allows you to pick the model size that best matches your machine:

| Machine Spec | Recommended LLM | Download Size | RAM / VRAM | Real-World Performance & Trade-off |
|---|---|---|---|---|
| **Entry / Standard Laptop**<br>*(Intel/M-series/AMD, integrated graphics)* | `llama3.2:3b` | ~2.0 GB | 8 GB System RAM | **Lightweight & Fast:** Downloads in 1–2 minutes; responsive even without a dedicated GPU. |
| **Mid-range / Workstation**<br>*(16 GB+ RAM or 6–8 GB VRAM GPU)* | `llama3.1:8b` or `qwen2.5:7b`<br>*(Sweet Spot)* | ~4.7 GB | 16 GB RAM or 6 GB+ VRAM | **Best Balance:** Fits 100% inside modern GPU VRAM for near-instant responses (~30–50 tokens/sec) and strong reasoning. |
| **High-end / Enthusiast**<br>*(32 GB–64 GB RAM + 10 GB+ GPU)* | `qwen2.5:32b` | ~19 GB | 32 GB–64 GB RAM / 10 GB+ VRAM | **Deepest Technical Reasoning:** Unmatched comprehension of dense architecture & technical documents; splits layers between GPU and system RAM (~6–12 tokens/sec). |

> **Universal Embedding Model:** `nomic-embed-text` (~274 MB) is lightweight, highly accurate for retrieval, and runs smoothly on all machines.

---

## 6. Setup & Installation

### Prerequisites (Before You Start)

Make sure each attendee has the following ready:

1. **OS:** Windows 10/11, macOS, or Linux.
2. **Python:** Python 3.11+ installed and available in terminal (`python --version`).
3. **Git:** Installed for cloning the repository.
4. **Ollama:** Installed and running locally (for default offline setup).
5. **Disk space:** At least 8 GB free (dependencies + model downloads).
6. **Network access:** Internet access to install packages and pull models.
7. **Local Ollama setup:** The LLM and embedding model are both served locally via Ollama.

For common Windows setup issues (path length, activation policy, PATH warnings), see [README-QA.md](README-QA.md).

### Step 1: Clone the Repository & Setup Environment

```bash
git clone https://github.com/AmirthaRajan/Flo_workshop_2026.git
cd Flo_workshop_2026

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

### Step 2: Download Ollama & Pull Your Models

1. Download and start [Ollama](https://ollama.com/download).
2. Pull the embedding model and the LLM that fits your hardware:

```bash
# Recommended default (the sweet spot):
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Or for lightweight laptops:
ollama pull llama3.2
ollama pull nomic-embed-text

# Or for high-end workstations:
ollama pull qwen2.5:32b
ollama pull nomic-embed-text
```

### Step 3: Configure `.env`

Open your local `.env` file and set your selected models:

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

## 7. Ollama-only Provider Architecture

The project is intentionally configured to use the same local stack for both embeddings and generation:

| Setup Configuration | `EMBEDDING_PROVIDER` | `MODEL_PROVIDER` | Description |
|---|---|---|---|
| **Fully Local (Default)** | `ollama` | `ollama` | 100% private, zero API costs, runs offline. |

> **Important Rule of Embeddings:** You must use the **exact same** embedding model to query an index that was used to create it. If you switch `OLLAMA_EMBEDDING_MODEL`, delete `data/vector_store/` and rebuild the knowledge base.

---

## 8. Running the Application

Launch the Streamlit web application:

```bash
streamlit run app.py
```

### How to Demo Step-by-Step:

1. **Verify Configuration:** Check the **LLM Provider** and **Embedding Provider** status cards at the top of the interface.
2. **Ingest Documents:**
   * Drop sample project documents (e.g., PDFs, Word architecture designs, or Confluence `.docx` exports) into the file uploader.
   * Or provide an accessible documentation URL.
   * Click **Build / Update Knowledge Base**. Watch the status steps: *Loading documents &rarr; Creating chunks &rarr; Generating embeddings & building vector store*.
3. **Ask a Question:**
   * Submit an onboarding question (e.g., *"How do I set up the local development environment?"* or *"What is the database migration strategy?"*).
4. **Inspect Results & Citations:**
   * Examine the synthesized **Answer**.
   * Review the **Sources** list showing exact file origins and page numbers.
   * Expand **Retrieved Context** to view the exact text chunks passed to the LLM prompt.

---

## 9. Live Demonstrations & Experiments

Try these live adjustments during your walkthrough:

1. **Context Inspection:** Open the *Retrieved Context* expander in Streamlit to show that the LLM is genuinely reading the retrieved chunks, not guessing.
2. **Handling Unanswerable Questions:** Ask a question that isn't mentioned anywhere in the uploaded docs (e.g., *"What is the company cafeteria menu?"*). Observe how the system admits it does not know rather than fabricating details.
3. **Chunk Boundary Tuning:** In `.env`, change `CHUNK_SIZE=200` vs `CHUNK_SIZE=1200` to show how chunk granularity affects search relevance.
4. **Instant Model Swapping:** Change `OLLAMA_LLM_MODEL` in `.env` from `llama3.2` to `qwen2.5:32b` or `llama3.1:8b` to compare response depth and speed without needing to re-index the documents.

---

## 10. Codebase Structure

```text
├── app.py                 # Streamlit UI interface & chat interaction
├── config.py              # Environment configuration & parameter validation
├── loaders.py             # Robust loaders for PDF, DOCX, Confluence MHTML & URLs
├── providers.py           # Ollama-only model abstraction layer
├── rag.py                 # Core RAG pipeline: chunking, embedding, FAISS index, prompt assembly
├── data/                  # Local storage for uploaded files and FAISS vector index
├── examples/              # Sample onboarding documentation
└── tests/                 # Fast, provider-independent unit tests
```

---

## 11. Production Considerations & Next Steps

This repository is designed to teach the fundamentals of RAG clearly and transparently. Moving from this baseline to a full production enterprise system involves:

* **Persistent Document Stores:** Replacing local FAISS files with scalable vector databases (Qdrant, Milvus, pgvector).
* **Advanced Retrieval:** Adding hybrid search (BM25 keyword search + dense vector retrieval) and cross-encoder rerankers (Cohere Rerank, BGE-reranker).
* **Access Control & Auth:** Integrating enterprise role-based permissions (RBAC) so users only retrieve documents they are authorized to see.
* **Conversational Memory:** Storing session history to support multi-turn dialogue and follow-up clarifications.
* **Evaluation Frameworks:** Continuous evaluation of retrieval precision and generation faithfulness using frameworks like Ragas or TruLens.