"""Semantic Embedding Providers.

Supports:
- LocalSentenceTransformer: Local CPU sentence-transformers (all-MiniLM-L6-v2)
- RemoteEmbeddingProvider: External REST embedding endpoint
- MockEmbeddingProvider: Deterministic pseudo-embeddings for fast unit testing & CI
"""
import hashlib
import math
from collections.abc import Sequence
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol for text embedding backends."""

    @property
    def dimension(self) -> int:
        """Vector dimensionality."""
        ...

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string into a float vector."""
        ...

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of text strings into float vectors."""
        ...


class LocalSentenceTransformer:
    """Lazy-loaded local sentence-transformers model (CPU optimized)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None
        self._dimension = 384

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device="cpu")
            dim_fn = getattr(self._model, "get_embedding_dimension", getattr(self._model, "get_sentence_embedding_dimension", None))
            self._dimension = dim_fn() if dim_fn else 384
        return self._model


    def embed_text(self, text: str) -> list[float]:
        model = self._get_model()
        vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return [float(x) for x in vec.tolist()]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        matrix = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)
        return [[float(x) for x in row] for row in matrix.tolist()]


class MockEmbeddingProvider:
    """Deterministic hash/n-gram pseudo-embedding provider for testing.

    Requires zero torch/neural network computation. Sub-millisecond execution.
    Produces unit-normalized 384-dimensional vectors.
    """

    def __init__(self, dimension: int = 384) -> None:
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        clean = text.lower().strip()
        vec = [0.0] * self._dim
        if not clean:
            vec[0] = 1.0
            return vec

        # Token and character n-gram hashing
        tokens = clean.split()
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            vec[idx] += 1.0

        for i in range(len(clean) - 2):
            trigram = clean[i:i + 3]
            h = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            vec[idx] += 0.5

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]
        else:
            vec[0] = 1.0
        return vec

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


class RemoteEmbeddingProvider:
    """HTTP client for remote embedding endpoints."""

    def __init__(self, endpoint_url: str, api_key: str = "", dimension: int = 384) -> None:
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        res = self.embed_batch([text])
        return res[0] if res else [0.0] * self._dim

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        import httpx
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        resp = httpx.post(self.endpoint_url, json={"texts": list(texts)}, headers=headers, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        return data.get("embeddings", [])
