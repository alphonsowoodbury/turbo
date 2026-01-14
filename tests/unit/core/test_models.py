"""Unit tests for core database models."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from turbo.core.models import Document, Issue, Project, Tag


class TestBaseModel:
    """Test the base model functionality."""

    @pytest.mark.asyncio
    async def test_base_model_has_id(self, test_session):
        """Test that base model automatically generates UUID."""
        project = Project(
            name="Test Project", description="Test Description", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        assert project.id is not None
        assert len(str(project.id)) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_base_model_has_timestamps(self, test_session):
        """Test that base model has created_at and updated_at."""
        project = Project(
            name="Test Project", description="Test Description", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        assert project.created_at is not None
        assert project.updated_at is not None
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_updated_at_changes_on_update(self, test_session):
        """Test that updated_at changes when model is updated."""
        project = Project(
            name="Test Project", description="Test Description", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        original_updated_at = project.updated_at

        # Update the project
        project.description = "Updated Description"
        await test_session.commit()

        assert project.updated_at > original_updated_at


class TestProjectModel:
    """Test the Project model."""

    @pytest.mark.asyncio
    async def test_create_project_with_required_fields(self, test_session):
        """Test creating a project with all required fields."""
        project = Project(
            name="Test Project", description="A test project", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.status == "active"
        assert project.priority == "medium"  # Default value
        assert project.is_archived is False  # Default value

    @pytest.mark.asyncio
    async def test_create_project_with_optional_fields(self, test_session):
        """Test creating a project with optional fields."""
        project = Project(
            name="High Priority Project",
            description="An important project",
            status="active",
            priority="high",
            completion_percentage=25.5,
        )
        test_session.add(project)
        await test_session.commit()

        assert project.priority == "high"
        assert project.completion_percentage == 25.5

    @pytest.mark.asyncio
    async def test_project_name_cannot_be_null(self, test_session):
        """Test that project name is required."""
        project = Project(description="A project without name", status="active")
        test_session.add(project)

        with pytest.raises(IntegrityError):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_project_description_cannot_be_null(self, test_session):
        """Test that project description is required."""
        project = Project(name="Test Project", status="active")
        test_session.add(project)

        with pytest.raises(IntegrityError):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_project_status_cannot_be_null(self, test_session):
        """Test that project status is required."""
        project = Project(name="Test Project", description="Test Description")
        test_session.add(project)

        with pytest.raises(IntegrityError):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_project_repr(self, test_session):
        """Test project string representation."""
        project = Project(
            name="Test Project", description="Test Description", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        repr_str = repr(project)
        assert "Test Project" in repr_str
        assert str(project.id) in repr_str

    @pytest.mark.asyncio
    async def test_project_can_have_issues(self, test_session):
        """Test that project can have multiple issues."""
        project = Project(
            name="Test Project", description="Test Description", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        issue1 = Issue(
            title="First Issue",
            description="First test issue",
            type="feature",
            status="open",
            project_id=project.id,
        )
        issue2 = Issue(
            title="Second Issue",
            description="Second test issue",
            type="bug",
            status="open",
            project_id=project.id,
        )

        test_session.add_all([issue1, issue2])
        await test_session.commit()

        # Refresh to load relationships
        await test_session.refresh(project)

        assert len(project.issues) == 2
        assert issue1 in project.issues
        assert issue2 in project.issues


class TestIssueModel:
    """Test the Issue model."""

    @pytest.mark.asyncio
    async def test_create_issue_with_required_fields(
        self, test_session, sample_project
    ):
        """Test creating an issue with all required fields."""
        issue = Issue(
            title="Test Issue",
            description="A test issue",
            type="feature",
            status="open",
            project_id=sample_project.id,
        )
        test_session.add(issue)
        await test_session.commit()

        assert issue.title == "Test Issue"
        assert issue.description == "A test issue"
        assert issue.type == "feature"
        assert issue.status == "open"
        assert issue.priority == "medium"  # Default value
        assert issue.project_id == sample_project.id

    @pytest.mark.asyncio
    async def test_create_issue_with_optional_fields(
        self, test_session, sample_project
    ):
        """Test creating an issue with optional fields."""
        issue = Issue(
            title="High Priority Bug",
            description="Critical bug that needs fixing",
            type="bug",
            status="open",
            priority="high",
            assignee="john.doe@example.com",
            project_id=sample_project.id,
        )
        test_session.add(issue)
        await test_session.commit()

        assert issue.priority == "high"
        assert issue.assignee == "john.doe@example.com"

    @pytest.mark.asyncio
    async def test_issue_belongs_to_project(self, test_session, sample_project):
        """Test that issue belongs to a project."""
        issue = Issue(
            title="Test Issue",
            description="A test issue",
            type="feature",
            status="open",
            project_id=sample_project.id,
        )
        test_session.add(issue)
        await test_session.commit()

        await test_session.refresh(issue)
        assert issue.project.id == sample_project.id
        assert issue.project.name == sample_project.name

    @pytest.mark.asyncio
    async def test_issue_project_id_cannot_be_null(self, test_session):
        """Test that issue must belong to a project."""
        issue = Issue(
            title="Orphan Issue",
            description="Issue without project",
            type="feature",
            status="open",
        )
        test_session.add(issue)

        with pytest.raises(IntegrityError):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_issue_title_cannot_be_null(self, test_session, sample_project):
        """Test that issue title is required."""
        issue = Issue(
            description="Issue without title",
            type="feature",
            status="open",
            project_id=sample_project.id,
        )
        test_session.add(issue)

        with pytest.raises(IntegrityError):
            await test_session.commit()


class TestDocumentModel:
    """Test the Document model."""

    @pytest.mark.asyncio
    async def test_create_document_with_required_fields(
        self, test_session, sample_project
    ):
        """Test creating a document with all required fields."""
        document = Document(
            title="Test Document",
            content="# Test Document\n\nThis is test content.",
            type="specification",
            format="markdown",
            project_id=sample_project.id,
        )
        test_session.add(document)
        await test_session.commit()

        assert document.title == "Test Document"
        assert document.content == "# Test Document\n\nThis is test content."
        assert document.type == "specification"
        assert document.format == "markdown"
        assert document.project_id == sample_project.id

    @pytest.mark.asyncio
    async def test_create_document_with_optional_fields(
        self, test_session, sample_project
    ):
        """Test creating a document with optional fields."""
        document = Document(
            title="API Documentation",
            content="API specs here...",
            type="api_doc",
            format="markdown",
            version="1.0",
            author="jane.doe@example.com",
            project_id=sample_project.id,
        )
        test_session.add(document)
        await test_session.commit()

        assert document.version == "1.0"
        assert document.author == "jane.doe@example.com"

    @pytest.mark.asyncio
    async def test_document_belongs_to_project(self, test_session, sample_project):
        """Test that document belongs to a project."""
        document = Document(
            title="Test Document",
            content="Test content",
            type="specification",
            format="markdown",
            project_id=sample_project.id,
        )
        test_session.add(document)
        await test_session.commit()

        await test_session.refresh(document)
        assert document.project.id == sample_project.id
        assert document.project.name == sample_project.name

    @pytest.mark.asyncio
    async def test_document_project_id_cannot_be_null(self, test_session):
        """Test that document must belong to a project."""
        document = Document(
            title="Orphan Document",
            content="Document without project",
            type="specification",
            format="markdown",
        )
        test_session.add(document)

        with pytest.raises(IntegrityError):
            await test_session.commit()


class TestTagModel:
    """Test the Tag model."""

    @pytest.mark.asyncio
    async def test_create_tag_with_required_fields(self, test_session):
        """Test creating a tag with all required fields."""
        tag = Tag(name="frontend", color="#FF5733")
        test_session.add(tag)
        await test_session.commit()

        assert tag.name == "frontend"
        assert tag.color == "#FF5733"

    @pytest.mark.asyncio
    async def test_create_tag_with_optional_description(self, test_session):
        """Test creating a tag with optional description."""
        tag = Tag(
            name="backend", color="#33FF57", description="Backend development tasks"
        )
        test_session.add(tag)
        await test_session.commit()

        assert tag.description == "Backend development tasks"

    @pytest.mark.asyncio
    async def test_tag_name_must_be_unique(self, test_session):
        """Test that tag names must be unique."""
        tag1 = Tag(name="duplicate", color="#FF0000")
        tag2 = Tag(name="duplicate", color="#00FF00")

        test_session.add(tag1)
        await test_session.commit()

        test_session.add(tag2)
        with pytest.raises(IntegrityError):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_tag_name_cannot_be_null(self, test_session):
        """Test that tag name is required."""
        tag = Tag(color="#FF0000")
        test_session.add(tag)

        with pytest.raises(IntegrityError):
            await test_session.commit()


class TestModelRelationships:
    """Test relationships between models."""

    @pytest.mark.asyncio
    async def test_project_issues_relationship(self, test_session):
        """Test the relationship between projects and issues."""
        project = Project(
            name="Test Project", description="Test Description", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        issue1 = Issue(
            title="Issue 1",
            description="First issue",
            type="feature",
            status="open",
            project_id=project.id,
        )
        issue2 = Issue(
            title="Issue 2",
            description="Second issue",
            type="bug",
            status="closed",
            project_id=project.id,
        )

        test_session.add_all([issue1, issue2])
        await test_session.commit()

        # Test project -> issues relationship
        await test_session.refresh(project)
        assert len(project.issues) == 2

        # Test issue -> project relationship
        await test_session.refresh(issue1)
        assert issue1.project.id == project.id

    @pytest.mark.asyncio
    async def test_project_documents_relationship(self, test_session):
        """Test the relationship between projects and documents."""
        project = Project(
            name="Test Project", description="Test Description", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        doc1 = Document(
            title="Doc 1",
            content="Content 1",
            type="specification",
            format="markdown",
            project_id=project.id,
        )
        doc2 = Document(
            title="Doc 2",
            content="Content 2",
            type="user_guide",
            format="markdown",
            project_id=project.id,
        )

        test_session.add_all([doc1, doc2])
        await test_session.commit()

        # Test project -> documents relationship
        await test_session.refresh(project)
        assert len(project.documents) == 2

        # Test document -> project relationship
        await test_session.refresh(doc1)
        assert doc1.project.id == project.id

    @pytest.mark.asyncio
    async def test_project_tags_many_to_many(self, test_session):
        """Test many-to-many relationship between projects and tags."""
        # Create tags
        frontend_tag = Tag(name="frontend", color="#FF5733")
        backend_tag = Tag(name="backend", color="#33FF57")
        test_session.add_all([frontend_tag, backend_tag])
        await test_session.commit()

        # Create project with tags
        project = Project(
            name="Full Stack Project",
            description="Both frontend and backend",
            status="active",
        )
        project.tags.extend([frontend_tag, backend_tag])
        test_session.add(project)
        await test_session.commit()

        # Test relationships
        await test_session.refresh(project)
        assert len(project.tags) == 2
        assert frontend_tag in project.tags
        assert backend_tag in project.tags

        await test_session.refresh(frontend_tag)
        assert project in frontend_tag.projects

    @pytest.mark.asyncio
    async def test_issue_tags_many_to_many(self, test_session, sample_project):
        """Test many-to-many relationship between issues and tags."""
        # Create tags
        bug_tag = Tag(name="bug", color="#FF0000")
        urgent_tag = Tag(name="urgent", color="#FF6600")
        test_session.add_all([bug_tag, urgent_tag])
        await test_session.commit()

        # Create issue with tags
        issue = Issue(
            title="Urgent Bug Fix",
            description="Critical bug needs immediate attention",
            type="bug",
            status="open",
            project_id=sample_project.id,
        )
        issue.tags.extend([bug_tag, urgent_tag])
        test_session.add(issue)
        await test_session.commit()

        # Test relationships
        await test_session.refresh(issue)
        assert len(issue.tags) == 2
        assert bug_tag in issue.tags
        assert urgent_tag in issue.tags

        await test_session.refresh(bug_tag)
        assert issue in bug_tag.issues

    @pytest.mark.asyncio
    async def test_cascade_delete_project_issues(self, test_session):
        """Test that deleting a project cascades to its issues."""
        project = Project(
            name="Temporary Project", description="Will be deleted", status="active"
        )
        test_session.add(project)
        await test_session.commit()

        issue = Issue(
            title="Issue to be deleted",
            description="This issue should be deleted with project",
            type="feature",
            status="open",
            project_id=project.id,
        )
        test_session.add(issue)
        await test_session.commit()

        # Delete the project
        await test_session.delete(project)
        await test_session.commit()

        # Verify issue is also deleted
        from sqlalchemy import select

        result = await test_session.execute(select(Issue).where(Issue.id == issue.id))
        deleted_issue = result.scalar_one_or_none()
        assert deleted_issue is None
