"""Integration tests for persistent learner profiles, mastery states, and interaction event stream."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ace.domain.learner import LearningPreferences
from ace.infrastructure.database.base import Base
from ace.infrastructure.database.models import SkillModel
from ace.infrastructure.database.repos.interaction_repo import InteractionRepository
from ace.infrastructure.database.repos.learner_repo import LearnerRepository
from ace.learner.mastery_service import LearnerMasteryService


@pytest.fixture
def test_db_session():
    """Create an isolated in-memory SQLite database for testing persistence."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed test skills
    skill1 = SkillModel(id="python_basics", name="Python Basics", category="backend", difficulty=1, estimated_hours=10)
    skill2 = SkillModel(id="docker_basics", name="Docker Basics", category="cloud_devops", difficulty=2, estimated_hours=15)
    session.add_all([skill1, skill2])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.integration
def test_learner_repository_crud(test_db_session: Session):
    repo = LearnerRepository(test_db_session)

    # 1. Create learner
    learner = repo.get_or_create_learner("learner-001", name="Alice")
    assert learner.id == "learner-001"
    assert learner.name == "Alice"

    # 2. Upsert skill state
    state = repo.upsert_skill_state(
        learner_id="learner-001",
        skill_id="python_basics",
        mastery=0.85,
        confidence=0.75,
        evidence_count=3,
        success_count=3,
        failure_count=0,
        last_evidence_id="quiz-1",
    )
    assert state.skill_id == "python_basics"
    assert state.estimated_mastery == 0.85
    assert state.success_count == 3

    # 3. Load profile
    profile = repo.load_learner_profile("learner-001")
    assert profile is not None
    assert profile.id == "learner-001"
    assert "python_basics" in profile.mastery_states
    assert profile.is_mastered("python_basics")


@pytest.mark.integration
def test_interaction_repository_and_idempotency(test_db_session: Session):
    repo = InteractionRepository(test_db_session)

    # 1. Record first interaction
    record1, is_new1 = repo.record_interaction(
        learner_id="learner-002",
        skill_id="python_basics",
        evidence=1.0,
        is_correct=True,
        difficulty=1,
        evidence_id="evt-101",
    )
    assert is_new1 is True
    assert record1.evidence_id == "evt-101"

    # 2. Re-send identical event with same evidence_id (Idempotency test)
    record2, is_new2 = repo.record_interaction(
        learner_id="learner-002",
        skill_id="python_basics",
        evidence=1.0,
        is_correct=True,
        difficulty=1,
        evidence_id="evt-101",
    )
    assert is_new2 is False
    assert record2.id == record1.id

    # 3. History replay stream length
    history = repo.get_learner_history("learner-002")
    assert len(history) == 1


@pytest.mark.integration
def test_mastery_service_with_persistent_backing(test_db_session: Session):
    learner_repo = LearnerRepository(test_db_session)
    interaction_repo = InteractionRepository(test_db_session)
    service = LearnerMasteryService(learner_repo=learner_repo, interaction_repo=interaction_repo)

    # Record first quiz pass
    st1 = service.record_evidence(
        learner_id="learner-003",
        skill_id="python_basics",
        evidence=True,
        evidence_id="assessment-1",
        difficulty=1,
    )
    assert st1.estimated_mastery > 0.10
    assert st1.evidence_count == 1
    assert st1.success_count == 1
    assert st1.failure_count == 0

    # Duplicate call with same evidence_id should NOT duplicate update
    st_dup = service.record_evidence(
        learner_id="learner-003",
        skill_id="python_basics",
        evidence=True,
        evidence_id="assessment-1",
        difficulty=1,
    )
    assert st_dup.evidence_count == 1
    assert st_dup.success_count == 1
    assert st_dup.estimated_mastery == st1.estimated_mastery

    # Record failure with new evidence_id
    st2 = service.record_evidence(
        learner_id="learner-003",
        skill_id="python_basics",
        evidence=False,
        evidence_id="assessment-2",
        difficulty=2,
    )
    assert st2.evidence_count == 2
    assert st2.success_count == 1
    assert st2.failure_count == 1
    assert st2.estimated_mastery < st1.estimated_mastery

    # Verify event stream in interaction table
    events = interaction_repo.get_learner_history("learner-003")
    assert len(events) == 2
    assert events[0].is_correct is True
    assert events[1].is_correct is False
