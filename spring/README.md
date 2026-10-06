# 🍃 Project Onboarding Chatbot — Spring Boot + LangChain4j Edition

The Java implementation of the workshop RAG application, built with **Spring Boot 4**, the open-source **[LangChain4j](https://docs.langchain4j.dev/)** library (the Java counterpart of LangChain) and **Thymeleaf**, using **Ollama** for both embeddings and generation.

> 📖 **Start with the [main README](../README.md)**. It explains RAG, the architecture, the tuning parameters, model sizing, Ollama setup and the demo script shared by both editions. This page only covers what is specific to Spring.
>
> Prefer Python? See the [Python edition](../python/README.md).

---

## Tech Stack

Every RAG building block comes from LangChain4j and has a direct LangChain (Python) equivalent:

| Concern | 🍃 Spring + LangChain4j | 🐍 Python + LangChain |
|---|---|---|
| Web UI | Spring Boot Web MVC + Thymeleaf | Streamlit |
| Load files | `FileSystemDocumentLoader` + `ApacheTikaDocumentParser` (one parser for PDF, DOCX and Confluence MHTML) | pypdf, python-docx, BeautifulSoup |
| Load web pages | Jsoup + `HtmlToTextDocumentTransformer` | `WebBaseLoader` |
| Chunking | `DocumentSplitters.recursive(chunkSize, overlap)` | `RecursiveCharacterTextSplitter` |
| Embeddings & LLM | `OllamaEmbeddingModel`, `OllamaChatModel` (auto-configured by `langchain4j-ollama-spring-boot4-starter`) | `OllamaEmbeddings`, `ChatOllama` |
| Vector store | `InMemoryEmbeddingStore`, saved to `data/vector_store/vector_store.json` | FAISS |
| Prompt | `PromptTemplate` | f-string |
| Configuration | `application.properties` + `.env` via `spring.config.import` | `python-dotenv` |
| Build | Maven (wrapper included, no install needed) | pip |

---

## Prerequisites

In addition to the [common prerequisites](../README.md#6-common-setup-both-editions):

* **Java 17+** (JDK) available in your terminal (`java -version`). Any distribution works (Temurin, SapMachine, Microsoft, Oracle, ...).
* **Maven is not required.** The included Maven wrapper (`mvnw` / `mvnw.cmd`) downloads Maven 3.9 automatically on first use.

Troubleshooting for Java, Maven and Windows is in [README-QA.md](README-QA.md).

---

## Setup

Make sure you have completed the [common setup](../README.md#6-common-setup-both-editions) (clone the repo, install Ollama, pull models). Then:

```bash
cd spring

# Create your local environment file
cp .env.example .env          # Linux / macOS
Copy-Item .env.example .env   # Windows PowerShell
```

### Configure `.env`

Open `spring/.env` and set your selected models. It uses **the same variables as the Python edition** (described in the [main README](../README.md#shared-env-settings)), plus two optional Spring-only settings:

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

# Spring-only settings
DOCUMENTS_PATH=data/documents   # where uploaded files are saved
SERVER_PORT=8080                # HTTP port of the web UI
```

How configuration is resolved:

1. `src/main/resources/application.properties` imports `.env` from the **current working directory** (`spring.config.import=optional:file:.env[.properties]`).
2. The `OLLAMA_*` variables are mapped onto `langchain4j.ollama.chat-model.*` and `langchain4j.ollama.embedding-model.*`. The LangChain4j starter then creates the `ChatModel` and `EmbeddingModel` beans, so there is no model-wiring code.
3. The remaining variables are mapped onto `workshop.*` and validated at startup by `WorkshopSettings.java` (positive numbers, `ollama` providers, `CHUNK_OVERLAP < CHUNK_SIZE`).
4. Real environment variables override values in `.env`, just as with `python-dotenv`.

---

## Running the Application

From the `spring/` folder:

```bash
# macOS / Linux
./mvnw spring-boot:run

# Windows PowerShell
.\mvnw.cmd spring-boot:run
```

Open http://localhost:8080 and follow the [demo walkthrough](../README.md#8-using-the-application-both-editions).

> Run commands from inside `spring/`: `.env`, uploaded files and the vector store are resolved relative to the working directory.

### Building a runnable JAR (optional)

```bash
./mvnw clean package
java -jar target/rag-onboarding-chatbot-1.0.0.jar
```

---

## Running the Tests

The tests are fast and do not need Ollama (they use a fake embedding model). They mirror `python/tests/test_workshop.py`.

```bash
./mvnw test          # macOS / Linux
.\mvnw.cmd test      # Windows PowerShell
```

---

## Codebase Structure

```text
spring/
├── pom.xml                              # Maven build: Spring Boot 4 + LangChain4j
├── mvnw, mvnw.cmd, .mvn/                # Maven wrapper (no Maven install needed)
├── .env.example                         # Configuration template (copy to .env)
├── src/main/java/com/flo/workshop/
│   ├── RagWorkshopApplication.java      # Spring Boot entry point
│   ├── WorkshopSettings.java            # ≙ config.py    – validated workshop settings
│   ├── DocumentLoaders.java             # ≙ loaders.py   – files via Tika, web pages via Jsoup
│   ├── RagService.java                  # ≙ rag.py       – split, embed, store, retrieve, prompt, answer
│   └── OnboardingController.java        # ≙ app.py       – web endpoints
├── src/main/resources/
│   ├── application.properties           # ≙ providers.py – Ollama models + .env mapping
│   └── templates/index.html             # ≙ Streamlit page – Configuration / Ingestion / Chat
├── src/test/java/com/flo/workshop/      # Fast, provider-independent unit tests
├── data/                                # Uploaded files and the JSON vector store
├── examples/                            # Sample onboarding documentation
└── README-QA.md                         # Troubleshooting
```

### Walking through `RagService.java` in the workshop

The whole RAG pipeline fits in one short class, step for step with `rag.py`:

```java
// 2. Chunking
DocumentSplitters.recursive(chunkSize, chunkOverlap).splitAll(documents);

// 3 + 4. Embed chunks and store them
vectorStore.addAll(embeddingModel.embedAll(chunks).content(), chunks);
vectorStore.serializeToFile(indexFile());

// 5 + 6. Embed the question and retrieve the TOP_K closest chunks
vectorStore.search(EmbeddingSearchRequest.builder()
        .queryEmbedding(embeddingModel.embed(question).content())
        .maxResults(topK).build());

// 7 + 8. Fill the prompt template and ask the LLM
chatModel.chat(PROMPT.apply(Map.of("context", context, "question", question, ...)).text());
```

### Spring-specific notes

* **Why not `AiServices` / `EmbeddingStoreContentRetriever`?** LangChain4j can do retrieval and prompt assembly for you in a few lines. The workshop keeps these steps explicit so you can see, and change, exactly what the LLM receives. Switching to `AiServices` is a good follow-up exercise.
* **Sources show file names, not page numbers:** the Tika parser reads a PDF as one document, which keeps the loader to a single line. The Python edition loads PDFs page by page and also shows page numbers.
* **Chunk boundaries differ slightly from Python:** `DocumentSplitters.recursive` splits on paragraphs, lines, sentences and then words, while Python's `RecursiveCharacterTextSplitter` skips the sentence level. Sizes and overlap mean the same thing in both.
* **Vector store format:** `InMemoryEmbeddingStore` saves plain JSON (no pickle) and keeps all vectors in memory, which suits demos. For production, swap it for another LangChain4j `EmbeddingStore` such as PgVector, Qdrant, Milvus or Elasticsearch. The rest of `RagService` stays the same.
* **Switching embedding models:** delete `spring/data/vector_store/` and rebuild the knowledge base.
