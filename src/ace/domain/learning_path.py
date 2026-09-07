"""Domain models for generated Learning Paths."""
from pydantic import BaseModel, Field


class LearningStep(BaseModel):
    """A single ordered step in a learning path."""

    order: int = Field(description="1-based position in the learning sequence")
    skill_id: str
    skill_name: str
    category: str
    estimated_hours: int
    rationale: str = Field(
        default="",
        description="Why this skill appears at this position (graph-derived or LLM-generated)",
    )
    prerequisites_satisfied: list[str] = Field(
        default_factory=list,
        description="Skill IDs that must be completed before this step",
    )


class LearningPath(BaseModel):
    """A complete, ordered learning path for a learner targeting a career."""

    learner_id: str
    career_id: str
    career_name: str
    total_skills: int
    total_estimated_hours: int
    steps: list[LearningStep]