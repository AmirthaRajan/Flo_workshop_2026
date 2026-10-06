package com.flo.workshop;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Small, environment-based settings for the workshop (equivalent of {@code config.py}).
 * Ollama model settings are read directly by the LangChain4j starter (see application.properties).
 */
@ConfigurationProperties(prefix = "workshop")
public record WorkshopSettings(
        String modelProvider,
        String embeddingProvider,
        int topK,
        int chunkSize,
        int chunkOverlap,
        String vectorStorePath,
        String documentsPath,
        boolean allowPrivateUrls) {

    public WorkshopSettings {
        if (topK <= 0 || chunkSize <= 0 || chunkOverlap <= 0) {
            throw new IllegalArgumentException("TOP_K, CHUNK_SIZE and CHUNK_OVERLAP must be greater than zero.");
        }
        if (!"ollama".equalsIgnoreCase(modelProvider)) {
            throw new IllegalArgumentException("MODEL_PROVIDER must be 'ollama'.");
        }
        if (!"ollama".equalsIgnoreCase(embeddingProvider)) {
            throw new IllegalArgumentException("EMBEDDING_PROVIDER must be 'ollama'.");
        }
        if (chunkOverlap >= chunkSize) {
            throw new IllegalArgumentException("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.");
        }
    }

    /** Settings with the same defaults as {@code .env.example}; handy for tests. */
    public static WorkshopSettings defaults() {
        return new WorkshopSettings("ollama", "ollama", 4, 800, 100, "data/vector_store", "data/documents", false);
    }
}
