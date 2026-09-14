"""Unit tests for hierarchical per-skill BKT parameter resolution and protocol conformance."""
import pytest

from ace.domain.knowledge_state import MasteryEstimator
from ace.domain.learner import SkillMasteryState
from ace.learner.bkt import BKTModel, BKTParameters


@pytest.mark.unit
def test_bkt_hierarchical_resolution():
    default_p = BKTParameters(p_l0=0.10, p_t=0.15, p_g=0.20, p_s=0.10)
    category_p = {"backend": BKTParameters(p_l0=0.20, p_t=0.25, p_g=0.15, p_s=0.08)}
    skill_p = {"docker_basics": BKTParameters(p_l0=0.30, p_t=0.35, p_g=0.10, p_s=0.05)}

    bkt = BKTModel(params=default_p, skill_params=skill_p, category_params=category_p)

    # 1. Direct skill match
    res_skill = bkt.get_params_for_skill("docker_basics", category="cloud_devops")
    assert res_skill.p_l0 == 0.30
    assert res_skill.p_t == 0.35

    # 2. Category fallback match
    res_cat = bkt.get_params_for_skill("python_basics", category="backend")
    assert res_cat.p_l0 == 0.20
    assert res_cat.p_t == 0.25

    # 3. Global default fallback
    res_default = bkt.get_params_for_skill("unknown_skill", category="unknown_cat")
    assert res_default.p_l0 == 0.10
    assert res_default.p_t == 0.15


@pytest.mark.unit
def test_bkt_behavioral_equivalence_with_defaults():
    # Verify that BKTModel with defaults behaves identically to standard BKT
    params = BKTParameters(p_l0=0.10, p_t=0.15, p_g=0.20, p_s=0.10)
    bkt = BKTModel(params=params)

    # Update with True evidence from prior 0.10
    mastery, conf = bkt.update(current_mastery=0.10, evidence=True, evidence_count=0)

    # Hand calculation:
    # denom = 0.10*(1-0.10) + 0.90*(0.20) = 0.09 + 0.18 = 0.27
    # posterior = 0.09 / 0.27 = 0.3333...
    # transition = 0.3333... + (1 - 0.3333...)*0.15 = 0.3333... + 0.10 = 0.4333...
    assert round(mastery, 2) == 0.43
    assert conf > 0.0


@pytest.mark.unit
def test_bkt_mastery_estimator_protocol():
    bkt = BKTModel()
    state = SkillMasteryState(skill_id="test_skill", estimated_mastery=0.78, confidence=0.82)

    # Conforms to MasteryEstimator
    assert isinstance(bkt, MasteryEstimator)
    assert bkt.estimate_mastery(state) == 0.78
