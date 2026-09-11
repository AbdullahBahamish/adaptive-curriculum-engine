"""Mastery tracking service for maintaining and updating learner states."""
from collections.abc import Sequence

from ace.domain.learner import (
    ConfirmedSkill,
    LearnerProfile,
    LearningPreferences,
    SkillMasteryState,
)
from ace.learner.bkt import BKTModel, BKTParameters


class LearnerMasteryService:
    """Manages probabilistic learner mastery states and incremental evidence updates."""

    def __init__(self, bkt_model: BKTModel | None = None) -> None:
        self.bkt = bkt_model or BKTModel(BKTParameters())
        self._profiles: dict[str, LearnerProfile] = {}

    def get_or_create_profile(
        self,
        learner_id: str,
        name: str = "",
        confirmed_skills: Sequence[str] = (),
        preferences: LearningPreferences | None = None,
    ) -> LearnerProfile:
        """Retrieve existing learner profile or initialize with confirmed skills."""
        if learner_id not in self._profiles:
            profile = LearnerProfile(
                id=learner_id,
                name=name,
                confirmed_skills=[ConfirmedSkill(skill_id=sid) for sid in confirmed_skills],
                preferences=preferences or LearningPreferences(),
            )
            # Initialize confirmed skills with high mastery and confidence
            for sid in confirmed_skills:
                profile.update_skill_mastery(
                    skill_id=sid,
                    mastery=1.0,
                    confidence=1.0,
                    evidence_count=1,
                    last_evidence="self_confirmed",
                )
            self._profiles[learner_id] = profile

        return self._profiles[learner_id]

    def record_evidence(
        self,
        learner_id: str,
        skill_id: str,
        evidence: float | bool,
        evidence_id: str | None = None,
        difficulty: int | None = None,
    ) -> SkillMasteryState:
        """Record an assessment or practice observation for a skill and update BKT mastery."""
        profile = self.get_or_create_profile(learner_id)
        current_state = profile.mastery_states.get(
            skill_id,
            SkillMasteryState(
                skill_id=skill_id,
                estimated_mastery=self.bkt.params.p_l0,
                confidence=0.3,
                evidence_count=0,
            ),
        )

        updated_state = self.bkt.update_state(
            state=current_state,
            evidence=evidence,
            evidence_id=evidence_id,
            difficulty=difficulty,
        )
        profile.mastery_states[skill_id] = updated_state
        return updated_state

    def batch_record_evidence(
        self,
        learner_id: str,
        observations: list[tuple[str, float | bool]],
    ) -> list[SkillMasteryState]:
        """Process a sequence of observations (skill_id, score)."""
        results = []
        for skill_id, evidence in observations:
            results.append(self.record_evidence(learner_id, skill_id, evidence))
        return results
