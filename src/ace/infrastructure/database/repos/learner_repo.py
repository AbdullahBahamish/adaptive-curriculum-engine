"""Repository for persistent LearnerProfile and SkillMasteryState operations."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ace.domain.learner import ConfirmedSkill, LearnerProfile, SkillMasteryState
from ace.infrastructure.database.models.learner import LearnerModel, LearnerSkillStateModel
from ace.infrastructure.database.repos.base import BaseRepository


class LearnerRepository(BaseRepository[LearnerModel]):
    """Provides database CRUD and domain mapping for learners and skill states."""

    def __init__(self, db: Session) -> None:
        super().__init__(LearnerModel, db)

    def get_or_create_learner(
        self,
        learner_id: str,
        name: str = "",
        target_career_id: str | None = None,
    ) -> LearnerModel:
        """Fetch existing learner record or create a new one."""
        learner = self.get(learner_id)
        if learner is None:
            learner = LearnerModel(
                id=learner_id,
                name=name or f"Learner {learner_id}",
                target_career_id=target_career_id,
            )
            self.db.add(learner)
            self.db.commit()
            self.db.refresh(learner)
        return learner

    def get_skill_states(self, learner_id: str) -> dict[str, SkillMasteryState]:
        """Fetch all persistent skill mastery states for a learner as domain objects."""
        stmt = select(LearnerSkillStateModel).where(LearnerSkillStateModel.learner_id == learner_id)
        records = self.db.scalars(stmt).all()

        domain_states: dict[str, SkillMasteryState] = {}
        for r in records:
            domain_states[r.skill_id] = SkillMasteryState(
                skill_id=r.skill_id,
                estimated_mastery=r.estimated_mastery,
                confidence=r.confidence,
                evidence_count=r.evidence_count,
                success_count=r.success_count,
                failure_count=r.failure_count,
                predicted_performance=r.predicted_performance,
                last_evidence=r.last_evidence_id,
                last_updated_at=r.last_updated_at.isoformat() if r.last_updated_at else None,
            )
        return domain_states

    def upsert_skill_state(
        self,
        learner_id: str,
        skill_id: str,
        mastery: float,
        confidence: float,
        evidence_count: int,
        success_count: int = 0,
        failure_count: int = 0,
        predicted_performance: float | None = None,
        last_evidence_id: str | None = None,
    ) -> SkillMasteryState:
        """Update or insert a skill mastery state in the database."""
        # Ensure learner exists
        self.get_or_create_learner(learner_id)

        stmt = select(LearnerSkillStateModel).where(
            LearnerSkillStateModel.learner_id == learner_id,
            LearnerSkillStateModel.skill_id == skill_id,
        )
        record = self.db.scalars(stmt).first()

        if record is None:
            record = LearnerSkillStateModel(
                learner_id=learner_id,
                skill_id=skill_id,
                estimated_mastery=mastery,
                confidence=confidence,
                evidence_count=evidence_count,
                success_count=success_count,
                failure_count=failure_count,
                predicted_performance=predicted_performance,
                last_evidence_id=last_evidence_id,
            )
            self.db.add(record)
        else:
            record.estimated_mastery = mastery
            record.confidence = confidence
            record.evidence_count = evidence_count
            record.success_count = success_count
            record.failure_count = failure_count
            if predicted_performance is not None:
                record.predicted_performance = predicted_performance
            record.last_evidence_id = last_evidence_id

        self.db.commit()
        self.db.refresh(record)

        return SkillMasteryState(
            skill_id=record.skill_id,
            estimated_mastery=record.estimated_mastery,
            confidence=record.confidence,
            evidence_count=record.evidence_count,
            success_count=record.success_count,
            failure_count=record.failure_count,
            predicted_performance=record.predicted_performance,
            last_evidence=record.last_evidence_id,
            last_updated_at=record.last_updated_at.isoformat() if record.last_updated_at else None,
        )

    def load_learner_profile(self, learner_id: str) -> LearnerProfile | None:
        """Load a full LearnerProfile domain entity from the database."""
        learner = self.get(learner_id)
        if learner is None:
            return None

        states = self.get_skill_states(learner_id)
        confirmed = [
            ConfirmedSkill(skill_id=sid)
            for sid, state in states.items()
            if state.last_evidence == "self_confirmed" or state.estimated_mastery >= 0.70
        ]

        return LearnerProfile(
            id=learner.id,
            name=learner.name,
            target_career_id=learner.target_career_id,
            confirmed_skills=confirmed,
            mastery_states=states,
        )
