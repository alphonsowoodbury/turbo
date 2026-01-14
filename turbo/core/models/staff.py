"""Staff model for AI domain experts and team coordinators."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base


class Staff(Base):
    """
    Staff model representing AI domain experts and leadership roles.

    Staff members can be @ mentioned in comments, monitor specific domains,
    and have assignments. Leadership staff have universal edit permissions.
    """

    __tablename__ = "staff"

    # Core identity
    handle: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    alias: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, unique=True, index=True
    )  # Short memorable name for @ mentions (e.g., "Chief", "Scrum", "Build")
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    persona: Mapped[str] = mapped_column(Text, nullable=False)

    # Role & Permissions
    role_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # leadership | domain_expert
    role_title: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # e.g., "Board Member", "Advisor", "Engineer", "Consultant"
    is_leadership_role: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # Configuration
    monitoring_scope: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={
            "entity_types": [],
            "tags": [],
            "focus": "",
            "metrics": [],
        },
    )
    capabilities: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=[],
    )
    allowed_tools: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=["list_projects", "get_project", "create_document"],
    )  # List of tool names this staff member can access

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # Performance & Rating
    overall_rating: Mapped[Optional[float]] = mapped_column(
        nullable=True, default=None
    )  # 0.0-5.0 rating
    performance_metrics: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={
            "completed_tasks": 0,
            "avg_response_time_hours": 0.0,
            "quality_score": 0.0,  # 0.0-100.0
            "completion_rate": 0.0,  # 0.0-100.0
            "total_assignments": 0,
        },
    )

    # Timestamps are inherited from BaseModel (created_at, updated_at)

    # Relationships
    conversations = relationship(
        "StaffConversation",
        back_populates="staff",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="StaffConversation.created_at",
    )
    review_requests = relationship(
        "ReviewRequest",
        back_populates="staff",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ReviewRequest.created_at.desc()",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Staff(id={self.id}, handle='@{self.handle}', name='{self.name}')>"
