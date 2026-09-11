"""Application Service for Learning Path Generation."""
from collections.abc import Sequence

from ace.core.exceptions import CareerNotFoundError
from ace.domain.learner import (
    ConfirmedSkill,
    LearnerProfile,
    LearningPreferences,
    SkillMasteryState,
)
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
from ace.ranking.ranker import PathRanker


class PathGenerationService:
    """Orchestrates candidate generation, multi-objective ranking, and path construction."""

    def __init__(
        self,
        career_repo: CareerRepository,
        skill_repo: SkillRepository,
        prereq_repo: PrerequisiteRepository,
        ranker: PathRanker | None = None,
    ):
        self.career_repo = career_repo
        self.skill_repo = skill_repo
        self.prereq_repo = prereq_repo
        self.ranker = ranker

    def generate_path(
        self,
        learner_id: str,
        career_id: str,
        confirmed_skill_ids: Sequence[str] = (),
        mastery_states: dict[str, SkillMasteryState] | None = None,
        preferences: LearningPreferences | None = None,
        learner_profile: LearnerProfile | None = None,
        strategy: str | None = None,
        return_alternatives: bool = False,
    ) -> LearningPath:
        """Generate a personalized, topologically ordered, multi-objective curriculum path.

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
        if learner_profile is not None:
            learner = learner_profile
        else:
            learner = LearnerProfile(
                id=learner_id,
                confirmed_skills=[ConfirmedSkill(skill_id=sid) for sid in confirmed_set],
                mastery_states=mastery_states or {},
                preferences=preferences or LearningPreferences(),
            )

        skill_map = {s.id: s for s in all_skills}
        gaps: list[SkillGap] = compute_skill_gaps(
            career=career,
            learner=learner,
            all_skills=skill_map,
            graph=graph,
        )

        learning_path = generate_learning_path(
            gaps=gaps,
            graph=graph,
            learner_id=learner_id,
            career_id=career.id,
            career_name=career.name,
            confirmed_skill_ids=confirmed_set,
            career=career,
            learner=learner,
            all_skills=skill_map,
            ranker=self.ranker,
            strategy=strategy,
            return_alternatives=return_alternatives,
        )

        return learning_path

