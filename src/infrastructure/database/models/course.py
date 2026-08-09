from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.university import University


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
    )

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id")
    )

    university: Mapped["University"] = relationship(
        back_populates="courses"
    )

    topics = relationship(
        "Topic",
        back_populates="course",
        cascade="all, delete-orphan"
    )