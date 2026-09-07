"""ORM model for the `skills` table."""
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ace.infrastructure.database.base import Base


class SkillModel(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, comment="Stable slug identifier")
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estimated_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    prerequisites_as_skill: Mapped[list["PrerequisiteModel"]] = relationship(
        "PrerequisiteModel",
        foreign_keys="PrerequisiteModel.skill_id",
        back_populates="skill",
        cascade="all, delete-orphan",
    )
    prerequisites_as_requirement: Mapped[list["PrerequisiteModel"]] = relationship(
        "PrerequisiteModel",
        foreign_keys="PrerequisiteModel.requires_skill_id",
        back_populates="required_skill",
    )


# Avoid circular import
from ace.infrastructure.database.models.prerequisite import PrerequisiteModel  # noqa: E402, F401