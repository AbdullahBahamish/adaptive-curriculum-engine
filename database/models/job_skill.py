from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class JobSkill(Base):
    __tablename__ = "job_skills"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "skill_id",
            name="uq_job_skill"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id"),
        nullable=False
    )

    required_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    # Relationships
    job = relationship(
        "Job",
        back_populates="job_skills"
    )

    skill = relationship(
        "Skill",
        back_populates="job_skills"
    )