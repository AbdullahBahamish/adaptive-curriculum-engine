from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import CheckConstraint

from database.base import Base


class StudentSkill(Base):
    __tablename__ = "student_skills"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "skill_id",
            name="uq_student_skill"
        ),
        CheckConstraint(
            "proficiency_level BETWEEN 1 AND 5",
            name="ck_proficiency_level"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id"),
        nullable=False
    )

    proficiency_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    student = relationship(
        "Student",
        back_populates="student_skills"
    )

    skill = relationship(
        "Skill",
        back_populates="student_skills"
    )