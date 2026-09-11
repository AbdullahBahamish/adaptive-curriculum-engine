"""Domain model for Prerequisite relationships between skills."""
from pydantic import BaseModel, Field


class Prerequisite(BaseModel):
    """A directed edge in the prerequisite graph.

    Means: to learn `skill_id`, the learner must first have `requires_skill_id`.
    """

    skill_id: str = Field(description="The skill that has a prerequisite")
    requires_skill_id: str = Field(description="The skill that must be learned first")
