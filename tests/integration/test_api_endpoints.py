"""Integration tests for all ACE REST API endpoints.

Tests:
  - Health check endpoint
  - API Key authentication (missing 401, wrong 403, valid 200)
  - Skills CRUD
  - Prerequisites management & automated cycle prevention
  - Careers & requirements management
  - Gap analysis calculation
  - Topological learning path generation
"""
import pytest
from fastapi.testclient import TestClient

from ace.api.main import app
from ace.core.config import settings


def test_health_endpoint(client: TestClient):
    """Health check is open and returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_api_key_authentication(test_db):
    """Endpoints must enforce X-Service-API-Key."""
    from ace.infrastructure.database.session import get_db
    app.dependency_overrides[get_db] = lambda: test_db
    try:
        with TestClient(app) as raw_client:
            # 1. Missing header -> 401
            resp = raw_client.get("/api/v1/skills")
            assert resp.status_code == 401

            # 2. Invalid header -> 403
            resp = raw_client.get("/api/v1/skills", headers={"X-Service-API-Key": "wrong-key"})
            assert resp.status_code == 403

            # 3. Valid header -> 200
            resp = raw_client.get("/api/v1/skills", headers={"X-Service-API-Key": settings.service_api_key})
            assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_skills_crud_flow(client: TestClient):
    """Create, fetch, update, and delete a skill."""
    # 1. Create skill
    payload = {
        "id": "prog_logic",
        "name": "Programming Logic",
        "category": "cs_foundations",
        "description": "Fundamental logic",
        "difficulty": 1,
        "estimated_hours": 20,
    }
    create_resp = client.post("/api/v1/skills", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["id"] == "prog_logic"
    assert created_data["name"] == "Programming Logic"

    # 2. Get skill by ID
    get_resp = client.get("/api/v1/skills/prog_logic")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Programming Logic"

    # 3. Update skill
    update_resp = client.put(
        "/api/v1/skills/prog_logic",
        json={"name": "Programming Logic & Problem Solving", "estimated_hours": 25},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Programming Logic & Problem Solving"
    assert update_resp.json()["estimated_hours"] == 25

    # 4. List skills with search query
    search_resp = client.get("/api/v1/skills", params={"search": "Logic"})
    assert search_resp.status_code == 200
    assert len(search_resp.json()) == 1

    # 5. Delete skill
    del_resp = client.delete("/api/v1/skills/prog_logic")
    assert del_resp.status_code == 204

    # 6. Verify deleted
    not_found_resp = client.get("/api/v1/skills/prog_logic")
    assert not_found_resp.status_code == 404


def test_prerequisites_and_cycle_prevention(client: TestClient):
    """Adding prerequisite edges must enforce DAG constraints and prevent cycles."""
    # Create 3 skills: A, B, C
    for s_id in ["skill_a", "skill_b", "skill_c"]:
        client.post(
            "/api/v1/skills",
            json={"id": s_id, "name": s_id.upper(), "category": "cs_foundations", "difficulty": 1, "estimated_hours": 10},
        )

    # Add edge 1: B requires A (A -> B)
    resp1 = client.post("/api/v1/prerequisites", json={"skill_id": "skill_b", "requires_skill_id": "skill_a"})
    assert resp1.status_code == 201

    # Add edge 2: C requires B (B -> C)
    resp2 = client.post("/api/v1/prerequisites", json={"skill_id": "skill_c", "requires_skill_id": "skill_b"})
    assert resp2.status_code == 201

    # Try to add edge 3: A requires C (C -> A). This would create cycle A -> B -> C -> A!
    cycle_resp = client.post("/api/v1/prerequisites", json={"skill_id": "skill_a", "requires_skill_id": "skill_c"})
    assert cycle_resp.status_code == 400
    assert "cycle" in cycle_resp.json()["detail"].lower()

    # Self-loop: A requires A
    self_loop_resp = client.post("/api/v1/prerequisites", json={"skill_id": "skill_a", "requires_skill_id": "skill_a"})
    assert self_loop_resp.status_code == 400

    # Delete edge
    del_resp = client.delete("/api/v1/prerequisites", params={"skill_id": "skill_b", "requires_skill_id": "skill_a"})
    assert del_resp.status_code == 204


def test_careers_and_requirements(client: TestClient):
    """Create career and manage required skills."""
    # Seed 2 skills
    for s_id in ["html5", "css3"]:
        client.post(
            "/api/v1/skills",
            json={"id": s_id, "name": s_id.upper(), "category": "frontend", "difficulty": 1, "estimated_hours": 15},
        )

    # Create career
    career_payload = {
        "id": "frontend_dev",
        "name": "Frontend Developer",
        "description": "Frontend engineering",
        "required_skills": [
            {"skill_id": "html5", "is_mandatory": True, "importance": 5},
            {"skill_id": "css3", "is_mandatory": False, "importance": 3},
        ],
    }
    resp = client.post("/api/v1/careers", json=career_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "frontend_dev"
    assert len(data["required_skills"]) == 2

    # Get career
    get_resp = client.get("/api/v1/careers/frontend_dev")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Frontend Developer"


def test_gap_analysis_flow(client: TestClient):
    """Gap analysis must accurately identify missing skills and completion percentage."""
    # Setup skills and career
    client.post("/api/v1/skills", json={"id": "html5", "name": "HTML5", "category": "frontend", "difficulty": 1, "estimated_hours": 10})
    client.post("/api/v1/skills", json={"id": "css3", "name": "CSS3", "category": "frontend", "difficulty": 1, "estimated_hours": 15})
    client.post("/api/v1/careers", json={
        "id": "fe_track",
        "name": "Frontend Track",
        "required_skills": [
            {"skill_id": "html5", "is_mandatory": True, "importance": 5},
            {"skill_id": "css3", "is_mandatory": True, "importance": 4},
        ],
    })

    # Learner confirmed 'html5' only
    req_body = {
        "learner_id": "learner-101",
        "career_id": "fe_track",
        "confirmed_skills": [{"skill_id": "html5"}],
    }
    resp = client.post("/api/v1/gap-analysis", json=req_body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["learner_id"] == "learner-101"
    assert data["career_id"] == "fe_track"
    assert data["total_required_skills"] == 2
    assert data["skills_confirmed"] == 1
    assert data["skills_missing"] == 1
    assert data["completion_percentage"] == 50.0
    assert len(data["gaps"]) == 1
    assert data["gaps"][0]["skill_id"] == "css3"


def test_learning_path_generation_flow(client: TestClient):
    """Learning path must be topologically ordered respecting prerequisite dependencies."""
    # Setup skills: html5 -> css3 -> responsive_design
    for sid, name, hrs in [
        ("html5", "HTML5", 10),
        ("css3", "CSS3", 15),
        ("responsive_design", "Responsive Design", 20),
    ]:
        client.post("/api/v1/skills", json={"id": sid, "name": name, "category": "frontend", "difficulty": 1, "estimated_hours": hrs})

    # Prerequisites: css3 requires html5; responsive_design requires css3
    client.post("/api/v1/prerequisites", json={"skill_id": "css3", "requires_skill_id": "html5"})
    client.post("/api/v1/prerequisites", json={"skill_id": "responsive_design", "requires_skill_id": "css3"})

    # Career requires responsive_design
    client.post("/api/v1/careers", json={
        "id": "responsive_designer",
        "name": "Responsive Web Designer",
        "required_skills": [
            {"skill_id": "responsive_design", "is_mandatory": True, "importance": 5},
        ],
    })

    # Learner has no skills confirmed -> engine must pull transitive prereqs (html5 and css3)!
    path_req = {
        "learner_id": "learner-202",
        "career_id": "responsive_designer",
        "confirmed_skills": [],
    }
    resp = client.post("/api/v1/learning-path", json=path_req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_skills"] == 3
    assert data["total_estimated_hours"] == 45

    # Steps must be topologically ordered: html5 (step 1), css3 (step 2), responsive_design (step 3)
    step_skill_ids = [s["skill_id"] for s in data["steps"]]
    assert step_skill_ids == ["html5", "css3", "responsive_design"]
