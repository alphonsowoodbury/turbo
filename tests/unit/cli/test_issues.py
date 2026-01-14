"""Tests for issue CLI commands."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from click.testing import CliRunner

from turbo.cli.commands.issues import issues_group
from turbo.core.schemas import IssueResponse, ProjectResponse


class TestIssueCLI:
    """Test issue CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_project_id = str(uuid4())
        self.sample_issue_id = str(uuid4())

        self.sample_issue = IssueResponse(
            id=self.sample_issue_id,
            title="Sample Issue",
            description="A sample issue",
            type="feature",
            status="open",
            priority="medium",
            project_id=self.sample_project_id,
            assignee=None,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        )

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_create_issue_success(self, mock_get_service):
        """Test successful issue creation."""
        mock_service = AsyncMock()
        mock_service.create_issue.return_value = self.sample_issue
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            issues_group,
            [
                "create",
                "--title",
                "Test Issue",
                "--description",
                "A test issue",
                "--project-id",
                self.sample_project_id,
                "--type",
                "bug",
                "--priority",
                "high",
            ],
        )

        assert result.exit_code == 0
        assert "Issue created successfully" in result.output
        assert self.sample_issue.title in result.output
        mock_service.create_issue.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_create_issue_missing_required_fields(self, mock_get_service):
        """Test issue creation with missing required fields."""
        result = self.runner.invoke(
            issues_group,
            [
                "create",
                "--title",
                "Test Issue",
                # Missing description and project-id
            ],
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_list_issues_success(self, mock_get_service):
        """Test listing issues."""
        mock_service = AsyncMock()
        mock_service.get_all_issues.return_value = [self.sample_issue]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["list"])

        assert result.exit_code == 0
        assert self.sample_issue.title in result.output
        assert self.sample_issue.status in result.output
        mock_service.get_all_issues.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_list_issues_by_project(self, mock_get_service):
        """Test listing issues by project."""
        mock_service = AsyncMock()
        mock_service.get_issues_by_project.return_value = [self.sample_issue]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            issues_group, ["list", "--project-id", self.sample_project_id]
        )

        assert result.exit_code == 0
        mock_service.get_issues_by_project.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_list_issues_by_status(self, mock_get_service):
        """Test listing issues by status."""
        mock_service = AsyncMock()
        mock_service.get_issues_by_status.return_value = [self.sample_issue]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["list", "--status", "open"])

        assert result.exit_code == 0
        mock_service.get_issues_by_status.assert_called_once_with("open")

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_list_issues_by_assignee(self, mock_get_service):
        """Test listing issues by assignee."""
        mock_service = AsyncMock()
        mock_service.get_issues_by_assignee.return_value = [self.sample_issue]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            issues_group, ["list", "--assignee", "dev@example.com"]
        )

        assert result.exit_code == 0
        mock_service.get_issues_by_assignee.assert_called_once_with("dev@example.com")

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_get_issue_success(self, mock_get_service):
        """Test getting issue by ID."""
        mock_service = AsyncMock()
        mock_service.get_issue_by_id.return_value = self.sample_issue
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["get", self.sample_issue_id])

        assert result.exit_code == 0
        assert self.sample_issue.title in result.output
        assert self.sample_issue.description in result.output
        mock_service.get_issue_by_id.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_update_issue_success(self, mock_get_service):
        """Test updating issue."""
        updated_issue = self.sample_issue.model_copy()
        updated_issue.title = "Updated Issue"
        updated_issue.status = "in_progress"

        mock_service = AsyncMock()
        mock_service.update_issue.return_value = updated_issue
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            issues_group,
            [
                "update",
                self.sample_issue_id,
                "--title",
                "Updated Issue",
                "--status",
                "in_progress",
            ],
        )

        assert result.exit_code == 0
        assert "Issue updated successfully" in result.output
        assert "Updated Issue" in result.output
        mock_service.update_issue.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_assign_issue_success(self, mock_get_service):
        """Test assigning issue to someone."""
        assigned_issue = self.sample_issue.model_copy()
        assigned_issue.assignee = "dev@example.com"

        mock_service = AsyncMock()
        mock_service.assign_issue.return_value = assigned_issue
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            issues_group, ["assign", self.sample_issue_id, "dev@example.com"]
        )

        assert result.exit_code == 0
        assert "Issue assigned successfully" in result.output
        assert "dev@example.com" in result.output
        mock_service.assign_issue.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_close_issue_success(self, mock_get_service):
        """Test closing issue."""
        closed_issue = self.sample_issue.model_copy()
        closed_issue.status = "closed"

        mock_service = AsyncMock()
        mock_service.close_issue.return_value = closed_issue
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["close", self.sample_issue_id])

        assert result.exit_code == 0
        assert "Issue closed successfully" in result.output
        mock_service.close_issue.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_reopen_issue_success(self, mock_get_service):
        """Test reopening issue."""
        reopened_issue = self.sample_issue.model_copy()
        reopened_issue.status = "open"

        mock_service = AsyncMock()
        mock_service.reopen_issue.return_value = reopened_issue
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["reopen", self.sample_issue_id])

        assert result.exit_code == 0
        assert "Issue reopened successfully" in result.output
        mock_service.reopen_issue.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_delete_issue_success(self, mock_get_service):
        """Test deleting issue."""
        mock_service = AsyncMock()
        mock_service.delete_issue.return_value = True
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            issues_group, ["delete", self.sample_issue_id, "--confirm"]
        )

        assert result.exit_code == 0
        assert "Issue deleted successfully" in result.output
        mock_service.delete_issue.assert_called_once()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_search_issues_success(self, mock_get_service):
        """Test searching issues."""
        mock_service = AsyncMock()
        mock_service.search_issues_by_title.return_value = [self.sample_issue]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["search", "Sample"])

        assert result.exit_code == 0
        assert self.sample_issue.title in result.output
        mock_service.search_issues_by_title.assert_called_once_with("Sample")


class TestIssueCLIWorkflow:
    """Test issue CLI workflow commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_issue_id = str(uuid4())

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_issue_workflow_start_work(self, mock_get_service):
        """Test starting work on an issue."""
        mock_service = AsyncMock()
        mock_service.start_work_on_issue.return_value = True
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["start", self.sample_issue_id])

        assert result.exit_code == 0
        assert "Started work on issue" in result.output

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_issue_workflow_submit_for_review(self, mock_get_service):
        """Test submitting issue for review."""
        mock_service = AsyncMock()
        mock_service.submit_for_review.return_value = True
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["review", self.sample_issue_id])

        assert result.exit_code == 0
        assert "Issue submitted for review" in result.output


class TestIssueCLIInteractive:
    """Test interactive issue CLI features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.issues.get_issue_service")
    @patch("turbo.cli.commands.issues.get_project_service")
    def test_create_issue_interactive(self, mock_project_service, mock_issue_service):
        """Test interactive issue creation."""
        # Mock project selection
        mock_projects = [
            ProjectResponse(
                id=str(uuid4()),
                name="Project 1",
                description="Description 1",
                priority="medium",
                status="active",
                completion_percentage=0.0,
                is_archived=False,
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
            )
        ]
        mock_project_service.return_value.get_all_projects.return_value = mock_projects
        mock_issue_service.return_value.create_issue.return_value = self.sample_issue

        # Test with interactive mode
        result = self.runner.invoke(
            issues_group,
            ["create", "--interactive"],
            input="Test Issue\nTest Description\n1\n1\n1\n",
        )

        # Should prompt for inputs
        assert "Title:" in result.output or result.exit_code == 0

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_bulk_update_issues(self, mock_get_service):
        """Test bulk updating issues."""
        mock_service = AsyncMock()
        mock_service.bulk_update_issues.return_value = 3
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            issues_group,
            [
                "bulk-update",
                "--status",
                "closed",
                "--ids",
                f"{uuid4()},{uuid4()},{uuid4()}",
            ],
        )

        assert result.exit_code == 0
        assert "Updated 3 issues" in result.output


class TestIssueCLIValidation:
    """Test issue CLI input validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_issue_type(self):
        """Test validation of issue type."""
        result = self.runner.invoke(
            issues_group,
            [
                "create",
                "--title",
                "Test",
                "--description",
                "Test",
                "--project-id",
                str(uuid4()),
                "--type",
                "invalid-type",
            ],
        )

        assert result.exit_code != 0

    def test_invalid_priority(self):
        """Test validation of priority."""
        result = self.runner.invoke(
            issues_group,
            [
                "create",
                "--title",
                "Test",
                "--description",
                "Test",
                "--project-id",
                str(uuid4()),
                "--priority",
                "invalid-priority",
            ],
        )

        assert result.exit_code != 0

    def test_invalid_email_format(self):
        """Test validation of email format for assignee."""
        result = self.runner.invoke(
            issues_group, ["assign", str(uuid4()), "not-an-email"]
        )

        assert result.exit_code != 0 or "Invalid email" in result.output

    def test_invalid_uuid_format(self):
        """Test handling of invalid UUID format."""
        result = self.runner.invoke(issues_group, ["get", "invalid-uuid"])

        assert result.exit_code != 0
        assert "Invalid UUID" in result.output or "not a valid UUID" in result.output


class TestIssueCLIOutput:
    """Test issue CLI output formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_list_issues_table_format(self, mock_get_service):
        """Test issues are displayed in table format."""
        issues = [
            IssueResponse(
                id=str(uuid4()),
                title="Issue 1",
                description="Description 1",
                type="bug",
                status="open",
                priority="high",
                project_id=str(uuid4()),
                assignee="dev1@example.com",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
            ),
            IssueResponse(
                id=str(uuid4()),
                title="Issue 2",
                description="Description 2",
                type="feature",
                status="closed",
                priority="low",
                project_id=str(uuid4()),
                assignee=None,
                created_at="2023-01-02T00:00:00Z",
                updated_at="2023-01-02T00:00:00Z",
            ),
        ]

        mock_service = AsyncMock()
        mock_service.get_all_issues.return_value = issues
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(issues_group, ["list"])

        assert result.exit_code == 0
        # Should contain table headers
        assert "Title" in result.output
        assert "Status" in result.output
        assert "Type" in result.output
        # Should contain issue data
        assert "Issue 1" in result.output
        assert "Issue 2" in result.output

    @patch("turbo.cli.commands.issues.get_issue_service")
    def test_get_issue_detailed_view(self, mock_get_service):
        """Test detailed issue view."""
        mock_service = AsyncMock()
        mock_service.get_issue_by_id.return_value = self.sample_issue
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            issues_group, ["get", str(self.sample_issue.id), "--detailed"]
        )

        assert result.exit_code == 0
        assert "ID:" in result.output
        assert "Created:" in result.output
        assert "Updated:" in result.output
