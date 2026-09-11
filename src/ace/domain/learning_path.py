from __future__ import annotations

from typing import Any

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
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Structured algorithmic justification codes",
    )
    unblocks_count: int = Field(
        default=0,
        ge=0,
        description="Downstream skills directly or transitively unblocked",
    )
    gap_score: float = Field(
        default=0.0,
        ge=0.0,
        description="Priority gap score of this skill",
    )
    difficulty_step: int = Field(
        default=0,
        description="Cognitive difficulty jump relative to previous step",
    )


class LearningPath(BaseModel):
    """A complete, ordered learning path for a learner targeting a career."""

    learner_id: str
    career_id: str
    career_name: str
    total_skills: int
    total_estimated_hours: int
    steps: list[LearningStep]
    strategy: str = Field(
        default="topological",
        description="Pathway generation archetype/strategy",
    )
    objective_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Normalized multi-objective scores",
    )
    composite_score: float = Field(
        default=0.0,
        description="Weighted composite score",
    )
    alternative_paths: list[LearningPath] = Field(
        default_factory=list,
        description="Diverse non-dominated candidate pathway alternatives",
    )
    pareto_tradeoffs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Trade-off summaries for alternative paths",
    )