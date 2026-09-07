"""Skills management endpoints (sync and inspection from upstream C# backend)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ace.api.dependencies import get_skill_repo, verify_api_key
from ace.infrastructure.database.models.skill import SkillModel
from ace.infrastructure.database.repos.skill_repo import SkillRepository

router = APIRouter(dependencies=[Depends(verify_api_key)])


# --- Pydantic Schemas ---

class SkillCreate(BaseModel):
    id: str = Field(description="Unique stable slug, e.g. 'html5'")
    name: str = Field(description="Human-readable title")
    category: str = Field(description="Domain category slug")
    description: Optional[str] = Field(default="", description="Summary of the skill")
    difficulty: int = Field(default=1, ge=1, le=5, description="Difficulty rating (1-5)")
    estimated_hours: int = Field(default=0, ge=0, description="Hours to acquire")


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    estimated_hours: Optional[int] = Field(default=None, ge=0)


class SkillResponse(BaseModel):
    id: str
    name: str
    category: str
    description: str
    difficulty: int
    estimated_hours: int


# --- Endpoints ---

@router.get("", response_model=list[SkillResponse], summary="List skills")
def list_skills(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    search: Optional[str] = Query(None, description="Filter by name substring"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    repo: SkillRepository = Depends(get_skill_repo),
) -> list[SkillResponse]:
    """Retrieve skills, optionally filtered by category or search query."""
    if search:
        models = repo.search_by_name(search)
    elif category:
        models = repo.list_by_category(category)
    else:
        models = repo.get_multi(skip=skip, limit=limit)

    return [
        SkillResponse(
            id=m.id,
            name=m.name,
            category=m.category,
            description=m.description or "",
            difficulty=m.difficulty,
            estimated_hours=m.estimated_hours,
        )
        for m in models
    ]


@router.get("/{skill_id}", response_model=SkillResponse, summary="Get skill by ID")
def get_skill(
    skill_id: str,
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillResponse:
    """Fetch single skill details by its ID slug."""
    model = repo.get_by_id(skill_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found.")
    return SkillResponse(
        id=model.id,
        name=model.name,
        category=model.category,
        description=model.description or "",
        difficulty=model.difficulty,
        estimated_hours=model.estimated_hours,
    )


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED, summary="Create a new skill")
def create_skill(
    payload: SkillCreate,
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillResponse:
    """Create a new skill record."""
    existing = repo.get_by_id(payload.id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Skill '{payload.id}' already exists.")

    model = SkillModel(
        id=payload.id,
        name=payload.name,
        category=payload.category,
        description=payload.description or "",
        difficulty=payload.difficulty,
        estimated_hours=payload.estimated_hours,
    )
    created = repo.create(model)
    return SkillResponse(
        id=created.id,
        name=created.name,
        category=created.category,
        description=created.description or "",
        difficulty=created.difficulty,
        estimated_hours=created.estimated_hours,
    )


@router.put("/{skill_id}", response_model=SkillResponse, summary="Update an existing skill")
def update_skill(
    skill_id: str,
    payload: SkillUpdate,
    repo: SkillRepository = Depends(get_skill_repo),
) -> SkillResponse:
    """Update properties of an existing skill."""
    model = repo.get_by_id(skill_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found.")

    if payload.name is not None:
        model.name = payload.name
    if payload.category is not None:
        model.category = payload.category
    if payload.description is not None:
        model.description = payload.description
    if payload.difficulty is not None:
        model.difficulty = payload.difficulty
    if payload.estimated_hours is not None:
        model.estimated_hours = payload.estimated_hours

    updated = repo.update(model)
    return SkillResponse(
        id=updated.id,
        name=updated.name,
        category=updated.category,
        description=updated.description or "",
        difficulty=updated.difficulty,
        estimated_hours=updated.estimated_hours,
    )


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a skill")
def delete_skill(
    skill_id: str,
    repo: SkillRepository = Depends(get_skill_repo),
) -> None:
    """Delete a skill and cascade-remove its associated prerequisite edges."""
    model = repo.get_by_id(skill_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found.")
    repo.delete(model)