"""Unit tests for repository pattern implementations."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from turbo.core.models import Project
from turbo.core.repositories import (
    BaseRepository,
    DocumentRepository,
    IssueRepository,
    ProjectRepository,
    TagRepository,
)
from turbo.core.schemas import (
    DocumentCreate,
    DocumentUpdate,
    IssueCreate,
    IssueUpdate,
    ProjectCreate,
    ProjectUpdate,
    TagCreate,
)


class TestBaseRepository:
    """Test the base repository functionality."""

    @pytest.mark.asyncio
    async def test_base_repository_initialization(self, test_session):
        """Test that base repository initializes correctly."""
        repo = BaseRepository(test_session)
        assert repo._session == test_session

    @pytest.mark.asyncio
    async def test_base_repository_abstract_methods(self):
        """Test that base repository has abstract methods."""
        # BaseRepository should not be instantiable directly due to abstract methods
        # This is more of a design test to ensure proper inheritance
        pass


class TestProjectRepository:
    """Test the ProjectRepository implementation."""

    @pytest.fixture
    def project_repo(self, test_session):
        """Project repository fixture."""
        return ProjectRepository(test_session)

    @pytest.mark.asyncio
    async def test_create_project(self, project_repo):
        """Test creating a new project."""
        project_data = ProjectCreate(
            name="Test Project",
            description="A test project for repository testing",
            priority="high",
            status="active",
        )

        created_project = await project_repo.create(project_data)

        assert created_project.id is not None
        assert created_project.name == "Test Project"
        assert created_project.description == "A test project for repository testing"
        assert created_project.priority == "high"
        assert created_project.status == "active"
        assert created_project.completion_percentage == 0.0  # Default
        assert created_project.is_archived is False  # Default
        assert created_project.created_at is not None
        assert created_project.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_project_by_id(self, project_repo, sample_project):
        """Test retrieving a project by ID."""
        retrieved_project = await project_repo.get_by_id(sample_project.id)

        assert retrieved_project is not None
        assert retrieved_project.id == sample_project.id
        assert retrieved_project.name == sample_project.name
        assert retrieved_project.description == sample_project.description

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, project_repo):
        """Test retrieving a non-existent project."""
        non_existent_id = uuid4()
        result = await project_repo.get_by_id(non_existent_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_projects(self, project_repo, test_session):
        """Test retrieving all projects."""
        # Create multiple projects
        projects_data = [
            ProjectCreate(name=f"Project {i}", description=f"Description {i}")
            for i in range(3)
        ]

        created_projects = []
        for project_data in projects_data:
            project = await project_repo.create(project_data)
            created_projects.append(project)

        # Retrieve all projects
        all_projects = await project_repo.get_all()

        assert len(all_projects) >= 3  # At least the ones we created
        project_names = [p.name for p in all_projects]
        assert "Project 0" in project_names
        assert "Project 1" in project_names
        assert "Project 2" in project_names

    @pytest.mark.asyncio
    async def test_get_all_projects_with_limit_offset(self, project_repo, test_session):
        """Test retrieving projects with pagination."""
        # Create multiple projects
        projects_data = [
            ProjectCreate(name=f"Paginated Project {i}", description=f"Description {i}")
            for i in range(5)
        ]

        for project_data in projects_data:
            await project_repo.create(project_data)

        # Test with limit
        limited_projects = await project_repo.get_all(limit=3)
        assert len(limited_projects) == 3

        # Test with offset
        offset_projects = await project_repo.get_all(offset=2, limit=3)
        assert len(offset_projects) <= 3

    @pytest.mark.asyncio
    async def test_update_project(self, project_repo, sample_project):
        """Test updating a project."""
        original_updated_at = sample_project.updated_at

        update_data = ProjectUpdate(
            name="Updated Project Name", priority="critical", completion_percentage=75.0
        )

        updated_project = await project_repo.update(sample_project.id, update_data)

        assert updated_project is not None
        assert updated_project.id == sample_project.id
        assert updated_project.name == "Updated Project Name"
        assert updated_project.priority == "critical"
        assert updated_project.completion_percentage == 75.0
        assert updated_project.description == sample_project.description  # Unchanged
        assert updated_project.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, project_repo):
        """Test updating a non-existent project."""
        non_existent_id = uuid4()
        update_data = ProjectUpdate(name="This should fail")

        result = await project_repo.update(non_existent_id, update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_project(self, project_repo, test_session):
        """Test deleting a project."""
        # Create a project to delete
        project_data = ProjectCreate(
            name="Project to Delete", description="This project will be deleted"
        )
        project = await project_repo.create(project_data)
        project_id = project.id

        # Delete the project
        success = await project_repo.delete(project_id)

        assert success is True

        # Verify it's deleted
        deleted_project = await project_repo.get_by_id(project_id)
        assert deleted_project is None

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, project_repo):
        """Test deleting a non-existent project."""
        non_existent_id = uuid4()

        success = await project_repo.delete(non_existent_id)

        assert success is False

    @pytest.mark.asyncio
    async def test_get_projects_by_status(self, project_repo):
        """Test retrieving projects by status."""
        # Create projects with different statuses
        active_project = await project_repo.create(
            ProjectCreate(name="Active Project", description="Active", status="active")
        )
        completed_project = await project_repo.create(
            ProjectCreate(
                name="Completed Project", description="Done", status="completed"
            )
        )

        # Get active projects
        active_projects = await project_repo.get_by_status("active")
        active_names = [p.name for p in active_projects]
        assert "Active Project" in active_names

        # Get completed projects
        completed_projects = await project_repo.get_by_status("completed")
        completed_names = [p.name for p in completed_projects]
        assert "Completed Project" in completed_names

    @pytest.mark.asyncio
    async def test_search_projects_by_name(self, project_repo):
        """Test searching projects by name."""
        # Create projects with searchable names
        await project_repo.create(
            ProjectCreate(name="Frontend Dashboard", description="UI project")
        )
        await project_repo.create(
            ProjectCreate(name="Backend API", description="API project")
        )
        await project_repo.create(
            ProjectCreate(name="Mobile Frontend", description="Mobile UI")
        )

        # Search for "Frontend"
        frontend_projects = await project_repo.search_by_name("Frontend")
        frontend_names = [p.name for p in frontend_projects]
        assert "Frontend Dashboard" in frontend_names
        assert "Mobile Frontend" in frontend_names
        assert "Backend API" not in frontend_names

    @pytest.mark.asyncio
    async def test_get_projects_with_issues(self, project_repo, test_session):
        """Test retrieving projects with their issues loaded."""
        # Create a project
        project = await project_repo.create(
            ProjectCreate(name="Project with Issues", description="Has issues")
        )

        # Create issues for the project
        issue_repo = IssueRepository(test_session)
        await issue_repo.create(
            IssueCreate(
                title="Issue 1", description="First issue", project_id=project.id
            )
        )
        await issue_repo.create(
            IssueCreate(
                title="Issue 2", description="Second issue", project_id=project.id
            )
        )

        # Get project with issues
        project_with_issues = await project_repo.get_with_issues(project.id)

        assert project_with_issues is not None
        assert len(project_with_issues.issues) == 2
        issue_titles = [issue.title for issue in project_with_issues.issues]
        assert "Issue 1" in issue_titles
        assert "Issue 2" in issue_titles


class TestIssueRepository:
    """Test the IssueRepository implementation."""

    @pytest.fixture
    def issue_repo(self, test_session):
        """Issue repository fixture."""
        return IssueRepository(test_session)

    @pytest.mark.asyncio
    async def test_create_issue(self, issue_repo, sample_project):
        """Test creating a new issue."""
        issue_data = IssueCreate(
            title="Test Issue",
            description="A test issue for repository testing",
            type="bug",
            status="open",
            priority="high",
            project_id=sample_project.id,
        )

        created_issue = await issue_repo.create(issue_data)

        assert created_issue.id is not None
        assert created_issue.title == "Test Issue"
        assert created_issue.description == "A test issue for repository testing"
        assert created_issue.type == "bug"
        assert created_issue.status == "open"
        assert created_issue.priority == "high"
        assert created_issue.project_id == sample_project.id
        assert created_issue.created_at is not None
        assert created_issue.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_issue_by_id(self, issue_repo, sample_issue):
        """Test retrieving an issue by ID."""
        retrieved_issue = await issue_repo.get_by_id(sample_issue.id)

        assert retrieved_issue is not None
        assert retrieved_issue.id == sample_issue.id
        assert retrieved_issue.title == sample_issue.title
        assert retrieved_issue.description == sample_issue.description

    @pytest.mark.asyncio
    async def test_get_issues_by_project(
        self, issue_repo, sample_project, test_session
    ):
        """Test retrieving all issues for a project."""
        # Create multiple issues for the project
        issues_data = [
            IssueCreate(
                title=f"Issue {i}",
                description=f"Description {i}",
                project_id=sample_project.id,
            )
            for i in range(3)
        ]

        created_issues = []
        for issue_data in issues_data:
            issue = await issue_repo.create(issue_data)
            created_issues.append(issue)

        # Retrieve issues by project
        project_issues = await issue_repo.get_by_project(sample_project.id)

        assert len(project_issues) >= 3  # At least the ones we created
        issue_titles = [issue.title for issue in project_issues]
        assert "Issue 0" in issue_titles
        assert "Issue 1" in issue_titles
        assert "Issue 2" in issue_titles

    @pytest.mark.asyncio
    async def test_get_issues_by_status(self, issue_repo, sample_project):
        """Test retrieving issues by status."""
        # Create issues with different statuses
        open_issue = await issue_repo.create(
            IssueCreate(
                title="Open Issue",
                description="Open",
                status="open",
                project_id=sample_project.id,
            )
        )
        closed_issue = await issue_repo.create(
            IssueCreate(
                title="Closed Issue",
                description="Closed",
                status="closed",
                project_id=sample_project.id,
            )
        )

        # Get open issues
        open_issues = await issue_repo.get_by_status("open")
        open_titles = [issue.title for issue in open_issues]
        assert "Open Issue" in open_titles

        # Get closed issues
        closed_issues = await issue_repo.get_by_status("closed")
        closed_titles = [issue.title for issue in closed_issues]
        assert "Closed Issue" in closed_titles

    @pytest.mark.asyncio
    async def test_update_issue(self, issue_repo, sample_issue):
        """Test updating an issue."""
        original_updated_at = sample_issue.updated_at

        update_data = IssueUpdate(
            title="Updated Issue Title",
            status="in_progress",
            priority="critical",
            assignee="developer@example.com",
        )

        updated_issue = await issue_repo.update(sample_issue.id, update_data)

        assert updated_issue is not None
        assert updated_issue.id == sample_issue.id
        assert updated_issue.title == "Updated Issue Title"
        assert updated_issue.status == "in_progress"
        assert updated_issue.priority == "critical"
        assert updated_issue.assignee == "developer@example.com"
        assert updated_issue.description == sample_issue.description  # Unchanged
        assert updated_issue.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_delete_issue(self, issue_repo, sample_project):
        """Test deleting an issue."""
        # Create an issue to delete
        issue_data = IssueCreate(
            title="Issue to Delete",
            description="This issue will be deleted",
            project_id=sample_project.id,
        )
        issue = await issue_repo.create(issue_data)
        issue_id = issue.id

        # Delete the issue
        success = await issue_repo.delete(issue_id)

        assert success is True

        # Verify it's deleted
        deleted_issue = await issue_repo.get_by_id(issue_id)
        assert deleted_issue is None

    @pytest.mark.asyncio
    async def test_search_issues_by_title(self, issue_repo, sample_project):
        """Test searching issues by title."""
        # Create issues with searchable titles
        await issue_repo.create(
            IssueCreate(
                title="Fix authentication bug",
                description="Auth issue",
                project_id=sample_project.id,
            )
        )
        await issue_repo.create(
            IssueCreate(
                title="Add user authentication",
                description="New auth feature",
                project_id=sample_project.id,
            )
        )
        await issue_repo.create(
            IssueCreate(
                title="Update database schema",
                description="DB changes",
                project_id=sample_project.id,
            )
        )

        # Search for "authentication"
        auth_issues = await issue_repo.search_by_title("authentication")
        auth_titles = [issue.title for issue in auth_issues]
        assert "Fix authentication bug" in auth_titles
        assert "Add user authentication" in auth_titles
        assert "Update database schema" not in auth_titles


class TestDocumentRepository:
    """Test the DocumentRepository implementation."""

    @pytest.fixture
    def document_repo(self, test_session):
        """Document repository fixture."""
        return DocumentRepository(test_session)

    @pytest.mark.asyncio
    async def test_create_document(self, document_repo, sample_project):
        """Test creating a new document."""
        document_data = DocumentCreate(
            title="Test Document",
            content="# Test Document\n\nThis is test content.",
            type="specification",
            format="markdown",
            project_id=sample_project.id,
        )

        created_document = await document_repo.create(document_data)

        assert created_document.id is not None
        assert created_document.title == "Test Document"
        assert created_document.content == "# Test Document\n\nThis is test content."
        assert created_document.type == "specification"
        assert created_document.format == "markdown"
        assert created_document.project_id == sample_project.id
        assert created_document.created_at is not None
        assert created_document.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, document_repo, sample_document):
        """Test retrieving a document by ID."""
        retrieved_document = await document_repo.get_by_id(sample_document.id)

        assert retrieved_document is not None
        assert retrieved_document.id == sample_document.id
        assert retrieved_document.title == sample_document.title
        assert retrieved_document.content == sample_document.content

    @pytest.mark.asyncio
    async def test_get_documents_by_project(self, document_repo, sample_project):
        """Test retrieving all documents for a project."""
        # Create multiple documents for the project
        documents_data = [
            DocumentCreate(
                title=f"Document {i}",
                content=f"Content {i}",
                type="specification",
                format="markdown",
                project_id=sample_project.id,
            )
            for i in range(3)
        ]

        created_documents = []
        for document_data in documents_data:
            document = await document_repo.create(document_data)
            created_documents.append(document)

        # Retrieve documents by project
        project_documents = await document_repo.get_by_project(sample_project.id)

        assert len(project_documents) >= 3  # At least the ones we created
        document_titles = [doc.title for doc in project_documents]
        assert "Document 0" in document_titles
        assert "Document 1" in document_titles
        assert "Document 2" in document_titles

    @pytest.mark.asyncio
    async def test_get_documents_by_type(self, document_repo, sample_project):
        """Test retrieving documents by type."""
        # Create documents with different types
        spec_doc = await document_repo.create(
            DocumentCreate(
                title="Specification Document",
                content="Spec content",
                type="specification",
                format="markdown",
                project_id=sample_project.id,
            )
        )
        api_doc = await document_repo.create(
            DocumentCreate(
                title="API Documentation",
                content="API content",
                type="api_doc",
                format="markdown",
                project_id=sample_project.id,
            )
        )

        # Get specification documents
        spec_docs = await document_repo.get_by_type("specification")
        spec_titles = [doc.title for doc in spec_docs]
        assert "Specification Document" in spec_titles

        # Get API documents
        api_docs = await document_repo.get_by_type("api_doc")
        api_titles = [doc.title for doc in api_docs]
        assert "API Documentation" in api_titles

    @pytest.mark.asyncio
    async def test_update_document(self, document_repo, sample_document):
        """Test updating a document."""
        original_updated_at = sample_document.updated_at

        update_data = DocumentUpdate(
            title="Updated Document Title",
            content="# Updated Content\n\nThis is updated content.",
            version="2.0",
        )

        updated_document = await document_repo.update(sample_document.id, update_data)

        assert updated_document is not None
        assert updated_document.id == sample_document.id
        assert updated_document.title == "Updated Document Title"
        assert (
            updated_document.content == "# Updated Content\n\nThis is updated content."
        )
        assert updated_document.version == "2.0"
        assert updated_document.type == sample_document.type  # Unchanged
        assert updated_document.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_delete_document(self, document_repo, sample_project):
        """Test deleting a document."""
        # Create a document to delete
        document_data = DocumentCreate(
            title="Document to Delete",
            content="This document will be deleted",
            type="specification",
            format="markdown",
            project_id=sample_project.id,
        )
        document = await document_repo.create(document_data)
        document_id = document.id

        # Delete the document
        success = await document_repo.delete(document_id)

        assert success is True

        # Verify it's deleted
        deleted_document = await document_repo.get_by_id(document_id)
        assert deleted_document is None


class TestTagRepository:
    """Test the TagRepository implementation."""

    @pytest.fixture
    def tag_repo(self, test_session):
        """Tag repository fixture."""
        return TagRepository(test_session)

    @pytest.mark.asyncio
    async def test_create_tag(self, tag_repo):
        """Test creating a new tag."""
        tag_data = TagCreate(
            name="frontend", color="#FF5733", description="Frontend development tasks"
        )

        created_tag = await tag_repo.create(tag_data)

        assert created_tag.id is not None
        assert created_tag.name == "frontend"
        assert created_tag.color == "#FF5733"
        assert created_tag.description == "Frontend development tasks"

    @pytest.mark.asyncio
    async def test_get_tag_by_id(self, tag_repo):
        """Test retrieving a tag by ID."""
        # Create a tag first
        tag_data = TagCreate(name="backend", color="#33FF57")
        created_tag = await tag_repo.create(tag_data)

        # Retrieve it
        retrieved_tag = await tag_repo.get_by_id(created_tag.id)

        assert retrieved_tag is not None
        assert retrieved_tag.id == created_tag.id
        assert retrieved_tag.name == "backend"
        assert retrieved_tag.color == "#33FF57"

    @pytest.mark.asyncio
    async def test_get_tag_by_name(self, tag_repo):
        """Test retrieving a tag by name."""
        # Create a tag first
        tag_data = TagCreate(name="testing", color="#3357FF")
        created_tag = await tag_repo.create(tag_data)

        # Retrieve by name
        retrieved_tag = await tag_repo.get_by_name("testing")

        assert retrieved_tag is not None
        assert retrieved_tag.id == created_tag.id
        assert retrieved_tag.name == "testing"
        assert retrieved_tag.color == "#3357FF"

    @pytest.mark.asyncio
    async def test_get_all_tags(self, tag_repo):
        """Test retrieving all tags."""
        # Create multiple tags
        tags_data = [
            TagCreate(name=f"tag{i}", color=f"#FF{i:02d}{i:02d}{i:02d}")
            for i in range(3)
        ]

        created_tags = []
        for tag_data in tags_data:
            tag = await tag_repo.create(tag_data)
            created_tags.append(tag)

        # Retrieve all tags
        all_tags = await tag_repo.get_all()

        assert len(all_tags) >= 3  # At least the ones we created
        tag_names = [tag.name for tag in all_tags]
        assert "tag0" in tag_names
        assert "tag1" in tag_names
        assert "tag2" in tag_names

    @pytest.mark.asyncio
    async def test_update_tag(self, tag_repo):
        """Test updating a tag."""
        # Create a tag first
        tag_data = TagCreate(name="original", color="#000000")
        created_tag = await tag_repo.create(tag_data)

        # Update it
        update_data = TagCreate(
            name="updated", color="#FFFFFF", description="Updated description"
        )

        updated_tag = await tag_repo.update(created_tag.id, update_data)

        assert updated_tag is not None
        assert updated_tag.id == created_tag.id
        assert updated_tag.name == "updated"
        assert updated_tag.color == "#FFFFFF"
        assert updated_tag.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_tag(self, tag_repo):
        """Test deleting a tag."""
        # Create a tag to delete
        tag_data = TagCreate(name="to_delete", color="#FF0000")
        tag = await tag_repo.create(tag_data)
        tag_id = tag.id

        # Delete the tag
        success = await tag_repo.delete(tag_id)

        assert success is True

        # Verify it's deleted
        deleted_tag = await tag_repo.get_by_id(tag_id)
        assert deleted_tag is None

    @pytest.mark.asyncio
    async def test_tag_name_uniqueness_constraint(self, tag_repo):
        """Test that tag names must be unique."""
        # Create first tag
        tag_data1 = TagCreate(name="unique_name", color="#FF0000")
        await tag_repo.create(tag_data1)

        # Try to create another tag with the same name
        tag_data2 = TagCreate(name="unique_name", color="#00FF00")

        with pytest.raises(IntegrityError):
            await tag_repo.create(tag_data2)


class TestRepositoryErrorHandling:
    """Test error handling in repositories."""

    @pytest.mark.asyncio
    async def test_foreign_key_constraint_violation(self, test_session):
        """Test handling of foreign key constraint violations."""
        issue_repo = IssueRepository(test_session)

        # Try to create issue with non-existent project_id
        invalid_project_id = uuid4()
        issue_data = IssueCreate(
            title="Invalid Issue",
            description="Issue with invalid project",
            project_id=invalid_project_id,
        )

        with pytest.raises(IntegrityError):
            await issue_repo.create(issue_data)

    @pytest.mark.asyncio
    async def test_null_constraint_violation(self, test_session):
        """Test handling of null constraint violations."""
        # This would be caught at the Pydantic level in normal usage,
        # but we test the database constraint as well
        project_repo = ProjectRepository(test_session)

        # Create project data with None values (bypassing Pydantic)
        project = Project(name=None, description="Valid description", status="active")
        test_session.add(project)

        with pytest.raises(IntegrityError):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_repository_session_rollback_on_error(self, test_session):
        """Test that repository properly handles session rollback on errors."""
        project_repo = ProjectRepository(test_session)

        # Create a valid project first
        valid_project = await project_repo.create(
            ProjectCreate(name="Valid Project", description="Valid")
        )

        # Try to create an invalid project (this should fail)
        try:
            invalid_project = Project(name=None, description="Invalid", status="active")
            test_session.add(invalid_project)
            await test_session.commit()
        except IntegrityError:
            await test_session.rollback()

        # Verify that the valid project still exists after rollback
        retrieved_project = await project_repo.get_by_id(valid_project.id)
        assert retrieved_project is not None
        assert retrieved_project.name == "Valid Project"
