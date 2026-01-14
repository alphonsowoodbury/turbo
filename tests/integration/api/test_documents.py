"""Integration tests for document API endpoints."""

from uuid import uuid4

from httpx import AsyncClient
import pytest


class TestDocumentAPI:
    """Test document API endpoints."""

    @pytest.mark.asyncio
    async def test_create_document_success(
        self, test_client: AsyncClient, sample_project
    ):
        """Test successful document creation."""
        document_data = {
            "title": "Test Document",
            "content": "# Test Document\n\nThis is test content.",
            "type": "specification",
            "format": "markdown",
            "version": "1.0",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/documents/", json=document_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == document_data["title"]
        assert data["content"] == document_data["content"]
        assert data["type"] == document_data["type"]
        assert data["format"] == document_data["format"]
        assert data["version"] == document_data["version"]
        assert data["project_id"] == document_data["project_id"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_document_validation_error(
        self, test_client: AsyncClient, sample_project
    ):
        """Test document creation with invalid data."""
        invalid_data = {
            "title": "",  # Empty title should fail
            "content": "Test content",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/documents/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_document_by_id_success(
        self, test_client: AsyncClient, sample_document
    ):
        """Test getting document by ID."""
        response = await test_client.get(f"/api/v1/documents/{sample_document.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_document.id)
        assert data["title"] == sample_document.title

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_found(self, test_client: AsyncClient):
        """Test getting non-existent document."""
        non_existent_id = uuid4()
        response = await test_client.get(f"/api/v1/documents/{non_existent_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_all_documents(
        self, test_client: AsyncClient, populated_database
    ):
        """Test getting all documents."""
        response = await test_client.get("/api/v1/documents/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_documents_with_pagination(
        self, test_client: AsyncClient, populated_database
    ):
        """Test getting documents with pagination."""
        response = await test_client.get("/api/v1/documents?limit=3&offset=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3

    @pytest.mark.asyncio
    async def test_update_document_success(
        self, test_client: AsyncClient, sample_document
    ):
        """Test successful document update."""
        update_data = {
            "title": "Updated Document Title",
            "content": "# Updated Content\n\nThis is updated content.",
            "version": "2.0",
        }

        response = await test_client.put(
            f"/api/v1/documents/{sample_document.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["content"] == update_data["content"]
        assert data["version"] == update_data["version"]

    @pytest.mark.asyncio
    async def test_update_document_not_found(self, test_client: AsyncClient):
        """Test updating non-existent document."""
        non_existent_id = uuid4()
        update_data = {"title": "Updated Title"}

        response = await test_client.put(
            f"/api/v1/documents/{non_existent_id}", json=update_data
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self, test_client: AsyncClient, sample_document
    ):
        """Test successful document deletion."""
        response = await test_client.delete(f"/api/v1/documents/{sample_document.id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, test_client: AsyncClient):
        """Test deleting non-existent document."""
        non_existent_id = uuid4()
        response = await test_client.delete(f"/api/v1/documents/{non_existent_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_documents_by_project(
        self, test_client: AsyncClient, sample_project
    ):
        """Test getting documents for a specific project."""
        response = await test_client.get(
            f"/api/v1/projects/{sample_project.id}/documents"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All documents should belong to the project
        for document in data:
            assert document["project_id"] == str(sample_project.id)

    @pytest.mark.asyncio
    async def test_get_documents_by_type(self, test_client: AsyncClient):
        """Test filtering documents by type."""
        response = await test_client.get("/api/v1/documents?type=specification")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All returned documents should have specification type
        for document in data:
            assert document["type"] == "specification"

    @pytest.mark.asyncio
    async def test_get_documents_by_format(self, test_client: AsyncClient):
        """Test filtering documents by format."""
        response = await test_client.get("/api/v1/documents?format=markdown")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_search_documents(self, test_client: AsyncClient, populated_database):
        """Test searching documents by title and content."""
        response = await test_client.get("/api/v1/documents/search?query=test")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_document_versions(
        self, test_client: AsyncClient, sample_document
    ):
        """Test getting document version history."""
        response = await test_client.get(
            f"/api/v1/documents/{sample_document.id}/versions"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_export_document(self, test_client: AsyncClient, sample_document):
        """Test exporting document in different formats."""
        # Test PDF export
        response = await test_client.get(
            f"/api/v1/documents/{sample_document.id}/export?format=pdf"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        # Test HTML export
        response = await test_client.get(
            f"/api/v1/documents/{sample_document.id}/export?format=html"
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestDocumentAPIValidation:
    """Test document API validation."""

    @pytest.mark.asyncio
    async def test_invalid_document_type(
        self, test_client: AsyncClient, sample_project
    ):
        """Test creating document with invalid type."""
        invalid_data = {
            "title": "Test Document",
            "content": "Test content",
            "type": "invalid_type",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/documents/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_document_format(
        self, test_client: AsyncClient, sample_project
    ):
        """Test creating document with invalid format."""
        invalid_data = {
            "title": "Test Document",
            "content": "Test content",
            "format": "invalid_format",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/documents/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_author_email(self, test_client: AsyncClient, sample_project):
        """Test creating document with invalid author email."""
        invalid_data = {
            "title": "Test Document",
            "content": "Test content",
            "author": "not-an-email",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/documents/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_content(self, test_client: AsyncClient, sample_project):
        """Test creating document with empty content."""
        invalid_data = {
            "title": "Test Document",
            "content": "",  # Empty content should fail
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/documents/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_project_id(self, test_client: AsyncClient):
        """Test creating document without project_id."""
        invalid_data = {
            "title": "Test Document",
            "content": "Test content",
            # Missing project_id
        }

        response = await test_client.post("/api/v1/documents/", json=invalid_data)

        assert response.status_code == 422


class TestDocumentAPITemplates:
    """Test document API template functionality."""

    @pytest.mark.asyncio
    async def test_create_document_from_template(
        self, test_client: AsyncClient, sample_project
    ):
        """Test creating document from template."""
        template_data = {
            "template_name": "api_specification",
            "title": "API Documentation",
            "project_id": str(sample_project.id),
            "variables": {"api_name": "Turbo API", "version": "1.0"},
        }

        response = await test_client.post(
            "/api/v1/documents/from-template", json=template_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == template_data["title"]
        assert "API" in data["content"]  # Template should be filled with variables

    @pytest.mark.asyncio
    async def test_get_available_templates(self, test_client: AsyncClient):
        """Test getting available document templates."""
        response = await test_client.get("/api/v1/documents/templates")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Check template structure
        if data:
            template = data[0]
            assert "name" in template
            assert "description" in template
            assert "variables" in template


class TestDocumentAPICollaboration:
    """Test document API collaboration features."""

    @pytest.mark.asyncio
    async def test_duplicate_document(self, test_client: AsyncClient, sample_document):
        """Test duplicating a document."""
        duplicate_data = {"title": "Duplicated Document", "version": "1.0"}

        response = await test_client.post(
            f"/api/v1/documents/{sample_document.id}/duplicate", json=duplicate_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == duplicate_data["title"]
        assert data["content"] == sample_document.content
        assert data["id"] != str(sample_document.id)

    @pytest.mark.asyncio
    async def test_bulk_operations(self, test_client: AsyncClient, sample_project):
        """Test bulk document operations."""
        # Create multiple documents first
        doc_ids = []
        for i in range(3):
            doc_data = {
                "title": f"Bulk Test Doc {i}",
                "content": f"Content {i}",
                "project_id": str(sample_project.id),
            }
            response = await test_client.post("/api/v1/documents/", json=doc_data)
            doc_ids.append(response.json()["id"])

        # Test bulk delete
        bulk_data = {"document_ids": doc_ids}
        response = await test_client.post(
            "/api/v1/documents/bulk-delete", json=bulk_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 3
