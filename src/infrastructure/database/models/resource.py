import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ResourceType(enum.Enum):
    VIDEO = "Video"
    COURSE = "Course"
    BOOK = "Book"
    ARTICLE = "Article"
    DOCUMENTATION = "Documentation"
    PROJECT = "Project"


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False
    )

    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType),
        nullable=False
    )

    skill = relationship(
        "Skill",
        back_populates="resources"
    )