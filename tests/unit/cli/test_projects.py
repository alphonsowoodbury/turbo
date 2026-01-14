"""Tests for project CLI commands."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from click.testing import CliRunner

from turbo.cli.commands.projects import projects_group
from turbo.core.schemas import ProjectResponse


class TestProjectCLI:
    """Test project CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_project_id = str(uuid4())
        self.sample_project = ProjectResponse(
            id=self.sample_project_id,
            name="Sample Project",
            description="A sample project",
            priority="medium",
            status="active",
            completion_percentage=0.0,
            is_archived=False,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        )

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_create_project_success(self, mock_get_service):
        """Test successful project creation."""
        mock_service = AsyncMock()
        mock_service.create_project.return_value = self.sample_project
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            projects_group,
            [
                "create",
                "--name",
                "Test Project",
                "--description",
                "A test project",
                "--priority",
                "high",
            ],
        )

        assert result.exit_code == 0
        assert "Project created successfully" in result.output
        assert self.sample_project.name in result.output
        mock_service.create_project.assert_called_once()

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_create_project_missing_name(self, mock_get_service):
        """Test project creation with missing name."""
        result = self.runner.invoke(
            projects_group, ["create", "--description", "A test project"]
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_create_project_invalid_priority(self, mock_get_service):
        """Test project creation with invalid priority."""
        result = self.runner.invoke(
            projects_group,
            [
                "create",
                "--name",
                "Test Project",
                "--description",
                "A test project",
                "--priority",
                "invalid",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_list_projects_success(self, mock_get_service):
        """Test listing projects."""
        mock_service = AsyncMock()
        mock_service.get_all_projects.return_value = [self.sample_project]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["list"])

        assert result.exit_code == 0
        assert self.sample_project.name in result.output
        assert self.sample_project.status in result.output
        mock_service.get_all_projects.assert_called_once()

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_list_projects_empty(self, mock_get_service):
        """Test listing projects when none exist."""
        mock_service = AsyncMock()
        mock_service.get_all_projects.return_value = []
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["list"])

        assert result.exit_code == 0
        assert "No projects found" in result.output

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_list_projects_with_status_filter(self, mock_get_service):
        """Test listing projects with status filter."""
        mock_service = AsyncMock()
        mock_service.get_projects_by_status.return_value = [self.sample_project]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["list", "--status", "active"])

        assert result.exit_code == 0
        mock_service.get_projects_by_status.assert_called_once_with("active")

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_get_project_success(self, mock_get_service):
        """Test getting project by ID."""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = self.sample_project
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["get", self.sample_project_id])

        assert result.exit_code == 0
        assert self.sample_project.name in result.output
        assert self.sample_project.description in result.output
        mock_service.get_project_by_id.assert_called_once()

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_get_project_not_found(self, mock_get_service):
        """Test getting non-existent project."""
        from turbo.utils.exceptions import ProjectNotFoundError

        mock_service = AsyncMock()
        mock_service.get_project_by_id.side_effect = ProjectNotFoundError(
            self.sample_project_id
        )
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["get", self.sample_project_id])

        assert result.exit_code != 0
        assert "not found" in result.output

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_update_project_success(self, mock_get_service):
        """Test updating project."""
        updated_project = self.sample_project.model_copy()
        updated_project.name = "Updated Project"

        mock_service = AsyncMock()
        mock_service.update_project.return_value = updated_project
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            projects_group,
            ["update", self.sample_project_id, "--name", "Updated Project"],
        )

        assert result.exit_code == 0
        assert "Project updated successfully" in result.output
        assert "Updated Project" in result.output
        mock_service.update_project.assert_called_once()

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_delete_project_success(self, mock_get_service):
        """Test deleting project."""
        mock_service = AsyncMock()
        mock_service.delete_project.return_value = True
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            projects_group, ["delete", self.sample_project_id, "--confirm"]
        )

        assert result.exit_code == 0
        assert "Project deleted successfully" in result.output
        mock_service.delete_project.assert_called_once()

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_delete_project_without_confirmation(self, mock_get_service):
        """Test deleting project without confirmation."""
        result = self.runner.invoke(projects_group, ["delete", self.sample_project_id])

        # Should prompt for confirmation
        assert result.exit_code != 0 or "Aborted" in result.output

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_archive_project_success(self, mock_get_service):
        """Test archiving project."""
        archived_project = self.sample_project.model_copy()
        archived_project.is_archived = True

        mock_service = AsyncMock()
        mock_service.archive_project.return_value = archived_project
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["archive", self.sample_project_id])

        assert result.exit_code == 0
        assert "Project archived successfully" in result.output
        mock_service.archive_project.assert_called_once()

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_search_projects_success(self, mock_get_service):
        """Test searching projects."""
        mock_service = AsyncMock()
        mock_service.search_projects_by_name.return_value = [self.sample_project]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["search", "Sample"])

        assert result.exit_code == 0
        assert self.sample_project.name in result.output
        mock_service.search_projects_by_name.assert_called_once_with("Sample")

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_project_stats_success(self, mock_get_service):
        """Test getting project statistics."""
        mock_stats = {
            "total_issues": 5,
            "open_issues": 3,
            "closed_issues": 2,
            "completion_rate": 40.0,
        }

        mock_service = AsyncMock()
        mock_service.get_project_statistics.return_value = mock_stats
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["stats", self.sample_project_id])

        assert result.exit_code == 0
        assert "Statistics for project" in result.output
        assert "5" in result.output  # total_issues
        assert "3" in result.output  # open_issues
        mock_service.get_project_statistics.assert_called_once()


class TestProjectCLIOutput:
    """Test project CLI output formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_list_projects_table_format(self, mock_get_service):
        """Test projects are displayed in table format."""
        projects = [
            ProjectResponse(
                id=str(uuid4()),
                name="Project 1",
                description="Description 1",
                priority="high",
                status="active",
                completion_percentage=25.0,
                is_archived=False,
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
            ),
            ProjectResponse(
                id=str(uuid4()),
                name="Project 2",
                description="Description 2",
                priority="low",
                status="completed",
                completion_percentage=100.0,
                is_archived=False,
                created_at="2023-01-02T00:00:00Z",
                updated_at="2023-01-02T00:00:00Z",
            ),
        ]

        mock_service = AsyncMock()
        mock_service.get_all_projects.return_value = projects
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["list"])

        assert result.exit_code == 0
        # Should contain table headers
        assert "Name" in result.output
        assert "Status" in result.output
        assert "Priority" in result.output
        # Should contain project data
        assert "Project 1" in result.output
        assert "Project 2" in result.output

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_list_projects_json_format(self, mock_get_service):
        """Test projects can be displayed in JSON format."""
        mock_service = AsyncMock()
        mock_service.get_all_projects.return_value = [self.sample_project]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(projects_group, ["list", "--format", "json"])

        assert result.exit_code == 0
        assert "{" in result.output  # JSON format
        assert '"name"' in result.output

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_get_project_detailed_view(self, mock_get_service):
        """Test detailed project view."""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = self.sample_project
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            projects_group, ["get", str(self.sample_project.id), "--detailed"]
        )

        assert result.exit_code == 0
        assert "ID:" in result.output
        assert "Created:" in result.output
        assert "Updated:" in result.output


class TestProjectCLIValidation:
    """Test project CLI input validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_uuid_format(self):
        """Test handling of invalid UUID format."""
        result = self.runner.invoke(projects_group, ["get", "invalid-uuid"])

        assert result.exit_code != 0
        assert "Invalid UUID" in result.output or "not a valid UUID" in result.output

    def test_priority_validation(self):
        """Test priority validation."""
        result = self.runner.invoke(
            projects_group,
            [
                "create",
                "--name",
                "Test",
                "--description",
                "Test",
                "--priority",
                "invalid-priority",
            ],
        )

        assert result.exit_code != 0

    def test_status_validation(self):
        """Test status validation."""
        result = self.runner.invoke(
            projects_group, ["update", str(uuid4()), "--status", "invalid-status"]
        )

        assert result.exit_code != 0

    def test_completion_percentage_validation(self):
        """Test completion percentage validation."""
        result = self.runner.invoke(
            projects_group,
            ["update", str(uuid4()), "--completion", "150"],  # Invalid percentage > 100
        )

        assert result.exit_code != 0
