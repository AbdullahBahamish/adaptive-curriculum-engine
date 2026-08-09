from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    student_skills = relationship(
        "StudentSkill",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    roadmaps = relationship(
        "Roadmap",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    student_skills = relationship(
        "StudentSkill",
        back_populates="student",
        cascade="all, delete-orphan"
    )