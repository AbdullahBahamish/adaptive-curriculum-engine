"""FastAPI dependency injection providers."""
from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from ace.application.gap_analysis_service import GapAnalysisService
from ace.application.path_generation_service import PathGenerationService
from ace.core.config import settings
from ace.core.security import verify_api_key
from ace.infrastructure.database.repos.career_repo import CareerRepository
from ace.infrastructure.database.repos.prerequisite_repo import PrerequisiteRepository
from ace.infrastructure.database.repos.skill_repo import SkillRepository
from ace.infrastructure.database.session import get_db
from ace.learner.bkt import BKTModel, BKTParameters
from ace.learner.mastery_service import LearnerMasteryService
from ace.ranking.ranker import HybridRanker, PathRanker
from ace.semantic.cache import EmbeddingCache
from ace.semantic.provider import LocalSentenceTransformer, MockEmbeddingProvider
from ace.semantic.vector_index import SkillVectorIndex


def get_session(db: Session = Depends(get_db)) -> Generator[Session]:
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


@lru_cache(maxsize=1)
def get_mastery_service() -> LearnerMasteryService:
    """Singleton provider for LearnerMasteryService."""
    params = BKTParameters(
        p_l0=settings.bkt_p_l0,
        p_t=settings.bkt_p_t,
        p_g=settings.bkt_p_g,
        p_s=settings.bkt_p_s,
    )
    return LearnerMasteryService(bkt_model=BKTModel(params))


@lru_cache(maxsize=1)
def get_vector_index() -> SkillVectorIndex:
    """Singleton provider for SkillVectorIndex."""
    cache = EmbeddingCache(cache_path=settings.embeddings_cache_path)
    provider = None
    if settings.embeddings_enabled:
        try:
            provider = LocalSentenceTransformer(settings.embeddings_model)
        except Exception:
            provider = MockEmbeddingProvider()

    index = SkillVectorIndex(provider=provider, cache=cache)
    # Load canonical embeddings if available
    index.load_precomputed(settings.canonical_embeddings_path)
    return index


def get_path_ranker() -> PathRanker:
    """Dependency provider for PathRanker."""
    return HybridRanker()


def get_gap_analysis_service(
    career_repo: CareerRepository = Depends(get_career_repo),
    skill_repo: SkillRepository = Depends(get_skill_repo),
    prereq_repo: PrerequisiteRepository = Depends(get_prerequisite_repo),
) -> GapAnalysisService:
    """Dependency provider for GapAnalysisService."""
    return GapAnalysisService(
        career_repo=career_repo,
        skill_repo=skill_repo,
        prereq_repo=prereq_repo,
    )


def get_path_generation_service(
    career_repo: CareerRepository = Depends(get_career_repo),
    skill_repo: SkillRepository = Depends(get_skill_repo),
    prereq_repo: PrerequisiteRepository = Depends(get_prerequisite_repo),
    ranker: PathRanker = Depends(get_path_ranker),
) -> PathGenerationService:
    """Dependency provider for PathGenerationService."""
    return PathGenerationService(
        career_repo=career_repo,
        skill_repo=skill_repo,
        prereq_repo=prereq_repo,
        ranker=ranker,
    )


__all__ = [
    "get_db",
    "get_session",
    "verify_api_key",
    "get_skill_repo",
    "get_career_repo",
    "get_prerequisite_repo",
    "get_mastery_service",
    "get_vector_index",
    "get_path_ranker",
    "get_gap_analysis_service",
    "get_path_generation_service",
]