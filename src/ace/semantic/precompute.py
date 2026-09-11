"""Precompute canonical embeddings for all seed skills and store on disk.

This script ensures instant zero-model startup for production ACE deployments.
"""
import json
import time
from pathlib import Path

from ace.semantic.provider import LocalSentenceTransformer, MockEmbeddingProvider


def precompute_canonical_embeddings(
    skills_path: str | Path = "data/seed/skills.json",
    output_path: str | Path = "data/processed/canonical_skill_embeddings.json",
    use_mock: bool = False,
) -> dict[str, list[float]]:
    """Generate and serialize embeddings for all canonical skills."""
    skills_file = Path(skills_path)
    out_file = Path(output_path)

    if not skills_file.exists():
        raise FileNotFoundError(f"Skills file not found: {skills_file}")

    with open(skills_file, encoding="utf-8") as f:
        skills = json.load(f)

    print(f"Loaded {len(skills)} canonical skills from {skills_file}")
    t0 = time.time()

    if use_mock:
        provider = MockEmbeddingProvider()
    else:
        try:
            provider = LocalSentenceTransformer("all-MiniLM-L6-v2")
        except Exception as exc:
            print(f"SentenceTransformer unavailable ({exc}), falling back to MockEmbeddingProvider")
            provider = MockEmbeddingProvider()

    skill_ids: list[str] = []
    texts: list[str] = []
    for s in skills:
        skill_ids.append(s["id"])
        name = s.get("name", "")
        cat = s.get("category", "")
        desc = s.get("description", "")
        texts.append(f"{name} ({cat}): {desc}".strip())

    vectors = provider.embed_batch(texts)
    embeddings_map = {sid: vec for sid, vec in zip(skill_ids, vectors)}

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(embeddings_map, f)

    elapsed = time.time() - t0
    print(f"Precomputed {len(embeddings_map)} embeddings in {elapsed:.2f}s -> Saved to {out_file}")
    return embeddings_map


if __name__ == "__main__":
    precompute_canonical_embeddings()
