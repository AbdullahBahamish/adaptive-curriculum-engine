"""ORM models package. Import all models here so Alembic auto-discovers them."""
from ace.infrastructure.database.models.skill import SkillModel
from ace.infrastructure.database.models.career import CareerModel, CareerSkillModel
from ace.infrastructure.database.models.prerequisite import PrerequisiteModel

__all__ = ["SkillModel", "CareerModel", "CareerSkillModel", "PrerequisiteModel"]