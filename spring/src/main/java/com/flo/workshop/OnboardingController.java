package com.flo.workshop;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.segment.TextSegment;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;

/** Web interface for the Project Onboarding RAG workshop (equivalent of {@code app.py}). */
@Controller
public class OnboardingController {

    private final WorkshopSettings settings;
    private final DocumentLoaders loaders;
    private final RagService rag;

    public OnboardingController(WorkshopSettings settings, DocumentLoaders loaders, RagService rag) {
        this.settings = settings;
        this.loaders = loaders;
        this.rag = rag;
    }

    /** One line per source (file name or URL) plus the chunk text shown under "Retrieved Context". */
    public record Source(String label, String content) {
    }

    @ModelAttribute
    void configuration(Model model) {
        model.addAttribute("llmProvider", title(settings.modelProvider()));
        model.addAttribute("embeddingProvider", title(settings.embeddingProvider()));
    }

    @GetMapping("/")
    String index() {
        return "index";
    }

    @PostMapping("/ingest")
    String ingest(@RequestParam(name = "files", required = false) List<MultipartFile> uploadedFiles,
            @RequestParam(name = "url", defaultValue = "") String url, Model model) {
        List<String> steps = new ArrayList<>();
        model.addAttribute("steps", steps);
        model.addAttribute("url", url);
        try {
            steps.add("Loading documents...");
            List<Document> documents = new ArrayList<>();
            if (uploadedFiles != null) {
                for (MultipartFile uploadedFile : uploadedFiles) {
                    if (!uploadedFile.isEmpty()) {
                        documents.add(loaders.loadFile(loaders.saveUploadedFile(uploadedFile)));
                    }
                }
            }
            if (!url.isBlank()) {
                documents.add(loaders.loadUrl(url.strip()));
            }
            if (documents.isEmpty()) {
                throw new IllegalArgumentException("Upload a document or enter a URL first.");
            }

            steps.add("Creating chunks...");
            List<TextSegment> chunks = rag.splitDocuments(documents);
            steps.add("Generating embeddings and building vector store...");
            rag.createVectorStore(chunks);
            steps.add("Knowledge base ready.");
            model.addAttribute("ingestSuccess", "Stored " + chunks.size() + " searchable chunks.");
        } catch (Exception error) {
            model.addAttribute("ingestError", "Could not build the knowledge base: " + error.getMessage()
                    + "\n\nCheck your model settings and make sure Ollama is running.");
        }
        return "index";
    }

    @PostMapping("/ask")
    String ask(@RequestParam(name = "question", defaultValue = "") String question, Model model) {
        model.addAttribute("question", question);
        try {
            RagService.Answer result = rag.answerQuestion(question);
            List<Source> sources = new ArrayList<>();
            for (TextSegment chunk : result.retrievedChunks()) {
                String source = chunk.metadata().getString("source");
                sources.add(new Source(source != null ? source : "Unknown source", chunk.text()));
            }
            model.addAttribute("answer", result.answer());
            model.addAttribute("sources", sources);
        } catch (Exception error) {
            model.addAttribute("askError", "Could not answer the question: " + error.getMessage()
                    + "\n\nBuild the knowledge base and check that the selected model is available.");
        }
        return "index";
    }

    private static String title(String value) {
        return value.isEmpty() ? value : value.substring(0, 1).toUpperCase(Locale.ROOT) + value.substring(1);
    }
}
