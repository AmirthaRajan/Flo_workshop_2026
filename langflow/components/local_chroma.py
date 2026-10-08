import hashlib
import os
from collections.abc import Mapping
from pathlib import Path

import chromadb
from chromadb.api import ClientAPI
from chromadb.errors import NotFoundError
from lfx.custom.custom_component.component import Component
from lfx.io import DropdownInput, HandleInput, IntInput, MessageTextInput, Output, StrInput
from lfx.schema.dataframe import DataFrame


class LocalChromaComponent(Component):
    display_name = "Local Chroma"
    description = "Persist document vectors locally or retrieve chunks using connected embeddings."
    icon = "Database"
    name = "LocalChroma"

    inputs = [
        DropdownInput(
            name="mode", display_name="Mode", options=["Ingest", "Retrieve"], value="Retrieve"
        ),
        HandleInput(
            name="embedding", display_name="Embedding Model", input_types=["Embeddings"],
            required=True,
        ),
        HandleInput(
            name="documents", display_name="Document Chunks",
            input_types=["DataFrame", "Table"], required=False,
        ),
        MessageTextInput(name="query", display_name="Search Query", value=""),
        StrInput(
            name="persist_directory", display_name="Persistence Directory",
            value=str(
                (Path(os.environ.get("LANGFLOW_CONFIG_DIR", "data")) / "explicit-chroma").resolve()
            ),
            required=True,
        ),
        StrInput(
            name="collection_name", display_name="Collection Name",
            value="workshop_explicit_rag", required=True,
        ),
        IntInput(name="top_k", display_name="Top K", value=4),
    ]

    outputs = [
        Output(display_name="Results", name="results", method="run_store"),
    ]

    def run_store(self) -> DataFrame:
        if self.mode not in {"Ingest", "Retrieve"}:
            raise ValueError("Mode must be Ingest or Retrieve.")
        directory = Path(self.persist_directory).expanduser()
        if not directory.is_absolute():
            raise ValueError("Persistence Directory must be an absolute local path.")
        if not self.collection_name.strip():
            raise ValueError("Collection Name cannot be empty.")
        if self.top_k < 1:
            raise ValueError("Top K must be at least 1.")

        model = getattr(self.embedding, "model", None)
        base_url = getattr(self.embedding, "base_url", None)
        if not model or not base_url:
            raise ValueError("Connect the Ollama Embeddings node with a model and base URL.")
        signature = f"{str(base_url).rstrip('/')}|{model}"
        with chromadb.PersistentClient(path=str(directory)) as client:
            return self._build_with_client(client, signature, str(directory))

    def _build_with_client(self, client: ClientAPI, signature: str, directory: str) -> DataFrame:
        if self.mode == "Ingest":
            if not isinstance(self.documents, DataFrame):
                raise ValueError("Connect Split Text's chunk table before running ingestion.")
            records = self.documents.to_dict(orient="records")
            if not records:
                raise ValueError("No document chunks were supplied.")
            texts, metadata, ids = [], [], []
            for row in records:
                text = row.get("text")
                if not isinstance(text, str) or not text.strip():
                    raise ValueError("Every document chunk must contain non-empty text.")
                filename = row.get("file_name", row.get("filename"))
                if not isinstance(filename, str) or not filename.strip():
                    raise ValueError("Every chunk must include file_name or filename metadata.")
                file_path = row.get("file_path", filename)
                if not isinstance(file_path, str):
                    raise ValueError("Chunk file_path must be a string.")
                texts.append(text)
                metadata.append({"file_name": filename, "file_path": file_path})
                ids.append(hashlib.sha256(f"{file_path}\0{text}".encode()).hexdigest())
            collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine", "embedding_signature": signature},
                embedding_function=None,
            )
            self._check_embedding(collection.metadata, signature)
            unique = {identifier: (text, meta) for identifier, text, meta in zip(ids, texts, metadata)}
            items = list(unique.items())
            for start in range(0, len(items), 64):
                batch = items[start:start + 64]
                batch_texts = [item[1][0] for item in batch]
                vectors = self.embedding.embed_documents(batch_texts)
                collection.upsert(
                    ids=[item[0] for item in batch],
                    documents=batch_texts,
                    metadatas=[item[1][1] for item in batch],
                    embeddings=vectors,
                )
            self.status = f"Indexed {len(unique)} unique chunks; collection has {collection.count()} chunks."
            return DataFrame([{
                "indexed_chunks": len(unique), "total_chunks": collection.count(),
                "collection": self.collection_name, "directory": str(directory),
            }])

        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("Connect Chat Input or enter a non-empty Search Query.")
        try:
            collection = client.get_collection(name=self.collection_name, embedding_function=None)
        except NotFoundError as exc:
            raise ValueError("Collection not found. Run the companion ingestion flow first.") from exc
        self._check_embedding(collection.metadata, signature)
        count = collection.count()
        if not count:
            raise ValueError("The collection is empty. Run the ingestion flow first.")
        result = collection.query(
            query_embeddings=[self.embedding.embed_query(self.query)],
            n_results=min(self.top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        documents = result["documents"]
        metadatas = result["metadatas"]
        distances = result["distances"]
        if documents is None or metadatas is None or distances is None:
            raise ValueError("Chroma returned incomplete search results.")
        rows = [
            {"content": text, "file_name": meta["file_name"],
             "file_path": meta["file_path"], "distance": distance}
            for text, meta, distance in zip(documents[0], metadatas[0], distances[0])
        ]
        self.status = f"Retrieved {len(rows)} chunks from {self.collection_name}."
        return DataFrame(rows)

    @staticmethod
    def _check_embedding(metadata: Mapping[str, object] | None, signature: str) -> None:
        if not metadata or metadata.get("embedding_signature") != signature:
            raise ValueError(
                "The collection uses a different embedding model. Use the original model "
                "or a new collection name and re-ingest."
            )
