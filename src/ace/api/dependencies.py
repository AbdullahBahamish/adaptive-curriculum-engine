"""FastAPI dependency injection providers."""
from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from ace.application.gap_analysis_service import GapAnalysisService
from ace.application.path_generation_service import PathGenerationService
from ace.core.security import verify_api_key
from ace.infrastructure.database.repos.career_repo import CareerRepository
from ace.infrastructure.database.repos.prerequisite_repo import PrerequisiteRepository
from ace.infrastructure.database.repos.skill_repo import SkillRepository
from ace.infrastructure.database.session import get_db


def get_session(db: Session = Depends(get_db)) -> Generator[Session, None, None]:
    """Provide a database session. Alias for get_db for clarity."""
    return db  # type: ignore[return-value]


def get_skill_repo(db: Session = Depends(get_db)) -> SkillRepository:
    """Dependency provider for SkillRepository."""
    return SkillRepository(db)


def get_career_repo(db: Session = Depends(get_db)) -> CareerRepository:
    """Dependency provider for CareerRepository."""
    return CareerRepository(db)


def get_prerequisite_repo(db: Session = Depends(get_db)) -> PrerequisiteRepository:
    """Dependency provider for PrerequisiteRepository."""
    return PrerequisiteRepository(db)


def get_gap_analysis_service(
    career_repo: CareerRepository = Depends(get_career_repo),
    skill_repo: SkillRepository = Depends(get_skill_repo),
) -> GapAnalysisService:
    """Dependency provider for GapAnalysisService."""
    return GapAnalysisService(career_repo=career_repo, skill_repo=skill_repo)


def get_path_generation_service(
    career_repo: CareerRepository = Depends(get_career_repo),
    skill_repo: SkillRepository = Depends(get_skill_repo),
    prereq_repo: PrerequisiteRepository = Depends(get_prerequisite_repo),
) -> PathGenerationService:
    """Dependency provider for PathGenerationService."""
    return PathGenerationService(
        career_repo=career_repo,
        skill_repo=skill_repo,
        prereq_repo=prereq_repo,
    )


__all__ = [
    "get_db",
    "get_session",
    "verify_api_key",
    "get_skill_repo",
    "get_career_repo",
    "get_prerequisite_repo",
    "get_gap_analysis_service",
    "get_path_generation_service",
]