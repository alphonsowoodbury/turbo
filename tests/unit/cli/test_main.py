"""Tests for main CLI application and global commands."""

import os
import tempfile
from unittest.mock import patch

from click.testing import CliRunner

from turbo.cli.main import cli


class TestMainCLI:
    """Test main CLI application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help message."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Turbo" in result.output
        assert "projects" in result.output
        assert "issues" in result.output
        assert "documents" in result.output
        assert "tags" in result.output

    def test_cli_version(self):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "1.0.0" in result.output or "version" in result.output.lower()

    def test_subcommand_help(self):
        """Test subcommand help messages."""
        subcommands = ["projects", "issues", "documents", "tags"]

        for subcommand in subcommands:
            result = self.runner.invoke(cli, [subcommand, "--help"])
            assert result.exit_code == 0
            assert subcommand in result.output.lower()


class TestInitCommand:
    """Test initialization command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.init.init_database")
    def test_init_success(self, mock_init_db):
        """Test successful initialization."""
        mock_init_db.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(cli, ["init", "--workspace", temp_dir])

            assert result.exit_code == 0
            assert "initialized successfully" in result.output
            mock_init_db.assert_called_once()

            # Check if workspace directories were created
            assert os.path.exists(os.path.join(temp_dir, ".turbo"))
            assert os.path.exists(os.path.join(temp_dir, ".turbo", "context"))
            assert os.path.exists(os.path.join(temp_dir, ".turbo", "templates"))
            assert os.path.exists(os.path.join(temp_dir, ".turbo", "responses"))

    def test_init_existing_workspace(self):
        """Test initialization in existing workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .turbo directory first
            turbo_dir = os.path.join(temp_dir, ".turbo")
            os.makedirs(turbo_dir)

            result = self.runner.invoke(cli, ["init", "--workspace", temp_dir])

            assert result.exit_code == 0
            assert "already initialized" in result.output or "existing" in result.output

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config_data = """
        [database]
        url = "sqlite:///custom.db"

        [api]
        port = 8080
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "config.toml")
            with open(config_file, "w") as f:
                f.write(config_data)

            result = self.runner.invoke(
                cli, ["init", "--workspace", temp_dir, "--config", config_file]
            )

            assert result.exit_code == 0
            assert "initialized" in result.output


class TestConfigCommand:
    """Test configuration command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.config.get_settings")
    def test_config_show(self, mock_get_settings):
        """Test showing configuration."""
        mock_settings = {
            "environment": "development",
            "debug": True,
            "database": {"url": "sqlite:///turbo.db"},
        }
        mock_get_settings.return_value = mock_settings

        result = self.runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0
        assert "environment" in result.output
        assert "development" in result.output

    def test_config_set(self):
        """Test setting configuration value."""
        result = self.runner.invoke(
            cli, ["config", "set", "database.url", "sqlite:///custom.db"]
        )

        assert result.exit_code == 0
        assert "Configuration updated" in result.output or "set" in result.output

    def test_config_get(self):
        """Test getting configuration value."""
        result = self.runner.invoke(cli, ["config", "get", "database.url"])

        assert result.exit_code == 0

    def test_config_validate(self):
        """Test configuration validation."""
        result = self.runner.invoke(cli, ["config", "validate"])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()


class TestStatusCommand:
    """Test status command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.status.get_project_service")
    @patch("turbo.cli.commands.status.get_issue_service")
    def test_status_overview(self, mock_issue_service, mock_project_service):
        """Test status overview."""
        # Mock statistics
        mock_project_service.return_value.get_project_count.return_value = 5
        mock_issue_service.return_value.get_issue_count.return_value = 25

        result = self.runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "Projects:" in result.output
        assert "Issues:" in result.output

    @patch("turbo.cli.commands.status.check_database_connection")
    def test_status_health(self, mock_check_db):
        """Test health status."""
        mock_check_db.return_value = True

        result = self.runner.invoke(cli, ["status", "--health"])

        assert result.exit_code == 0
        assert "Database:" in result.output

    @patch("turbo.cli.commands.status.get_recent_activity")
    def test_status_recent(self, mock_get_activity):
        """Test recent activity."""
        mock_activity = [
            {
                "type": "project_created",
                "name": "New Project",
                "timestamp": "2023-01-01T00:00:00Z",
            }
        ]
        mock_get_activity.return_value = mock_activity

        result = self.runner.invoke(cli, ["status", "--recent"])

        assert result.exit_code == 0
        assert "Recent activity:" in result.output


class TestExportCommand:
    """Test export command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.export.get_project_service")
    @patch("turbo.cli.commands.export.get_issue_service")
    @patch("turbo.cli.commands.export.get_document_service")
    def test_export_all_data(
        self, mock_doc_service, mock_issue_service, mock_project_service
    ):
        """Test exporting all data."""
        # Mock data
        mock_project_service.return_value.get_all_projects.return_value = []
        mock_issue_service.return_value.get_all_issues.return_value = []
        mock_doc_service.return_value.get_all_documents.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "export.json")

            result = self.runner.invoke(
                cli, ["export", "--output", output_file, "--format", "json"]
            )

            assert result.exit_code == 0
            assert "exported successfully" in result.output
            assert os.path.exists(output_file)

    @patch("turbo.cli.commands.export.get_project_service")
    def test_export_projects_only(self, mock_project_service):
        """Test exporting projects only."""
        mock_project_service.return_value.get_all_projects.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "projects.csv")

            result = self.runner.invoke(
                cli,
                [
                    "export",
                    "--output",
                    output_file,
                    "--format",
                    "csv",
                    "--type",
                    "projects",
                ],
            )

            assert result.exit_code == 0
            assert "exported successfully" in result.output

    def test_export_invalid_format(self):
        """Test export with invalid format."""
        result = self.runner.invoke(
            cli, ["export", "--output", "export.txt", "--format", "invalid"]
        )

        assert result.exit_code != 0
        assert "Invalid format" in result.output or "format" in result.output


class TestImportCommand:
    """Test import command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.import.get_project_service")
    def test_import_projects(self, mock_project_service):
        """Test importing projects."""
        import_data = """[
            {
                "name": "Imported Project",
                "description": "An imported project",
                "priority": "medium",
                "status": "active"
            }
        ]"""

        mock_project_service.return_value.create_project.return_value = None

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write(import_data)
            temp_file = f.name

        try:
            result = self.runner.invoke(
                cli, ["import", "--file", temp_file, "--type", "projects"]
            )

            assert result.exit_code == 0
            assert "imported successfully" in result.output
        finally:
            os.unlink(temp_file)

    def test_import_file_not_found(self):
        """Test import with non-existent file."""
        result = self.runner.invoke(
            cli, ["import", "--file", "non-existent.json", "--type", "projects"]
        )

        assert result.exit_code != 0
        assert "File not found" in result.output or "No such file" in result.output

    def test_import_invalid_format(self):
        """Test import with invalid file format."""
        invalid_data = "invalid json content"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write(invalid_data)
            temp_file = f.name

        try:
            result = self.runner.invoke(
                cli, ["import", "--file", temp_file, "--type", "projects"]
            )

            assert result.exit_code != 0
            assert "Invalid" in result.output or "error" in result.output.lower()
        finally:
            os.unlink(temp_file)


class TestSearchCommand:
    """Test global search command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.search.get_project_service")
    @patch("turbo.cli.commands.search.get_issue_service")
    @patch("turbo.cli.commands.search.get_document_service")
    def test_search_all(
        self, mock_doc_service, mock_issue_service, mock_project_service
    ):
        """Test searching across all entities."""
        # Mock search results
        mock_project_service.return_value.search_projects_by_name.return_value = []
        mock_issue_service.return_value.search_issues_by_title.return_value = []
        mock_doc_service.return_value.search_documents.return_value = []

        result = self.runner.invoke(cli, ["search", "test query"])

        assert result.exit_code == 0
        assert "Search results" in result.output

    @patch("turbo.cli.commands.search.get_project_service")
    def test_search_projects_only(self, mock_project_service):
        """Test searching projects only."""
        mock_project_service.return_value.search_projects_by_name.return_value = []

        result = self.runner.invoke(cli, ["search", "test query", "--type", "projects"])

        assert result.exit_code == 0
        mock_project_service.return_value.search_projects_by_name.assert_called_once()


class TestCompletionCommand:
    """Test shell completion command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_completion_bash(self):
        """Test bash completion generation."""
        result = self.runner.invoke(cli, ["completion", "bash"])

        assert result.exit_code == 0
        assert "complete" in result.output or "completion" in result.output

    def test_completion_zsh(self):
        """Test zsh completion generation."""
        result = self.runner.invoke(cli, ["completion", "zsh"])

        assert result.exit_code == 0

    def test_completion_install(self):
        """Test completion installation."""
        result = self.runner.invoke(cli, ["completion", "install", "--shell", "bash"])

        # Should either succeed or provide helpful message
        assert result.exit_code == 0 or "install" in result.output


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_command(self):
        """Test handling of invalid command."""
        result = self.runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        assert "No such command" in result.output or "invalid" in result.output.lower()

    def test_database_connection_error(self):
        """Test handling of database connection error."""
        with patch("turbo.cli.main.init_database") as mock_init:
            mock_init.side_effect = Exception("Database connection failed")

            result = self.runner.invoke(cli, ["init"])

            assert result.exit_code != 0
            assert "error" in result.output.lower()

    def test_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        with patch("turbo.cli.commands.projects.get_project_service") as mock_service:
            mock_service.side_effect = KeyboardInterrupt()

            result = self.runner.invoke(cli, ["projects", "list"])

            assert result.exit_code != 0


class TestCLIVerbosity:
    """Test CLI verbosity options."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_verbose_output(self, mock_service):
        """Test verbose output."""
        mock_service.return_value.get_all_projects.return_value = []

        result = self.runner.invoke(cli, ["--verbose", "projects", "list"])

        assert result.exit_code == 0
        # Verbose mode should show more details

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_quiet_output(self, mock_service):
        """Test quiet output."""
        mock_service.return_value.get_all_projects.return_value = []

        result = self.runner.invoke(cli, ["--quiet", "projects", "list"])

        assert result.exit_code == 0
        # Quiet mode should show minimal output

    @patch("turbo.cli.commands.projects.get_project_service")
    def test_debug_output(self, mock_service):
        """Test debug output."""
        mock_service.return_value.get_all_projects.return_value = []

        result = self.runner.invoke(cli, ["--debug", "projects", "list"])

        assert result.exit_code == 0
        # Debug mode should show debug information
