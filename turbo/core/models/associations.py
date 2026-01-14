"""Association tables for many-to-many relationships."""

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID

from turbo.core.database.base import Base

# Many-to-many association table for projects and tags
project_tags = Table(
    "project_tags",
    Base.metadata,
    Column(
        "project_id",
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for issues and tags
issue_tags = Table(
    "issue_tags",
    Base.metadata,
    Column(
        "issue_id",
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for projects and blueprints
project_blueprints = Table(
    "project_blueprints",
    Base.metadata,
    Column(
        "project_id",
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "blueprint_id",
        UUID(as_uuid=True),
        ForeignKey("blueprints.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for milestones and issues
milestone_issues = Table(
    "milestone_issues",
    Base.metadata,
    Column(
        "milestone_id",
        UUID(as_uuid=True),
        ForeignKey("milestones.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "issue_id",
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for milestones and tags
milestone_tags = Table(
    "milestone_tags",
    Base.metadata,
    Column(
        "milestone_id",
        UUID(as_uuid=True),
        ForeignKey("milestones.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for milestones and documents
milestone_documents = Table(
    "milestone_documents",
    Base.metadata,
    Column(
        "milestone_id",
        UUID(as_uuid=True),
        ForeignKey("milestones.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for initiatives and issues
initiative_issues = Table(
    "initiative_issues",
    Base.metadata,
    Column(
        "initiative_id",
        UUID(as_uuid=True),
        ForeignKey("initiatives.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "issue_id",
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for initiatives and tags
initiative_tags = Table(
    "initiative_tags",
    Base.metadata,
    Column(
        "initiative_id",
        UUID(as_uuid=True),
        ForeignKey("initiatives.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for initiatives and documents
initiative_documents = Table(
    "initiative_documents",
    Base.metadata,
    Column(
        "initiative_id",
        UUID(as_uuid=True),
        ForeignKey("initiatives.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for literature and tags
literature_tags = Table(
    "literature_tags",
    Base.metadata,
    Column(
        "literature_id",
        UUID(as_uuid=True),
        ForeignKey("literature.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for skills and tags
skill_tags = Table(
    "skill_tags",
    Base.metadata,
    Column(
        "skill_id",
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for notes and tags
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column(
        "note_id",
        UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for companies and tags
company_tags = Table(
    "company_tags",
    Base.metadata,
    Column(
        "company_id",
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for job_applications and tags
job_application_tags = Table(
    "job_application_tags",
    Base.metadata,
    Column(
        "job_application_id",
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for network_contacts and tags
network_contact_tags = Table(
    "network_contact_tags",
    Base.metadata,
    Column(
        "network_contact_id",
        UUID(as_uuid=True),
        ForeignKey("network_contacts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for work_experiences and tags
work_experience_tags = Table(
    "work_experience_tags",
    Base.metadata,
    Column(
        "work_experience_id",
        UUID(as_uuid=True),
        ForeignKey("work_experiences.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-many association table for achievement_facts and tags
achievement_fact_tags = Table(
    "achievement_fact_tags",
    Base.metadata,
    Column(
        "achievement_fact_id",
        UUID(as_uuid=True),
        ForeignKey("achievement_facts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Issue dependency tracking table
# Represents blocking relationships between issues
issue_dependencies = Table(
    "issue_dependencies",
    Base.metadata,
    Column(
        "blocking_issue_id",
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "blocked_issue_id",
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "dependency_type",
        String(50),
        nullable=False,
        default="blocks",
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    ),
    CheckConstraint("blocking_issue_id <> blocked_issue_id", name="no_self_dependency"),
)
