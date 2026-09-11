"""Semantic matching, embeddings, and vector indexing package."""
from ace.semantic.cache import EmbeddingCache
from ace.semantic.provider import (
    EmbeddingProvider,
    LocalSentenceTransformer,
    MockEmbeddingProvider,
    RemoteEmbeddingProvider,
)
from ace.semantic.vector_index import SkillVectorIndex, normalize_text

__all__ = [
    "EmbeddingProvider",
    "LocalSentenceTransformer",
    "MockEmbeddingProvider",
    "RemoteEmbeddingProvider",
    "EmbeddingCache",
    "SkillVectorIndex",
    "normalize_text",
]
