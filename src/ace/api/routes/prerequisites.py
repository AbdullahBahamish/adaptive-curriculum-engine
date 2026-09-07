"""Prerequisites management endpoints (sync and DAG edge maintenance)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ace.api.dependencies import get_prerequisite_repo, get_skill_repo, verify_api_key
from ace.domain.prerequisite import Prerequisite
from ace.graph import build_prerequisite_graph
from ace.graph.validator import validate_graph, CycleDetectedError
from ace.infrastructure.database.models.prerequisite import PrerequisiteModel
from ace.infrastructure.database.repos.prerequisite_repo import PrerequisiteRepository
from ace.infrastructure.database.repos.skill_repo import SkillRepository

router = APIRouter(dependencies=[Depends(verify_api_key)])


# --- Pydantic Schemas ---

class PrerequisiteCreate(BaseModel):
    skill_id: str = Field(description="The dependent skill that has the prerequisite")
    requires_skill_id: str = Field(description="The prerequisite skill that must be learned first")


class PrerequisiteResponse(BaseModel):
    skill_id: str
    requires_skill_id: str


# --- Endpoints ---

@router.get("", response_model=list[PrerequisiteResponse], summary="List all prerequisite edges")
def list_prerequisites(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    repo: PrerequisiteRepository = Depends(get_prerequisite_repo),
) -> list[PrerequisiteResponse]:
    """Retrieve all directed prerequisite edges in the curriculum graph."""
    models = repo.get_multi(skip=skip, limit=limit)
    return [
        PrerequisiteResponse(skill_id=m.skill_id, requires_skill_id=m.requires_skill_id)
        for m in models
    ]


@router.get("/skill/{skill_id}", response_model=list[PrerequisiteResponse], summary="Get prerequisites for a skill")
def get_prerequisites_for_skill(
    skill_id: str,
    repo: PrerequisiteRepository = Depends(get_prerequisite_repo),
) -> list[PrerequisiteResponse]:
    """Get all skills that must be learned before `skill_id`."""
    models = repo.get_prerequisites_for_skill(skill_id)
    return [
        PrerequisiteResponse(skill_id=m.skill_id, requires_skill_id=m.requires_skill_id)
        for m in models
    ]


@router.get("/dependents/{skill_id}", response_model=list[PrerequisiteResponse], summary="Get dependents of a skill")
def get_dependents_for_skill(
    skill_id: str,
    repo: PrerequisiteRepository = Depends(get_prerequisite_repo),
) -> list[PrerequisiteResponse]:
    """Get all skills that require `skill_id` as a prerequisite."""
    models = repo.get_dependents_for_skill(skill_id)
    return [
        PrerequisiteResponse(skill_id=m.skill_id, requires_skill_id=m.requires_skill_id)
        for m in models
    ]


@router.post("", response_model=PrerequisiteResponse, status_code=status.HTTP_201_CREATED, summary="Add a prerequisite edge")
def add_prerequisite(
    payload: PrerequisiteCreate,
    prereq_repo: PrerequisiteRepository = Depends(get_prerequisite_repo),
    skill_repo: SkillRepository = Depends(get_skill_repo),
) -> PrerequisiteResponse:
    """Add a directed prerequisite edge with automated cycle prevention.

    Validates:
      1. Both skills exist in the database.
      2. No self-loops (skill_id != requires_skill_id).
      3. Edge does not already exist.
      4. Adding this edge will NOT introduce a cycle into the prerequisite graph.
    """
    if payload.skill_id == payload.requires_skill_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A skill cannot be a prerequisite of itself.",
        )

    # 1. Verify skills exist
    skill = skill_repo.get_by_id(payload.skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target skill '{payload.skill_id}' not found.",
        )
    required = skill_repo.get_by_id(payload.requires_skill_id)
    if not required:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prerequisite skill '{payload.requires_skill_id}' not found.",
        )

    # 2. Check if edge already exists
    existing = prereq_repo.get_edge(payload.skill_id, payload.requires_skill_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prerequisite relationship already exists.",
        )

    # 3. Simulate new graph to verify DAG property (Cycle Prevention)
    all_skills = skill_repo.list_all_domain()
    current_prereqs = prereq_repo.list_all_domain()
    candidate_prereqs = current_prereqs + [
        Prerequisite(skill_id=payload.skill_id, requires_skill_id=payload.requires_skill_id)
    ]
    graph = build_prerequisite_graph(all_skills, candidate_prereqs)
    try:
        validate_graph(graph)
    except CycleDetectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add prerequisite: introduces a cycle {exc.cycle}",
        ) from exc

    # 4. Save edge
    model = PrerequisiteModel(
        skill_id=payload.skill_id,
        requires_skill_id=payload.requires_skill_id,
    )
    created = prereq_repo.create(model)
    return PrerequisiteResponse(
        skill_id=created.skill_id,
        requires_skill_id=created.requires_skill_id,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a prerequisite edge")
def delete_prerequisite(
    skill_id: str = Query(..., description="Target skill"),
    requires_skill_id: str = Query(..., description="Required skill"),
    repo: PrerequisiteRepository = Depends(get_prerequisite_repo),
) -> None:
    """Remove a prerequisite edge from the graph."""
    deleted = repo.delete_edge(skill_id, requires_skill_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge '{requires_skill_id} -> {skill_id}' not found.",
        )