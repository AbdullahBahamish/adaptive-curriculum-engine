"""Mastery tracking and Bayesian Knowledge Tracing API endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ace.api.dependencies import get_mastery_service, verify_api_key
from ace.learner.mastery_service import LearnerMasteryService

router = APIRouter(prefix="/mastery", dependencies=[Depends(verify_api_key)], tags=["Mastery"])


class EvidenceUpdate(BaseModel):
    learner_id: str
    skill_id: str
    evidence: float | bool = Field(description="Boolean pass/fail or continuous score in [0.0, 1.0]")
    evidence_id: str | None = Field(default=None, description="Assessment or quiz identifier")
    difficulty: int | None = Field(default=None, ge=1, le=5, description="Item difficulty level")


class BatchEvidenceUpdate(BaseModel):
    learner_id: str
    observations: list[EvidenceUpdate]


class SkillMasteryOut(BaseModel):
    skill_id: str
    estimated_mastery: float
    confidence: float
    evidence_count: int
    last_evidence: str | None
    difficulty_history: list[int]


class LearnerMasteryProfileResponse(BaseModel):
    learner_id: str
    name: str
    skills: dict[str, SkillMasteryOut]


@router.post("/update", response_model=SkillMasteryOut, summary="Record assessment evidence and update BKT mastery")
def update_mastery(
    update: EvidenceUpdate,
    service: LearnerMasteryService = Depends(get_mastery_service),
) -> SkillMasteryOut:
    """Record an interaction or assessment score, applying Bayesian Knowledge Tracing."""
    updated = service.record_evidence(
        learner_id=update.learner_id,
        skill_id=update.skill_id,
        evidence=update.evidence,
        evidence_id=update.evidence_id,
        difficulty=update.difficulty,
    )
    return SkillMasteryOut(
        skill_id=updated.skill_id,
        estimated_mastery=updated.estimated_mastery,
        confidence=updated.confidence,
        evidence_count=updated.evidence_count,
        last_evidence=updated.last_evidence,
        difficulty_history=updated.difficulty_history,
    )


@router.post("/batch", response_model=list[SkillMasteryOut], summary="Record batch assessment evidence")
def batch_update_mastery(
    batch: BatchEvidenceUpdate,
    service: LearnerMasteryService = Depends(get_mastery_service),
) -> list[SkillMasteryOut]:
    """Record multiple observations in sequential order."""
    results = []
    for obs in batch.observations:
        updated = service.record_evidence(
            learner_id=batch.learner_id,
            skill_id=obs.skill_id,
            evidence=obs.evidence,
            evidence_id=obs.evidence_id,
            difficulty=obs.difficulty,
        )
        results.append(
            SkillMasteryOut(
                skill_id=updated.skill_id,
                estimated_mastery=updated.estimated_mastery,
                confidence=updated.confidence,
                evidence_count=updated.evidence_count,
                last_evidence=updated.last_evidence,
                difficulty_history=updated.difficulty_history,
            )
        )
    return results


@router.get("/{learner_id}", response_model=LearnerMasteryProfileResponse, summary="Get learner mastery profile")
def get_learner_mastery(
    learner_id: str,
    service: LearnerMasteryService = Depends(get_mastery_service),
) -> LearnerMasteryProfileResponse:
    """Retrieve all current probabilistic skill masteries for a learner."""
    profile = service.get_or_create_profile(learner_id)
    skills_out = {
        sid: SkillMasteryOut(
            skill_id=st.skill_id,
            estimated_mastery=st.estimated_mastery,
            confidence=st.confidence,
            evidence_count=st.evidence_count,
            last_evidence=st.last_evidence,
            difficulty_history=st.difficulty_history,
        )
        for sid, st in profile.mastery_states.items()
    }
    return LearnerMasteryProfileResponse(
        learner_id=profile.id,
        name=profile.name,
        skills=skills_out,
    )
