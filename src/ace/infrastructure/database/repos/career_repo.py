"""Repository for Career profiles and skill requirements."""
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, and_

from ace.domain.career import Career, CareerSkillRequirement
from ace.infrastructure.database.models.career import CareerModel, CareerSkillModel
from ace.infrastructure.database.repos.base import BaseRepository


class CareerRepository(BaseRepository[CareerModel]):
    """Data access repository for careers and their required skills."""

    def __init__(self, db: Session):
        super().__init__(CareerModel, db)

    def get_by_id(self, career_id: str, load_skills: bool = True) -> CareerModel | None:
        """Fetch a career by ID slug, optionally eager loading required skills."""
        stmt = select(CareerModel).where(CareerModel.id == career_id)
        if load_skills:
            stmt = stmt.options(selectinload(CareerModel.required_skills))
        return self.db.scalars(stmt).first()

    def list_all_with_skills(self) -> list[CareerModel]:
        """Fetch all careers with their required skills eager loaded."""
        stmt = select(CareerModel).options(selectinload(CareerModel.required_skills))
        return list(self.db.scalars(stmt).all())

    def add_or_update_required_skill(
        self,
        career_id: str,
        skill_id: str,
        is_mandatory: bool = True,
        importance: int = 1,
    ) -> CareerSkillModel:
        """Add or update a skill requirement for a career."""
        stmt = select(CareerSkillModel).where(
            and_(
                CareerSkillModel.career_id == career_id,
                CareerSkillModel.skill_id == skill_id,
            )
        )
        req = self.db.scalars(stmt).first()
        if req:
            req.is_mandatory = is_mandatory
            req.importance = importance
        else:
            req = CareerSkillModel(
                career_id=career_id,
                skill_id=skill_id,
                is_mandatory=is_mandatory,
                importance=importance,
            )
            self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def remove_required_skill(self, career_id: str, skill_id: str) -> bool:
        """Remove a skill requirement from a career."""
        stmt = select(CareerSkillModel).where(
            and_(
                CareerSkillModel.career_id == career_id,
                CareerSkillModel.skill_id == skill_id,
            )
        )
        req = self.db.scalars(stmt).first()
        if req:
            self.db.delete(req)
            self.db.commit()
            return True
        return False

    @staticmethod
    def to_domain(model: CareerModel) -> Career:
        """Hydrate a domain Career entity from an ORM CareerModel."""
        required_skills = [
            CareerSkillRequirement(
                skill_id=r.skill_id,
                is_mandatory=r.is_mandatory,
                importance=r.importance,
            )
            for r in (model.required_skills or [])
        ]
        return Career(
            id=model.id,
            name=model.name,
            description=model.description or "",
            required_skills=required_skills,
        )

    def get_career_domain(self, career_id: str) -> Career | None:
        """Get career as domain object by ID."""
        model = self.get_by_id(career_id, load_skills=True)
        return self.to_domain(model) if model else None

    def list_all_careers_domain(self) -> list[Career]:
        """Return all careers hydrated into domain Career objects."""
        models = self.list_all_with_skills()
        return [self.to_domain(m) for m in models]
