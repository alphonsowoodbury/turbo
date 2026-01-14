"""Tag model definition."""


from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from turbo.core.database.base import Base
from turbo.core.models.associations import (
    achievement_fact_tags,
    company_tags,
    initiative_tags,
    issue_tags,
    job_application_tags,
    literature_tags,
    milestone_tags,
    network_contact_tags,
    note_tags,
    project_tags,
    skill_tags,
    work_experience_tags,
)


class Tag(Base):
    """Tag model for categorizing projects and issues."""

    __tablename__ = "tags"

    # Required fields
    name = Column(String(50), nullable=False, unique=True, index=True)
    color = Column(String(7), nullable=False)  # Hex color code

    # Optional fields
    description = Column(String(200), nullable=True)

    # Relationships
    projects = relationship(
        "Project", secondary=project_tags, back_populates="tags", lazy="select"
    )

    issues = relationship(
        "Issue", secondary=issue_tags, back_populates="tags", lazy="select"
    )

    milestones = relationship(
        "Milestone", secondary=milestone_tags, back_populates="tags", lazy="select"
    )

    initiatives = relationship(
        "Initiative", secondary=initiative_tags, back_populates="tags", lazy="select"
    )

    literature = relationship(
        "Literature", secondary=literature_tags, back_populates="tags", lazy="select"
    )

    skills = relationship(
        "Skill", secondary=skill_tags, back_populates="tags", lazy="select"
    )

    notes = relationship(
        "Note", secondary=note_tags, back_populates="tags", lazy="select"
    )

    companies = relationship(
        "Company", secondary=company_tags, back_populates="tags", lazy="select"
    )

    job_applications = relationship(
        "JobApplication", secondary=job_application_tags, back_populates="tags", lazy="select"
    )

    network_contacts = relationship(
        "NetworkContact", secondary=network_contact_tags, back_populates="tags", lazy="select"
    )

    work_experiences = relationship(
        "WorkExperience", secondary=work_experience_tags, back_populates="tags", lazy="select"
    )

    achievement_facts = relationship(
        "AchievementFact", secondary=achievement_fact_tags, back_populates="tags", lazy="select"
    )

    def __repr__(self) -> str:
        """String representation of the tag."""
        return f"<Tag(id={self.id}, name='{self.name}')>"
