"""Unit tests for CandidatePathwayGenerator and strict topological validity."""
import networkx as nx
import pytest

from ace.domain.career import Career, CareerSkillRequirement
from ace.domain.learner import LearnerProfile
from ace.domain.skill import DifficultyLevel, Skill
from ace.graph.builder import build_prerequisite_graph
from ace.graph.graph_metrics import get_graph_metrics
from ace.planner.candidate_generator import CandidatePathwayGenerator


@pytest.fixture
def complex_curriculum():
    skills = [
        Skill(id="math_foundations", name="Math Foundations", category="Foundations", difficulty=DifficultyLevel.BEGINNER, estimated_hours=10),
        Skill(id="prog_logic", name="Programming Logic", category="Foundations", difficulty=DifficultyLevel.BEGINNER, estimated_hours=15),
        Skill(id="data_structures", name="Data Structures", category="CS Core", difficulty=DifficultyLevel.INTERMEDIATE, estimated_hours=30),
        Skill(id="algorithms", name="Algorithms", category="CS Core", difficulty=DifficultyLevel.ADVANCED, estimated_hours=40),
        Skill(id="web_basics", name="Web Basics", category="Frontend", difficulty=DifficultyLevel.BEGINNER, estimated_hours=12),
        Skill(id="react_framework", name="React Framework", category="Frontend", difficulty=DifficultyLevel.INTERMEDIATE, estimated_hours=25),
        Skill(id="backend_api", name="Backend API", category="Backend", difficulty=DifficultyLevel.INTERMEDIATE, estimated_hours=28),
        Skill(id="system_design", name="System Design", category="Architecture", difficulty=DifficultyLevel.EXPERT, estimated_hours=50),
    ]
    # Prerequisite edges: (prereq -> dependent)
    # math_foundations -> data_structures
    # prog_logic -> data_structures
    # data_structures -> algorithms
    # prog_logic -> web_basics
    # web_basics -> react_framework
    # data_structures -> backend_api
    # algorithms -> system_design
    # backend_api -> system_design
    graph = nx.DiGraph()
    for s in skills:
        graph.add_node(s.id, name=s.name, category=s.category, difficulty=int(s.difficulty), estimated_hours=s.estimated_hours)

    edges = [
        ("math_foundations", "data_structures"),
        ("prog_logic", "data_structures"),
        ("data_structures", "algorithms"),
        ("prog_logic", "web_basics"),
        ("web_basics", "react_framework"),
        ("data_structures", "backend_api"),
        ("algorithms", "system_design"),
        ("backend_api", "system_design"),
    ]
    graph.add_edges_from(edges)

    career = Career(
        id="fullstack_lead",
        name="Fullstack Lead",
        required_skills=[
            CareerSkillRequirement(skill_id="system_design", is_mandatory=True, importance=5),
            CareerSkillRequirement(skill_id="react_framework", is_mandatory=True, importance=4),
            CareerSkillRequirement(skill_id="backend_api", is_mandatory=True, importance=4),
            CareerSkillRequirement(skill_id="algorithms", is_mandatory=True, importance=3),
        ],
    )
    return graph, career, {s.id: s for s in skills}


@pytest.mark.unit
def test_all_candidates_satisfy_topological_invariants(complex_curriculum):
    graph, career, skill_map = complex_curriculum
    learner = LearnerProfile(id="test_learner")
    metrics = get_graph_metrics(graph)

    generator = CandidatePathwayGenerator(
        subgraph=graph,
        career=career,
        learner=learner,
        all_skills=skill_map,
        metrics=metrics,
    )

    candidates = generator.generate_all(beam_width=5)
    assert len(candidates) >= 3

    for cand in candidates:
        path = cand.skill_ids
        assert len(path) == len(graph.nodes)
        pos = {sid: idx for idx, sid in enumerate(path)}

        # Strict invariant assertion: for all u -> v, pos[u] < pos[v]
        for u, v in graph.edges:
            assert pos[u] < pos[v], f"Strategy '{cand.strategy}' violated invariant: {u} (pos {pos[u]}) >= {v} (pos {pos[v]})"


@pytest.mark.unit
def test_candidate_diversity(complex_curriculum):
    graph, career, skill_map = complex_curriculum
    learner = LearnerProfile(id="test_learner")
    generator = CandidatePathwayGenerator(subgraph=graph, career=career, learner=learner, all_skills=skill_map)

    foundational = generator.generate_foundational_first()
    quick_wins = generator.generate_quick_wins()

    # Foundational first should schedule low depth/foundation early
    assert foundational.skill_ids[0] in {"math_foundations", "prog_logic"}
    # Quick wins schedules shortest hours first
    assert quick_wins.skill_ids[0] in {"math_foundations", "web_basics"}
