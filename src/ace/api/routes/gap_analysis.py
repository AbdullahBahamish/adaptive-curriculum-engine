"""Gap Analysis endpoint — the primary intelligence endpoint consumed by C# backend."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ace.api.dependencies import get_gap_analysis_service, verify_api_key
from ace.application.gap_analysis_service import GapAnalysisService
from ace.core.exceptions import CareerNotFoundError

router = APIRouter(dependencies=[Depends(verify_api_key)])


# --- Request / Response schemas ---

class ConfirmedSkillInput(BaseModel):
    skill_id: str = Field(description="ID of a skill the learner has confirmed")


class GapAnalysisRequest(BaseModel):
    learner_id: str = Field(description="Learner identifier from the C# backend")
    career_id: str = Field(description="Target career ID")
    confirmed_skills: list[ConfirmedSkillInput] = Field(
        default_factory=list,
        description="Skills the learner has self-confirmed (Yes/No model)",
    )


class SkillGapItem(BaseModel):
    skill_id: str
    skill_name: str
    category: str
    difficulty: int
    estimated_hours: int
    is_mandatory: bool


class GapAnalysisResponse(BaseModel):
    learner_id: str
    career_id: str
    career_name: str
    total_required_skills: int
    skills_confirmed: int
    skills_missing: int
    completion_percentage: float = Field(description="Percentage of required skills already confirmed")
    gaps: list[SkillGapItem]


# --- Route ---

@router.post(
    "/gap-analysis",
    response_model=GapAnalysisResponse,
    summary="Analyse skill gaps between learner and target career",
)
def analyse_gaps(
    request: GapAnalysisRequest,
    service: GapAnalysisService = Depends(get_gap_analysis_service),
) -> GapAnalysisResponse:
    """Compute which required career skills the learner has not yet confirmed.

    The C# backend sends:
    - The learner's current confirmed skill set (binary: have or don't have).
    - The target career ID.

    Returns a structured gap report ordered by importance.
    """
    confirmed_ids = [s.skill_id for s in request.confirmed_skills]
    try:
        report = service.analyze_gaps(
            learner_id=request.learner_id,
            career_id=request.career_id,
            confirmed_skill_ids=confirmed_ids,
        )
    except CareerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    mandatory_map = {r.skill_id: r.is_mandatory for r in report.career.required_skills}

    return GapAnalysisResponse(
        learner_id=report.learner_id,
        career_id=report.career_id,
        career_name=report.career_name,
        total_required_skills=report.total_required_skills,
        skills_confirmed=report.skills_confirmed,
        skills_missing=report.skills_missing,
        completion_percentage=report.completion_percentage,
        gaps=[
            SkillGapItem(
                skill_id=g.skill.id,
                skill_name=g.skill.name,
                category=g.skill.category,
                difficulty=g.skill.difficulty,
                estimated_hours=g.skill.estimated_hours,
                is_mandatory=mandatory_map.get(g.skill.id, True),
            )
            for g in report.gaps
        ],
    )