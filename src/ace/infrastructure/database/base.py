"""SQLAlchemy declarative base shared by all ORM models."""
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column
from sqlalchemy import String
import uuid


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass