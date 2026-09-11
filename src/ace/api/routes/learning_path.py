from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ace.api.dependencies import get_path_generation_service, verify_api_key
from ace.application.path_generation_service import PathGenerationService
from ace.core.exceptions import CareerNotFoundError, CycleDetectedError
from ace.domain.learner import LearningPreferences, PacePreference, SkillMasteryState
from ace.infrastructure.llm.explainer import CurriculumExplainer

router = APIRouter(dependencies=[Depends(verify_api_key)])


class LearningPathRequest(BaseModel):
    learner_id: str
    career_id: str
    confirmed_skills: list[str] = Field(
        default_factory=list,
        description="List of skill IDs the learner has confirmed",
    )
    mastery_states: dict[str, float] = Field(
        default_factory=dict,
        description="Optional probabilistic mastery map: skill_id -> score in [0, 1]",
    )
    pace_preference: str = Field(
        default="balanced",
        description="Pacing archetype: balanced | foundational_first | fast_track | domain_focused",
    )
    weekly_hours_budget: int = Field(default=10, ge=1, le=80)
    max_total_hours: int | None = None
    strategy: str | None = Field(default=None, description="Force a specific sequencing archetype")
    return_alternatives: bool = Field(default=False, description="Whether to include Pareto alternative pathways")
    explain: bool = Field(default=False, description="Include natural language curriculum explanation")


class LearningStepOut(BaseModel):
    order: int
    skill_id: str
    skill_name: str
    category: str
    estimated_hours: int
    rationale: str
    prerequisites_satisfied: list[str]
    reason_codes: list[str] = Field(default_factory=list)
    unblocks_count: int = 0
    gap_score: float = 0.0
    difficulty_step: int = 0


class LearningPathResponse(BaseModel):
    learner_id: str
    career_id: str
    career_name: str
    total_skills: int
    total_estimated_hours: int
    steps: list[LearningStepOut]
    strategy: str = "topological"
    composite_score: float = 0.0
    objective_scores: dict[str, float] = Field(default_factory=dict)
    pareto_tradeoffs: list[dict[str, Any]] = Field(default_factory=list)
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    explanation: str | None = None


@router.post(
    "/learning-path",
    response_model=LearningPathResponse,
    summary="Generate a personalized, multi-objective learning path for a learner",
)
def generate_path(
    request: LearningPathRequest,
    service: PathGenerationService = Depends(get_path_generation_service),
) -> LearningPathResponse:
    """Generates an ordered, prerequisite-aware, multi-objective curriculum path.

    The C# backend calls this to get the optimal pedagogical sequence,
    supporting learner pacing preferences, mastery states, and Pareto alternatives.
    """
    try:
        pref_enum = PacePreference(request.pace_preference.lower())
    except ValueError:
        pref_enum = PacePreference.BALANCED

    preferences = LearningPreferences(
        weekly_hours_budget=request.weekly_hours_budget,
        max_total_hours=request.max_total_hours,
        pace_preference=pref_enum,
    )

    mastery_objs = {
        sid: SkillMasteryState(skill_id=sid, estimated_mastery=score, confidence=0.8, evidence_count=1)
        for sid, score in request.mastery_states.items()
    }

    try:
        path = service.generate_path(
            learner_id=request.learner_id,
            career_id=request.career_id,
            confirmed_skill_ids=request.confirmed_skills,
            mastery_states=mastery_objs if mastery_objs else None,
            preferences=preferences,
            strategy=request.strategy,
            return_alternatives=request.return_alternatives,
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

    explanation = None
    if request.explain:
        explainer = CurriculumExplainer()
        explanation = explainer.explain_path(path)

    alt_dicts = []
    for alt in path.alternative_paths:
        alt_dicts.append({
            "strategy": alt.strategy,
            "total_skills": alt.total_skills,
            "total_estimated_hours": alt.total_estimated_hours,
            "composite_score": alt.composite_score,
            "objective_scores": alt.objective_scores,
            "step_ids": [s.skill_id for s in alt.steps],
        })

    return LearningPathResponse(
        learner_id=path.learner_id,
        career_id=path.career_id,
        career_name=path.career_name,
        total_skills=path.total_skills,
        total_estimated_hours=path.total_estimated_hours,
        strategy=path.strategy,
        composite_score=path.composite_score,
        objective_scores=path.objective_scores,
        pareto_tradeoffs=path.pareto_tradeoffs,
        alternatives=alt_dicts,
        explanation=explanation,
        steps=[
            LearningStepOut(
                order=s.order,
                skill_id=s.skill_id,
                skill_name=s.skill_name,
                category=s.category,
                estimated_hours=s.estimated_hours,
                rationale=s.rationale,
                prerequisites_satisfied=s.prerequisites_satisfied,
                reason_codes=s.reason_codes,
                unblocks_count=s.unblocks_count,
                gap_score=s.gap_score,
                difficulty_step=s.difficulty_step,
            )
            for s in path.steps
        ],
    )