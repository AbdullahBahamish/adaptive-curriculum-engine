"""Application Service for Skill Gap Analysis."""
from collections.abc import Sequence
from dataclasses import dataclass

from ace.core.exceptions import CareerNotFoundError
from ace.domain.career import Career
from ace.domain.learner import ConfirmedSkill, LearnerProfile, SkillMasteryState
from ace.domain.skill import SkillGap
from ace.graph import build_prerequisite_graph, compute_skill_gaps
from ace.infrastructure.database.repos.career_repo import CareerRepository
from ace.infrastructure.database.repos.prerequisite_repo import PrerequisiteRepository
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

    def __init__(
        self,
        career_repo: CareerRepository,
        skill_repo: SkillRepository,
        prereq_repo: PrerequisiteRepository | None = None,
    ):
        self.career_repo = career_repo
        self.skill_repo = skill_repo
        self.prereq_repo = prereq_repo

    def analyze_gaps(
        self,
        learner_id: str,
        career_id: str,
        confirmed_skill_ids: Sequence[str] = (),
        mastery_states: dict[str, SkillMasteryState] | None = None,
        learner_profile: LearnerProfile | None = None,
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

        if learner_profile is not None:
            learner = learner_profile
        else:
            learner = LearnerProfile(
                id=learner_id,
                confirmed_skills=[ConfirmedSkill(skill_id=sid) for sid in confirmed_skill_ids],
                mastery_states=mastery_states or {},
            )

        # Build graph for prerequisite impact if repo is provided
        graph = None
        if self.prereq_repo is not None:
            all_skills = self.skill_repo.list_all_domain()
            all_prereqs = self.prereq_repo.list_all_domain()
            graph = build_prerequisite_graph(all_skills, all_prereqs)

        gaps = compute_skill_gaps(career=career, learner=learner, all_skills=skill_map, graph=graph)

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

