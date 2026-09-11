"""Unit tests for semantic embeddings, vector cache, and SkillVectorIndex."""
from pathlib import Path
import pytest

from ace.domain.skill import Skill
from ace.semantic.cache import EmbeddingCache
from ace.semantic.provider import MockEmbeddingProvider
from ace.semantic.vector_index import SkillVectorIndex, normalize_text


@pytest.mark.unit
def test_mock_embedding_provider():
    provider = MockEmbeddingProvider(dimension=384)
    assert provider.dimension == 384
    vec = provider.embed_text("python programming language")
    assert len(vec) == 384
    # Unit normalized
    norm = sum(x * x for x in vec)
    assert pytest.approx(norm, rel=1e-3) == 1.0


@pytest.mark.unit
def test_embedding_cache_operations(tmp_path: Path):
    cache_file = tmp_path / "test_cache.json"
    cache = EmbeddingCache(cache_path=cache_file, max_memory_items=10)

    assert cache.get("hello world") is None
    vec = [0.1, 0.2, 0.3]
    cache.set("hello world", vec)
    assert cache.get("hello world") == vec
    assert cache.get("  HELLO   WORLD  ") == vec  # Key normalization

    cache.save()
    assert cache_file.exists()

    # Reload from disk
    new_cache = EmbeddingCache(cache_path=cache_file)
    assert new_cache.get("hello world") == vec


@pytest.mark.unit
def test_skill_vector_index_search():
    skills = [
        Skill(id="python_core", name="Python Core", category="Backend", description="Object oriented Python"),
        Skill(id="react_ui", name="React UI", category="Frontend", description="React hooks components state"),
        Skill(id="docker_devops", name="Docker", category="DevOps", description="Docker containerization images"),
    ]
    provider = MockEmbeddingProvider()
    index = SkillVectorIndex(provider=provider)
    index.build_from_skills(skills)

    assert index.is_indexed

    # Search for Python
    results = index.search("Python programming", top_k=2, min_score=0.1)
    assert len(results) > 0
    top_skill_id, score = results[0]
    assert top_skill_id == "python_core"
    assert score > 0.0


@pytest.mark.unit
def test_skill_vector_index_precomputed_loader():
    index = SkillVectorIndex()
    loaded = index.load_precomputed("data/processed/canonical_skill_embeddings.json")
    if loaded:
        assert index.is_indexed
        results = index.search("JavaScript DOM HTML", top_k=3, min_score=0.2)
        assert len(results) > 0
