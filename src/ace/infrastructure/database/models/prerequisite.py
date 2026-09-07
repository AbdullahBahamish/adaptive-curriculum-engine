"""ORM model for prerequisite edges in the skill graph."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ace.infrastructure.database.base import Base


class PrerequisiteModel(Base):
    __tablename__ = "prerequisites"

    skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    requires_skill_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )

    skill: Mapped["SkillModel"] = relationship(
        "SkillModel", foreign_keys=[skill_id], back_populates="prerequisites_as_skill"
    )
    required_skill: Mapped["SkillModel"] = relationship(
        "SkillModel",
        foreign_keys=[requires_skill_id],
        back_populates="prerequisites_as_requirement",
    )


from ace.infrastructure.database.models.skill import SkillModel  # noqa: E402, F401