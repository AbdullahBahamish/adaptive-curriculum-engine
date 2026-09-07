"""Tests for the seed dataset.

Validates:
  1. All 3 seed JSON files exist (skills.json, prerequisites.json, careers.json).
  2. Exactly 112 skills exist across the 7 recognized categories.
  3. Exactly 6 target careers exist.
  4. Prerequisite graph forms a valid Directed Acyclic Graph (DAG) with zero cycles.
  5. Referential integrity: all prerequisite endpoints and career required skills exist.
  6. Every career has at least one mandatory skill.
"""
import json
from pathlib import Path
import pytest
import networkx as nx

from ace.domain.skill import Skill
from ace.domain.prerequisite import Prerequisite
from ace.graph.builder import build_prerequisite_graph
from ace.graph.validator import validate_graph, CycleDetectedError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SEED_DIR = PROJECT_ROOT / "data" / "seed"


@pytest.fixture
def skills_data() -> list[dict]:
    path = SEED_DIR / "skills.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def prerequisites_data() -> list[dict]:
    path = SEED_DIR / "prerequisites.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def careers_data() -> list[dict]:
    path = SEED_DIR / "careers.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_seed_skills_count_and_categories(skills_data):
    """Seed dataset must define 112 skills covering all 7 technical domains."""
    assert len(skills_data) == 112

    skill_ids = [s["id"] for s in skills_data]
    assert len(skill_ids) == len(set(skill_ids)), "Duplicate skill IDs found!"

    expected_categories = {
        "cs_foundations",
        "frontend",
        "backend",
        "cloud_devops",
        "cybersecurity",
        "data_ai_ml",
        "software_engineering_practices",
    }
    found_categories = {s["category"] for s in skills_data}
    assert found_categories == expected_categories


def test_seed_careers_definition(careers_data, skills_data):
    """Seed dataset must define the 6 primary careers with valid skill links."""
    assert len(careers_data) == 6

    expected_careers = {
        "frontend_developer",
        "backend_developer",
        "fullstack_developer",
        "ai_ml_engineer",
        "cybersecurity_analyst",
        "cloud_engineer",
    }
    found_careers = {c["id"] for c in careers_data}
    assert found_careers == expected_careers

    skill_id_set = {s["id"] for s in skills_data}

    for career in careers_data:
        reqs = career.get("required_skills", [])
        assert len(reqs) > 0, f"Career {career['id']} has no required skills"

        # Must have at least one mandatory skill
        mandatory = [r for r in reqs if r.get("is_mandatory", False)]
        assert len(mandatory) > 0, f"Career {career['id']} has no mandatory skills"

        # Check all referenced skills exist in skills.json
        for r in reqs:
            assert r["skill_id"] in skill_id_set, (
                f"Career '{career['id']}' references unknown skill '{r['skill_id']}'"
            )


def test_seed_prerequisites_referential_integrity(prerequisites_data, skills_data):
    """Every prerequisite edge must connect two valid, distinct skills in skills.json."""
    skill_id_set = {s["id"] for s in skills_data}
    assert len(prerequisites_data) > 0

    for p in prerequisites_data:
        s_id = p["skill_id"]
        req_id = p["requires_skill_id"]
        assert s_id in skill_id_set, f"Prerequisite references unknown skill_id: {s_id}"
        assert req_id in skill_id_set, f"Prerequisite references unknown requires_skill_id: {req_id}"
        assert s_id != req_id, f"Self-referential prerequisite detected: {s_id}"


def test_seed_graph_is_valid_dag(skills_data, prerequisites_data):
    """The graph constructed from the seed data must be an acyclic DAG."""
    skills = [Skill(**s) for s in skills_data]
    prereqs = [Prerequisite(**p) for p in prerequisites_data]

    graph = build_prerequisite_graph(skills, prereqs)
    assert len(graph.nodes) == 112

    # validate_graph will raise CycleDetectedError if not a DAG
    validate_graph(graph)
    assert nx.is_directed_acyclic_graph(graph) is True
