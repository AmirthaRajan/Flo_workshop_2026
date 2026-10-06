# Workshop Q&A (Spring + LangChain4j Edition): Setup & Troubleshooting

Run every command below from the `spring` folder of the repository.

For the Python edition, see [../python/README-QA.md](../python/README-QA.md).

## Q1) `java` is not recognized, or the wrapper says JAVA_HOME is not set

### Fix

Install a JDK 17 or newer (e.g. [Eclipse Temurin](https://adoptium.net/)), then confirm:

```powershell
java -version
```

If `java` works but the wrapper still complains, point `JAVA_HOME` at the JDK folder for the current session:

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17"   # adjust to your install
.\mvnw.cmd -v
```

## Q2) `.\mvnw.cmd` is blocked or `./mvnw: Permission denied`

* **Windows:** run `.\mvnw.cmd` (not `mvnw`) from PowerShell. If your organization blocks scripts, use `cmd /c mvnw.cmd spring-boot:run`.
* **macOS / Linux:** make the script executable once: `chmod +x mvnw`.

## Q3) The first build is slow or fails to download dependencies

The first run downloads Maven and all dependencies (~150 MB) into `~/.m2`. Behind a corporate proxy, configure it in `~/.m2/settings.xml` ([Maven proxy guide](https://maven.apache.org/guides/mini/guide-proxies.html)) and rerun:

```powershell
.\mvnw.cmd -U clean test
```

## Q4) "model is required" or "model '<your-llm-model>' not found"

The model names in `.env` are missing or still contain the `<placeholder>` values from `.env.example`. The app still starts; the error appears the first time you ingest or ask.

* Make sure `spring/.env` exists (copied from `.env.example`) and contains real model names.
* Start the app **from the `spring` folder**: `.env` is read from the current working directory.
* Restart the app after editing `.env`. Settings are read at startup.

## Q5) "Connection refused" or "I/O error on POST request for http://localhost:11434/..."

Ollama is not running or is listening elsewhere.

```powershell
ollama list                      # starts/contacts the Ollama service
curl http://localhost:11434      # should reply "Ollama is running"
```

If Ollama runs on another host or port, set `OLLAMA_BASE_URL` in `.env`.

## Q6) "model 'xyz' not found"

Pull the model you configured:

```powershell
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

## Q7) Port 8080 is already in use

Set another port in `.env` (`SERVER_PORT=8081`) or for one run:

```powershell
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.arguments=--server.port=8081"
```

## Q8) Answers look wrong after changing the embedding model or chunk size

The existing `data/vector_store/vector_store.json` was built with the old settings. Delete it and rebuild the knowledge base:

```powershell
Remove-Item -Recurse -Force data\vector_store\*.json
```

## Q9) Clicking a button seems to do nothing (no GPU)

On a CPU-only machine Ollama is slow, so the page waits while the model works. The button changes to "⏳ Thinking…" until the answer arrives. Typical times for a 7B model on CPU:

* **Ask:** about 20–60 seconds.
* **Build / Update Knowledge Base:** about 1 minute per 100–300 chunks. A 100-page document can take several minutes.

Click once and wait. Requests time out after 5 minutes (`langchain4j.ollama.*.timeout` in `application.properties`). To check that your models are downloaded and where they are running:

```powershell
ollama list   # downloaded models, e.g. qwen2.5:7b and nomic-embed-text
ollama ps     # models currently loaded, and whether they run on CPU or GPU
```

For faster answers on CPU, use a smaller model such as `OLLAMA_LLM_MODEL=qwen2.5:3b` or `llama3.2:3b` (`ollama pull` it first).

## Q10) Log warning: "POI does not currently support template.main+xml (glossary) parts"

This is harmless. Your Word file contains a glossary or Quick Parts template section, which the parser skips. The main document text is still loaded.

## Verified end-to-end setup commands (copy/paste)

```powershell
Set-Location C:\Users\<USER_NAME>\Dev\Flo_workshop_2026\spring
Copy-Item .env.example .env      # then edit the model names
java -version
.\mvnw.cmd test
.\mvnw.cmd spring-boot:run       # open http://localhost:8080
```
