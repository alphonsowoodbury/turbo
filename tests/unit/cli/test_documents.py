"""Tests for document CLI commands."""

import os
import tempfile
from unittest.mock import AsyncMock, mock_open, patch
from uuid import uuid4

from click.testing import CliRunner

from turbo.cli.commands.documents import documents_group
from turbo.core.schemas import DocumentResponse


class TestDocumentCLI:
    """Test document CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_project_id = str(uuid4())
        self.sample_document_id = str(uuid4())

        self.sample_document = DocumentResponse(
            id=self.sample_document_id,
            title="Sample Document",
            content="# Sample Document\n\nThis is sample content.",
            type="specification",
            format="markdown",
            version="1.0",
            author="author@example.com",
            project_id=self.sample_project_id,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        )

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_create_document_success(self, mock_get_service):
        """Test successful document creation."""
        mock_service = AsyncMock()
        mock_service.create_document.return_value = self.sample_document
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group,
            [
                "create",
                "--title",
                "Test Document",
                "--content",
                "Test content",
                "--project-id",
                self.sample_project_id,
                "--type",
                "specification",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0
        assert "Document created successfully" in result.output
        assert self.sample_document.title in result.output
        mock_service.create_document.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="# Test Content\n\nFrom file.",
    )
    def test_create_document_from_file(self, mock_file, mock_get_service):
        """Test creating document from file."""
        mock_service = AsyncMock()
        mock_service.create_document.return_value = self.sample_document
        mock_get_service.return_value = mock_service

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            f.write("# Test Content\n\nFrom file.")
            temp_file = f.name

        try:
            result = self.runner.invoke(
                documents_group,
                [
                    "create",
                    "--title",
                    "Test Document",
                    "--project-id",
                    self.sample_project_id,
                    "--from-file",
                    temp_file,
                ],
            )

            assert result.exit_code == 0
            assert "Document created successfully" in result.output
            mock_service.create_document.assert_called_once()
        finally:
            os.unlink(temp_file)

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_list_documents_success(self, mock_get_service):
        """Test listing documents."""
        mock_service = AsyncMock()
        mock_service.get_all_documents.return_value = [self.sample_document]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(documents_group, ["list"])

        assert result.exit_code == 0
        assert self.sample_document.title in result.output
        assert self.sample_document.type in result.output
        mock_service.get_all_documents.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_list_documents_by_project(self, mock_get_service):
        """Test listing documents by project."""
        mock_service = AsyncMock()
        mock_service.get_documents_by_project.return_value = [self.sample_document]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group, ["list", "--project-id", self.sample_project_id]
        )

        assert result.exit_code == 0
        mock_service.get_documents_by_project.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_list_documents_by_type(self, mock_get_service):
        """Test listing documents by type."""
        mock_service = AsyncMock()
        mock_service.get_documents_by_type.return_value = [self.sample_document]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group, ["list", "--type", "specification"]
        )

        assert result.exit_code == 0
        mock_service.get_documents_by_type.assert_called_once_with("specification")

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_get_document_success(self, mock_get_service):
        """Test getting document by ID."""
        mock_service = AsyncMock()
        mock_service.get_document_by_id.return_value = self.sample_document
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(documents_group, ["get", self.sample_document_id])

        assert result.exit_code == 0
        assert self.sample_document.title in result.output
        assert self.sample_document.content in result.output
        mock_service.get_document_by_id.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_update_document_success(self, mock_get_service):
        """Test updating document."""
        updated_document = self.sample_document.model_copy()
        updated_document.title = "Updated Document"
        updated_document.version = "2.0"

        mock_service = AsyncMock()
        mock_service.update_document.return_value = updated_document
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group,
            [
                "update",
                self.sample_document_id,
                "--title",
                "Updated Document",
                "--version",
                "2.0",
            ],
        )

        assert result.exit_code == 0
        assert "Document updated successfully" in result.output
        assert "Updated Document" in result.output
        mock_service.update_document.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_delete_document_success(self, mock_get_service):
        """Test deleting document."""
        mock_service = AsyncMock()
        mock_service.delete_document.return_value = True
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group, ["delete", self.sample_document_id, "--confirm"]
        )

        assert result.exit_code == 0
        assert "Document deleted successfully" in result.output
        mock_service.delete_document.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_search_documents_success(self, mock_get_service):
        """Test searching documents."""
        mock_service = AsyncMock()
        mock_service.search_documents.return_value = [self.sample_document]
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(documents_group, ["search", "Sample"])

        assert result.exit_code == 0
        assert self.sample_document.title in result.output
        mock_service.search_documents.assert_called_once_with("Sample")

    @patch("turbo.cli.commands.documents.get_document_service")
    @patch("builtins.open", new_callable=mock_open)
    def test_export_document_success(self, mock_file, mock_get_service):
        """Test exporting document."""
        mock_service = AsyncMock()
        mock_service.export_document.return_value = (b"PDF content", "application/pdf")
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group,
            [
                "export",
                self.sample_document_id,
                "--format",
                "pdf",
                "--output",
                "test.pdf",
            ],
        )

        assert result.exit_code == 0
        assert "Document exported successfully" in result.output
        mock_service.export_document.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_view_document_content(self, mock_get_service):
        """Test viewing document content."""
        mock_service = AsyncMock()
        mock_service.get_document_by_id.return_value = self.sample_document
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(documents_group, ["view", self.sample_document_id])

        assert result.exit_code == 0
        assert self.sample_document.content in result.output
        mock_service.get_document_by_id.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_duplicate_document_success(self, mock_get_service):
        """Test duplicating document."""
        duplicated_document = self.sample_document.model_copy()
        duplicated_document.id = str(uuid4())
        duplicated_document.title = "Copy of Sample Document"

        mock_service = AsyncMock()
        mock_service.duplicate_document.return_value = duplicated_document
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group,
            [
                "duplicate",
                self.sample_document_id,
                "--title",
                "Copy of Sample Document",
            ],
        )

        assert result.exit_code == 0
        assert "Document duplicated successfully" in result.output
        mock_service.duplicate_document.assert_called_once()


class TestDocumentCLITemplates:
    """Test document CLI template commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_list_templates_success(self, mock_get_service):
        """Test listing available templates."""
        mock_templates = [
            {
                "name": "api_spec",
                "description": "API Specification Template",
                "variables": ["api_name", "version"],
            },
            {
                "name": "user_guide",
                "description": "User Guide Template",
                "variables": ["product_name", "version"],
            },
        ]

        mock_service = AsyncMock()
        mock_service.get_available_templates.return_value = mock_templates
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(documents_group, ["templates"])

        assert result.exit_code == 0
        assert "api_spec" in result.output
        assert "user_guide" in result.output
        mock_service.get_available_templates.assert_called_once()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_create_from_template_success(self, mock_get_service):
        """Test creating document from template."""
        mock_document = DocumentResponse(
            id=str(uuid4()),
            title="API Documentation",
            content="# Turbo API v1.0\n\nGenerated from template.",
            type="api_doc",
            format="markdown",
            version="1.0",
            author=None,
            project_id=str(uuid4()),
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        )

        mock_service = AsyncMock()
        mock_service.create_document_from_template.return_value = mock_document
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group,
            [
                "from-template",
                "--template",
                "api_spec",
                "--title",
                "API Documentation",
                "--project-id",
                str(uuid4()),
                "--variable",
                "api_name=Turbo API",
                "--variable",
                "version=1.0",
            ],
        )

        assert result.exit_code == 0
        assert "Document created from template" in result.output
        mock_service.create_document_from_template.assert_called_once()


class TestDocumentCLIValidation:
    """Test document CLI input validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_document_type(self):
        """Test validation of document type."""
        result = self.runner.invoke(
            documents_group,
            [
                "create",
                "--title",
                "Test",
                "--content",
                "Test",
                "--project-id",
                str(uuid4()),
                "--type",
                "invalid-type",
            ],
        )

        assert result.exit_code != 0

    def test_invalid_document_format(self):
        """Test validation of document format."""
        result = self.runner.invoke(
            documents_group,
            [
                "create",
                "--title",
                "Test",
                "--content",
                "Test",
                "--project-id",
                str(uuid4()),
                "--format",
                "invalid-format",
            ],
        )

        assert result.exit_code != 0

    def test_invalid_export_format(self):
        """Test validation of export format."""
        result = self.runner.invoke(
            documents_group, ["export", str(uuid4()), "--format", "invalid-format"]
        )

        assert result.exit_code != 0

    def test_missing_required_fields(self):
        """Test validation of required fields."""
        result = self.runner.invoke(
            documents_group,
            [
                "create",
                "--title",
                "Test",
                # Missing content and project-id
            ],
        )

        assert result.exit_code != 0

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        result = self.runner.invoke(
            documents_group,
            [
                "create",
                "--title",
                "Test",
                "--project-id",
                str(uuid4()),
                "--from-file",
                "non-existent-file.md",
            ],
        )

        assert result.exit_code != 0
        assert "File not found" in result.output or "No such file" in result.output


class TestDocumentCLIEditor:
    """Test document CLI editor integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.documents.get_document_service")
    @patch("turbo.cli.commands.documents.click.edit")
    def test_edit_document_content(self, mock_edit, mock_get_service):
        """Test editing document content in external editor."""
        sample_document = DocumentResponse(
            id=str(uuid4()),
            title="Sample Document",
            content="# Original Content\n\nThis is original.",
            type="specification",
            format="markdown",
            version="1.0",
            author=None,
            project_id=str(uuid4()),
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        )

        updated_document = sample_document.model_copy()
        updated_document.content = "# Updated Content\n\nThis is updated."

        mock_edit.return_value = "# Updated Content\n\nThis is updated."
        mock_service = AsyncMock()
        mock_service.get_document_by_id.return_value = sample_document
        mock_service.update_document.return_value = updated_document
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(documents_group, ["edit", str(sample_document.id)])

        assert result.exit_code == 0
        assert "Document updated successfully" in result.output
        mock_edit.assert_called_once()
        mock_service.update_document.assert_called_once()


class TestDocumentCLIOutput:
    """Test document CLI output formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_list_documents_table_format(self, mock_get_service):
        """Test documents are displayed in table format."""
        documents = [
            DocumentResponse(
                id=str(uuid4()),
                title="Document 1",
                content="Content 1",
                type="specification",
                format="markdown",
                version="1.0",
                author="author1@example.com",
                project_id=str(uuid4()),
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
            ),
            DocumentResponse(
                id=str(uuid4()),
                title="Document 2",
                content="Content 2",
                type="user_guide",
                format="html",
                version="2.0",
                author="author2@example.com",
                project_id=str(uuid4()),
                created_at="2023-01-02T00:00:00Z",
                updated_at="2023-01-02T00:00:00Z",
            ),
        ]

        mock_service = AsyncMock()
        mock_service.get_all_documents.return_value = documents
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(documents_group, ["list"])

        assert result.exit_code == 0
        # Should contain table headers
        assert "Title" in result.output
        assert "Type" in result.output
        assert "Format" in result.output
        # Should contain document data
        assert "Document 1" in result.output
        assert "Document 2" in result.output

    @patch("turbo.cli.commands.documents.get_document_service")
    def test_get_document_detailed_view(self, mock_get_service):
        """Test detailed document view."""
        mock_service = AsyncMock()
        mock_service.get_document_by_id.return_value = self.sample_document
        mock_get_service.return_value = mock_service

        result = self.runner.invoke(
            documents_group, ["get", str(self.sample_document.id), "--detailed"]
        )

        assert result.exit_code == 0
        assert "ID:" in result.output
        assert "Version:" in result.output
        assert "Author:" in result.output
        assert "Created:" in result.output
