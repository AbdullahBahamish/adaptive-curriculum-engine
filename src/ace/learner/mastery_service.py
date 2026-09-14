from collections.abc import Sequence
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from ace.domain.learner import (
    ConfirmedSkill,
    LearnerProfile,
    LearningPreferences,
    SkillMasteryState,
)
from ace.learner.bkt import BKTModel, BKTParameters

if TYPE_CHECKING:
    from ace.infrastructure.database.repos.interaction_repo import InteractionRepository
    from ace.infrastructure.database.repos.learner_repo import LearnerRepository


class LearnerMasteryService:
    """Manages probabilistic learner mastery states, practice history, and persistent event logging."""

    def __init__(
        self,
        bkt_model: BKTModel | None = None,
        learner_repo: "LearnerRepository | None" = None,
        interaction_repo: "InteractionRepository | None" = None,
    ) -> None:
        self.bkt = bkt_model or BKTModel(BKTParameters())
        self.learner_repo = learner_repo
        self.interaction_repo = interaction_repo
        self._profiles: dict[str, LearnerProfile] = {}

    def get_or_create_profile(
        self,
        learner_id: str,
        name: str = "",
        confirmed_skills: Sequence[str] = (),
        preferences: LearningPreferences | None = None,
    ) -> LearnerProfile:
        """Retrieve existing learner profile or initialize with confirmed skills."""
        if learner_id in self._profiles:
            return self._profiles[learner_id]

        # Attempt to load from database if repository is configured
        if self.learner_repo is not None:
            loaded = self.learner_repo.load_learner_profile(learner_id)
            if loaded is not None:
                self._profiles[learner_id] = loaded
                return loaded
            # Register new learner in DB
            self.learner_repo.get_or_create_learner(learner_id=learner_id, name=name)

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
            if self.learner_repo is not None:
                self.learner_repo.upsert_skill_state(
                    learner_id=learner_id,
                    skill_id=sid,
                    mastery=1.0,
                    confidence=1.0,
                    evidence_count=1,
                    success_count=1,
                    failure_count=0,
                    last_evidence_id="self_confirmed",
                )

        self._profiles[learner_id] = profile
        return profile

    def record_evidence(
        self,
        learner_id: str,
        skill_id: str,
        evidence: float | bool,
        evidence_id: str | None = None,
        difficulty: int | None = None,
    ) -> SkillMasteryState:
        """Record an interaction event, apply BKT update, and persist raw event & state."""
        # 1. Idempotent interaction recording if interaction repo is configured
        is_correct = (evidence is True) if isinstance(evidence, bool) else (float(evidence) >= 0.5)
        numeric_evidence = 1.0 if evidence is True else (0.0 if evidence is False else float(evidence))

        if self.interaction_repo is not None:
            _, is_new = self.interaction_repo.record_interaction(
                learner_id=learner_id,
                skill_id=skill_id,
                evidence=numeric_evidence,
                is_correct=is_correct,
                difficulty=difficulty,
                evidence_id=evidence_id,
            )
            if not is_new:
                # Duplicate event detected; return existing state without duplicate updating
                profile = self.get_or_create_profile(learner_id)
                if skill_id in profile.mastery_states:
                    return profile.mastery_states[skill_id]

        profile = self.get_or_create_profile(learner_id)
        current_state = profile.mastery_states.get(
            skill_id,
            SkillMasteryState(
                skill_id=skill_id,
                estimated_mastery=self.bkt.get_params_for_skill(skill_id).p_l0 if hasattr(self.bkt, "get_params_for_skill") else self.bkt.params.p_l0,
                confidence=0.3,
                evidence_count=0,
                success_count=0,
                failure_count=0,
            ),
        )

        # 2. BKT State Update
        updated_state = self.bkt.update_state(
            state=current_state,
            evidence=evidence,
            evidence_id=evidence_id,
            difficulty=difficulty,
        )

        # 3. Practice Counts (Separate Success vs Failure)
        new_successes = current_state.success_count + (1 if is_correct else 0)
        new_failures = current_state.failure_count + (0 if is_correct else 1)
        now_iso = datetime.now(timezone.utc).isoformat()

        final_state = SkillMasteryState(
            skill_id=skill_id,
            estimated_mastery=updated_state.estimated_mastery,
            confidence=updated_state.confidence,
            evidence_count=updated_state.evidence_count,
            success_count=new_successes,
            failure_count=new_failures,
            predicted_performance=current_state.predicted_performance,
            last_evidence=evidence_id or current_state.last_evidence,
            difficulty_history=updated_state.difficulty_history,
            last_updated_at=now_iso,
        )

        # 4. Save to DB if repository configured
        if self.learner_repo is not None:
            final_state = self.learner_repo.upsert_skill_state(
                learner_id=learner_id,
                skill_id=skill_id,
                mastery=final_state.estimated_mastery,
                confidence=final_state.confidence,
                evidence_count=final_state.evidence_count,
                success_count=final_state.success_count,
                failure_count=final_state.failure_count,
                predicted_performance=final_state.predicted_performance,
                last_evidence_id=final_state.last_evidence,
            )

        profile.mastery_states[skill_id] = final_state
        return final_state

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

