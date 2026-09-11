"""Domain models for Skills — the atomic unit of the knowledge graph.

These are pure Pydantic models with no database dependency.
They represent the business concept, not the DB table.
"""
from enum import Enum, IntEnum

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


class GapStatus(str, Enum):
    """Categorical gap and readiness classification."""
    MISSING = "MISSING"
    WEAKLY_MASTERED = "WEAKLY_MASTERED"
    ADEQUATELY_MASTERED = "ADEQUATELY_MASTERED"
    STRONGLY_MASTERED = "STRONGLY_MASTERED"
    BLOCKED_BY_PREREQUISITE = "BLOCKED_BY_PREREQUISITE"
    READY_TO_LEARN = "READY_TO_LEARN"


class Skill(BaseModel):
    """A single learnable skill in the curriculum system."""

    id: str = Field(description="Stable slug identifier, e.g. 'JS_FUNDAMENTALS'")
    name: str = Field(description="Human-readable name, e.g. 'JavaScript Fundamentals'")
    category: str = Field(description="Career-domain grouping")
    description: str = Field(default="", description="What this skill covers")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)
    estimated_hours: int = Field(default=0, ge=0, description="Typical time to acquire")


class SkillGap(BaseModel):
    """A skill that a learner is missing or partially mastering for their selected career."""

    skill: Skill
    is_missing: bool = Field(default=True, description="True if learner has not confirmed or strongly mastered this skill")
    mastery: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimated probabilistic mastery in [0, 1]")
    status: GapStatus = Field(default=GapStatus.MISSING, description="Categorical gap/readiness status")
    gap_score: float = Field(default=0.0, ge=0.0, description="Multi-factor weighted gap priority score")
    reason_codes: list[str] = Field(default_factory=list, description="Machine-readable gap reason codes")
    prerequisite_impact: float = Field(default=1.0, ge=0.0, description="Downstream unblocking impact")
    target_relevance: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance to target career")
    is_mandatory: bool = Field(default=True, description="Whether skill is mandatory for career")