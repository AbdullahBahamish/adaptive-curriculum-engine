"""Learning Path generation endpoint."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ace.api.dependencies import get_path_generation_service, verify_api_key
from ace.application.path_generation_service import PathGenerationService
from ace.core.exceptions import CareerNotFoundError, CycleDetectedError

router = APIRouter(dependencies=[Depends(verify_api_key)])


class LearningPathRequest(BaseModel):
    learner_id: str
    career_id: str
    confirmed_skills: list[str] = Field(
        default_factory=list,
        description="List of skill IDs the learner has confirmed",
    )


class LearningStepOut(BaseModel):
    order: int
    skill_id: str
    skill_name: str
    category: str
    estimated_hours: int
    rationale: str
    prerequisites_satisfied: list[str]


class LearningPathResponse(BaseModel):
    learner_id: str
    career_id: str
    career_name: str
    total_skills: int
    total_estimated_hours: int
    steps: list[LearningStepOut]


@router.post(
    "/learning-path",
    response_model=LearningPathResponse,
    summary="Generate a topologically ordered learning path for a learner",
)
def generate_path(
    request: LearningPathRequest,
    service: PathGenerationService = Depends(get_path_generation_service),
) -> LearningPathResponse:
    """Generates an ordered, prerequisite-aware learning path.

    The C# backend calls this after gap analysis to get the actual
    step-by-step plan the learner should follow.
    """
    try:
        path = service.generate_path(
            learner_id=request.learner_id,
            career_id=request.career_id,
            confirmed_skill_ids=request.confirmed_skills,
        )
    except CareerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CycleDetectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prerequisite graph cycle error: {exc}",
        ) from exc

    return LearningPathResponse(
        learner_id=path.learner_id,
        career_id=path.career_id,
        career_name=path.career_name,
        total_skills=path.total_skills,
        total_estimated_hours=path.total_estimated_hours,
        steps=[
            LearningStepOut(
                order=s.order,
                skill_id=s.skill_id,
                skill_name=s.skill_name,
                category=s.category,
                estimated_hours=s.estimated_hours,
                rationale=s.rationale,
                prerequisites_satisfied=s.prerequisites_satisfied,
            )
            for s in path.steps
        ],
    )