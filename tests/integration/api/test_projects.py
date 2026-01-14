"""Integration tests for project API endpoints."""

from uuid import uuid4

from httpx import AsyncClient
import pytest


class TestProjectAPI:
    """Test project API endpoints."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, test_client: AsyncClient):
        """Test successful project creation."""
        project_data = {
            "name": "Test Project",
            "description": "A test project",
            "priority": "high",
            "status": "active",
        }

        response = await test_client.post("/api/v1/projects/", json=project_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["priority"] == project_data["priority"]
        assert data["status"] == project_data["status"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_project_validation_error(self, test_client: AsyncClient):
        """Test project creation with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should fail
            "description": "A test project",
        }

        response = await test_client.post("/api/v1/projects/", json=invalid_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_get_project_by_id_success(
        self, test_client: AsyncClient, sample_project
    ):
        """Test getting project by ID."""
        response = await test_client.get(f"/api/v1/projects/{sample_project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_project.id)
        assert data["name"] == sample_project.name

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, test_client: AsyncClient):
        """Test getting non-existent project."""
        non_existent_id = uuid4()
        response = await test_client.get(f"/api/v1/projects/{non_existent_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_all_projects(self, test_client: AsyncClient, populated_database):
        """Test getting all projects."""
        response = await test_client.get("/api/v1/projects/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check first project structure
        project = data[0]
        assert "id" in project
        assert "name" in project
        assert "description" in project

    @pytest.mark.asyncio
    async def test_get_projects_with_pagination(
        self, test_client: AsyncClient, populated_database
    ):
        """Test getting projects with pagination."""
        response = await test_client.get("/api/v1/projects?limit=2&offset=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

    @pytest.mark.asyncio
    async def test_update_project_success(
        self, test_client: AsyncClient, sample_project
    ):
        """Test successful project update."""
        update_data = {"name": "Updated Project Name", "priority": "critical"}

        response = await test_client.put(
            f"/api/v1/projects/{sample_project.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["priority"] == update_data["priority"]
        assert data["id"] == str(sample_project.id)

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, test_client: AsyncClient):
        """Test updating non-existent project."""
        non_existent_id = uuid4()
        update_data = {"name": "Updated Name"}

        response = await test_client.put(
            f"/api/v1/projects/{non_existent_id}", json=update_data
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_success(
        self, test_client: AsyncClient, sample_project
    ):
        """Test successful project deletion."""
        response = await test_client.delete(f"/api/v1/projects/{sample_project.id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, test_client: AsyncClient):
        """Test deleting non-existent project."""
        non_existent_id = uuid4()
        response = await test_client.delete(f"/api/v1/projects/{non_existent_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_project(self, test_client: AsyncClient, sample_project):
        """Test archiving a project."""
        response = await test_client.post(
            f"/api/v1/projects/{sample_project.id}/archive"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is True

    @pytest.mark.asyncio
    async def test_get_project_statistics(
        self, test_client: AsyncClient, sample_project
    ):
        """Test getting project statistics."""
        response = await test_client.get(f"/api/v1/projects/{sample_project.id}/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_issues" in data
        assert "open_issues" in data
        assert "closed_issues" in data
        assert "completion_rate" in data

    @pytest.mark.asyncio
    async def test_search_projects(self, test_client: AsyncClient, populated_database):
        """Test searching projects by name."""
        response = await test_client.get("/api/v1/projects/search?query=Test")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_projects_by_status(
        self, test_client: AsyncClient, populated_database
    ):
        """Test filtering projects by status."""
        response = await test_client.get("/api/v1/projects?status=active")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All returned projects should have active status
        for project in data:
            assert project["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_projects_by_priority(
        self, test_client: AsyncClient, populated_database
    ):
        """Test filtering projects by priority."""
        response = await test_client.get("/api/v1/projects?priority=high")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestProjectAPIErrorHandling:
    """Test project API error handling."""

    @pytest.mark.asyncio
    async def test_invalid_uuid_format(self, test_client: AsyncClient):
        """Test handling of invalid UUID format."""
        response = await test_client.get("/api/v1/projects/invalid-uuid")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, test_client: AsyncClient):
        """Test creation with missing required fields."""
        incomplete_data = {"name": "Test Project"}  # Missing description

        response = await test_client.post("/api/v1/projects/", json=incomplete_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_field_values(self, test_client: AsyncClient):
        """Test creation with invalid field values."""
        invalid_data = {
            "name": "Test Project",
            "description": "Test description",
            "priority": "invalid_priority",  # Invalid priority
            "completion_percentage": 150.0,  # Invalid percentage
        }

        response = await test_client.post("/api/v1/projects/", json=invalid_data)

        assert response.status_code == 422


class TestProjectAPIPermissions:
    """Test project API permissions and security."""

    @pytest.mark.asyncio
    async def test_cors_headers(self, test_client: AsyncClient):
        """Test CORS headers are present."""
        response = await test_client.get("/api/v1/projects/")

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    @pytest.mark.asyncio
    async def test_content_type_json(self, test_client: AsyncClient, sample_project):
        """Test API returns proper JSON content type."""
        response = await test_client.get(f"/api/v1/projects/{sample_project.id}")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


class TestProjectAPIRelationships:
    """Test project API with related entities."""

    @pytest.mark.asyncio
    async def test_get_project_with_issues(
        self, test_client: AsyncClient, sample_project, sample_issue
    ):
        """Test getting project with its issues."""
        response = await test_client.get(f"/api/v1/projects/{sample_project.id}/issues")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_project_with_documents(
        self, test_client: AsyncClient, sample_project, sample_document
    ):
        """Test getting project with its documents."""
        response = await test_client.get(
            f"/api/v1/projects/{sample_project.id}/documents"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_add_tag_to_project(self, test_client: AsyncClient, sample_project):
        """Test adding tags to a project."""
        tag_data = {"name": "frontend", "color": "#FF5733"}

        # First create a tag
        tag_response = await test_client.post("/api/v1/tags/", json=tag_data)
        assert tag_response.status_code == 201
        tag_id = tag_response.json()["id"]

        # Then add it to the project
        response = await test_client.post(
            f"/api/v1/projects/{sample_project.id}/tags/{tag_id}"
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_remove_tag_from_project(
        self, test_client: AsyncClient, sample_project
    ):
        """Test removing tags from a project."""
        # Assuming we have a tag associated with the project
        tag_data = {"name": "backend", "color": "#33FF57"}
        tag_response = await test_client.post("/api/v1/tags/", json=tag_data)
        tag_id = tag_response.json()["id"]

        # Add tag to project
        await test_client.post(f"/api/v1/projects/{sample_project.id}/tags/{tag_id}")

        # Remove tag from project
        response = await test_client.delete(
            f"/api/v1/projects/{sample_project.id}/tags/{tag_id}"
        )

        assert response.status_code == 204
