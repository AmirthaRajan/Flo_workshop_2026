package com.flo.workshop;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.splitter.DocumentSplitters;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.input.PromptTemplate;
import dev.langchain4j.store.embedding.EmbeddingMatch;
import dev.langchain4j.store.embedding.EmbeddingSearchRequest;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import org.springframework.stereotype.Service;

/** The complete, intentionally small RAG workflow (equivalent of {@code rag.py}). */
@Service
public class RagService {

    public static final String FALLBACK_ANSWER = "I could not find that information in the project documentation.";

    private static final PromptTemplate PROMPT = PromptTemplate.from("""
            You are a project onboarding assistant.

            Answer the user's question using ONLY the provided context.

            If the answer cannot be found in the context, say:
            "{{fallback}}"

            Context:
            {{context}}

            Question:
            {{question}}
            """);

    private final WorkshopSettings settings;
    private final EmbeddingModel embeddingModel;
    private final ChatModel chatModel;

    // Both models are created by the LangChain4j Ollama starter from application.properties.
    public RagService(WorkshopSettings settings, EmbeddingModel embeddingModel, ChatModel chatModel) {
        this.settings = settings;
        this.embeddingModel = embeddingModel;
        this.chatModel = chatModel;
    }

    public record Answer(String answer, List<TextSegment> retrievedChunks) {
    }

    /** Split documents so retrieval can select only the relevant information. */
    public List<TextSegment> splitDocuments(List<Document> documents) {
        // Overlap keeps ideas near a chunk boundary from being separated completely.
        return DocumentSplitters.recursive(settings.chunkSize(), settings.chunkOverlap()).splitAll(documents);
    }

    /** Convert chunks to vectors and persist the searchable vector store as JSON on disk. */
    public synchronized InMemoryEmbeddingStore<TextSegment> createVectorStore(List<TextSegment> chunks)
            throws IOException {
        if (chunks.isEmpty()) {
            throw new IllegalArgumentException("No document text was found to add to the knowledge base.");
        }
        InMemoryEmbeddingStore<TextSegment> vectorStore =
                Files.exists(indexFile()) ? InMemoryEmbeddingStore.fromFile(indexFile()) : new InMemoryEmbeddingStore<>();

        // Embeddings let us compare meaning instead of only matching exact words.
        List<Embedding> embeddings = embeddingModel.embedAll(chunks).content();
        vectorStore.addAll(embeddings, chunks);

        Files.createDirectories(indexFile().getParent());
        vectorStore.serializeToFile(indexFile());
        return vectorStore;
    }

    /** Open the locally persisted knowledge base. */
    public InMemoryEmbeddingStore<TextSegment> loadVectorStore() {
        if (!Files.exists(indexFile())) {
            throw new IllegalStateException("No knowledge base exists yet. Ingest a document or URL first.");
        }
        return InMemoryEmbeddingStore.fromFile(indexFile());
    }

    /** Keep the teaching prompt visible and easy to experiment with. */
    public static String buildPrompt(String context, String question) {
        return PROMPT.apply(Map.of("fallback", FALLBACK_ANSWER, "context", context, "question", question)).text();
    }

    /** Retrieve context first, then ask the selected LLM for an answer. */
    public Answer answerQuestion(String question) {
        if (question == null || question.isBlank()) {
            throw new IllegalArgumentException("Enter a question about the project.");
        }

        // Retrieve relevant chunks before asking the LLM, which limits its context.
        EmbeddingSearchRequest search = EmbeddingSearchRequest.builder()
                .queryEmbedding(embeddingModel.embed(question).content())
                .maxResults(settings.topK())
                .build();
        List<TextSegment> retrievedChunks = loadVectorStore().search(search).matches().stream()
                .map(EmbeddingMatch::embedded)
                .toList();

        String context = retrievedChunks.stream().map(TextSegment::text).collect(Collectors.joining("\n\n---\n\n"));
        String answer = chatModel.chat(buildPrompt(context, question));
        return new Answer(answer, retrievedChunks);
    }

    private Path indexFile() {
        return Path.of(settings.vectorStorePath(), "vector_store.json");
    }
}
