"""Performance Factors Analysis (PFA) Response Performance Model.

Models the cumulative effect of practice on future response correctness:
    logit(P(Y = 1)) = beta_k + mu_k * success_count + rho_k * failure_count
    P(Y = 1) = sigmoid(logit)

where:
    - beta_k: baseline skill intercept / difficulty
    - mu_k: learning rate from successful practice (mu_k > 0)
    - rho_k: learning rate from learning through failure recovery (rho_k >= 0)

Note: PFA computes `predicted_performance` P(response=1). It is semantically
distinct from latent mastery P(mastery). It does NOT modify `estimated_mastery`.
"""
from dataclasses import dataclass
import math

from ace.domain.learner import SkillMasteryState


@dataclass(frozen=True)
class PFAParameters:
    """Hyperparameters for Performance Factors Analysis on a skill."""
    beta: float = 0.0   # Baseline intercept logit (0.0 corresponds to prior 0.50 probability)
    mu: float = 0.35    # Success practice coefficient (log-odds boost per success)
    rho: float = 0.10   # Failure practice coefficient (log-odds boost per failure)


def sigmoid(x: float) -> float:
    """Numerically stable standard logistic sigmoid function."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


class PFAModel:
    """Performance Factors Analysis engine for predicting response correctness."""

    def __init__(
        self,
        default_params: PFAParameters | None = None,
        skill_params: dict[str, PFAParameters] | None = None,
        category_params: dict[str, PFAParameters] | None = None,
    ) -> None:
        self.default_params = default_params or PFAParameters()
        self.skill_params = skill_params or {}
        self.category_params = category_params or {}

    def get_params_for_skill(self, skill_id: str, category: str | None = None) -> PFAParameters:
        """Hierarchical parameter resolution: skill -> category -> global default."""
        if skill_id in self.skill_params:
            return self.skill_params[skill_id]
        if category and category in self.category_params:
            return self.category_params[category]
        return self.default_params

    def predict_performance(self, state: SkillMasteryState, category: str | None = None) -> float:
        """Predict probability of future response correctness P(response=1) in [0.0, 1.0]."""
        params = self.get_params_for_skill(state.skill_id, category=category)
        logit = params.beta + (params.mu * state.success_count) + (params.rho * state.failure_count)
        prob = sigmoid(logit)
        return round(max(0.01, min(0.99, prob)), 4)

    def update_state(
        self,
        state: SkillMasteryState,
        evidence: float | bool,
        evidence_id: str | None = None,
        difficulty: int | None = None,
        category: str | None = None,
    ) -> SkillMasteryState:
        """Update practice counts and compute predicted performance without altering mastery."""
        is_correct = (evidence is True) if isinstance(evidence, bool) else (float(evidence) >= 0.5)
        new_successes = state.success_count + (1 if is_correct else 0)
        new_failures = state.failure_count + (0 if is_correct else 1)

        temp_state = SkillMasteryState(
            skill_id=state.skill_id,
            estimated_mastery=state.estimated_mastery,
            confidence=state.confidence,
            evidence_count=state.evidence_count + 1,
            success_count=new_successes,
            failure_count=new_failures,
            predicted_performance=None,
            last_evidence=evidence_id or state.last_evidence,
            difficulty_history=list(state.difficulty_history) + ([difficulty] if difficulty is not None else []),
            last_updated_at=state.last_updated_at,
        )

        pred = self.predict_performance(temp_state, category=category)
        temp_state.predicted_performance = pred
        return temp_state
