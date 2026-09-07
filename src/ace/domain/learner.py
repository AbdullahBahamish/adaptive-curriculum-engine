"""Domain models for Learner profiles."""
from pydantic import BaseModel, Field


class ConfirmedSkill(BaseModel):
    """A skill a learner has self-confirmed they possess (binary Yes/No model)."""

    skill_id: str = Field(description="References Skill.id")


class LearnerProfile(BaseModel):
    """A learner and their current confirmed skill set."""

    id: str = Field(description="Learner identifier (from C# backend)")
    name: str = Field(default="")
    confirmed_skills: list[ConfirmedSkill] = Field(default_factory=list)

    @property
    def confirmed_skill_ids(self) -> set[str]:
        """Return the set of skill IDs the learner has confirmed."""
        return {s.skill_id for s in self.confirmed_skills}