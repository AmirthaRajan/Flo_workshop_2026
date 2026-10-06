package com.flo.workshop;

import static org.assertj.core.api.Assertions.assertThat;

import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.embedding.EmbeddingModel;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** The application must start without Ollama running; models are only contacted on use. */
@SpringBootTest(properties = {"OLLAMA_LLM_MODEL=test-llm", "OLLAMA_EMBEDDING_MODEL=test-embed"})
class RagWorkshopApplicationTests {

    @Autowired
    private WorkshopSettings settings;

    @Autowired
    private ChatModel chatModel;

    @Autowired
    private EmbeddingModel embeddingModel;

    @Test
    void contextLoadsWithAutoConfiguredOllamaModels() {
        assertThat(settings.modelProvider()).isEqualTo("ollama");
        assertThat(chatModel).isNotNull();
        assertThat(embeddingModel).isNotNull();
    }
}
