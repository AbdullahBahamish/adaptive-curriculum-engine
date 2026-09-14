"""Unit tests for Performance Factors Analysis (PFA) response prediction model."""
import pytest

from ace.domain.knowledge_state import KnowledgeTracer, PerformancePredictor
from ace.domain.learner import SkillMasteryState
from ace.learner.pfa import PFAModel, PFAParameters


@pytest.mark.unit
def test_pfa_protocol_conformance():
    pfa = PFAModel()
    state = SkillMasteryState(skill_id="docker_basics", estimated_mastery=0.40)

    assert isinstance(pfa, PerformancePredictor)
    assert isinstance(pfa, KnowledgeTracer)


@pytest.mark.unit
def test_pfa_initial_prediction_and_practice_scaling():
    pfa = PFAModel(default_params=PFAParameters(beta=0.0, mu=0.40, rho=0.10))
    state = SkillMasteryState(skill_id="docker_basics", success_count=0, failure_count=0)

    # 0 practice: logit = 0 -> prob = 0.50
    pred0 = pfa.predict_performance(state)
    assert pred0 == 0.50

    # 3 successes: logit = 0 + 3*0.40 = 1.20 -> prob ~ 0.7685
    state_succ = SkillMasteryState(skill_id="docker_basics", success_count=3, failure_count=0)
    pred_succ = pfa.predict_performance(state_succ)
    assert pred_succ > pred0
    assert round(pred_succ, 2) == 0.77

    # 3 failures: logit = 0 + 3*0.10 = 0.30 -> prob ~ 0.5744
    state_fail = SkillMasteryState(skill_id="docker_basics", success_count=0, failure_count=3)
    pred_fail = pfa.predict_performance(state_fail)
    assert pred_fail > pred0
    assert pred_succ > pred_fail  # Success practice yields stronger improvement than failure


@pytest.mark.unit
def test_pfa_preserves_mastery_state_semantic_integrity():
    pfa = PFAModel()
    initial_state = SkillMasteryState(
        skill_id="react_hooks",
        estimated_mastery=0.62,
        confidence=0.70,
        evidence_count=2,
        success_count=1,
        failure_count=1,
    )

    # Update state through PFA
    updated = pfa.update_state(initial_state, evidence=True)

    # Crucial Invariant: PFA must NOT alter latent estimated_mastery!
    assert updated.estimated_mastery == 0.62
    assert updated.success_count == 2
    assert updated.failure_count == 1
    assert updated.evidence_count == 3
    assert updated.predicted_performance is not None
    assert updated.predicted_performance > 0.50


@pytest.mark.unit
def test_pfa_hierarchical_resolution():
    default_p = PFAParameters(beta=-0.5, mu=0.30, rho=0.05)
    skill_p = {"k8s_deploy": PFAParameters(beta=-1.2, mu=0.50, rho=0.15)}
    category_p = {"cloud_devops": PFAParameters(beta=-0.8, mu=0.40, rho=0.10)}

    pfa = PFAModel(default_params=default_p, skill_params=skill_p, category_params=category_p)

    assert pfa.get_params_for_skill("k8s_deploy").beta == -1.2
    assert pfa.get_params_for_skill("terraform_iac", category="cloud_devops").beta == -0.8
    assert pfa.get_params_for_skill("python_basics", category="backend").beta == -0.5
