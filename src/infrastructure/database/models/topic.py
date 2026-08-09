from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship 

from database.base import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable = True
    )

    importance: Mapped[float] = mapped_column(
        Float,
        nullable = True
    )

    # Relationships
    course = relationship(
        "Course",
        back_populates="topics"
    )

    skills = relationship(
        "Skill",
        back_populates="topic",
        cascade="all, delete-orphan"
    )