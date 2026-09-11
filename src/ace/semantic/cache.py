"""Embedding cache — dual memory LRU and persistent JSON disk cache."""
import json
from collections import OrderedDict
from pathlib import Path


class EmbeddingCache:
    """Two-tier LRU in-memory and persistent disk cache for text embeddings."""

    def __init__(
        self,
        cache_path: str | Path | None = None,
        max_memory_items: int = 1000,
    ) -> None:
        self.cache_path = Path(cache_path) if cache_path else Path("data/processed/embeddings_cache.json")
        self.max_memory_items = max_memory_items
        self._memory_cache: OrderedDict[str, list[float]] = OrderedDict()
        self._dirty = False
        self._load_disk_cache()

    def _normalize_key(self, text: str) -> str:
        return " ".join(text.lower().strip().split())

    def _load_disk_cache(self) -> None:
        """Load cached embeddings from disk if file exists."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, list):
                                self._memory_cache[k] = v
            except Exception:
                pass  # Corrupted cache — proceed with empty

    def get(self, text: str) -> list[float] | None:
        """Retrieve embedding from cache or return None on miss."""
        key = self._normalize_key(text)
        if key in self._memory_cache:
            self._memory_cache.move_to_end(key)
            return self._memory_cache[key]
        return None

    def set(self, text: str, embedding: list[float]) -> None:
        """Store an embedding in memory and mark cache dirty for flush."""
        key = self._normalize_key(text)
        self._memory_cache[key] = embedding
        self._memory_cache.move_to_end(key)
        self._dirty = True

        if len(self._memory_cache) > self.max_memory_items:
            self._memory_cache.popitem(last=False)

    def save(self) -> None:
        """Persist current memory cache to disk."""
        if not self._dirty:
            return
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(dict(self._memory_cache), f)
            self._dirty = False
        except Exception:
            pass

    def __len__(self) -> int:
        return len(self._memory_cache)
