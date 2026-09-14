"""ORM model for immutable learner interaction event stream."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ace.infrastructure.database.base import Base


class LearnerInteractionModel(Base):
    """ORM model for `learner_interactions` table.

    Serves as the canonical immutable event store for replaying learner histories
    and training/evaluating knowledge-tracing models.
    """
    __tablename__ = "learner_interactions"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    learner_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("learners.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False
    )
    evidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    learner: Mapped["LearnerModel"] = relationship("LearnerModel", back_populates="interactions")

    __table_args__ = (
        UniqueConstraint("learner_id", "evidence_id", name="uq_learner_evidence_id"),
    )


# Circular import avoidance
from ace.infrastructure.database.models.learner import LearnerModel  # noqa: E402, F401
