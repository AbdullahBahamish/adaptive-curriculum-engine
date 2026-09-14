"""ORM models for learner profiles and persistent skill mastery states."""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ace.infrastructure.database.base import Base


class LearnerModel(Base):
    """ORM model for `learners` table."""
    __tablename__ = "learners"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    target_career_id: Mapped[str | None] = mapped_column(
        String(100), ForeignKey("careers.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    skill_states: Mapped[list["LearnerSkillStateModel"]] = relationship(
        "LearnerSkillStateModel",
        back_populates="learner",
        cascade="all, delete-orphan",
    )
    interactions: Mapped[list["LearnerInteractionModel"]] = relationship(
        "LearnerInteractionModel",
        back_populates="learner",
        cascade="all, delete-orphan",
    )


class LearnerSkillStateModel(Base):
    """ORM model for `learner_skill_states` table."""
    __tablename__ = "learner_skill_states"

    learner_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("learners.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    estimated_mastery: Mapped[float] = mapped_column(Float, nullable=False, default=0.10)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.30)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    predicted_performance: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_evidence_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    learner: Mapped["LearnerModel"] = relationship("LearnerModel", back_populates="skill_states")


# Circular import avoidance
from ace.infrastructure.database.models.interaction import LearnerInteractionModel  # noqa: E402, F401
