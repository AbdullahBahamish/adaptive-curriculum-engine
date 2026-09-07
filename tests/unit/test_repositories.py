"""Unit tests for Database Repositories using an in-memory SQLite database."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ace.infrastructure.database.base import Base
from ace.infrastructure.database.models import SkillModel, PrerequisiteModel, CareerModel
from ace.infrastructure.database.repos import (
    SkillRepository,
    PrerequisiteRepository,
    CareerRepository,
)


@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite database and session for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_skill_repository_crud(db_session):
    repo = SkillRepository(db_session)
    assert repo.count() == 0

    # Create
    skill_model = SkillModel(
        id="python_basics",
        name="Python Basics",
        category="backend",
        description="Core Python",
        difficulty=1,
        estimated_hours=20,
    )
    repo.create(skill_model)
    assert repo.count() == 1

    # Fetch
    fetched = repo.get_by_id("python_basics")
    assert fetched is not None
    assert fetched.name == "Python Basics"

    # Hydrate domain
    domain_skill = repo.to_domain(fetched)
    assert domain_skill.id == "python_basics"
    assert domain_skill.difficulty == 1

    # Query by category
    backend_skills = repo.list_by_category("backend")
    assert len(backend_skills) == 1
    assert repo.list_by_category("frontend") == []


def test_prerequisite_repository(db_session):
    skill_repo = SkillRepository(db_session)
    prereq_repo = PrerequisiteRepository(db_session)

    # Add 2 skills
    skill_repo.create(SkillModel(id="python_basics", name="Python Basics", category="backend"))
    skill_repo.create(SkillModel(id="python_advanced", name="Python Advanced", category="backend"))

    # Add prerequisite: python_advanced requires python_basics
    edge = PrerequisiteModel(skill_id="python_advanced", requires_skill_id="python_basics")
    prereq_repo.create(edge)

    prereqs = prereq_repo.get_prerequisites_for_skill("python_advanced")
    assert len(prereqs) == 1
    assert prereqs[0].requires_skill_id == "python_basics"

    dependents = prereq_repo.get_dependents_for_skill("python_basics")
    assert len(dependents) == 1
    assert dependents[0].skill_id == "python_advanced"

    # Delete edge
    deleted = prereq_repo.delete_edge("python_advanced", "python_basics")
    assert deleted is True
    assert len(prereq_repo.get_prerequisites_for_skill("python_advanced")) == 0


def test_career_repository(db_session):
    skill_repo = SkillRepository(db_session)
    career_repo = CareerRepository(db_session)

    skill_repo.create(SkillModel(id="react_basics", name="React Basics", category="frontend"))
    skill_repo.create(SkillModel(id="typescript", name="TypeScript", category="frontend"))

    career_model = CareerModel(id="frontend_developer", name="Frontend Developer", description="Frontend track")
    career_repo.create(career_model)

    # Add requirements
    career_repo.add_or_update_required_skill("frontend_developer", "react_basics", is_mandatory=True, importance=5)
    career_repo.add_or_update_required_skill("frontend_developer", "typescript", is_mandatory=False, importance=3)

    career_domain = career_repo.get_career_domain("frontend_developer")
    assert career_domain is not None
    assert len(career_domain.required_skills) == 2
    assert career_domain.required_skills[0].skill_id in ("react_basics", "typescript")

    # Remove requirement
    removed = career_repo.remove_required_skill("frontend_developer", "typescript")
    assert removed is True
    updated_domain = career_repo.get_career_domain("frontend_developer")
    assert len(updated_domain.required_skills) == 1
    assert updated_domain.required_skills[0].skill_id == "react_basics"
