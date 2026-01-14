"""NetworkContact model definition for career management."""

from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from turbo.core.database.base import Base
from turbo.core.models.associations import network_contact_tags


class NetworkContact(Base):
    """NetworkContact model for tracking professional network and job search contacts."""

    __tablename__ = "network_contacts"

    # Foreign keys
    company_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )  # Optional: may not be at a company we're tracking

    # Contact info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    linkedin_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)

    # Professional info
    current_title = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)  # Text field for companies not in our companies table

    # Contact type
    contact_type = Column(
        String(50),
        nullable=True,
        index=True
    )  # recruiter_internal, recruiter_external, hiring_manager, peer, referrer, mentor, former_colleague

    # Relationship tracking
    relationship_strength = Column(
        String(20),
        nullable=False,
        default="cold",
        index=True
    )  # cold, warm, hot
    last_contact_date = Column(DateTime(timezone=True), nullable=True, index=True)
    next_followup_date = Column(DateTime(timezone=True), nullable=True, index=True)
    interaction_count = Column(Integer, default=0)

    # Context
    how_we_met = Column(Text, nullable=True)
    conversation_history = Column(Text, nullable=True)
    referral_status = Column(String(50), nullable=True)  # none, requested, agreed, completed

    # Social
    github_url = Column(String(500), nullable=True)
    personal_website = Column(String(500), nullable=True)
    twitter_url = Column(String(500), nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    company = relationship("Company", back_populates="network_contacts")

    tags = relationship(
        "Tag",
        secondary=network_contact_tags,
        back_populates="network_contacts",
        lazy="select"
    )

    def __repr__(self) -> str:
        """String representation of the network contact."""
        full_name = f"{self.first_name} {self.last_name}"
        return f"<NetworkContact(id={self.id}, name='{full_name}', type='{self.contact_type}')>"
