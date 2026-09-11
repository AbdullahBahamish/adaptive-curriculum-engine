"""Repository for Skills and domain model hydration."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ace.domain.skill import DifficultyLevel, Skill
from ace.infrastructure.database.models.skill import SkillModel
from ace.infrastructure.database.repos.base import BaseRepository


class SkillRepository(BaseRepository[SkillModel]):
    """Data access repository for the skills table."""

    def __init__(self, db: Session):
        super().__init__(SkillModel, db)

    def get_by_id(self, skill_id: str) -> SkillModel | None:
        """Fetch a skill model by its ID slug."""
        return self.get(skill_id)

    def get_by_ids(self, skill_ids: list[str]) -> list[SkillModel]:
        """Fetch multiple skills by their IDs."""
        if not skill_ids:
            return []
        stmt = select(SkillModel).where(SkillModel.id.in_(skill_ids))
        return list(self.db.scalars(stmt).all())

    def list_by_category(self, category: str) -> list[SkillModel]:
        """Filter skills by category slug."""
        stmt = select(SkillModel).where(SkillModel.category == category)
        return list(self.db.scalars(stmt).all())

    def search_by_name(self, query: str) -> list[SkillModel]:
        """Search skills with case-insensitive name matching."""
        stmt = select(SkillModel).where(SkillModel.name.ilike(f"%{query}%"))
        return list(self.db.scalars(stmt).all())

    @staticmethod
    def to_domain(model: SkillModel) -> Skill:
        """Hydrate a domain Skill entity from an ORM SkillModel."""
        return Skill(
            id=model.id,
            name=model.name,
            category=model.category,
            description=model.description or "",
            difficulty=DifficultyLevel(model.difficulty) if model.difficulty in DifficultyLevel else DifficultyLevel.BEGINNER,
            estimated_hours=model.estimated_hours,
        )

    def list_all_domain(self) -> list[Skill]:
        """Return all skills hydrated into pure domain Skill objects."""
        models = self.get_all()
        return [self.to_domain(m) for m in models]
