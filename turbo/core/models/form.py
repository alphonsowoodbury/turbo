"""Form models for dynamic structured input."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy import JSON, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base


class FormStatus(str, Enum):
    """Form lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Form(Base):
    """
    Form model representing a structured input form.

    Can be attached to issues, documents, or projects.
    Schema defines the form structure (fields, validation, etc).
    """

    __tablename__ = "forms"

    # Note: id, created_at, updated_at inherited from Base

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Form schema (field definitions)
    schema: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Status
    status: Mapped[FormStatus] = mapped_column(
        String(20), default=FormStatus.DRAFT, nullable=False
    )

    # Relationships to entities
    issue_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("issues.id", ondelete="CASCADE"), nullable=True
    )
    document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True
    )
    project_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )

    # Creator info
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user"
    )  # 'user' or 'ai'

    # Workflow configuration
    on_submit: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    responses: Mapped[list["FormResponse"]] = relationship(
        "FormResponse", back_populates="form", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Form {self.title} ({self.status})>"


class FormResponse(Base):
    """
    Form response storing user's answers to a form.

    Uses JSON for fast queries while maintaining flexibility.
    Single response per form (can be edited).
    """

    __tablename__ = "form_responses"

    # Note: id, created_at, updated_at inherited from Base

    form_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False
    )

    # Response data (JSON for queryability)
    responses: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Responder info
    responded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    responded_by_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user"
    )

    # Completion tracking
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    form: Mapped[Form] = relationship("Form", back_populates="responses")
    audit_log: Mapped[list["FormResponseAudit"]] = relationship(
        "FormResponseAudit", back_populates="response", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FormResponse for {self.form_id} by {self.responded_by}>"


class FormResponseAudit(Base):
    """
    Audit trail for form response changes.

    Tracks who changed what and when for compliance/history.
    """

    __tablename__ = "form_response_audit"

    # Note: id, created_at, updated_at inherited from Base

    response_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("form_responses.id", ondelete="CASCADE"), nullable=False
    )

    # What changed
    field_id: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Who changed it
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_by_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user"
    )

    # When
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    response: Mapped[FormResponse] = relationship(
        "FormResponse", back_populates="audit_log"
    )

    def __repr__(self) -> str:
        return f"<FormResponseAudit {self.field_id} at {self.changed_at}>"
