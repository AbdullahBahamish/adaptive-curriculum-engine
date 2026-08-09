from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(1000)
    )

    topic = relationship(
        "Topic",
        back_populates="skills"
    )

    job_skills = relationship(
        "JobSkill",
        back_populates="skill",
        cascade="all, delete-orphan"
    )

    student_skills = relationship(
        "StudentSkill",
        back_populates="skill",
        cascade="all, delete-orphan"
    )

    resources = relationship(
        "Resource",
        back_populates="skill",
        cascade="all, delete-orphan"
    )