import os
from dataclasses import dataclass, field
from typing import Optional, Literal, Any, Dict

from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

import chromadb
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions


class ChromaDB:

    def __init__(self, client: ClientAPI, embedding_fn):
        self._client = client
        self._embedding_fn = embedding_fn

    def get_collection(self,
                       name: str,
                       metadata: Optional[Dict[str, Any]] = None,
                       **kwargs):
        return self._client.get_or_create_collection(
            name=name,
            metadata=metadata,
            embedding_function=self._embedding_fn,
            **kwargs,
        )

    def create_collection(self,
                          name: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          **kwargs):
        return self._client.create_collection(
            name=name,
            metadata=metadata,
            embedding_function=self._embedding_fn,
            **kwargs,
        )

    def raw(self) -> ClientAPI:
        """Access the underlying chroma client when needed."""
        return self._client

    def list_collections(self):
        return self._client.list_collections()

    def delete_collection(self, name: str):
        return self._client.delete_collection(name)


@dataclass(frozen=True)
class ChromaConfig:

    mode: Literal["local", "server"] = field(default_factory=lambda: os.getenv(
        "CHROMA_MODE", "local").lower())  # type: ignore
    persist_dir: str = field(
        default_factory=lambda: os.getenv("CHROMA_PERSIST_DIR", "./.chroma"))
    host: Optional[str] = field(default_factory=lambda: os.getenv("CHROMA_HOST"))
    port: Optional[str] = field(default_factory=lambda: os.getenv("CHROMA_PORT"))
    tenant: Optional[str] = field(default_factory=lambda: os.getenv("CHROMA_TENANT"))
    database: Optional[str] = field(
        default_factory=lambda: os.getenv("CHROMA_DATABASE"))

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_embed_model: str = field(default_factory=lambda: os.getenv(
        "OPENAI_EMBED_MODEL", "text-embedding-3-small"))

    def _embedding_fn(self):
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.openai_api_key,
            model_name=self.openai_embed_model,
        )

    def connect(self) -> ChromaDB:

        mode = (self.mode or "local").lower()
        if mode == "server":
            if not self.host or not self.port:
                raise RuntimeError(
                    "CHROMA_HOST and CHROMA_PORT must be set for server mode")
            client = chromadb.HttpClient(
                host=self.host,
                port=int(self.port),
                settings=Settings(
                    anonymized_telemetry=False,
                    tenant=self.tenant,
                    database=self.database,
                ),
            )
        elif mode == "local":
            client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    tenant=self.tenant,
                    database=self.database,
                ),
            )
        else:
            raise ValueError(f"Unsupported CHROMA_MODE: {self.mode}")

        return ChromaDB(client=client, embedding_fn=self._embedding_fn())
