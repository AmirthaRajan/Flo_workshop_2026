import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FlowExportTests(unittest.TestCase):
    def setUp(self):
        self.flows = [
            json.loads((ROOT / "flows" / filename).read_text(encoding="utf-8"))
            for filename in (
                "explicit-chroma-ingestion.json",
                "explicit-ollama-chroma-rag.json",
            )
        ]

    def test_exports_are_portable_and_embed_current_component(self):
        code = (ROOT / "components" / "local_chroma.py").read_text(encoding="utf-8")
        for flow in self.flows:
            with self.subTest(flow=flow["name"]):
                for field in ("folder_id", "user_id", "workspace_id"):
                    self.assertNotIn(field, flow)
                serialized = json.dumps(flow)
                self.assertNotIn("_frontend_node_", serialized)
                self.assertNotIn("F:\\\\Development", serialized)
                self.assertNotIn("68ee0fe5-8092-4093-9fc2-d4a691bf2215", serialized)
                nodes = flow["data"]["nodes"]
                self.assertFalse(any(n["data"]["type"] == "Knowledge" for n in nodes))
                chroma = next(n for n in nodes if n["data"]["type"] == "LocalChroma")
                template = chroma["data"]["node"]["template"]
                self.assertEqual(template["code"]["value"], code)
                compile(template["code"]["value"], "embedded_local_chroma.py", "exec")
                self.assertEqual(template["persist_directory"]["value"], "")
                self.assertEqual(template["collection_name"]["value"], "workshop_explicit_rag")
                self.assertEqual(chroma["data"]["node"]["outputs"][0]["method"], "run_store")
                for node in nodes:
                    for field in node["data"]["node"].get("template", {}).values():
                        if isinstance(field, dict) and field.get("password"):
                            self.assertEqual(field["value"], "")
                            self.assertFalse(field["load_from_db"])

    def test_ingestion_and_retrieval_wiring(self):
        ingestion, retrieval = self.flows
        self.assertEqual(len(ingestion["data"]["edges"]), 3)
        self.assertEqual(len(retrieval["data"]["edges"]), 7)
        for flow in self.flows:
            with self.subTest(flow=flow["name"]):
                nodes = {node["id"]: node for node in flow["data"]["nodes"]}
                for edge in flow["data"]["edges"]:
                    self.assertIn(edge["source"], nodes)
                    self.assertIn(edge["target"], nodes)
                    self.assertEqual(edge["data"]["sourceHandle"]["id"], edge["source"])
                    self.assertEqual(edge["data"]["targetHandle"]["id"], edge["target"])
                chroma = next(n for n in nodes.values() if n["data"]["type"] == "LocalChroma")
                embedding = next(
                    n for n in nodes.values()
                    if n["data"]["node"].get("display_name") == "Ollama Embeddings"
                )
                self.assertTrue(any(
                    edge["source"] == embedding["id"]
                    and edge["target"] == chroma["id"]
                    and edge["data"]["targetHandle"]["fieldName"] == "embedding"
                    for edge in flow["data"]["edges"]
                ))
        file_node = next(
            n for n in ingestion["data"]["nodes"] if n["data"]["type"] == "File"
        )
        self.assertEqual(file_node["data"]["node"]["template"]["path"]["value"], [])
        self.assertEqual(file_node["data"]["node"]["template"]["path"]["file_path"], [])
        chat = next(n for n in retrieval["data"]["nodes"] if n["data"]["type"] == "ChatInput")
        self.assertEqual(chat["data"]["node"]["template"]["input_value"]["value"], "")
        parser = next(n for n in retrieval["data"]["nodes"] if n["data"]["type"] == "parser")
        self.assertTrue(any(
            edge["source"].startswith("LocalChroma")
            and edge["target"] == parser["id"]
            for edge in retrieval["data"]["edges"]
        ))


if __name__ == "__main__":
    unittest.main()
