"""Unit tests for the prerequisite graph engine.

These tests validate the core intelligence of the AI layer:
- DAG construction
- Cycle detection
- Topological sort correctness
- Skill gap computation
"""
import pytest
import networkx as nx

from ace.domain.skill import Skill, DifficultyLevel
from ace.domain.prerequisite import Prerequisite
from ace.domain.career import Career, CareerSkillRequirement
from ace.domain.learner import LearnerProfile, ConfirmedSkill
from ace.core.exceptions import CycleDetectedError
from ace.graph.builder import build_prerequisite_graph
from ace.graph.validator import validate_graph
from ace.graph.gap_analyzer import compute_skill_gaps
from ace.graph.solver import generate_learning_path


# --- Fixtures ---

@pytest.fixture
def sample_skills() -> list[Skill]:
    return [
        Skill(id="HTML_CSS",       name="HTML & CSS",              category="Frontend", difficulty=DifficultyLevel.BEGINNER,     estimated_hours=40),
        Skill(id="JS_FUNDAMENTALS",name="JavaScript Fundamentals", category="Frontend", difficulty=DifficultyLevel.ELEMENTARY,   estimated_hours=60),
        Skill(id="REACT_BASICS",   name="React Basics",            category="Frontend", difficulty=DifficultyLevel.INTERMEDIATE, estimated_hours=80),
        Skill(id="TYPESCRIPT",     name="TypeScript",              category="Frontend", difficulty=DifficultyLevel.INTERMEDIATE, estimated_hours=50),
    ]


@pytest.fixture
def sample_prerequisites() -> list[Prerequisite]:
    return [
        Prerequisite(skill_id="JS_FUNDAMENTALS", requires_skill_id="HTML_CSS"),
        Prerequisite(skill_id="REACT_BASICS",    requires_skill_id="JS_FUNDAMENTALS"),
        Prerequisite(skill_id="TYPESCRIPT",      requires_skill_id="JS_FUNDAMENTALS"),
    ]


@pytest.fixture
def sample_graph(sample_skills, sample_prerequisites) -> nx.DiGraph:
    return build_prerequisite_graph(sample_skills, sample_prerequisites)


@pytest.fixture
def frontend_career() -> Career:
    return Career(
        id="frontend_developer",
        name="Frontend Developer",
        required_skills=[
            CareerSkillRequirement(skill_id="HTML_CSS",        is_mandatory=True, importance=5),
            CareerSkillRequirement(skill_id="JS_FUNDAMENTALS", is_mandatory=True, importance=5),
            CareerSkillRequirement(skill_id="REACT_BASICS",    is_mandatory=True, importance=4),
            CareerSkillRequirement(skill_id="TYPESCRIPT",      is_mandatory=True, importance=3),
        ],
    )


# --- Graph Builder Tests ---

@pytest.mark.unit
class TestGraphBuilder:
    def test_builds_correct_node_count(self, sample_graph, sample_skills):
        assert len(sample_graph.nodes) == len(sample_skills)

    def test_builds_correct_edge_count(self, sample_graph, sample_prerequisites):
        assert len(sample_graph.edges) == len(sample_prerequisites)

    def test_edge_direction_is_correct(self, sample_graph):
        # HTML_CSS -> JS_FUNDAMENTALS means HTML_CSS must come first
        assert sample_graph.has_edge("HTML_CSS", "JS_FUNDAMENTALS")

    def test_node_metadata_is_stored(self, sample_graph):
        node = sample_graph.nodes["REACT_BASICS"]
        assert node["name"] == "React Basics"
        assert node["estimated_hours"] == 80


# --- Graph Validator Tests ---

@pytest.mark.unit
class TestGraphValidator:
    def test_valid_dag_passes(self, sample_graph):
        validate_graph(sample_graph)  # Should not raise

    def test_cycle_raises_error(self):
        cyclic_skills = [
            Skill(id="A", name="A", category="Test"),
            Skill(id="B", name="B", category="Test"),
        ]
        cyclic_prereqs = [
            Prerequisite(skill_id="B", requires_skill_id="A"),
            Prerequisite(skill_id="A", requires_skill_id="B"),
        ]
        graph = build_prerequisite_graph(cyclic_skills, cyclic_prereqs)
        with pytest.raises(CycleDetectedError):
            validate_graph(graph)

    def test_cycle_error_contains_cycle_info(self):
        skills = [Skill(id="X", name="X", category="T"), Skill(id="Y", name="Y", category="T")]
        prereqs = [Prerequisite(skill_id="Y", requires_skill_id="X"), Prerequisite(skill_id="X", requires_skill_id="Y")]
        graph = build_prerequisite_graph(skills, prereqs)
        with pytest.raises(CycleDetectedError) as exc_info:
            validate_graph(graph)
        assert len(exc_info.value.cycle) >= 2


# --- Gap Analyzer Tests ---

@pytest.mark.unit
class TestGapAnalyzer:
    def test_learner_with_no_skills_has_all_gaps(self, frontend_career, sample_skills):
        learner = LearnerProfile(id="learner-1", confirmed_skills=[])
        skill_map = {s.id: s for s in sample_skills}
        gaps = compute_skill_gaps(career=frontend_career, learner=learner, all_skills=skill_map)
        assert len(gaps) == 4

    def test_learner_with_all_skills_has_no_gaps(self, frontend_career, sample_skills):
        learner = LearnerProfile(
            id="learner-2",
            confirmed_skills=[ConfirmedSkill(skill_id=s.id) for s in sample_skills],
        )
        skill_map = {s.id: s for s in sample_skills}
        gaps = compute_skill_gaps(career=frontend_career, learner=learner, all_skills=skill_map)
        assert len(gaps) == 0

    def test_gaps_exclude_confirmed_skills(self, frontend_career, sample_skills):
        learner = LearnerProfile(
            id="learner-3",
            confirmed_skills=[ConfirmedSkill(skill_id="HTML_CSS"), ConfirmedSkill(skill_id="JS_FUNDAMENTALS")],
        )
        skill_map = {s.id: s for s in sample_skills}
        gaps = compute_skill_gaps(career=frontend_career, learner=learner, all_skills=skill_map)
        gap_ids = {g.skill.id for g in gaps}
        assert "HTML_CSS" not in gap_ids
        assert "JS_FUNDAMENTALS" not in gap_ids
        assert "REACT_BASICS" in gap_ids


# --- Learning Path Solver Tests ---

@pytest.mark.unit
class TestLearningPathSolver:
    def test_path_respects_prerequisite_order(self, sample_skills, sample_prerequisites, frontend_career):
        graph = build_prerequisite_graph(sample_skills, sample_prerequisites)
        skill_map = {s.id: s for s in sample_skills}
        learner = LearnerProfile(id="l1", confirmed_skills=[])
        gaps = compute_skill_gaps(career=frontend_career, learner=learner, all_skills=skill_map)

        path = generate_learning_path(
            gaps=gaps, graph=graph,
            learner_id="l1", career_id="frontend_developer",
            career_name="Frontend Developer", confirmed_skill_ids=set(),
        )

        step_ids = [s.skill_id for s in path.steps]
        # HTML_CSS must appear before JS_FUNDAMENTALS
        assert step_ids.index("HTML_CSS") < step_ids.index("JS_FUNDAMENTALS")
        # JS_FUNDAMENTALS must appear before REACT_BASICS and TYPESCRIPT
        assert step_ids.index("JS_FUNDAMENTALS") < step_ids.index("REACT_BASICS")
        assert step_ids.index("JS_FUNDAMENTALS") < step_ids.index("TYPESCRIPT")

    def test_path_excludes_confirmed_skills(self, sample_skills, sample_prerequisites, frontend_career):
        graph = build_prerequisite_graph(sample_skills, sample_prerequisites)
        skill_map = {s.id: s for s in sample_skills}
        confirmed = {"HTML_CSS", "JS_FUNDAMENTALS"}
        learner = LearnerProfile(
            id="l2",
            confirmed_skills=[ConfirmedSkill(skill_id=sid) for sid in confirmed],
        )
        gaps = compute_skill_gaps(career=frontend_career, learner=learner, all_skills=skill_map)

        path = generate_learning_path(
            gaps=gaps, graph=graph,
            learner_id="l2", career_id="frontend_developer",
            career_name="Frontend Developer", confirmed_skill_ids=confirmed,
        )

        step_ids = {s.skill_id for s in path.steps}
        assert "HTML_CSS" not in step_ids
        assert "JS_FUNDAMENTALS" not in step_ids

    def test_total_hours_is_sum_of_step_hours(self, sample_skills, sample_prerequisites, frontend_career):
        graph = build_prerequisite_graph(sample_skills, sample_prerequisites)
        skill_map = {s.id: s for s in sample_skills}
        learner = LearnerProfile(id="l3", confirmed_skills=[])
        gaps = compute_skill_gaps(career=frontend_career, learner=learner, all_skills=skill_map)
        path = generate_learning_path(
            gaps=gaps, graph=graph, learner_id="l3",
            career_id="frontend_developer", career_name="Frontend Developer",
            confirmed_skill_ids=set(),
        )
        assert path.total_estimated_hours == sum(s.estimated_hours for s in path.steps)