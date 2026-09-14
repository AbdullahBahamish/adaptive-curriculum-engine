"""ORM models package. Import all models here so Alembic auto-discovers them."""
from ace.infrastructure.database.models.career import CareerModel, CareerSkillModel
from ace.infrastructure.database.models.interaction import LearnerInteractionModel
from ace.infrastructure.database.models.learner import LearnerModel, LearnerSkillStateModel
from ace.infrastructure.database.models.prerequisite import PrerequisiteModel
from ace.infrastructure.database.models.skill import SkillModel

__all__ = [
    "SkillModel",
    "CareerModel",
    "CareerSkillModel",
    "PrerequisiteModel",
    "LearnerModel",
    "LearnerSkillStateModel",
    "LearnerInteractionModel",
]
