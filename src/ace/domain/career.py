"""Domain models for Careers and their skill requirements."""
from pydantic import BaseModel, Field


class CareerSkillRequirement(BaseModel):
    """A skill required by a career, with its importance weight."""

    skill_id: str = Field(description="References Skill.id")
    is_mandatory: bool = Field(
        default=True,
        description="If False, skill is recommended but not required",
    )
    importance: int = Field(
        default=1,
        ge=1,
        le=5,
        description="1=nice-to-have, 5=critical. Used to prioritise gap ordering.",
    )


class Career(BaseModel):
    """A target career that a learner can select."""

    id: str = Field(description="Stable slug, e.g. 'frontend_developer'")
    name: str = Field(description="Display name, e.g. 'Frontend Developer'")
    description: str = Field(default="")
    required_skills: list[CareerSkillRequirement] = Field(default_factory=list)