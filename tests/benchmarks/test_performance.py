"""Performance and resource constraint benchmarks for ACE on CPU."""
import json
import time
import tracemalloc
import pytest

from ace.domain.career import Career, CareerSkillRequirement
from ace.domain.learner import LearnerProfile
from ace.domain.prerequisite import Prerequisite
from ace.domain.skill import Skill
from ace.graph.builder import build_prerequisite_graph
from ace.graph.gap_analyzer import compute_skill_gaps
from ace.graph.solver import generate_learning_path
from ace.semantic.vector_index import SkillVectorIndex


@pytest.fixture(scope="module")
def benchmark_data():
    with open("data/seed/skills.json", "r", encoding="utf-8") as f:
        skills = [Skill(**s) for s in json.load(f)]
    with open("data/seed/prerequisites.json", "r", encoding="utf-8") as f:
        prereqs = [Prerequisite(**p) for p in json.load(f)]
    with open("data/seed/careers.json", "r", encoding="utf-8") as f:
        careers_raw = json.load(f)

    graph = build_prerequisite_graph(skills, prereqs)
    target_career = Career(
        id=careers_raw[0]["id"],
        name=careers_raw[0]["name"],
        required_skills=[CareerSkillRequirement(**r) for r in careers_raw[0]["required_skills"]],
    )
    skill_map = {s.id: s for s in skills}

    vector_index = SkillVectorIndex()
    vector_index.load_precomputed("data/processed/canonical_skill_embeddings.json")

    return graph, target_career, skill_map, vector_index


@pytest.mark.unit
def test_vector_search_latency(benchmark_data):
    _, _, _, vector_index = benchmark_data
    if not vector_index.is_indexed:
        pytest.skip("Precomputed embeddings not found")

    # Warmup
    vector_index.search("python programming", top_k=5)

    times = []
    for _ in range(50):
        t0 = time.perf_counter()
        results = vector_index.search("react frontend components", top_k=5)
        times.append((time.perf_counter() - t0) * 1000)

    avg_ms = sum(times) / len(times)
    # Cosine vector retrieval should execute in < 2.0ms on CPU
    assert avg_ms < 2.0, f"Vector search average latency {avg_ms:.2f}ms exceeded 2.0ms ceiling"


@pytest.mark.unit
def test_end_to_end_path_generation_latency(benchmark_data):
    graph, target_career, skill_map, _ = benchmark_data
    learner = LearnerProfile(id="bench_learner")

    gaps = compute_skill_gaps(target_career, learner, skill_map, graph=graph)

    # Warmup
    generate_learning_path(
        gaps=gaps,
        graph=graph,
        learner_id=learner.id,
        career_id=target_career.id,
        career_name=target_career.name,
        confirmed_skill_ids=set(),
        career=target_career,
        learner=learner,
        all_skills=skill_map,
    )

    times = []
    for _ in range(20):
        t0 = time.perf_counter()
        path = generate_learning_path(
            gaps=gaps,
            graph=graph,
            learner_id=learner.id,
            career_id=target_career.id,
            career_name=target_career.name,
            confirmed_skill_ids=set(),
            career=target_career,
            learner=learner,
            all_skills=skill_map,
        )
        times.append((time.perf_counter() - t0) * 1000)

    avg_ms = sum(times) / len(times)
    # Average latency must be < 35.0ms on CPU
    assert avg_ms < 35.0, f"Average latency {avg_ms:.2f}ms exceeded 35.0ms ceiling"


@pytest.mark.unit
def test_memory_ceiling_under_150mb(benchmark_data):
    tracemalloc.start()
    graph, target_career, skill_map, _ = benchmark_data
    learner = LearnerProfile(id="mem_learner")
    gaps = compute_skill_gaps(target_career, learner, skill_map, graph=graph)

    # Run 10 iterations
    for _ in range(10):
        generate_learning_path(
            gaps=gaps,
            graph=graph,
            learner_id=learner.id,
            career_id=target_career.id,
            career_name=target_career.name,
            confirmed_skill_ids=set(),
            career=target_career,
            learner=learner,
            all_skills=skill_map,
            return_alternatives=True,
        )

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = peak / (1024 * 1024)

    # Must stay well under 150MB memory ceiling
    assert peak_mb < 150.0, f"Peak memory {peak_mb:.2f}MB exceeded 150MB ceiling"
