"""Unit tests for core business services."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from turbo.core.models import Document, Issue, Project, Tag
from turbo.core.schemas import (
    DocumentCreate,
    DocumentResponse,
    IssueCreate,
    IssueResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TagCreate,
    TagResponse,
)
from turbo.core.services import (
    DocumentService,
    IssueService,
    ProjectService,
    TagService,
)
from turbo.utils.exceptions import (
    DuplicateResourceError,
    IssueNotFoundError,
    ProjectNotFoundError,
    TagNotFoundError,
)


class TestProjectService:
    """Test the ProjectService business logic."""

    @pytest.fixture
    def mock_project_repository(self):
        """Mock project repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_issue_repository(self):
        """Mock issue repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_document_repository(self):
        """Mock document repository."""
        return AsyncMock()

    @pytest.fixture
    def project_service(
        self, mock_project_repository, mock_issue_repository, mock_document_repository
    ):
        """Project service with mocked dependencies."""
        return ProjectService(
            project_repository=mock_project_repository,
            issue_repository=mock_issue_repository,
            document_repository=mock_document_repository,
        )

    @pytest.mark.asyncio
    async def test_create_project_success(
        self, project_service, mock_project_repository
    ):
        """Test successful project creation."""
        # Arrange
        project_data = ProjectCreate(
            name="Test Project", description="A test project", priority="high"
        )

        expected_project = Project(
            id=uuid4(),
            name="Test Project",
            description="A test project",
            priority="high",
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_project_repository.create.return_value = expected_project

        # Act
        result = await project_service.create_project(project_data)

        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.name == "Test Project"
        assert result.description == "A test project"
        assert result.priority == "high"
        mock_project_repository.create.assert_called_once_with(project_data)

    @pytest.mark.asyncio
    async def test_get_project_by_id_success(
        self, project_service, mock_project_repository
    ):
        """Test successful project retrieval by ID."""
        # Arrange
        project_id = uuid4()
        expected_project = Project(
            id=project_id,
            name="Test Project",
            description="A test project",
            status="active",
        )

        mock_project_repository.get_by_id.return_value = expected_project

        # Act
        result = await project_service.get_project_by_id(project_id)

        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.id == project_id
        assert result.name == "Test Project"
        mock_project_repository.get_by_id.assert_called_once_with(project_id)

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(
        self, project_service, mock_project_repository
    ):
        """Test project not found scenario."""
        # Arrange
        project_id = uuid4()
        mock_project_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ProjectNotFoundError) as exc_info:
            await project_service.get_project_by_id(project_id)

        assert exc_info.value.project_id == project_id
        mock_project_repository.get_by_id.assert_called_once_with(project_id)

    @pytest.mark.asyncio
    async def test_get_all_projects(self, project_service, mock_project_repository):
        """Test retrieving all projects."""
        # Arrange
        projects = [
            Project(
                id=uuid4(),
                name=f"Project {i}",
                description=f"Description {i}",
                status="active",
            )
            for i in range(3)
        ]

        mock_project_repository.get_all.return_value = projects

        # Act
        result = await project_service.get_all_projects()

        # Assert
        assert len(result) == 3
        assert all(isinstance(project, ProjectResponse) for project in result)
        assert result[0].name == "Project 0"
        assert result[1].name == "Project 1"
        assert result[2].name == "Project 2"
        mock_project_repository.get_all.assert_called_once_with(limit=None, offset=None)

    @pytest.mark.asyncio
    async def test_get_all_projects_with_pagination(
        self, project_service, mock_project_repository
    ):
        """Test retrieving projects with pagination."""
        # Arrange
        projects = [
            Project(
                id=uuid4(),
                name=f"Project {i}",
                description=f"Description {i}",
                status="active",
            )
            for i in range(2)
        ]

        mock_project_repository.get_all.return_value = projects

        # Act
        result = await project_service.get_all_projects(limit=10, offset=5)

        # Assert
        assert len(result) == 2
        mock_project_repository.get_all.assert_called_once_with(limit=10, offset=5)

    @pytest.mark.asyncio
    async def test_update_project_success(
        self, project_service, mock_project_repository
    ):
        """Test successful project update."""
        # Arrange
        project_id = uuid4()
        update_data = ProjectUpdate(name="Updated Project", priority="critical")

        updated_project = Project(
            id=project_id,
            name="Updated Project",
            description="Original description",
            priority="critical",
            status="active",
        )

        mock_project_repository.update.return_value = updated_project

        # Act
        result = await project_service.update_project(project_id, update_data)

        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.id == project_id
        assert result.name == "Updated Project"
        assert result.priority == "critical"
        mock_project_repository.update.assert_called_once_with(project_id, update_data)

    @pytest.mark.asyncio
    async def test_update_project_not_found(
        self, project_service, mock_project_repository
    ):
        """Test updating non-existent project."""
        # Arrange
        project_id = uuid4()
        update_data = ProjectUpdate(name="Updated Project")

        mock_project_repository.update.return_value = None

        # Act & Assert
        with pytest.raises(ProjectNotFoundError) as exc_info:
            await project_service.update_project(project_id, update_data)

        assert exc_info.value.project_id == project_id
        mock_project_repository.update.assert_called_once_with(project_id, update_data)

    @pytest.mark.asyncio
    async def test_delete_project_success(
        self, project_service, mock_project_repository
    ):
        """Test successful project deletion."""
        # Arrange
        project_id = uuid4()
        mock_project_repository.delete.return_value = True

        # Act
        result = await project_service.delete_project(project_id)

        # Assert
        assert result is True
        mock_project_repository.delete.assert_called_once_with(project_id)

    @pytest.mark.asyncio
    async def test_delete_project_not_found(
        self, project_service, mock_project_repository
    ):
        """Test deleting non-existent project."""
        # Arrange
        project_id = uuid4()
        mock_project_repository.delete.return_value = False

        # Act & Assert
        with pytest.raises(ProjectNotFoundError) as exc_info:
            await project_service.delete_project(project_id)

        assert exc_info.value.project_id == project_id
        mock_project_repository.delete.assert_called_once_with(project_id)

    @pytest.mark.asyncio
    async def test_get_project_statistics(
        self, project_service, mock_project_repository, mock_issue_repository
    ):
        """Test getting project statistics."""
        # Arrange
        project_id = uuid4()
        project = Project(
            id=project_id, name="Test Project", description="Test", status="active"
        )

        issues = [
            Issue(
                id=uuid4(),
                title=f"Issue {i}",
                description=f"Desc {i}",
                status="open" if i < 2 else "closed",
                type="bug",
                project_id=project_id,
            )
            for i in range(5)
        ]

        mock_project_repository.get_by_id.return_value = project
        mock_issue_repository.get_by_project.return_value = issues

        # Act
        result = await project_service.get_project_statistics(project_id)

        # Assert
        assert result["project_id"] == project_id
        assert result["total_issues"] == 5
        assert result["open_issues"] == 2
        assert result["closed_issues"] == 3
        assert result["completion_rate"] == 60.0  # 3/5 * 100
        mock_project_repository.get_by_id.assert_called_once_with(project_id)
        mock_issue_repository.get_by_project.assert_called_once_with(project_id)

    @pytest.mark.asyncio
    async def test_archive_project(self, project_service, mock_project_repository):
        """Test archiving a project."""
        # Arrange
        project_id = uuid4()
        archived_project = Project(
            id=project_id,
            name="Test Project",
            description="Test",
            status="active",
            is_archived=True,
        )

        mock_project_repository.update.return_value = archived_project

        # Act
        result = await project_service.archive_project(project_id)

        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.is_archived is True

        # Verify the update call was made with is_archived=True
        mock_project_repository.update.assert_called_once()
        call_args = mock_project_repository.update.call_args
        assert call_args[0][0] == project_id  # project_id argument
        assert (
            call_args[0][1].is_archived is True
        )  # ProjectUpdate with is_archived=True


class TestIssueService:
    """Test the IssueService business logic."""

    @pytest.fixture
    def mock_issue_repository(self):
        """Mock issue repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_project_repository(self):
        """Mock project repository."""
        return AsyncMock()

    @pytest.fixture
    def issue_service(self, mock_issue_repository, mock_project_repository):
        """Issue service with mocked dependencies."""
        return IssueService(
            issue_repository=mock_issue_repository,
            project_repository=mock_project_repository,
        )

    @pytest.mark.asyncio
    async def test_create_issue_success(
        self, issue_service, mock_issue_repository, mock_project_repository
    ):
        """Test successful issue creation."""
        # Arrange
        project_id = uuid4()
        issue_data = IssueCreate(
            title="Test Issue",
            description="A test issue",
            type="bug",
            project_id=project_id,
        )

        project = Project(
            id=project_id, name="Test Project", description="Test", status="active"
        )
        expected_issue = Issue(
            id=uuid4(),
            title="Test Issue",
            description="A test issue",
            type="bug",
            status="open",
            project_id=project_id,
        )

        mock_project_repository.get_by_id.return_value = project
        mock_issue_repository.create.return_value = expected_issue

        # Act
        result = await issue_service.create_issue(issue_data)

        # Assert
        assert isinstance(result, IssueResponse)
        assert result.title == "Test Issue"
        assert result.description == "A test issue"
        assert result.type == "bug"
        mock_project_repository.get_by_id.assert_called_once_with(project_id)
        mock_issue_repository.create.assert_called_once_with(issue_data)

    @pytest.mark.asyncio
    async def test_create_issue_invalid_project(
        self, issue_service, mock_issue_repository, mock_project_repository
    ):
        """Test creating issue with invalid project ID."""
        # Arrange
        project_id = uuid4()
        issue_data = IssueCreate(
            title="Test Issue", description="A test issue", project_id=project_id
        )

        mock_project_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ProjectNotFoundError) as exc_info:
            await issue_service.create_issue(issue_data)

        assert exc_info.value.project_id == project_id
        mock_project_repository.get_by_id.assert_called_once_with(project_id)
        mock_issue_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_issue_by_id_success(self, issue_service, mock_issue_repository):
        """Test successful issue retrieval by ID."""
        # Arrange
        issue_id = uuid4()
        project_id = uuid4()
        expected_issue = Issue(
            id=issue_id,
            title="Test Issue",
            description="A test issue",
            type="bug",
            status="open",
            project_id=project_id,
        )

        mock_issue_repository.get_by_id.return_value = expected_issue

        # Act
        result = await issue_service.get_issue_by_id(issue_id)

        # Assert
        assert isinstance(result, IssueResponse)
        assert result.id == issue_id
        assert result.title == "Test Issue"
        mock_issue_repository.get_by_id.assert_called_once_with(issue_id)

    @pytest.mark.asyncio
    async def test_get_issue_by_id_not_found(
        self, issue_service, mock_issue_repository
    ):
        """Test issue not found scenario."""
        # Arrange
        issue_id = uuid4()
        mock_issue_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(IssueNotFoundError) as exc_info:
            await issue_service.get_issue_by_id(issue_id)

        assert exc_info.value.issue_id == issue_id
        mock_issue_repository.get_by_id.assert_called_once_with(issue_id)

    @pytest.mark.asyncio
    async def test_assign_issue(self, issue_service, mock_issue_repository):
        """Test assigning an issue to someone."""
        # Arrange
        issue_id = uuid4()
        assignee = "developer@example.com"

        updated_issue = Issue(
            id=issue_id,
            title="Test Issue",
            description="Test",
            type="bug",
            status="open",
            assignee=assignee,
            project_id=uuid4(),
        )

        mock_issue_repository.update.return_value = updated_issue

        # Act
        result = await issue_service.assign_issue(issue_id, assignee)

        # Assert
        assert isinstance(result, IssueResponse)
        assert result.assignee == assignee

        # Verify the update call was made with correct assignee
        mock_issue_repository.update.assert_called_once()
        call_args = mock_issue_repository.update.call_args
        assert call_args[0][0] == issue_id  # issue_id argument
        assert call_args[0][1].assignee == assignee  # IssueUpdate with assignee

    @pytest.mark.asyncio
    async def test_close_issue(self, issue_service, mock_issue_repository):
        """Test closing an issue."""
        # Arrange
        issue_id = uuid4()

        closed_issue = Issue(
            id=issue_id,
            title="Test Issue",
            description="Test",
            type="bug",
            status="closed",
            project_id=uuid4(),
        )

        mock_issue_repository.update.return_value = closed_issue

        # Act
        result = await issue_service.close_issue(issue_id)

        # Assert
        assert isinstance(result, IssueResponse)
        assert result.status == "closed"

        # Verify the update call was made with status="closed"
        mock_issue_repository.update.assert_called_once()
        call_args = mock_issue_repository.update.call_args
        assert call_args[0][0] == issue_id  # issue_id argument
        assert call_args[0][1].status == "closed"  # IssueUpdate with status


class TestDocumentService:
    """Test the DocumentService business logic."""

    @pytest.fixture
    def mock_document_repository(self):
        """Mock document repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_project_repository(self):
        """Mock project repository."""
        return AsyncMock()

    @pytest.fixture
    def document_service(self, mock_document_repository, mock_project_repository):
        """Document service with mocked dependencies."""
        return DocumentService(
            document_repository=mock_document_repository,
            project_repository=mock_project_repository,
        )

    @pytest.mark.asyncio
    async def test_create_document_success(
        self, document_service, mock_document_repository, mock_project_repository
    ):
        """Test successful document creation."""
        # Arrange
        project_id = uuid4()
        document_data = DocumentCreate(
            title="Test Document",
            content="# Test Document\n\nContent here",
            type="specification",
            format="markdown",
            project_id=project_id,
        )

        project = Project(
            id=project_id, name="Test Project", description="Test", status="active"
        )
        expected_document = Document(
            id=uuid4(),
            title="Test Document",
            content="# Test Document\n\nContent here",
            type="specification",
            format="markdown",
            project_id=project_id,
        )

        mock_project_repository.get_by_id.return_value = project
        mock_document_repository.create.return_value = expected_document

        # Act
        result = await document_service.create_document(document_data)

        # Assert
        assert isinstance(result, DocumentResponse)
        assert result.title == "Test Document"
        assert result.content == "# Test Document\n\nContent here"
        assert result.type == "specification"
        mock_project_repository.get_by_id.assert_called_once_with(project_id)
        mock_document_repository.create.assert_called_once_with(document_data)

    @pytest.mark.asyncio
    async def test_create_document_invalid_project(
        self, document_service, mock_document_repository, mock_project_repository
    ):
        """Test creating document with invalid project ID."""
        # Arrange
        project_id = uuid4()
        document_data = DocumentCreate(
            title="Test Document",
            content="Content",
            type="specification",
            format="markdown",
            project_id=project_id,
        )

        mock_project_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ProjectNotFoundError) as exc_info:
            await document_service.create_document(document_data)

        assert exc_info.value.project_id == project_id
        mock_project_repository.get_by_id.assert_called_once_with(project_id)
        mock_document_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_document_from_template(
        self, document_service, mock_document_repository
    ):
        """Test generating document from template."""
        # Arrange
        project_id = uuid4()
        template_name = "technical_spec"
        context = {"project_name": "Test Project", "author": "Developer"}

        generated_document = Document(
            id=uuid4(),
            title="Generated Technical Specification",
            content="# Technical Specification for Test Project\n\nAuthor: Developer",
            type="specification",
            format="markdown",
            project_id=project_id,
        )

        mock_document_repository.create.return_value = generated_document

        # Act
        with patch(
            "turbo.core.services.document_service.generate_from_template"
        ) as mock_generate:
            mock_generate.return_value = {
                "title": "Generated Technical Specification",
                "content": "# Technical Specification for Test Project\n\nAuthor: Developer",
            }

            result = await document_service.generate_document_from_template(
                project_id, template_name, context
            )

        # Assert
        assert isinstance(result, DocumentResponse)
        assert result.title == "Generated Technical Specification"
        assert "Test Project" in result.content
        assert "Developer" in result.content
        mock_generate.assert_called_once_with(template_name, context)


class TestTagService:
    """Test the TagService business logic."""

    @pytest.fixture
    def mock_tag_repository(self):
        """Mock tag repository."""
        return AsyncMock()

    @pytest.fixture
    def tag_service(self, mock_tag_repository):
        """Tag service with mocked dependencies."""
        return TagService(tag_repository=mock_tag_repository)

    @pytest.mark.asyncio
    async def test_create_tag_success(self, tag_service, mock_tag_repository):
        """Test successful tag creation."""
        # Arrange
        tag_data = TagCreate(
            name="frontend", color="#FF5733", description="Frontend development tasks"
        )

        expected_tag = Tag(
            id=uuid4(),
            name="frontend",
            color="#FF5733",
            description="Frontend development tasks",
        )

        mock_tag_repository.get_by_name.return_value = None  # Tag doesn't exist
        mock_tag_repository.create.return_value = expected_tag

        # Act
        result = await tag_service.create_tag(tag_data)

        # Assert
        assert isinstance(result, TagResponse)
        assert result.name == "frontend"
        assert result.color == "#FF5733"
        assert result.description == "Frontend development tasks"
        mock_tag_repository.get_by_name.assert_called_once_with("frontend")
        mock_tag_repository.create.assert_called_once_with(tag_data)

    @pytest.mark.asyncio
    async def test_create_tag_duplicate_name(self, tag_service, mock_tag_repository):
        """Test creating tag with duplicate name."""
        # Arrange
        tag_data = TagCreate(name="existing", color="#FF5733")

        existing_tag = Tag(id=uuid4(), name="existing", color="#000000")
        mock_tag_repository.get_by_name.return_value = existing_tag

        # Act & Assert
        with pytest.raises(DuplicateResourceError) as exc_info:
            await tag_service.create_tag(tag_data)

        assert "Tag with name 'existing' already exists" in str(exc_info.value)
        mock_tag_repository.get_by_name.assert_called_once_with("existing")
        mock_tag_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_tag_by_id_success(self, tag_service, mock_tag_repository):
        """Test successful tag retrieval by ID."""
        # Arrange
        tag_id = uuid4()
        expected_tag = Tag(
            id=tag_id,
            name="backend",
            color="#33FF57",
            description="Backend development",
        )

        mock_tag_repository.get_by_id.return_value = expected_tag

        # Act
        result = await tag_service.get_tag_by_id(tag_id)

        # Assert
        assert isinstance(result, TagResponse)
        assert result.id == tag_id
        assert result.name == "backend"
        mock_tag_repository.get_by_id.assert_called_once_with(tag_id)

    @pytest.mark.asyncio
    async def test_get_tag_by_id_not_found(self, tag_service, mock_tag_repository):
        """Test tag not found scenario."""
        # Arrange
        tag_id = uuid4()
        mock_tag_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(TagNotFoundError) as exc_info:
            await tag_service.get_tag_by_id(tag_id)

        assert exc_info.value.tag_id == tag_id
        mock_tag_repository.get_by_id.assert_called_once_with(tag_id)


class TestServiceErrorHandling:
    """Test error handling across services."""

    @pytest.mark.asyncio
    async def test_service_handles_repository_exceptions(self):
        """Test that services properly handle repository exceptions."""
        # Arrange
        mock_repo = AsyncMock()
        mock_repo.get_by_id.side_effect = Exception("Database connection failed")

        service = ProjectService(
            project_repository=mock_repo,
            issue_repository=AsyncMock(),
            document_repository=AsyncMock(),
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.get_project_by_id(uuid4())

        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_service_input_validation(self):
        """Test that services validate input parameters."""
        mock_repo = AsyncMock()
        service = ProjectService(
            project_repository=mock_repo,
            issue_repository=AsyncMock(),
            document_repository=AsyncMock(),
        )

        # Test with invalid UUID (this would be caught by Pydantic in real usage)
        # This test ensures service methods handle invalid inputs gracefully
        with pytest.raises((ValueError, TypeError)):
            await service.get_project_by_id("invalid-uuid")
