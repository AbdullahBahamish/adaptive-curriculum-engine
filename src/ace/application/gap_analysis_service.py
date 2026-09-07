"""Application Service for Skill Gap Analysis."""
from dataclasses import dataclass
from typing import Sequence

from ace.core.exceptions import CareerNotFoundError
from ace.domain.career import Career
from ace.domain.learner import ConfirmedSkill, LearnerProfile
from ace.domain.skill import SkillGap
from ace.graph.gap_analyzer import compute_skill_gaps
from ace.infrastructure.database.repos.career_repo import CareerRepository
from ace.infrastructure.database.repos.skill_repo import SkillRepository


@dataclass
class GapAnalysisReport:
    """Calculated gap report between learner skills and target career requirements."""
    learner_id: str
    career_id: str
    career_name: str
    total_required_skills: int
    skills_confirmed: int
    skills_missing: int
    completion_percentage: float
    gaps: list[SkillGap]
    career: Career


class GapAnalysisService:
    """Orchestrates skill gap evaluation between a learner and career profile."""

    def __init__(self, career_repo: CareerRepository, skill_repo: SkillRepository):
        self.career_repo = career_repo
        self.skill_repo = skill_repo

    def analyze_gaps(
        self,
        learner_id: str,
        career_id: str,
        confirmed_skill_ids: Sequence[str],
    ) -> GapAnalysisReport:
        """Analyze gaps between confirmed skills and target career requirements.

        Raises:
            CareerNotFoundError: If the career_id does not exist.
        """
        career = self.career_repo.get_career_domain(career_id)
        if career is None:
            raise CareerNotFoundError(f"Career '{career_id}' not found.")

        # Hydrate all required skill objects
        required_skill_ids = [req.skill_id for req in career.required_skills]
        skill_models = self.skill_repo.get_by_ids(required_skill_ids)
        skill_map = {sm.id: self.skill_repo.to_domain(sm) for sm in skill_models}

        learner = LearnerProfile(
            id=learner_id,
            confirmed_skills=[ConfirmedSkill(skill_id=sid) for sid in confirmed_skill_ids],
        )

        gaps = compute_skill_gaps(career=career, learner=learner, all_skills=skill_map)

        total_required = len(career.required_skills)
        skills_missing = len(gaps)
        skills_confirmed = total_required - skills_missing
        completion_pct = round((skills_confirmed / total_required * 100) if total_required else 0.0, 1)

        return GapAnalysisReport(
            learner_id=learner_id,
            career_id=career.id,
            career_name=career.name,
            total_required_skills=total_required,
            skills_confirmed=skills_confirmed,
            skills_missing=skills_missing,
            completion_percentage=completion_pct,
            gaps=gaps,
            career=career,
        )
