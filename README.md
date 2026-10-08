# Building Your First RAG Application
## Project Onboarding Chatbot

A step-by-step, interactive guide to building and running a local Retrieval-Augmented Generation (RAG) application that answers questions directly from project PDFs, Word documents, web pages, and accessible internal documentation.

The same application is implemented twice so you can follow the workshop in the stack you are most comfortable with. Both use the **LangChain** family of libraries: [LangChain](https://python.langchain.com/) in Python and its Java counterpart [LangChain4j](https://docs.langchain4j.dev/) in Spring, so the concepts and names match.

| Edition | Folder | Stack | Start here |
|---|---|---|---|
| 🐍 **Python** | [`python/`](python/) | LangChain · FAISS · Streamlit | [python/README.md](python/README.md) |
| 🍃 **Java / Spring** | [`spring/`](spring/) | Spring Boot · LangChain4j · Thymeleaf | [spring/README.md](spring/README.md) |
| **Langflow visual workshop** | [`langflow/`](langflow/) | Langflow · Ollama · Chroma | [langflow/README.md](langflow/README.md) |

The [Langflow workshop project](langflow/README.md) includes importable
drag-and-drop ingestion and chat flows with separate Split Text, Ollama
Embeddings and local Chroma components. It is a Markdown-based teaching
edition, not a full migration of the original applications' specialized loaders.

This README covers everything **both editions share**: the concepts, architecture, configuration knobs, model sizing, Ollama setup and demo script. Each edition's README only covers installing, running and testing that edition.

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
 │  │    Vector Store     │ (Saved locally to disk)       │
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
 │  │  Similarity Search  │ (Vector distance search;      │
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

1. **Document Loading:** Reads files (PDF, DOCX, Confluence MHTML exports) and web pages, extracting clean text with source metadata (file name, page number, URL).
2. **Text Chunking:** Splits long documents into manageable chunks (default: 800 characters) with overlap (100 characters) to avoid splitting sentences or thoughts in half.
3. **Embedding Generation:** Passes chunks through an embedding model (`nomic-embed-text`) which maps semantic meaning into numbers (vectors).
4. **Vector Storage:** Indexes the vectors in a local vector store on disk (`data/vector_store`).
5. **Query Embedding:** Converts incoming user questions into vector representations using the identical embedding model.
6. **Vector Search:** Performs a similarity search against the vector store to retrieve the top $K$ most semantically relevant text chunks.
7. **Prompt Injection:** Injects the retrieved chunks directly into a prompt template alongside the user question.
8. **LLM Generation:** The LLM produces a concise, accurate answer strictly grounded in the provided context.

### How each step maps to code

Both editions are deliberately structured the same way, file for file, and use the equivalent LangChain / LangChain4j building blocks:

| Step | Responsibility | 🐍 Python (`python/`) | 🍃 Spring (`spring/src/main/java/com/flo/workshop/`) |
|---|---|---|---|
| — | Configuration & validation | `config.py` (python-dotenv) | `WorkshopSettings.java` + `application.properties` |
| 1 | Document loading (PDF, DOCX, MHTML, URL) | `loaders.py` → pypdf, python-docx, BeautifulSoup, `WebBaseLoader` | `DocumentLoaders.java` → `FileSystemDocumentLoader` + `ApacheTikaDocumentParser`, `HtmlToTextDocumentTransformer` |
| 2 | Chunking | `rag.py` → `RecursiveCharacterTextSplitter` | `RagService.java` → `DocumentSplitters.recursive` |
| 3, 5 | Embeddings & LLM | `providers.py` → `OllamaEmbeddings` / `ChatOllama` | `application.properties` → `OllamaEmbeddingModel` / `OllamaChatModel` auto-configured by the LangChain4j Spring Boot starter |
| 4, 6 | Vector store & search | `rag.py` → `FAISS` (`index.faiss` + `index.pkl`) | `RagService.java` → `InMemoryEmbeddingStore` (`vector_store.json`) |
| 7, 8 | Prompt & generation | `rag.py` → `build_prompt`, `answer_question` | `RagService.java` → `PromptTemplate`, `buildPrompt`, `answerQuestion` |
| — | User interface | `app.py` (Streamlit) | `OnboardingController.java` + `templates/index.html` (Thymeleaf) |
| — | Tests (no Ollama needed) | `tests/test_workshop.py` | `src/test/java/.../WorkshopTests.java` |

The prompt template and the fallback answer (*"I could not find that information in the project documentation."*) are identical in both editions.

---

## 4. Key Concepts & Tuning Parameters

When configuring a RAG pipeline, you control three primary knobs in the `.env` file of the edition you are running:

* **`CHUNK_SIZE` (e.g., 800):** How many characters each document chunk contains.
  * *Too small:* Loses context, sentences get fragmented.
  * *Too large:* Retrieves diluted information, exceeds prompt limits, or distracts the LLM.
* **`CHUNK_OVERLAP` (e.g., 100):** The number of characters shared between adjacent chunks. This prevents losing critical context that falls right on a boundary. Must be smaller than `CHUNK_SIZE`.
* **`TOP_K` (e.g., 4):** How many top matching chunks are retrieved and passed to the LLM.

### Shared `.env` settings

Both editions read the **same variable names** from a `.env` file in their own folder (copy `.env.example` to `.env`):

| Variable | Default | Purpose |
|---|---|---|
| `MODEL_PROVIDER` | `ollama` | LLM provider (only `ollama` is supported) |
| `EMBEDDING_PROVIDER` | `ollama` | Embedding provider (only `ollama` is supported) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is listening |
| `OLLAMA_LLM_MODEL` | *(required)* | Chat model, e.g. `llama3.1:8b` |
| `OLLAMA_EMBEDDING_MODEL` | *(required)* | Embedding model, e.g. `nomic-embed-text` |
| `TOP_K` | `4` | Chunks retrieved per question |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `CHUNK_OVERLAP` | `100` | Characters shared between chunks |
| `VECTOR_STORE_PATH` | `data/vector_store` | Where the index is persisted |
| `ALLOW_PRIVATE_URLS` | `false` | Allow loading URLs that resolve to private/internal IPs (only for a trusted internal wiki) |

Each edition's README lists any extra, edition-specific settings.

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

## 6. Common Setup (Both Editions)

### Prerequisites

1. **OS:** Windows 10/11, macOS, or Linux.
2. **Git:** Installed for cloning the repository.
3. **Ollama:** Installed and running locally.
4. **Disk space:** At least 8 GB free (dependencies + model downloads).
5. **Network access:** Internet access to install packages and pull models.
6. **Language runtime:** Python 3.11+ **or** Java 17+ — see the edition README.

### Step 1: Clone the repository

```bash
git clone https://github.com/AmirthaRajan/Flo_workshop_2026.git
cd Flo_workshop_2026
```

### Step 2: Download Ollama & pull your models

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

### Step 3: Continue with your edition

* 🐍 Python → [python/README.md](python/README.md)
* 🍃 Spring + LangChain4j → [spring/README.md](spring/README.md)

---

## 7. Ollama-only Provider Architecture

The project is intentionally configured to use the same local stack for both embeddings and generation:

| Setup Configuration | `EMBEDDING_PROVIDER` | `MODEL_PROVIDER` | Description |
|---|---|---|---|
| **Fully Local (Default)** | `ollama` | `ollama` | 100% private, zero API costs, runs offline. |

> **Important Rule of Embeddings:** You must use the **exact same** embedding model to query an index that was used to create it. If you switch `OLLAMA_EMBEDDING_MODEL`, delete that edition's `data/vector_store/` folder and rebuild the knowledge base.

The two editions keep **separate** `data/` folders and use different index formats (FAISS vs. JSON), so a knowledge base built in one edition is not visible to the other.

---

## 8. Using the Application (Both Editions)

Both UIs have the same three sections:

1. **Configuration:** Check the **LLM Provider** and **Embedding Provider** status cards at the top of the interface.
2. **Knowledge ingestion:**
   * Drop sample project documents (e.g., PDFs, Word architecture designs, or Confluence `.docx` exports) into the file uploader.
   * Or provide an accessible documentation URL.
   * Click **Build / Update Knowledge Base**. Watch the status steps: *Loading documents &rarr; Creating chunks &rarr; Generating embeddings & building vector store*.
3. **Chat:**
   * Submit an onboarding question (e.g., *"How do I set up the local development environment?"* or *"What is the database migration strategy?"*).
   * Examine the synthesized **Answer**.
   * Review the **Sources** list showing exact file origins (the Python edition also shows PDF page numbers).
   * Expand **Retrieved Context** to view the exact text chunks passed to the LLM prompt.

A small sample document is provided in each edition's `examples/` folder.

---

## 9. Live Demonstrations & Experiments

Try these live adjustments during your walkthrough:

1. **Context Inspection:** Open the *Retrieved Context* section to show that the LLM is genuinely reading the retrieved chunks, not guessing.
2. **Handling Unanswerable Questions:** Ask a question that isn't mentioned anywhere in the uploaded docs (e.g., *"What is the company cafeteria menu?"*). Observe how the system admits it does not know rather than fabricating details.
3. **Chunk Boundary Tuning:** In `.env`, change `CHUNK_SIZE=200` vs `CHUNK_SIZE=1200` (delete `data/vector_store/` and re-ingest) to show how chunk granularity affects search relevance.
4. **Instant Model Swapping:** Change `OLLAMA_LLM_MODEL` in `.env` from `llama3.2` to `qwen2.5:32b` or `llama3.1:8b` to compare response depth and speed without needing to re-index the documents.
5. **Same pipeline, two stacks:** Run both editions side by side (Streamlit on port 8501, Spring on port 8080) against the same documents and compare the answers.

---

## 10. Repository Structure

```text
├── README.md              # This file: shared concepts, architecture & setup
├── LICENSE
├── python/                # 🐍 Python edition (LangChain + FAISS + Streamlit)
│   ├── README.md          #    Python install / run / test guide
│   └── README-QA.md       #    Windows troubleshooting for Python
└── spring/                # 🍃 Spring edition (Spring Boot + LangChain4j + Thymeleaf)
    ├── README.md          #    Java install / run / test guide
    └── README-QA.md       #    Troubleshooting for Java / Maven
```

---

## 11. Production Considerations & Next Steps

This repository is designed to teach the fundamentals of RAG clearly and transparently. Moving from this baseline to a full production enterprise system involves:

* **Persistent Document Stores:** Replacing the local file-based vector stores (FAISS / LangChain4j `InMemoryEmbeddingStore`) with scalable vector databases (Qdrant, Milvus, pgvector). Both LangChain and LangChain4j ship integrations for these.
* **Advanced Retrieval:** Adding hybrid search (BM25 keyword search + dense vector retrieval) and cross-encoder rerankers (Cohere Rerank, BGE-reranker).
* **Access Control & Auth:** Integrating enterprise role-based permissions (RBAC) so users only retrieve documents they are authorized to see.
* **Conversational Memory:** Storing session history to support multi-turn dialogue and follow-up clarifications.
* **Evaluation Frameworks:** Continuous evaluation of retrieval precision and generation faithfulness using frameworks like Ragas or TruLens (Python) or LangChain4j-compatible tooling (Java).
