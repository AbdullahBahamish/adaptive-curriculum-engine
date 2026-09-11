"""Base generic repository for SQLAlchemy models.

Follows the Repository Pattern to decouple data persistence logic from
the domain/application service layer.
"""
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from ace.infrastructure.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic CRUD repository for SQLAlchemy models."""

    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: Any) -> ModelType | None:
        """Fetch a single record by primary key."""
        return self.db.get(self.model, id)

    def get_multi(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Fetch records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_all(self) -> list[ModelType]:
        """Fetch all records without pagination."""
        stmt = select(self.model)
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        """Return total row count for the model."""
        stmt = select(self.model)
        return len(list(self.db.scalars(stmt).all()))

    def create(self, obj: ModelType) -> ModelType:
        """Persist a new entity instance."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        """Save updates to an existing entity."""
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        """Remove an entity from the database."""
        self.db.delete(obj)
        self.db.commit()
