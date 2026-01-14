"""Tests for tag CLI commands."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from click.testing import CliRunner

from turbo.cli.commands.tags import tags_group
from turbo.core.schemas import IssueResponse, ProjectResponse, TagResponse


class TestTagCLI:
    """Test tag CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_tag_id = str(uuid4())

        self.sample_tag = TagResponse(
            id=self.sample_tag_id,
            name="sample-tag",
            color="#FF5733",
            description="A sample tag for testing",
        )

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_create_tag_success(self, mock_get_service):
        """Test successful tag creation."""
        mock_service = AsyncMock()
        mock_service.create_tag.return_value = self.sample_tag
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            tags_group,
            [
                "create",
                "--name",
                "test-tag",
                "--color",
                "#FF5733",
                "--description",
                "A test tag",
            ],
        )

        assert result.exit_code == 0
        assert "Tag created successfully" in result.output
        assert self.sample_tag.name in result.output
        mock_service.create_tag.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_create_tag_with_color_picker(self, mock_get_service):
        """Test tag creation with interactive color picker."""
        mock_service = AsyncMock()
        mock_service.create_tag.return_value = self.sample_tag
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            tags_group,
            ["create", "--name", "test-tag", "--interactive-color"],
            input="1\n",
        )  # Select first color from palette

        assert result.exit_code == 0
        mock_service.create_tag.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_create_tag_duplicate_name(self, mock_get_service):
        """Test tag creation with duplicate name."""
        from turbo.utils.exceptions import DuplicateResourceError

        mock_service = AsyncMock()
        mock_service.create_tag.side_effect = DuplicateResourceError(
            "Tag", "name 'existing-tag'"
        )
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            tags_group, ["create", "--name", "existing-tag", "--color", "#FF5733"]
        )

        assert result.exit_code != 0
        assert "already exists" in result.output or "duplicate" in result.output.lower()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_list_tags_success(self, mock_get_service):
        """Test listing tags."""
        mock_service = AsyncMock()
        mock_service.get_all_tags.return_value = [self.sample_tag]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["list"])

        assert result.exit_code == 0
        assert self.sample_tag.name in result.output
        assert self.sample_tag.color in result.output
        mock_service.get_all_tags.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_list_tags_by_color(self, mock_get_service):
        """Test listing tags by color."""
        mock_service = AsyncMock()
        mock_service.get_tags_by_color.return_value = [self.sample_tag]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["list", "--color", "#FF5733"])

        assert result.exit_code == 0
        mock_service.get_tags_by_color.assert_called_once_with("#FF5733")

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_list_tags_popular(self, mock_get_service):
        """Test listing popular tags."""
        mock_service = AsyncMock()
        mock_service.get_popular_tags.return_value = [self.sample_tag]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["list", "--popular", "--limit", "10"])

        assert result.exit_code == 0
        mock_service.get_popular_tags.assert_called_once_with(limit=10)

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_list_tags_unused(self, mock_get_service):
        """Test listing unused tags."""
        mock_service = AsyncMock()
        mock_service.get_unused_tags.return_value = [self.sample_tag]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["list", "--unused"])

        assert result.exit_code == 0
        mock_service.get_unused_tags.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_get_tag_success(self, mock_get_service):
        """Test getting tag by ID."""
        mock_service = AsyncMock()
        mock_service.get_tag_by_id.return_value = self.sample_tag
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["get", self.sample_tag_id])

        assert result.exit_code == 0
        assert self.sample_tag.name in result.output
        assert self.sample_tag.description in result.output
        mock_service.get_tag_by_id.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_update_tag_success(self, mock_get_service):
        """Test updating tag."""
        updated_tag = self.sample_tag.model_copy()
        updated_tag.name = "updated-tag"
        updated_tag.color = "#33FF57"

        mock_service = AsyncMock()
        mock_service.update_tag.return_value = updated_tag
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            tags_group,
            [
                "update",
                self.sample_tag_id,
                "--name",
                "updated-tag",
                "--color",
                "#33FF57",
            ],
        )

        assert result.exit_code == 0
        assert "Tag updated successfully" in result.output
        assert "updated-tag" in result.output
        mock_service.update_tag.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_delete_tag_success(self, mock_get_service):
        """Test deleting tag."""
        mock_service = AsyncMock()
        mock_service.delete_tag.return_value = True
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            tags_group, ["delete", self.sample_tag_id, "--confirm"]
        )

        assert result.exit_code == 0
        assert "Tag deleted successfully" in result.output
        mock_service.delete_tag.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_search_tags_success(self, mock_get_service):
        """Test searching tags."""
        mock_service = AsyncMock()
        mock_service.search_tags.return_value = [self.sample_tag]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["search", "sample"])

        assert result.exit_code == 0
        assert self.sample_tag.name in result.output
        mock_service.search_tags.assert_called_once_with("sample")


class TestTagCLIUsage:
    """Test tag CLI usage and statistics commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_tag_id = str(uuid4())

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_tag_usage_stats(self, mock_get_service):
        """Test getting tag usage statistics."""
        mock_stats = {"project_count": 5, "issue_count": 12, "total_usage": 17}

        mock_service = AsyncMock()
        mock_service.get_tag_usage_statistics.return_value = mock_stats
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["stats", self.sample_tag_id])

        assert result.exit_code == 0
        assert "Usage statistics" in result.output
        assert "5" in result.output  # project_count
        assert "12" in result.output  # issue_count
        mock_service.get_tag_usage_statistics.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_list_projects_with_tag(self, mock_get_service):
        """Test listing projects with specific tag."""
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

        mock_service = AsyncMock()
        mock_service.get_projects_with_tag.return_value = mock_projects
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["projects", self.sample_tag_id])

        assert result.exit_code == 0
        assert "Project 1" in result.output
        mock_service.get_projects_with_tag.assert_called_once()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_list_issues_with_tag(self, mock_get_service):
        """Test listing issues with specific tag."""
        mock_issues = [
            IssueResponse(
                id=str(uuid4()),
                title="Issue 1",
                description="Description 1",
                type="bug",
                status="open",
                priority="high",
                project_id=str(uuid4()),
                assignee=None,
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
            )
        ]

        mock_service = AsyncMock()
        mock_service.get_issues_with_tag.return_value = mock_issues
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["issues", self.sample_tag_id])

        assert result.exit_code == 0
        assert "Issue 1" in result.output
        mock_service.get_issues_with_tag.assert_called_once()


class TestTagCLIColorHelpers:
    """Test tag CLI color helper commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_color_palette_display(self):
        """Test displaying color palette."""
        result = self.runner.invoke(tags_group, ["colors"])

        assert result.exit_code == 0
        assert "Available colors:" in result.output or "Color palette:" in result.output

    def test_color_preview(self):
        """Test color preview functionality."""
        result = self.runner.invoke(tags_group, ["preview-color", "#FF5733"])

        assert result.exit_code == 0
        assert "#FF5733" in result.output

    def test_random_color_generator(self):
        """Test random color generation."""
        result = self.runner.invoke(tags_group, ["random-color"])

        assert result.exit_code == 0
        assert "#" in result.output  # Should output a hex color


class TestTagCLIValidation:
    """Test tag CLI input validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_color_format(self):
        """Test validation of color format."""
        result = self.runner.invoke(
            tags_group,
            ["create", "--name", "test-tag", "--color", "red"],  # Should be hex format
        )

        assert result.exit_code != 0
        assert "Invalid color format" in result.output or "hex format" in result.output

    def test_color_case_handling(self):
        """Test color case handling."""
        result = self.runner.invoke(
            tags_group,
            [
                "create",
                "--name",
                "test-tag",
                "--color",
                "#ff5733",  # lowercase should be accepted
            ],
        )

        # Should either work or provide helpful message
        assert result.exit_code == 0 or "case" in result.output

    def test_name_length_validation(self):
        """Test tag name length validation."""
        long_name = "a" * 51  # Assuming max length is 50
        result = self.runner.invoke(
            tags_group, ["create", "--name", long_name, "--color", "#FF5733"]
        )

        assert result.exit_code != 0

    def test_description_length_validation(self):
        """Test tag description length validation."""
        long_description = "a" * 201  # Assuming max length is 200
        result = self.runner.invoke(
            tags_group,
            [
                "create",
                "--name",
                "test-tag",
                "--color",
                "#FF5733",
                "--description",
                long_description,
            ],
        )

        assert result.exit_code != 0

    def test_whitespace_name_validation(self):
        """Test that tag names with only whitespace are rejected."""
        result = self.runner.invoke(
            tags_group,
            ["create", "--name", "   ", "--color", "#FF5733"],  # Only whitespace
        )

        assert result.exit_code != 0

    def test_invalid_uuid_format(self):
        """Test handling of invalid UUID format."""
        result = self.runner.invoke(tags_group, ["get", "invalid-uuid"])

        assert result.exit_code != 0
        assert "Invalid UUID" in result.output or "not a valid UUID" in result.output


class TestTagCLIOutput:
    """Test tag CLI output formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_list_tags_table_format(self, mock_get_service):
        """Test tags are displayed in table format."""
        tags = [
            TagResponse(
                id=str(uuid4()),
                name="frontend",
                color="#FF5733",
                description="Frontend development",
            ),
            TagResponse(
                id=str(uuid4()),
                name="backend",
                color="#33FF57",
                description="Backend development",
            ),
        ]

        mock_service = AsyncMock()
        mock_service.get_all_tags.return_value = tags
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["list"])

        assert result.exit_code == 0
        # Should contain table headers
        assert "Name" in result.output
        assert "Color" in result.output
        # Should contain tag data
        assert "frontend" in result.output
        assert "backend" in result.output

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_list_tags_with_color_display(self, mock_get_service):
        """Test tags are displayed with colored output."""
        mock_service = AsyncMock()
        mock_service.get_all_tags.return_value = [self.sample_tag]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(tags_group, ["list", "--show-colors"])

        assert result.exit_code == 0
        # Should include ANSI color codes or color representation
        assert self.sample_tag.name in result.output

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_get_tag_detailed_view(self, mock_get_service):
        """Test detailed tag view."""
        mock_service = AsyncMock()
        mock_service.get_tag_by_id.return_value = self.sample_tag
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            tags_group, ["get", str(self.sample_tag.id), "--detailed"]
        )

        assert result.exit_code == 0
        assert "ID:" in result.output
        assert "Name:" in result.output
        assert "Color:" in result.output
        assert "Description:" in result.output


class TestTagCLIBulkOperations:
    """Test tag CLI bulk operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_bulk_create_tags(self, mock_get_service):
        """Test bulk creating tags from file."""
        mock_service = AsyncMock()
        mock_service.create_tag.return_value = self.sample_tag
        mock_get_service.return_value = mock_service

        # Mock file content
        import os
        import tempfile

        tags_data = """frontend,#FF5733,Frontend development
backend,#33FF57,Backend development
database,#3357FF,Database operations"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write(tags_data)
            temp_file = f.name

        try:
            result = self.runner.invoke(
                tags_group, ["bulk-create", "--from-file", temp_file]
            )

            assert result.exit_code == 0
            assert "tags created" in result.output
        finally:
            os.unlink(temp_file)

    @patch("turbo.cli.commands.tags.get_tag_service")
    def test_bulk_delete_tags(self, mock_get_service):
        """Test bulk deleting tags."""
        mock_service = AsyncMock()
        mock_service.delete_tag.return_value = True
        mock_get_service.return_value = mock_service

        tag_ids = [str(uuid4()), str(uuid4()), str(uuid4())]

        result = self.runner.invoke(
            tags_group, ["bulk-delete", "--ids", ",".join(tag_ids), "--confirm"]
        )

        assert result.exit_code == 0
        assert "tags deleted" in result.output
