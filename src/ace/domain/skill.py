"""Domain models for Skills — the atomic unit of the knowledge graph.

These are pure Pydantic models with no database dependency.
They represent the business concept, not the DB table.
"""
from enum import IntEnum

from pydantic import BaseModel, Field


class DifficultyLevel(IntEnum):
    """Cognitive difficulty of acquiring a skill."""
    BEGINNER = 1
    ELEMENTARY = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5


class SkillCategory(str):
    """Loose enum for career-domain categorisation (admin-extensible)."""
    FRONTEND = "Frontend"
    BACKEND = "Backend"
    DEVOPS = "DevOps"
    AI_ML = "AI/ML"
    CYBERSECURITY = "Cybersecurity"
    CLOUD = "Cloud"
    GENERAL = "General"


class Skill(BaseModel):
    """A single learnable skill in the curriculum system."""

    id: str = Field(description="Stable slug identifier, e.g. 'JS_FUNDAMENTALS'")
    name: str = Field(description="Human-readable name, e.g. 'JavaScript Fundamentals'")
    category: str = Field(description="Career-domain grouping")
    description: str = Field(default="", description="What this skill covers")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)
    estimated_hours: int = Field(default=0, ge=0, description="Typical time to acquire")


class SkillGap(BaseModel):
    """A skill that a learner is missing for their selected career."""

    skill: Skill
    is_missing: bool = Field(description="True if learner has not confirmed this skill at all")