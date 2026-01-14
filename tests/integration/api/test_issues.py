"""Integration tests for issue API endpoints."""

from uuid import uuid4

from httpx import AsyncClient
import pytest


class TestIssueAPI:
    """Test issue API endpoints."""

    @pytest.mark.asyncio
    async def test_create_issue_success(self, test_client: AsyncClient, sample_project):
        """Test successful issue creation."""
        issue_data = {
            "title": "Test Issue",
            "description": "A test issue description",
            "type": "feature",
            "status": "open",
            "priority": "high",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/issues/", json=issue_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == issue_data["title"]
        assert data["description"] == issue_data["description"]
        assert data["type"] == issue_data["type"]
        assert data["status"] == issue_data["status"]
        assert data["priority"] == issue_data["priority"]
        assert data["project_id"] == issue_data["project_id"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_issue_validation_error(
        self, test_client: AsyncClient, sample_project
    ):
        """Test issue creation with invalid data."""
        invalid_data = {
            "title": "",  # Empty title should fail
            "description": "A test issue",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/issues/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_issue_by_id_success(
        self, test_client: AsyncClient, sample_issue
    ):
        """Test getting issue by ID."""
        response = await test_client.get(f"/api/v1/issues/{sample_issue.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_issue.id)
        assert data["title"] == sample_issue.title

    @pytest.mark.asyncio
    async def test_get_issue_by_id_not_found(self, test_client: AsyncClient):
        """Test getting non-existent issue."""
        non_existent_id = uuid4()
        response = await test_client.get(f"/api/v1/issues/{non_existent_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_all_issues(self, test_client: AsyncClient, populated_database):
        """Test getting all issues."""
        response = await test_client.get("/api/v1/issues/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_issues_with_pagination(
        self, test_client: AsyncClient, populated_database
    ):
        """Test getting issues with pagination."""
        response = await test_client.get("/api/v1/issues?limit=5&offset=2")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_update_issue_success(self, test_client: AsyncClient, sample_issue):
        """Test successful issue update."""
        update_data = {
            "title": "Updated Issue Title",
            "status": "in_progress",
            "priority": "critical",
        }

        response = await test_client.put(
            f"/api/v1/issues/{sample_issue.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["status"] == update_data["status"]
        assert data["priority"] == update_data["priority"]

    @pytest.mark.asyncio
    async def test_update_issue_not_found(self, test_client: AsyncClient):
        """Test updating non-existent issue."""
        non_existent_id = uuid4()
        update_data = {"title": "Updated Title"}

        response = await test_client.put(
            f"/api/v1/issues/{non_existent_id}", json=update_data
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_issue_success(self, test_client: AsyncClient, sample_issue):
        """Test successful issue deletion."""
        response = await test_client.delete(f"/api/v1/issues/{sample_issue.id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_issue_not_found(self, test_client: AsyncClient):
        """Test deleting non-existent issue."""
        non_existent_id = uuid4()
        response = await test_client.delete(f"/api/v1/issues/{non_existent_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_issue(self, test_client: AsyncClient, sample_issue):
        """Test assigning an issue to someone."""
        assignment_data = {"assignee": "developer@example.com"}

        response = await test_client.post(
            f"/api/v1/issues/{sample_issue.id}/assign", json=assignment_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assignee"] == assignment_data["assignee"]

    @pytest.mark.asyncio
    async def test_close_issue(self, test_client: AsyncClient, sample_issue):
        """Test closing an issue."""
        response = await test_client.post(f"/api/v1/issues/{sample_issue.id}/close")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"

    @pytest.mark.asyncio
    async def test_reopen_issue(self, test_client: AsyncClient, sample_issue):
        """Test reopening a closed issue."""
        # First close the issue
        await test_client.post(f"/api/v1/issues/{sample_issue.id}/close")

        # Then reopen it
        response = await test_client.post(f"/api/v1/issues/{sample_issue.id}/reopen")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "open"

    @pytest.mark.asyncio
    async def test_get_issues_by_project(
        self, test_client: AsyncClient, sample_project
    ):
        """Test getting issues for a specific project."""
        response = await test_client.get(f"/api/v1/projects/{sample_project.id}/issues")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All issues should belong to the project
        for issue in data:
            assert issue["project_id"] == str(sample_project.id)

    @pytest.mark.asyncio
    async def test_get_issues_by_status(self, test_client: AsyncClient):
        """Test filtering issues by status."""
        response = await test_client.get("/api/v1/issues?status=open")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All returned issues should have open status
        for issue in data:
            assert issue["status"] == "open"

    @pytest.mark.asyncio
    async def test_get_issues_by_assignee(self, test_client: AsyncClient):
        """Test filtering issues by assignee."""
        assignee = "developer@example.com"
        response = await test_client.get(f"/api/v1/issues?assignee={assignee}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_search_issues(self, test_client: AsyncClient, populated_database):
        """Test searching issues by title."""
        response = await test_client.get("/api/v1/issues/search?query=Test")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestIssueAPIValidation:
    """Test issue API validation."""

    @pytest.mark.asyncio
    async def test_invalid_issue_type(self, test_client: AsyncClient, sample_project):
        """Test creating issue with invalid type."""
        invalid_data = {
            "title": "Test Issue",
            "description": "Test description",
            "type": "invalid_type",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/issues/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_issue_status(self, test_client: AsyncClient, sample_project):
        """Test creating issue with invalid status."""
        invalid_data = {
            "title": "Test Issue",
            "description": "Test description",
            "status": "invalid_status",
            "project_id": str(sample_project.id),
        }

        response = await test_client.post("/api/v1/issues/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_email_assignee(self, test_client: AsyncClient, sample_issue):
        """Test assigning issue with invalid email."""
        invalid_assignment = {"assignee": "not-an-email"}

        response = await test_client.post(
            f"/api/v1/issues/{sample_issue.id}/assign", json=invalid_assignment
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_project_id(self, test_client: AsyncClient):
        """Test creating issue without project_id."""
        invalid_data = {
            "title": "Test Issue",
            "description": "Test description",
            # Missing project_id
        }

        response = await test_client.post("/api/v1/issues/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_nonexistent_project_id(self, test_client: AsyncClient):
        """Test creating issue with non-existent project_id."""
        invalid_data = {
            "title": "Test Issue",
            "description": "Test description",
            "project_id": str(uuid4()),  # Non-existent project
        }

        response = await test_client.post("/api/v1/issues/", json=invalid_data)

        assert response.status_code == 404


class TestIssueAPIRelationships:
    """Test issue API with related entities."""

    @pytest.mark.asyncio
    async def test_add_tag_to_issue(self, test_client: AsyncClient, sample_issue):
        """Test adding tags to an issue."""
        tag_data = {"name": "bug", "color": "#FF3333"}

        # Create a tag
        tag_response = await test_client.post("/api/v1/tags/", json=tag_data)
        assert tag_response.status_code == 201
        tag_id = tag_response.json()["id"]

        # Add tag to issue
        response = await test_client.post(
            f"/api/v1/issues/{sample_issue.id}/tags/{tag_id}"
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_remove_tag_from_issue(self, test_client: AsyncClient, sample_issue):
        """Test removing tags from an issue."""
        tag_data = {"name": "feature", "color": "#33FF33"}
        tag_response = await test_client.post("/api/v1/tags/", json=tag_data)
        tag_id = tag_response.json()["id"]

        # Add tag to issue
        await test_client.post(f"/api/v1/issues/{sample_issue.id}/tags/{tag_id}")

        # Remove tag from issue
        response = await test_client.delete(
            f"/api/v1/issues/{sample_issue.id}/tags/{tag_id}"
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_get_issue_tags(self, test_client: AsyncClient, sample_issue):
        """Test getting tags for an issue."""
        response = await test_client.get(f"/api/v1/issues/{sample_issue.id}/tags")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
