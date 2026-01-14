"""Unit tests for Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

from pydantic import ValidationError
import pytest

from turbo.core.schemas import (
    DocumentCreate,
    IssueCreate,
    IssueResponse,
    IssueUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TagCreate,
    TagResponse,
)


class TestProjectSchemas:
    """Test Project Pydantic schemas."""

    def test_project_create_valid_data(self):
        """Test creating a valid ProjectCreate schema."""
        data = {
            "name": "Test Project",
            "description": "A test project for unit testing",
            "priority": "high",
            "status": "active",
        }

        project = ProjectCreate(**data)

        assert project.name == "Test Project"
        assert project.description == "A test project for unit testing"
        assert project.priority == "high"
        assert project.status == "active"

    def test_project_create_with_defaults(self):
        """Test ProjectCreate with default values."""
        data = {"name": "Minimal Project", "description": "Just name and description"}

        project = ProjectCreate(**data)

        assert project.name == "Minimal Project"
        assert project.description == "Just name and description"
        assert project.priority == "medium"  # Default value
        assert project.status == "active"  # Default value

    def test_project_create_name_validation(self):
        """Test that project name validation works."""
        # Empty name should fail
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="", description="Valid description")

        assert "ensure this value has at least 1 characters" in str(exc_info.value)

        # Name too long should fail
        long_name = "x" * 101  # Max length is 100
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name=long_name, description="Valid description")

        assert "ensure this value has at most 100 characters" in str(exc_info.value)

        # Whitespace-only name should fail
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="   ", description="Valid description")

        assert "Name cannot be empty or whitespace" in str(exc_info.value)

    def test_project_create_description_validation(self):
        """Test that project description validation works."""
        # Empty description should fail
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="Valid Name", description="")

        assert "ensure this value has at least 1 characters" in str(exc_info.value)

        # Whitespace-only description should fail
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="Valid Name", description="   ")

        assert "Description cannot be empty or whitespace" in str(exc_info.value)

    def test_project_create_priority_validation(self):
        """Test priority field validation."""
        valid_priorities = ["low", "medium", "high", "critical"]

        for priority in valid_priorities:
            project = ProjectCreate(
                name="Test Project", description="Test Description", priority=priority
            )
            assert project.priority == priority

        # Invalid priority should fail
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                name="Test Project", description="Test Description", priority="invalid"
            )

        assert "unexpected value" in str(exc_info.value)

    def test_project_create_status_validation(self):
        """Test status field validation."""
        valid_statuses = ["active", "on_hold", "completed", "archived"]

        for status in valid_statuses:
            project = ProjectCreate(
                name="Test Project", description="Test Description", status=status
            )
            assert project.status == status

        # Invalid status should fail
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                name="Test Project", description="Test Description", status="invalid"
            )

        assert "unexpected value" in str(exc_info.value)

    def test_project_create_completion_percentage_validation(self):
        """Test completion percentage validation."""
        # Valid percentages
        valid_percentages = [0.0, 25.5, 50.0, 75.0, 100.0]

        for percentage in valid_percentages:
            project = ProjectCreate(
                name="Test Project",
                description="Test Description",
                completion_percentage=percentage,
            )
            assert project.completion_percentage == percentage

        # Invalid percentages should fail
        invalid_percentages = [-1.0, 100.1, 150.0]

        for percentage in invalid_percentages:
            with pytest.raises(ValidationError) as exc_info:
                ProjectCreate(
                    name="Test Project",
                    description="Test Description",
                    completion_percentage=percentage,
                )

            assert "ensure this value is greater than or equal to 0" in str(
                exc_info.value
            ) or "ensure this value is less than or equal to 100" in str(exc_info.value)

    def test_project_update_schema(self):
        """Test ProjectUpdate schema allows partial updates."""
        # All fields optional for updates
        update = ProjectUpdate()
        assert update.name is None
        assert update.description is None
        assert update.priority is None
        assert update.status is None

        # Partial update
        update = ProjectUpdate(name="Updated Name", priority="high")
        assert update.name == "Updated Name"
        assert update.priority == "high"
        assert update.description is None
        assert update.status is None

    def test_project_response_schema(self):
        """Test ProjectResponse schema."""
        project_id = uuid4()
        now = datetime.now()

        data = {
            "id": project_id,
            "name": "Test Project",
            "description": "Test Description",
            "priority": "medium",
            "status": "active",
            "completion_percentage": 50.0,
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
        }

        response = ProjectResponse(**data)

        assert response.id == project_id
        assert response.name == "Test Project"
        assert response.description == "Test Description"
        assert response.priority == "medium"
        assert response.status == "active"
        assert response.completion_percentage == 50.0
        assert response.is_archived is False
        assert response.created_at == now
        assert response.updated_at == now


class TestIssueSchemas:
    """Test Issue Pydantic schemas."""

    def test_issue_create_valid_data(self):
        """Test creating a valid IssueCreate schema."""
        project_id = uuid4()
        data = {
            "title": "Test Issue",
            "description": "A test issue for unit testing",
            "type": "bug",
            "status": "open",
            "priority": "high",
            "project_id": project_id,
        }

        issue = IssueCreate(**data)

        assert issue.title == "Test Issue"
        assert issue.description == "A test issue for unit testing"
        assert issue.type == "bug"
        assert issue.status == "open"
        assert issue.priority == "high"
        assert issue.project_id == project_id

    def test_issue_create_with_defaults(self):
        """Test IssueCreate with default values."""
        project_id = uuid4()
        data = {
            "title": "Minimal Issue",
            "description": "Just title and description",
            "project_id": project_id,
        }

        issue = IssueCreate(**data)

        assert issue.title == "Minimal Issue"
        assert issue.description == "Just title and description"
        assert issue.type == "task"  # Default value
        assert issue.status == "open"  # Default value
        assert issue.priority == "medium"  # Default value
        assert issue.project_id == project_id

    def test_issue_create_title_validation(self):
        """Test issue title validation."""
        project_id = uuid4()

        # Empty title should fail
        with pytest.raises(ValidationError) as exc_info:
            IssueCreate(
                title="", description="Valid description", project_id=project_id
            )

        assert "ensure this value has at least 1 characters" in str(exc_info.value)

        # Title too long should fail
        long_title = "x" * 201  # Max length is 200
        with pytest.raises(ValidationError) as exc_info:
            IssueCreate(
                title=long_title, description="Valid description", project_id=project_id
            )

        assert "ensure this value has at most 200 characters" in str(exc_info.value)

    def test_issue_create_type_validation(self):
        """Test issue type validation."""
        project_id = uuid4()
        valid_types = ["feature", "bug", "task", "enhancement", "documentation"]

        for issue_type in valid_types:
            issue = IssueCreate(
                title="Test Issue",
                description="Test Description",
                type=issue_type,
                project_id=project_id,
            )
            assert issue.type == issue_type

        # Invalid type should fail
        with pytest.raises(ValidationError) as exc_info:
            IssueCreate(
                title="Test Issue",
                description="Test Description",
                type="invalid_type",
                project_id=project_id,
            )

        assert "unexpected value" in str(exc_info.value)

    def test_issue_create_status_validation(self):
        """Test issue status validation."""
        project_id = uuid4()
        valid_statuses = ["open", "in_progress", "review", "testing", "closed"]

        for status in valid_statuses:
            issue = IssueCreate(
                title="Test Issue",
                description="Test Description",
                status=status,
                project_id=project_id,
            )
            assert issue.status == status

        # Invalid status should fail
        with pytest.raises(ValidationError) as exc_info:
            IssueCreate(
                title="Test Issue",
                description="Test Description",
                status="invalid_status",
                project_id=project_id,
            )

        assert "unexpected value" in str(exc_info.value)

    def test_issue_create_assignee_email_validation(self):
        """Test assignee email validation."""
        project_id = uuid4()

        # Valid email
        issue = IssueCreate(
            title="Test Issue",
            description="Test Description",
            assignee="user@example.com",
            project_id=project_id,
        )
        assert issue.assignee == "user@example.com"

        # Invalid email should fail
        with pytest.raises(ValidationError) as exc_info:
            IssueCreate(
                title="Test Issue",
                description="Test Description",
                assignee="invalid-email",
                project_id=project_id,
            )

        assert "value is not a valid email address" in str(exc_info.value)

    def test_issue_update_schema(self):
        """Test IssueUpdate schema allows partial updates."""
        # All fields optional for updates
        update = IssueUpdate()
        assert update.title is None
        assert update.description is None
        assert update.type is None
        assert update.status is None

        # Partial update
        update = IssueUpdate(title="Updated Title", status="in_progress")
        assert update.title == "Updated Title"
        assert update.status == "in_progress"
        assert update.description is None
        assert update.type is None

    def test_issue_response_schema(self):
        """Test IssueResponse schema."""
        issue_id = uuid4()
        project_id = uuid4()
        now = datetime.now()

        data = {
            "id": issue_id,
            "title": "Test Issue",
            "description": "Test Description",
            "type": "bug",
            "status": "open",
            "priority": "high",
            "assignee": "user@example.com",
            "project_id": project_id,
            "created_at": now,
            "updated_at": now,
        }

        response = IssueResponse(**data)

        assert response.id == issue_id
        assert response.title == "Test Issue"
        assert response.description == "Test Description"
        assert response.type == "bug"
        assert response.status == "open"
        assert response.priority == "high"
        assert response.assignee == "user@example.com"
        assert response.project_id == project_id
        assert response.created_at == now
        assert response.updated_at == now


class TestDocumentSchemas:
    """Test Document Pydantic schemas."""

    def test_document_create_valid_data(self):
        """Test creating a valid DocumentCreate schema."""
        project_id = uuid4()
        data = {
            "title": "Test Document",
            "content": "# Test Document\n\nThis is test content.",
            "type": "specification",
            "format": "markdown",
            "project_id": project_id,
        }

        document = DocumentCreate(**data)

        assert document.title == "Test Document"
        assert document.content == "# Test Document\n\nThis is test content."
        assert document.type == "specification"
        assert document.format == "markdown"
        assert document.project_id == project_id

    def test_document_create_with_optional_fields(self):
        """Test DocumentCreate with optional fields."""
        project_id = uuid4()
        data = {
            "title": "API Documentation",
            "content": "API specification content...",
            "type": "api_doc",
            "format": "markdown",
            "version": "1.0",
            "author": "author@example.com",
            "project_id": project_id,
        }

        document = DocumentCreate(**data)

        assert document.version == "1.0"
        assert document.author == "author@example.com"

    def test_document_create_title_validation(self):
        """Test document title validation."""
        project_id = uuid4()

        # Empty title should fail
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(
                title="",
                content="Valid content",
                type="specification",
                format="markdown",
                project_id=project_id,
            )

        assert "ensure this value has at least 1 characters" in str(exc_info.value)

    def test_document_create_type_validation(self):
        """Test document type validation."""
        project_id = uuid4()
        valid_types = [
            "specification",
            "user_guide",
            "api_doc",
            "readme",
            "changelog",
            "requirements",
            "design",
            "other",
        ]

        for doc_type in valid_types:
            document = DocumentCreate(
                title="Test Document",
                content="Test content",
                type=doc_type,
                format="markdown",
                project_id=project_id,
            )
            assert document.type == doc_type

        # Invalid type should fail
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(
                title="Test Document",
                content="Test content",
                type="invalid_type",
                format="markdown",
                project_id=project_id,
            )

        assert "unexpected value" in str(exc_info.value)

    def test_document_create_format_validation(self):
        """Test document format validation."""
        project_id = uuid4()
        valid_formats = ["markdown", "html", "text", "pdf", "docx"]

        for doc_format in valid_formats:
            document = DocumentCreate(
                title="Test Document",
                content="Test content",
                type="specification",
                format=doc_format,
                project_id=project_id,
            )
            assert document.format == doc_format

        # Invalid format should fail
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(
                title="Test Document",
                content="Test content",
                type="specification",
                format="invalid_format",
                project_id=project_id,
            )

        assert "unexpected value" in str(exc_info.value)

    def test_document_create_author_email_validation(self):
        """Test author email validation."""
        project_id = uuid4()

        # Valid email
        document = DocumentCreate(
            title="Test Document",
            content="Test content",
            type="specification",
            format="markdown",
            author="author@example.com",
            project_id=project_id,
        )
        assert document.author == "author@example.com"

        # Invalid email should fail
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(
                title="Test Document",
                content="Test content",
                type="specification",
                format="markdown",
                author="invalid-email",
                project_id=project_id,
            )

        assert "value is not a valid email address" in str(exc_info.value)


class TestTagSchemas:
    """Test Tag Pydantic schemas."""

    def test_tag_create_valid_data(self):
        """Test creating a valid TagCreate schema."""
        data = {
            "name": "frontend",
            "color": "#FF5733",
            "description": "Frontend development tasks",
        }

        tag = TagCreate(**data)

        assert tag.name == "frontend"
        assert tag.color == "#FF5733"
        assert tag.description == "Frontend development tasks"

    def test_tag_create_name_validation(self):
        """Test tag name validation."""
        # Valid name
        tag = TagCreate(name="backend", color="#33FF57")
        assert tag.name == "backend"

        # Empty name should fail
        with pytest.raises(ValidationError) as exc_info:
            TagCreate(name="", color="#FF0000")

        assert "ensure this value has at least 1 characters" in str(exc_info.value)

        # Name too long should fail
        long_name = "x" * 51  # Max length is 50
        with pytest.raises(ValidationError) as exc_info:
            TagCreate(name=long_name, color="#FF0000")

        assert "ensure this value has at most 50 characters" in str(exc_info.value)

    def test_tag_create_color_validation(self):
        """Test tag color validation."""
        # Valid hex colors
        valid_colors = ["#FF5733", "#33FF57", "#3357FF", "#000000", "#FFFFFF"]

        for color in valid_colors:
            tag = TagCreate(name="test", color=color)
            assert tag.color == color

        # Invalid color formats should fail
        invalid_colors = ["FF5733", "#GG5733", "red", "#12345", "#1234567"]

        for color in invalid_colors:
            with pytest.raises(ValidationError) as exc_info:
                TagCreate(name="test", color=color)

            assert "Invalid hex color format" in str(exc_info.value)

    def test_tag_response_schema(self):
        """Test TagResponse schema."""
        tag_id = uuid4()

        data = {
            "id": tag_id,
            "name": "frontend",
            "color": "#FF5733",
            "description": "Frontend development tasks",
        }

        response = TagResponse(**data)

        assert response.id == tag_id
        assert response.name == "frontend"
        assert response.color == "#FF5733"
        assert response.description == "Frontend development tasks"


class TestSchemaValidation:
    """Test advanced schema validation features."""

    def test_name_whitespace_validation(self):
        """Test that names with only whitespace are rejected."""
        # Project name
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="   ", description="Valid description")
        assert "Name cannot be empty or whitespace" in str(exc_info.value)

        # Issue title
        project_id = uuid4()
        with pytest.raises(ValidationError) as exc_info:
            IssueCreate(
                title="   ", description="Valid description", project_id=project_id
            )
        assert "Title cannot be empty or whitespace" in str(exc_info.value)

    def test_description_whitespace_validation(self):
        """Test that descriptions with only whitespace are rejected."""
        # Project description
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="Valid Name", description="   ")
        assert "Description cannot be empty or whitespace" in str(exc_info.value)

        # Issue description
        project_id = uuid4()
        with pytest.raises(ValidationError) as exc_info:
            IssueCreate(title="Valid Title", description="   ", project_id=project_id)
        assert "Description cannot be empty or whitespace" in str(exc_info.value)

    def test_uuid_validation(self):
        """Test UUID field validation."""
        # Valid UUID
        valid_uuid = uuid4()
        project = ProjectCreate(name="Test Project", description="Test Description")
        # This would be tested in the context where project_id is passed

        # Invalid UUID string should fail in actual usage
        # This is more relevant for API endpoint testing
