"""Skill model definition."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.database.base import Base
from turbo.core.models.associations import skill_tags


class Skill(Base):
    """Skill model representing professional skills and expertise."""

    __tablename__ = "skills"

    # Required fields
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="technical", index=True)
    proficiency_level = Column(String(20), nullable=False, default="intermediate")

    # Optional fields
    description = Column(String, nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_endorsed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        "last_used_at", nullable=True
    )

    # Relationships
    tags = relationship(
        "Tag", secondary=skill_tags, back_populates="skills", lazy="select"
    )

    def __repr__(self) -> str:
        """String representation of the skill."""
        return f"<Skill(id={self.id}, name='{self.name}')>"
