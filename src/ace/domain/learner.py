from enum import Enum

from pydantic import BaseModel, Field


class PacePreference(str, Enum):
    """Learning pacing and pathway prioritization preference."""
    BALANCED = "balanced"
    FOUNDATIONAL_FIRST = "foundational_first"
    FAST_TRACK = "fast_track"
    DOMAIN_FOCUSED = "domain_focused"


class LearningPreferences(BaseModel):
    """Learner goals, time budget, and pedagogical preferences."""
    weekly_hours_budget: int = Field(default=10, ge=1, le=80, description="Available study hours per week")
    max_total_hours: int | None = Field(default=None, description="Optional cap on total curriculum hours")
    pace_preference: PacePreference = Field(default=PacePreference.BALANCED)
    preferred_categories: list[str] = Field(default_factory=list, description="Preferred skill domains")


class SkillMasteryState(BaseModel):
    """Estimated probabilistic mastery of an individual skill."""
    skill_id: str = Field(description="References Skill.id")
    estimated_mastery: float = Field(default=0.0, ge=0.0, le=1.0, description="P(mastery) in [0, 1]")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in estimation")
    evidence_count: int = Field(default=0, ge=0, description="Number of observed evaluations/interactions")
    last_evidence: str | None = Field(default=None, description="Identifier of last assessment/quiz")
    difficulty_history: list[int] = Field(default_factory=list, description="Historical item difficulties")


class ConfirmedSkill(BaseModel):
    """A skill a learner has self-confirmed they possess (binary Yes/No model)."""

    skill_id: str = Field(description="References Skill.id")


class LearnerProfile(BaseModel):
    """A comprehensive learner model supporting probabilistic mastery and preferences."""

    id: str = Field(description="Learner identifier (from upstream backend)")
    name: str = Field(default="")
    confirmed_skills: list[ConfirmedSkill] = Field(default_factory=list)
    mastery_states: dict[str, SkillMasteryState] = Field(default_factory=dict)
    preferences: LearningPreferences = Field(default_factory=LearningPreferences)
    target_career_id: str | None = None
    completed_courses: list[str] = Field(default_factory=list)

    @property
    def confirmed_skill_ids(self) -> set[str]:
        """Return set of skill IDs considered mastered (binary confirmation or mastery >= 0.7)."""
        binary_ids = {s.skill_id for s in self.confirmed_skills}
        probabilistic_ids = {
            sid for sid, state in self.mastery_states.items()
            if state.estimated_mastery >= 0.7
        }
        return binary_ids | probabilistic_ids

    def get_mastery(self, skill_id: str) -> float:
        """Return the estimated mastery in [0.0, 1.0] for a skill."""
        if skill_id in self.mastery_states:
            return self.mastery_states[skill_id].estimated_mastery
        if skill_id in {s.skill_id for s in self.confirmed_skills}:
            return 1.0
        return 0.0

    def get_confidence(self, skill_id: str) -> float:
        """Return estimation confidence in [0.0, 1.0] for a skill."""
        if skill_id in self.mastery_states:
            return self.mastery_states[skill_id].confidence
        if skill_id in {s.skill_id for s in self.confirmed_skills}:
            return 1.0
        return 0.0

    def is_mastered(self, skill_id: str, threshold: float = 0.7) -> bool:
        """Check if skill meets or exceeds the mastery threshold."""
        return self.get_mastery(skill_id) >= threshold

    def update_skill_mastery(
        self,
        skill_id: str,
        mastery: float,
        confidence: float,
        evidence_count: int | None = None,
        last_evidence: str | None = None,
    ) -> None:
        """Update or register a skill's mastery state."""
        existing = self.mastery_states.get(skill_id)
        new_count = (existing.evidence_count + 1) if existing and evidence_count is None else (evidence_count or 1)
        self.mastery_states[skill_id] = SkillMasteryState(
            skill_id=skill_id,
            estimated_mastery=max(0.0, min(1.0, mastery)),
            confidence=max(0.0, min(1.0, confidence)),
            evidence_count=new_count,
            last_evidence=last_evidence,
            difficulty_history=list(existing.difficulty_history) if existing else [],
        )