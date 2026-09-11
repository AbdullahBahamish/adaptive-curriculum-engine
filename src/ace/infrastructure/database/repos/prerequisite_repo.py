"""Repository for Prerequisite relationships and graph edge hydration."""
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ace.domain.prerequisite import Prerequisite
from ace.infrastructure.database.models.prerequisite import PrerequisiteModel
from ace.infrastructure.database.repos.base import BaseRepository


class PrerequisiteRepository(BaseRepository[PrerequisiteModel]):
    """Data access repository for prerequisite edges."""

    def __init__(self, db: Session):
        super().__init__(PrerequisiteModel, db)

    def get_prerequisites_for_skill(self, skill_id: str) -> list[PrerequisiteModel]:
        """Fetch all prerequisites that must be learned before `skill_id`."""
        stmt = select(PrerequisiteModel).where(PrerequisiteModel.skill_id == skill_id)
        return list(self.db.scalars(stmt).all())

    def get_dependents_for_skill(self, skill_id: str) -> list[PrerequisiteModel]:
        """Fetch all skills that depend on `skill_id` as a prerequisite."""
        stmt = select(PrerequisiteModel).where(PrerequisiteModel.requires_skill_id == skill_id)
        return list(self.db.scalars(stmt).all())

    def get_edge(self, skill_id: str, requires_skill_id: str) -> PrerequisiteModel | None:
        """Fetch a specific prerequisite edge."""
        stmt = select(PrerequisiteModel).where(
            and_(
                PrerequisiteModel.skill_id == skill_id,
                PrerequisiteModel.requires_skill_id == requires_skill_id,
            )
        )
        return self.db.scalars(stmt).first()

    def delete_edge(self, skill_id: str, requires_skill_id: str) -> bool:
        """Delete an edge if it exists."""
        edge = self.get_edge(skill_id, requires_skill_id)
        if edge:
            self.delete(edge)
            return True
        return False

    @staticmethod
    def to_domain(model: PrerequisiteModel) -> Prerequisite:
        """Hydrate a domain Prerequisite entity from an ORM PrerequisiteModel."""
        return Prerequisite(
            skill_id=model.skill_id,
            requires_skill_id=model.requires_skill_id,
        )

    def list_all_domain(self) -> list[Prerequisite]:
        """Return all prerequisite edges hydrated into domain Prerequisite objects."""
        models = self.get_all()
        return [self.to_domain(m) for m in models]
