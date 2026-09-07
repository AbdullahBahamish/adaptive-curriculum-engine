"""Careers management endpoints (sync and inspection from upstream C# backend)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ace.api.dependencies import get_career_repo, get_skill_repo, verify_api_key
from ace.infrastructure.database.models.career import CareerModel
from ace.infrastructure.database.repos.career_repo import CareerRepository
from ace.infrastructure.database.repos.skill_repo import SkillRepository

router = APIRouter(dependencies=[Depends(verify_api_key)])


# --- Pydantic Schemas ---

class CareerSkillReqItem(BaseModel):
    skill_id: str
    is_mandatory: bool = True
    importance: int = Field(default=1, ge=1, le=5)


class CareerCreate(BaseModel):
    id: str = Field(description="Unique stable slug, e.g. 'frontend_developer'")
    name: str = Field(description="Display title")
    description: Optional[str] = Field(default="")
    required_skills: list[CareerSkillReqItem] = Field(default_factory=list)


class CareerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CareerResponse(BaseModel):
    id: str
    name: str
    description: str
    required_skills: list[CareerSkillReqItem]


# --- Endpoints ---

@router.get("", response_model=list[CareerResponse], summary="List all careers")
def list_careers(
    repo: CareerRepository = Depends(get_career_repo),
) -> list[CareerResponse]:
    """List all available careers with their required skills."""
    careers = repo.list_all_careers_domain()
    return [
        CareerResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            required_skills=[
                CareerSkillReqItem(
                    skill_id=r.skill_id,
                    is_mandatory=r.is_mandatory,
                    importance=r.importance,
                )
                for r in c.required_skills
            ],
        )
        for c in careers
    ]


@router.get("/{career_id}", response_model=CareerResponse, summary="Get career by ID")
def get_career(
    career_id: str,
    repo: CareerRepository = Depends(get_career_repo),
) -> CareerResponse:
    """Fetch single career profile and required skills."""
    career = repo.get_career_domain(career_id)
    if not career:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Career '{career_id}' not found.")
    return CareerResponse(
        id=career.id,
        name=career.name,
        description=career.description,
        required_skills=[
            CareerSkillReqItem(
                skill_id=r.skill_id,
                is_mandatory=r.is_mandatory,
                importance=r.importance,
            )
            for r in career.required_skills
        ],
    )


@router.post("", response_model=CareerResponse, status_code=status.HTTP_201_CREATED, summary="Create a new career")
def create_career(
    payload: CareerCreate,
    career_repo: CareerRepository = Depends(get_career_repo),
    skill_repo: SkillRepository = Depends(get_skill_repo),
) -> CareerResponse:
    """Create a new career track with optional initial required skills."""
    existing = career_repo.get_by_id(payload.id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Career '{payload.id}' already exists.")

    career_model = CareerModel(
        id=payload.id,
        name=payload.name,
        description=payload.description or "",
    )
    career_repo.create(career_model)

    for req in payload.required_skills:
        skill = skill_repo.get_by_id(req.skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add requirement: Skill '{req.skill_id}' does not exist.",
            )
        career_repo.add_or_update_required_skill(
            career_id=payload.id,
            skill_id=req.skill_id,
            is_mandatory=req.is_mandatory,
            importance=req.importance,
        )

    career = career_repo.get_career_domain(payload.id)
    assert career is not None
    return CareerResponse(
        id=career.id,
        name=career.name,
        description=career.description,
        required_skills=[
            CareerSkillReqItem(
                skill_id=r.skill_id,
                is_mandatory=r.is_mandatory,
                importance=r.importance,
            )
            for r in career.required_skills
        ],
    )


@router.put("/{career_id}", response_model=CareerResponse, summary="Update career details")
def update_career(
    career_id: str,
    payload: CareerUpdate,
    repo: CareerRepository = Depends(get_career_repo),
) -> CareerResponse:
    """Update title or description of a career."""
    model = repo.get_by_id(career_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Career '{career_id}' not found.")

    if payload.name is not None:
        model.name = payload.name
    if payload.description is not None:
        model.description = payload.description

    repo.update(model)
    career = repo.get_career_domain(career_id)
    assert career is not None
    return CareerResponse(
        id=career.id,
        name=career.name,
        description=career.description,
        required_skills=[
            CareerSkillReqItem(
                skill_id=r.skill_id,
                is_mandatory=r.is_mandatory,
                importance=r.importance,
            )
            for r in career.required_skills
        ],
    )


@router.delete("/{career_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a career")
def delete_career(
    career_id: str,
    repo: CareerRepository = Depends(get_career_repo),
) -> None:
    """Delete a career track."""
    model = repo.get_by_id(career_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Career '{career_id}' not found.")
    repo.delete(model)


@router.post("/{career_id}/skills", response_model=CareerSkillReqItem, summary="Attach skill to career")
def attach_skill_to_career(
    career_id: str,
    payload: CareerSkillReqItem,
    career_repo: CareerRepository = Depends(get_career_repo),
    skill_repo: SkillRepository = Depends(get_skill_repo),
) -> CareerSkillReqItem:
    """Add or update a skill requirement for a career."""
    career = career_repo.get_by_id(career_id)
    if not career:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Career '{career_id}' not found.")

    skill = skill_repo.get_by_id(payload.skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{payload.skill_id}' not found.")

    req = career_repo.add_or_update_required_skill(
        career_id=career_id,
        skill_id=payload.skill_id,
        is_mandatory=payload.is_mandatory,
        importance=payload.importance,
    )
    return CareerSkillReqItem(
        skill_id=req.skill_id,
        is_mandatory=req.is_mandatory,
        importance=req.importance,
    )


@router.delete("/{career_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Detach skill from career")
def detach_skill_from_career(
    career_id: str,
    skill_id: str,
    career_repo: CareerRepository = Depends(get_career_repo),
) -> None:
    """Remove a skill requirement from a career."""
    removed = career_repo.remove_required_skill(career_id=career_id, skill_id=skill_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirement for skill '{skill_id}' on career '{career_id}' not found.",
        )