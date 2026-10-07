package com.flo.workshop;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.FileOutputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.Metadata;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.output.Response;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Focused tests for provider-independent workshop logic (mirrors python/tests/test_workshop.py). */
class WorkshopTests {

    @Nested
    class ConfigTests {

        @Test
        void ollamaIsTheOnlySupportedProvider() {
            WorkshopSettings configured = WorkshopSettings.defaults();

            assertThat(configured.modelProvider()).isEqualTo("ollama");
            assertThat(configured.embeddingProvider()).isEqualTo("ollama");
        }

        @Test
        void invalidProviderIsRejected() {
            assertThatThrownBy(() -> new WorkshopSettings("openai", "ollama", 4, 800, 100, "x", "y", false))
                    .hasMessageContaining("MODEL_PROVIDER");
        }

        @Test
        void overlapMustBeSmallerThanChunkSize() {
            assertThatThrownBy(() -> new WorkshopSettings("ollama", "ollama", 4, 100, 100, "x", "y", false))
                    .hasMessageContaining("CHUNK_OVERLAP");
        }
    }

    @Nested
    class LoaderTests {

        private final DocumentLoaders loaders = new DocumentLoaders(WorkshopSettings.defaults());

        @Test
        void docxLoaderPreservesSourceName(@TempDir Path directory) throws Exception {
            Path path = directory.resolve("guide.docx");
            try (XWPFDocument document = new XWPFDocument(); OutputStream out = new FileOutputStream(path.toFile())) {
                document.createParagraph().createRun().setText("Run the project locally.");
                document.write(out);
            }

            Document loaded = loaders.loadFile(path);

            assertThat(loaded.text().strip()).isEqualTo("Run the project locally.");
            assertThat(loaded.metadata().getString("source")).isEqualTo("guide.docx");
        }

        @Test
        void confluenceWordExportIsLoadedAsMhtml(@TempDir Path directory) throws Exception {
            String mhtml = "MIME-Version: 1.0\r\n"
                    + "Content-Type: multipart/related; boundary=\"b1\"\r\n\r\n"
                    + "--b1\r\n"
                    + "Content-Type: text/html; charset=UTF-8\r\n"
                    + "Content-Transfer-Encoding: quoted-printable\r\n\r\n"
                    + "<html><head><style>p{}</style></head>"
                    + "<body><h1>Setup</h1><p>Run =3D ok.</p></body></html>\r\n"
                    + "--b1--\r\n";
            Path path = directory.resolve("export.docx");
            Files.writeString(path, mhtml);

            Document loaded = loaders.loadFile(path);

            assertThat(loaded.text()).contains("Setup", "Run = ok.").doesNotContain("p{}");
            assertThat(loaded.metadata().getString("source")).isEqualTo("export.docx");
        }

        @Test
        void urlRequiresHttpOrHttps() {
            assertThatThrownBy(() -> loaders.loadUrl("example.com/docs")).hasMessageContaining("complete URL");
        }

        @Test
        void privateUrlIsBlockedByDefault() {
            DocumentLoaders localhostResolver = new DocumentLoaders(WorkshopSettings.defaults()) {
                @Override
                protected InetAddress[] resolve(String host) {
                    return new InetAddress[] {InetAddress.getLoopbackAddress()};
                }
            };

            assertThatThrownBy(() -> localhostResolver.loadUrl("http://localhost/project"))
                    .hasMessageContaining("Private network URLs");
        }

        @Test
        void publicAddressesAreDistinguishedFromPrivateOnes() throws Exception {
            assertThat(DocumentLoaders.isPublic(InetAddress.getByName("8.8.8.8"))).isTrue();
            assertThat(DocumentLoaders.isPublic(InetAddress.getByName("10.1.2.3"))).isFalse();
            assertThat(DocumentLoaders.isPublic(InetAddress.getByName("169.254.169.254"))).isFalse();
            assertThat(DocumentLoaders.isPublic(InetAddress.getByName("100.64.0.1"))).isFalse();
            assertThat(DocumentLoaders.isPublic(InetAddress.getByName("fd00::1"))).isFalse();
        }
    }

    @Nested
    class RagTests {

        @Test
        void splitDocumentsKeepsSourceMetadata() {
            RagService rag = new RagService(WorkshopSettings.defaults(), new FakeEmbeddings(), null);
            List<Document> documents = List.of(Document.from("project setup ".repeat(100), Metadata.from("source", "guide")));

            List<TextSegment> chunks = rag.splitDocuments(documents);

            assertThat(chunks).hasSizeGreaterThan(1);
            assertThat(chunks).allSatisfy(chunk -> assertThat(chunk.metadata().getString("source")).isEqualTo("guide"));
        }

        @Test
        void promptContainsContextQuestionAndFallback() {
            String prompt = RagService.buildPrompt("Use Java 17.", "Which Java version?");

            assertThat(prompt).contains("Use Java 17.", "Which Java version?", RagService.FALLBACK_ANSWER);
        }

        @Test
        void newBuildReplacesPersistedVectorStoreContents(@TempDir Path directory) throws Exception {
            WorkshopSettings settings = new WorkshopSettings("ollama", "ollama", 4, 800, 100, directory.toString(), "y", false);
            RagService rag = new RagService(settings, new FakeEmbeddings(), null);

            rag.createVectorStore(List.of(TextSegment.from("first")));
            rag.createVectorStore(List.of(TextSegment.from("second")));

            assertThat(rag.loadVectorStore().size()).isEqualTo(1);
        }

        @Test
        void resetVectorStoreRemovesPersistedContents(@TempDir Path directory) throws Exception {
            WorkshopSettings settings = new WorkshopSettings("ollama", "ollama", 4, 800, 100, directory.toString(), "y", false);
            RagService rag = new RagService(settings, new FakeEmbeddings(), null);

            rag.createVectorStore(List.of(TextSegment.from("first")));
            rag.resetVectorStore();

            assertThat(Files.exists(Path.of(directory.toString(), "vector_store.json"))).isFalse();
        }
    }

    /** Deterministic embeddings so tests never need a running Ollama server. */
    static class FakeEmbeddings implements EmbeddingModel {

        @Override
        public Response<List<Embedding>> embedAll(List<TextSegment> segments) {
            return Response.from(segments.stream()
                    .map(segment -> Embedding.from(new float[] {segment.text().length(), 1.0f}))
                    .toList());
        }
    }
}
