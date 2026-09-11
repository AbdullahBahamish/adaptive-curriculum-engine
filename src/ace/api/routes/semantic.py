"""Semantic skill matching and vector retrieval API endpoint."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ace.api.dependencies import get_skill_repo, get_vector_index, verify_api_key
from ace.infrastructure.database.repos.skill_repo import SkillRepository
from ace.semantic.vector_index import SkillVectorIndex

router = APIRouter(prefix="/semantic", dependencies=[Depends(verify_api_key)], tags=["Semantic Matching"])


class SemanticMatchRequest(BaseModel):
    query: str = Field(description="Natural language description of technical skills or experience")
    top_k: int = Field(default=5, ge=1, le=50, description="Max skills to return")
    min_score: float = Field(default=0.35, ge=0.0, le=1.0, description="Minimum cosine similarity threshold")


class SkillMatchResult(BaseModel):
    skill_id: str
    name: str
    category: str
    similarity_score: float
    difficulty: int
    estimated_hours: int


class SemanticMatchResponse(BaseModel):
    query: str
    matches: list[SkillMatchResult]
    total_matches: int


@router.post("/match", response_model=SemanticMatchResponse, summary="Match free text to curriculum skills")
def match_skills_semantic(
    request: SemanticMatchRequest,
    index: SkillVectorIndex = Depends(get_vector_index),
    skill_repo: SkillRepository = Depends(get_skill_repo),
) -> SemanticMatchResponse:
    """Find the most semantically relevant skills using sub-millisecond cosine vector similarity."""
    results = index.search(
        query=request.query,
        top_k=request.top_k,
        min_score=request.min_score,
    )

    if not results:
        return SemanticMatchResponse(query=request.query, matches=[], total_matches=0)

    matched_ids = [sid for sid, _ in results]
    models = skill_repo.get_by_ids(matched_ids)
    model_map = {m.id: m for m in models}

    matches_out: list[SkillMatchResult] = []
    for sid, score in results:
        m = model_map.get(sid)
        if m:
            matches_out.append(
                SkillMatchResult(
                    skill_id=m.id,
                    name=m.name,
                    category=m.category,
                    similarity_score=score,
                    difficulty=m.difficulty,
                    estimated_hours=m.estimated_hours,
                )
            )
        else:
            matches_out.append(
                SkillMatchResult(
                    skill_id=sid,
                    name=sid,
                    category="General",
                    similarity_score=score,
                    difficulty=1,
                    estimated_hours=0,
                )
            )

    return SemanticMatchResponse(
        query=request.query,
        matches=matches_out,
        total_matches=len(matches_out),
    )
