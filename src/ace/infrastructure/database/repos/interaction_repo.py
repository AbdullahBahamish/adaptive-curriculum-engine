"""Repository for immutable learner interaction event stream."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ace.infrastructure.database.models.interaction import LearnerInteractionModel
from ace.infrastructure.database.models.learner import LearnerModel
from ace.infrastructure.database.repos.base import BaseRepository


class InteractionRepository(BaseRepository[LearnerInteractionModel]):
    """Provides append-only interaction logging with idempotency verification."""

    def __init__(self, db: Session) -> None:
        super().__init__(LearnerInteractionModel, db)

    def record_interaction(
        self,
        learner_id: str,
        skill_id: str,
        evidence: float,
        is_correct: bool,
        difficulty: int | None = None,
        evidence_id: str | None = None,
    ) -> tuple[LearnerInteractionModel, bool]:
        """Record an interaction event.

        Returns:
            tuple of (interaction_record, is_new: bool).
            If `evidence_id` is provided and an interaction with `(learner_id, evidence_id)`
            already exists, returns (existing_record, False) to prevent duplicate counting.
        """
        # Idempotency check if evidence_id is supplied
        if evidence_id is not None:
            stmt = select(LearnerInteractionModel).where(
                LearnerInteractionModel.learner_id == learner_id,
                LearnerInteractionModel.evidence_id == evidence_id,
            )
            existing = self.db.scalars(stmt).first()
            if existing is not None:
                return existing, False

        # Ensure learner exists before recording interaction
        learner = self.db.get(LearnerModel, learner_id)
        if learner is None:
            learner = LearnerModel(id=learner_id, name=f"Learner {learner_id}")
            self.db.add(learner)
            self.db.flush()

        interaction = LearnerInteractionModel(
            learner_id=learner_id,
            skill_id=skill_id,
            evidence=evidence,
            is_correct=is_correct,
            difficulty=difficulty,
            evidence_id=evidence_id,
        )
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)

        return interaction, True

    def get_learner_history(
        self,
        learner_id: str,
        skill_id: str | None = None,
    ) -> list[LearnerInteractionModel]:
        """Return chronological interaction events for a learner (replay stream)."""
        stmt = select(LearnerInteractionModel).where(LearnerInteractionModel.learner_id == learner_id)
        if skill_id is not None:
            stmt = stmt.where(LearnerInteractionModel.skill_id == skill_id)
        stmt = stmt.order_by(LearnerInteractionModel.created_at.asc(), LearnerInteractionModel.id.asc())
        return list(self.db.scalars(stmt).all())
