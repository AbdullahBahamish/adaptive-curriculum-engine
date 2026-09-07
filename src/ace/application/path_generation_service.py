"""Application Service for Learning Path Generation."""
from typing import Sequence

from ace.core.exceptions import CareerNotFoundError
from ace.domain.learner import ConfirmedSkill, LearnerProfile
from ace.domain.learning_path import LearningPath
from ace.domain.skill import SkillGap
from ace.graph import (
    build_prerequisite_graph,
    compute_skill_gaps,
    generate_learning_path,
)
from ace.infrastructure.database.repos.career_repo import CareerRepository
from ace.infrastructure.database.repos.prerequisite_repo import PrerequisiteRepository
from ace.infrastructure.database.repos.skill_repo import SkillRepository


class PathGenerationService:
    """Orchestrates topological prerequisite resolution and learning path generation."""

    def __init__(
        self,
        career_repo: CareerRepository,
        skill_repo: SkillRepository,
        prereq_repo: PrerequisiteRepository,
    ):
        self.career_repo = career_repo
        self.skill_repo = skill_repo
        self.prereq_repo = prereq_repo

    def generate_path(
        self,
        learner_id: str,
        career_id: str,
        confirmed_skill_ids: Sequence[str],
    ) -> LearningPath:
        """Generate a personalized, topologically ordered curriculum path.

        Raises:
            CareerNotFoundError: If the target career does not exist.
            CycleDetectedError: If a cycle exists in the prerequisite graph.
        """
        career = self.career_repo.get_career_domain(career_id)
        if career is None:
            raise CareerNotFoundError(f"Career '{career_id}' not found.")

        # Load all skills and prerequisite edges from database
        all_skills = self.skill_repo.list_all_domain()
        all_prereqs = self.prereq_repo.list_all_domain()

        graph = build_prerequisite_graph(skills=all_skills, prerequisites=all_prereqs)

        confirmed_set = set(confirmed_skill_ids)
        learner = LearnerProfile(
            id=learner_id,
            confirmed_skills=[ConfirmedSkill(skill_id=sid) for sid in confirmed_set],
        )

        skill_map = {s.id: s for s in all_skills}
        gaps: list[SkillGap] = compute_skill_gaps(
            career=career,
            learner=learner,
            all_skills=skill_map,
        )

        learning_path = generate_learning_path(
            gaps=gaps,
            graph=graph,
            learner_id=learner_id,
            career_id=career.id,
            career_name=career.name,
            confirmed_skill_ids=confirmed_set,
        )

        return learning_path
