from __future__ import annotations

import math

import chromadb

from job_agent.config.loader import load_config
from job_agent.ports.embedder import EmbedderPort


class Embedder:
    """EmbedderPort implementation using Chroma's built-in embedding function."""

    def __init__(self, collection_name: str | None = None) -> None:
        _, app_config = load_config()
        name = collection_name or app_config.chroma.job_embeddings_collection
        self._client = chromadb.HttpClient(host="localhost", port=8001)
        self._ef = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=name, embedding_function=self._ef
        )

    async def embed(self, text: str) -> list[float]:
        result = self._ef([text])
        return list(result[0])

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)


# Verify protocol compliance at import time
def _check() -> None:
    _: EmbedderPort = Embedder.__new__(Embedder)  # type: ignore[type-abstract]


_check()
