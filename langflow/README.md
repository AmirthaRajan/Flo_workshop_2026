# Langflow RAG workshop project

This is the drag-and-drop edition of the Project Onboarding Chatbot. It exposes
chunking, Ollama embeddings, and a local Chroma vector database as separate
components instead of using the bundled Knowledge component.

Related implementations:

- [Workshop overview](../README.md): RAG concepts, architecture and demonstration.
- [Python project](../python/README.md): LangChain, FAISS and Streamlit.
- [Spring project](../spring/README.md): Spring Boot, LangChain4j and Thymeleaf.

## Included project files

| File | Purpose |
| --- | --- |
| [Start-Langflow.ps1](Start-Langflow.ps1) | Start an isolated localhost server |
| [requirements.txt](requirements.txt) | Pinned Langflow and Chroma dependencies |
| [flows/explicit-chroma-ingestion.json](flows/explicit-chroma-ingestion.json) | Importable document-ingestion flow |
| [flows/explicit-ollama-chroma-rag.json](flows/explicit-ollama-chroma-rag.json) | Importable retrieval and chat flow |
| [components/local_chroma.py](components/local_chroma.py) | Custom persistent Chroma component |
| [tests/test_local_chroma.py](tests/test_local_chroma.py) | Persistence, metadata, validation and build-lifecycle tests |
| [tests/test_flow_exports.py](tests/test_flow_exports.py) | Export portability and wiring checks |

No virtual environment, uploaded documents, vector index, Langflow database,
credentials or Ollama models are included. Runtime files are ignored by Git.
The custom Chroma code is embedded in both flow exports, so importing a flow
does not require manually adding the component source to Langflow.

## 1. Install

Use **Python 3.12** (the workshop was tested with Python 3.12.10), PowerShell,
and a locally installed Ollama server.

From this directory:

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
ollama pull nomic-embed-text:latest
ollama pull llama3.2:latest
& .\Start-Langflow.ps1
```

Open <http://127.0.0.1:7860>. Ollama must be running at
`http://127.0.0.1:11434`. Downloading packages and models requires internet;
document embedding, retrieval and generation use the local services.

The launcher binds only to `127.0.0.1`, stores Langflow state under this
project's `data` directory, disables telemetry settings, and enables auto-login
for the local workshop. Do not expose this configuration on a public network.

### Existing running installation

The server created during workshop preparation still runs from the separate
`langflow-workshop` installation alongside the repository. Adding this project
does not move or modify that server or its data.

Use that existing server if you want to keep its current flows and documents.
Do not start this launcher while another server occupies port 7860.
A fresh installation here starts with a separate Langflow database; follow the
import steps below.

## 2. Import and configure both flows

1. In Langflow's project screen, click **Upload a flow** and import
   [explicit-chroma-ingestion.json](flows/explicit-chroma-ingestion.json).
2. Import [explicit-ollama-chroma-rag.json](flows/explicit-ollama-chroma-rag.json).
3. In **Local Chroma in both flows**, set **Persistence Directory** to the same
   absolute local directory. Compute an appropriate path from this directory:

   ```powershell
   Join-Path $PWD.Path 'data\explicit-chroma'
   ```

   Paste the resulting absolute path into both nodes. The exported field is
   deliberately blank to avoid silently indexing into another machine's path.
4. Keep **Collection Name** equal in both nodes, initially
   `workshop_explicit_rag`.
5. Check both **Ollama Embeddings** nodes: base URL
   `http://127.0.0.1:11434`, model `nomic-embed-text:latest`.
6. In the chat flow's **Language Model**, select Ollama and `llama3.2:latest`.
   A new installation may require selecting or refreshing the model in the UI.
7. Save both flows with **Ctrl+S**.

The exports intentionally contain no selected uploaded documents or original
project/folder identifiers. Select documents from your own server next.

## 3. Upload documents and build the index

Open **Workshop - Explicit Chroma Ingestion**:

```text
Read File -> Split Text -> Local Chroma (Ingest)
                              ^
                              |
                       Ollama Embeddings
```

1. On **Read File**, click **Select files**.
2. Upload your documents in the upload area, select them, and confirm with
   **Select files**.
3. For a reproducible first demo, use the workshop
   [main README](../README.md) and [Python README](../python/README.md).
   Markdown documents were used for the end-to-end validation; specialized
   MHTML/URL behavior from the original applications is not migrated.
4. Check **Split Text**: chunk size **800**, overlap **100**.
5. Check **Local Chroma**: mode **Ingest**.
6. Click **Run component** on **Local Chroma**.
7. Wait for the successful build. Its output contains `indexed_chunks`,
   `total_chunks`, `collection`, and `directory`.

Uploading alone does not index a document. Running Local Chroma executes
Read File and Split Text, embeds the chunks, and stores vectors and source
metadata on disk.

## 4. Ask questions

Open **Workshop - Explicit Ollama Chroma RAG**:

```text
Chat Input -> Local Chroma (Retrieve) -> Parser -> Prompt -> Language Model -> Chat Output
                  ^                                 ^
                  |                                 |
          Ollama Embeddings                  Chat Input question
```

Check **Local Chroma** mode **Retrieve** and **Top K** **4**. Click
**Playground** and ask:

> Which UI framework is used in the Python edition and in the Java edition?

With the example documents, the expected answer identifies Streamlit and
Thymeleaf and includes source filename labels.

Try an unsupported question:

> What is the published ticket price for attending this workshop?

The prompt instructs the model to return exactly:

```text
I could not find that information in the project documentation.
```

This is a prompting convention, not a deterministic hallucination-prevention
guarantee. Verify responses when presenting or using other documents/models.

### What each component demonstrates

- **Read File:** loads document text and metadata.
- **Split Text:** creates overlapping chunks during ingestion, not per question.
- **Ollama Embeddings:** provides the embedding model to Chroma. It does not
  output a table of vectors; Chroma calls the model to embed chunks or queries.
- **Local Chroma:** persists vectors during ingestion; searches them during chat.
  It is a custom component using `chromadb`, not Knowledge relabeled.
- **Parser:** formats retrieved `content` and `file_name` into prompt context.
- **Prompt:** combines retrieved context with the user's question.
- **Language Model:** uses `llama3.2:latest` to generate the answer.
- **Chat Output:** displays the response in Playground.

## Index management and troubleshooting

- **New documents:** select/upload them in Read File and run ingestion again.
- **Duplicates:** re-ingesting the same unchanged file/chunk does not add another
  vector. Identifiers are derived from file path and text; uploading a separate
  copy with a different path may produce additional records.
- **Removed/changed documents:** ingestion is additive. Unselecting a file does
  not remove its old vectors, and edits can leave older chunks in the collection.
  For a clean corpus, use a new Collection Name in both flows and ingest again.
- **Embedding model changes:** use the same embedding model and endpoint in both
  flows. Use a new collection and re-ingest when changing the model.
- **Missing/empty collection:** run ingestion before chat; check that both
  Persistence Directory and Collection Name match.
- **Ollama connection errors:** confirm Ollama is running and both models are
  installed. Refresh/select models in Langflow if needed.
- **No filename metadata:** inspect Read File/Split Text output. Local Chroma
  requires `file_name` or `filename` on every chunk.
- **Citations:** retrieved rows contain `content`, `file_name`, `file_path`,
  and `distance`. Files with the same basename have the same filename citation;
  use distinctive filenames to make a workshop easier to follow.

## Tests

From this directory, after installing dependencies:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Component tests use temporary Chroma collections and deterministic embeddings;
they do not need Ollama. They cover persistence, repeat ingestion, citations,
invalid inputs, model mismatch, and the Langflow async build lifecycle.
Export tests check wiring, matching collection settings, embedded component
code, and removal of machine-specific upload references.

The original running flows were verified with 32 chunks, top-four retrieval,
filename citations, and the missing-information response. The exports here
require selecting your own documents and configuring the storage path before
running; your chunk count depends on the documents you upload.
