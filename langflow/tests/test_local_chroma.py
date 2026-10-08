import asyncio
import tempfile
import unittest

from components.local_chroma import LocalChromaComponent
from lfx.schema.dataframe import DataFrame


class TestEmbeddings:
    model = "test-model"
    base_url = "http://localhost:11434"

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        return [1.0, 0.0] if "python" in text.lower() else [0.0, 1.0]


class LocalChromaTests(unittest.TestCase):
    def component(self, directory, **kwargs):
        component = LocalChromaComponent()
        component.set(
            embedding=TestEmbeddings(), persist_directory=directory,
            collection_name="test_workshop", top_k=1, **kwargs,
        )
        return component

    def test_persistence_citations_and_idempotent_ingestion(self):
        with tempfile.TemporaryDirectory() as directory:
            chunks = DataFrame([
                {"text": "Python uses Streamlit.", "filename": "python.md",
                 "file_path": "python.md"},
                {"text": "Java uses Thymeleaf.", "filename": "java.md",
                 "file_path": "java.md"},
            ])
            for _ in range(2):
                output = self.component(directory, mode="Ingest", documents=chunks).run_store()
                self.assertEqual(output.iloc[0]["indexed_chunks"], 2)
                self.assertEqual(output.iloc[0]["total_chunks"], 2)
            result = self.component(directory, mode="Retrieve", query="Python UI").run_store()
            self.assertEqual(list(result.columns), ["content", "file_name", "file_path", "distance"])
            self.assertEqual(len(result), 1)
            self.assertEqual(result.iloc[0]["file_name"], "python.md")
            self.assertEqual(result.iloc[0]["content"], "Python uses Streamlit.")
            result = self.component(directory, mode="Retrieve", query="Java UI").run_store()
            self.assertEqual(result.iloc[0]["file_name"], "java.md")
            results, _ = asyncio.run(
                self.component(directory, mode="Retrieve", query="Python UI").build_results()
            )
            self.assertEqual(results["results"].iloc[0]["file_name"], "python.md")

    def test_missing_collection_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Run the companion ingestion"):
                self.component(directory, mode="Retrieve", query="test").run_store()

    def test_bad_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "non-empty Search Query"):
                self.component(directory, mode="Retrieve", query="").run_store()
            with self.assertRaisesRegex(ValueError, "file_name or filename"):
                self.component(directory, mode="Ingest", documents=DataFrame([
                    {"text": "missing source"}
                ])).run_store()

    def test_embedding_model_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            self.component(directory, mode="Ingest", documents=DataFrame([
                {"text": "Python", "file_name": "python.md"}
            ])).run_store()
            component = self.component(directory, mode="Retrieve", query="Python")
            embedding = TestEmbeddings()
            embedding.model = "different-model"
            component.set(embedding=embedding)
            with self.assertRaisesRegex(ValueError, "different embedding model"):
                component.run_store()


if __name__ == "__main__":
    unittest.main()
