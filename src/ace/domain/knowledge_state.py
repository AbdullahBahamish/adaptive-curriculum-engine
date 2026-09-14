"""Knowledge tracing domain contracts and capability protocols."""
from typing import Any, Protocol, runtime_checkable

from ace.domain.learner import SkillMasteryState


@runtime_checkable
class KnowledgeTracer(Protocol):
    """Minimal state-update contract for learner-modelling algorithms."""

    def update_state(
        self,
        state: SkillMasteryState,
        evidence: float | bool,
        evidence_id: str | None = None,
        difficulty: int | None = None,
        **kwargs: Any,
    ) -> SkillMasteryState:
        """Given current state and evidence, compute and return the updated state."""
        ...


@runtime_checkable
class MasteryEstimator(Protocol):
    """Capability protocol for models estimating latent competency P(mastery)."""

    def estimate_mastery(self, state: SkillMasteryState) -> float:
        """Return the estimated latent mastery probability in [0.0, 1.0]."""
        ...


@runtime_checkable
class PerformancePredictor(Protocol):
    """Capability protocol for models predicting future response correctness P(response=1)."""

    def predict_performance(self, state: SkillMasteryState) -> float:
        """Return the predicted probability of correctly answering the next item in [0.0, 1.0]."""
        ...
