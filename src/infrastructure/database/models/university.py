from typing import TYPE_CHECKING
from sqlalchemy import String 
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

if TYPE_CHECKING:
    from database.models.course import Course


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    
    name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )   

    website: Mapped[str | None] = mapped_column(
        String(200),
    )

    courses: Mapped[list["Course"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
    )