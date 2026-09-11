"""ORM models for Careers and Career-Skill requirements."""
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ace.infrastructure.database.base import Base


class CareerModel(Base):
    __tablename__ = "careers"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")

    required_skills: Mapped[list["CareerSkillModel"]] = relationship(
        "CareerSkillModel", back_populates="career", cascade="all, delete-orphan"
    )


class CareerSkillModel(Base):
    __tablename__ = "career_skills"

    career_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("careers.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    career: Mapped["CareerModel"] = relationship("CareerModel", back_populates="required_skills")
