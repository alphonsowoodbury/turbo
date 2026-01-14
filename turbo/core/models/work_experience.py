"""Work experience model."""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Numeric, CheckConstraint
from sqlalchemy import JSON, UUID as PGUUID
from sqlalchemy.orm import relationship

from turbo.core.database.base import Base


class WorkExperience(Base):
    """Work experience and employment history."""

    __tablename__ = "work_experiences"

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign keys
    company_id: Optional[UUID] = Column(PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)

    # Role details
    role_title: str = Column(String(255), nullable=False)
    start_date: date = Column(Date, nullable=False)
    end_date: Optional[date] = Column(Date, nullable=True)
    is_current: bool = Column(Boolean, default=False, nullable=False)

    # Flexible context fields
    team_context: Optional[dict] = Column(JSON, nullable=True)  # team_size, reporting_to, cross_functional_teams
    technologies: Optional[list] = Column(JSON, nullable=True)  # Array of tech names

    # Additional context
    location: Optional[str] = Column(String(255), nullable=True)
    employment_type: Optional[str] = Column(String(50), nullable=True)  # full_time, part_time, contract, freelance
    department: Optional[str] = Column(String(100), nullable=True)

    # Timestamps
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="work_experiences")
    achievements = relationship("AchievementFact", back_populates="experience", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="work_experience_tags", back_populates="work_experiences")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "employment_type IN ('full_time', 'part_time', 'contract', 'freelance')",
            name="work_experiences_employment_type_check"
        ),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="work_experiences_dates_check"
        ),
        CheckConstraint(
            "(is_current = TRUE AND end_date IS NULL) OR (is_current = FALSE)",
            name="work_experiences_current_check"
        ),
    )

    def __repr__(self) -> str:
        return f"<WorkExperience(id={self.id}, role_title='{self.role_title}', company_id={self.company_id})>"


class AchievementFact(Base):
    """Granular, atomic achievement facts - prevents AI hallucination through factual precision."""

    __tablename__ = "achievement_facts"

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign keys
    experience_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("work_experiences.id", ondelete="CASCADE"), nullable=False)

    # Core factual statement
    fact_text: str = Column(Text, nullable=False)

    # Quantifiable metrics
    metric_type: Optional[str] = Column(String(50), nullable=True)  # cost_savings, time_reduction, scale, etc.
    metric_value: Optional[float] = Column(Numeric(15, 2), nullable=True)
    metric_unit: Optional[str] = Column(String(50), nullable=True)  # percentage, dollars, days, etc.

    # Multi-dimensional tagging
    dimensions: list = Column(JSON, nullable=False, default=list)  # ["leadership", "technical", "cost_optimization"]
    leadership_principles: list = Column(JSON, nullable=False, default=list)  # ["frugality", "bias_for_action"]
    skills_used: list = Column(JSON, nullable=False, default=list)  # Array of skill names

    # STAR components
    context: Optional[str] = Column(Text, nullable=True)  # Situation/Task
    impact: Optional[str] = Column(Text, nullable=True)  # Result/Impact

    # Ordering
    display_order: int = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    experience = relationship("WorkExperience", back_populates="achievements")
    tags = relationship("Tag", secondary="achievement_fact_tags", back_populates="achievement_facts")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "metric_value IS NULL OR metric_value >= 0",
            name="achievement_facts_metric_value_check"
        ),
    )

    def __repr__(self) -> str:
        return f"<AchievementFact(id={self.id}, experience_id={self.experience_id}, metric_type='{self.metric_type}')>"
