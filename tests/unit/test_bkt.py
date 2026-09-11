"""Unit tests for Bayesian Knowledge Tracing (BKT) and Learner Mastery Service."""
import pytest

from ace.domain.learner import LearnerProfile, SkillMasteryState
from ace.learner.bkt import BKTModel, BKTParameters
from ace.learner.mastery_service import LearnerMasteryService


@pytest.mark.unit
def test_bkt_initial_update_success():
    bkt = BKTModel(BKTParameters(p_l0=0.10, p_t=0.15, p_g=0.20, p_s=0.10))
    # Starting from prior 0.10, correct answer should increase mastery
    new_mastery, conf = bkt.update(current_mastery=0.10, evidence=True, evidence_count=0)
    assert new_mastery > 0.10
    assert 0.0 <= new_mastery <= 1.0
    assert conf > 0.0


@pytest.mark.unit
def test_bkt_initial_update_failure():
    bkt = BKTModel(BKTParameters(p_l0=0.50, p_t=0.10, p_g=0.20, p_s=0.10))
    # Answering incorrectly should decrease belief in mastery
    new_mastery, conf = bkt.update(current_mastery=0.50, evidence=False, evidence_count=0)
    assert new_mastery < 0.50
    assert 0.0 <= new_mastery <= 1.0


@pytest.mark.unit
def test_bkt_repeated_successes_converge_towards_mastery():
    bkt = BKTModel()
    mastery = 0.10
    conf = 0.2
    for count in range(6):
        mastery, conf = bkt.update(mastery, evidence=True, evidence_count=count)

    assert mastery > 0.85
    assert conf > 0.70


@pytest.mark.unit
def test_bkt_continuous_score():
    bkt = BKTModel()
    # High score should yield higher posterior than low score
    m_high, _ = bkt.update(0.3, evidence=0.95, evidence_count=1)
    m_low, _ = bkt.update(0.3, evidence=0.10, evidence_count=1)
    assert m_high > m_low


@pytest.mark.unit
def test_bkt_predict_correctness():
    bkt = BKTModel(BKTParameters(p_g=0.2, p_s=0.1))
    p_unmastered = bkt.predict_correctness(mastery=0.0)
    p_mastered = bkt.predict_correctness(mastery=1.0)
    assert p_unmastered == 0.20
    assert p_mastered == 0.90


@pytest.mark.unit
def test_learner_mastery_service_lifecycle():
    service = LearnerMasteryService()
    profile = service.get_or_create_profile("learner-99", confirmed_skills=["html5"])
    assert profile.is_mastered("html5")
    assert profile.get_mastery("html5") == 1.0

    # Record quiz on new skill
    state = service.record_evidence("learner-99", "python_basics", evidence=True, difficulty=2)
    assert state.estimated_mastery > 0.10
    assert state.evidence_count == 1
    assert state.difficulty_history == [2]

    # Another success
    state2 = service.record_evidence("learner-99", "python_basics", evidence=True, difficulty=2)
    assert state2.estimated_mastery > state.estimated_mastery
    assert state2.evidence_count == 2
