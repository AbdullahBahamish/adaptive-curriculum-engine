"""Skill Vector Index — CPU-optimized cosine similarity retrieval over canonical skill vectors."""
import json
import re
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from ace.domain.skill import Skill
from ace.semantic.cache import EmbeddingCache
from ace.semantic.provider import EmbeddingProvider, LocalSentenceTransformer, MockEmbeddingProvider


def normalize_text(text: str) -> str:
    """Normalize input text for consistent semantic matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s\-\.]", " ", text)
    return " ".join(text.split())


class SkillVectorIndex:
    """In-memory normalized vector index for sub-millisecond semantic skill retrieval."""

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        cache: EmbeddingCache | None = None,
    ) -> None:
        if provider is None:
            try:
                self.provider = LocalSentenceTransformer()
            except Exception:
                self.provider = MockEmbeddingProvider()
        else:
            self.provider = provider

        self.cache = cache or EmbeddingCache()
        self._skill_ids: list[str] = []
        self._matrix: np.ndarray | None = None  # Shape (N, D), normalized


    @property
    def is_indexed(self) -> bool:
        return self._matrix is not None and len(self._skill_ids) > 0

    def load_precomputed(self, embeddings_path: str | Path) -> bool:
        """Load precomputed canonical embeddings from a JSON file."""
        path = Path(embeddings_path)
        if not path.exists():
            return False

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or not data:
                return False

            ids: list[str] = []
            vectors: list[list[float]] = []

            for sid, vec in data.items():
                ids.append(sid)
                vectors.append(vec)

            arr = np.array(vectors, dtype=np.float32)
            # Ensure unit-normalization for cosine dot-product
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._matrix = arr / norms
            self._skill_ids = ids
            return True
        except Exception:
            return False

    def build_from_skills(
        self,
        skills: Sequence[Skill],
        provider: EmbeddingProvider | None = None,
    ) -> None:
        """Build the index by generating embeddings for a sequence of skills."""
        prov = provider or self.provider or MockEmbeddingProvider()
        self._skill_ids = [s.id for s in skills]
        texts = [f"{s.name} ({s.category}): {s.description}".strip() for s in skills]

        vectors: list[list[float]] = []
        missing_indices: list[int] = []
        missing_texts: list[str] = []

        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached is not None:
                vectors.append(cached)
            else:
                vectors.append([])  # Placeholder
                missing_indices.append(i)
                missing_texts.append(text)

        if missing_texts:
            new_vectors = prov.embed_batch(missing_texts)
            for idx, text, vec in zip(missing_indices, missing_texts, new_vectors):
                vectors[idx] = vec
                self.cache.set(text, vec)
            self.cache.save()

        arr = np.array(vectors, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._matrix = arr / norms

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.35,
    ) -> list[tuple[str, float]]:
        """Find the most semantically relevant skills for a query text.

        Returns:
            list of (skill_id, cosine_similarity_score) sorted by score descending.
        """
        if self._matrix is None or not self._skill_ids:
            return []

        norm_query = normalize_text(query)
        if not norm_query:
            return []

        # Check cache or embed
        query_vec = self.cache.get(norm_query)
        if query_vec is None:
            if self.provider is None:
                self.provider = MockEmbeddingProvider()
            query_vec = self.provider.embed_text(norm_query)
            self.cache.set(norm_query, query_vec)

        q_arr = np.array(query_vec, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm > 0:
            q_arr /= q_norm

        # Cosine similarity is dot product of unit vectors
        scores = np.dot(self._matrix, q_arr)

        # Filter and rank
        indices = np.argsort(-scores)
        results: list[tuple[str, float]] = []
        for idx in indices:
            score = float(scores[idx])
            if score < min_score:
                break
            results.append((self._skill_ids[idx], round(score, 4)))
            if len(results) >= top_k:
                break

        return results
