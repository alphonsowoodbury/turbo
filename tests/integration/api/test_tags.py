"""Integration tests for tag API endpoints."""

from uuid import uuid4

from httpx import AsyncClient
import pytest


class TestTagAPI:
    """Test tag API endpoints."""

    @pytest.mark.asyncio
    async def test_create_tag_success(self, test_client: AsyncClient):
        """Test successful tag creation."""
        tag_data = {
            "name": "frontend",
            "color": "#FF5733",
            "description": "Frontend development related",
        }

        response = await test_client.post("/api/v1/tags/", json=tag_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == tag_data["name"]
        assert data["color"] == tag_data["color"]
        assert data["description"] == tag_data["description"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_tag_validation_error(self, test_client: AsyncClient):
        """Test tag creation with invalid data."""
        invalid_data = {"name": "", "color": "#FF5733"}  # Empty name should fail

        response = await test_client.post("/api/v1/tags/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_tag_duplicate_name(self, test_client: AsyncClient):
        """Test creating tag with duplicate name."""
        tag_data = {"name": "backend", "color": "#33FF57"}

        # Create first tag
        response1 = await test_client.post("/api/v1/tags/", json=tag_data)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await test_client.post("/api/v1/tags/", json=tag_data)
        assert response2.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_get_tag_by_id_success(self, test_client: AsyncClient):
        """Test getting tag by ID."""
        # First create a tag
        tag_data = {"name": "testing", "color": "#5733FF"}
        create_response = await test_client.post("/api/v1/tags/", json=tag_data)
        tag_id = create_response.json()["id"]

        response = await test_client.get(f"/api/v1/tags/{tag_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tag_id
        assert data["name"] == tag_data["name"]

    @pytest.mark.asyncio
    async def test_get_tag_by_id_not_found(self, test_client: AsyncClient):
        """Test getting non-existent tag."""
        non_existent_id = uuid4()
        response = await test_client.get(f"/api/v1/tags/{non_existent_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_all_tags(self, test_client: AsyncClient):
        """Test getting all tags."""
        # Create some tags first
        tags_data = [
            {"name": "api", "color": "#FF3333"},
            {"name": "database", "color": "#33FF33"},
            {"name": "ui", "color": "#3333FF"},
        ]

        for tag_data in tags_data:
            await test_client.post("/api/v1/tags/", json=tag_data)

        response = await test_client.get("/api/v1/tags/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(tags_data)

    @pytest.mark.asyncio
    async def test_get_tags_with_pagination(self, test_client: AsyncClient):
        """Test getting tags with pagination."""
        response = await test_client.get("/api/v1/tags?limit=2&offset=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

    @pytest.mark.asyncio
    async def test_update_tag_success(self, test_client: AsyncClient):
        """Test successful tag update."""
        # Create a tag first
        tag_data = {"name": "performance", "color": "#FFFF33"}
        create_response = await test_client.post("/api/v1/tags/", json=tag_data)
        tag_id = create_response.json()["id"]

        update_data = {
            "name": "performance-optimization",
            "color": "#FF8833",
            "description": "Performance optimization tasks",
        }

        response = await test_client.put(f"/api/v1/tags/{tag_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["color"] == update_data["color"]
        assert data["description"] == update_data["description"]

    @pytest.mark.asyncio
    async def test_update_tag_not_found(self, test_client: AsyncClient):
        """Test updating non-existent tag."""
        non_existent_id = uuid4()
        update_data = {"name": "updated-name"}

        response = await test_client.put(
            f"/api/v1/tags/{non_existent_id}", json=update_data
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_tag_success(self, test_client: AsyncClient):
        """Test successful tag deletion."""
        # Create a tag first
        tag_data = {"name": "temporary", "color": "#888888"}
        create_response = await test_client.post("/api/v1/tags/", json=tag_data)
        tag_id = create_response.json()["id"]

        response = await test_client.delete(f"/api/v1/tags/{tag_id}")

        assert response.status_code == 204

        # Verify tag is deleted
        get_response = await test_client.get(f"/api/v1/tags/{tag_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_tag_not_found(self, test_client: AsyncClient):
        """Test deleting non-existent tag."""
        non_existent_id = uuid4()
        response = await test_client.delete(f"/api/v1/tags/{non_existent_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_tags(self, test_client: AsyncClient):
        """Test searching tags by name."""
        # Create some tags first
        tags_data = [
            {"name": "javascript", "color": "#F7DF1E"},
            {"name": "java", "color": "#ED8B00"},
            {"name": "python", "color": "#3776AB"},
        ]

        for tag_data in tags_data:
            await test_client.post("/api/v1/tags/", json=tag_data)

        response = await test_client.get("/api/v1/tags/search?query=java")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should return both "javascript" and "java"
        tag_names = [tag["name"] for tag in data]
        assert "javascript" in tag_names
        assert "java" in tag_names

    @pytest.mark.asyncio
    async def test_get_tags_by_color(self, test_client: AsyncClient):
        """Test filtering tags by color."""
        color = "#FF0000"
        tag_data = {"name": "red-tag", "color": color}
        await test_client.post("/api/v1/tags/", json=tag_data)

        response = await test_client.get(f"/api/v1/tags?color={color}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All returned tags should have the specified color
        for tag in data:
            assert tag["color"] == color

    @pytest.mark.asyncio
    async def test_get_popular_tags(self, test_client: AsyncClient):
        """Test getting popular tags."""
        response = await test_client.get("/api/v1/tags/popular?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    @pytest.mark.asyncio
    async def test_get_unused_tags(self, test_client: AsyncClient):
        """Test getting unused tags."""
        # Create a tag that won't be used
        tag_data = {"name": "unused-tag", "color": "#CCCCCC"}
        await test_client.post("/api/v1/tags/", json=tag_data)

        response = await test_client.get("/api/v1/tags/unused")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTagAPIValidation:
    """Test tag API validation."""

    @pytest.mark.asyncio
    async def test_invalid_color_format(self, test_client: AsyncClient):
        """Test creating tag with invalid color format."""
        invalid_data = {
            "name": "invalid-color-tag",
            "color": "red",  # Should be hex format
        }

        response = await test_client.post("/api/v1/tags/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_color_case_insensitive(self, test_client: AsyncClient):
        """Test that color validation is case insensitive."""
        tag_data = {"name": "case-test", "color": "#ff5733"}  # lowercase hex

        response = await test_client.post("/api/v1/tags/", json=tag_data)

        assert response.status_code == 201
        data = response.json()
        assert data["color"] == "#FF5733"  # Should be converted to uppercase

    @pytest.mark.asyncio
    async def test_name_length_validation(self, test_client: AsyncClient):
        """Test tag name length validation."""
        # Too long name
        long_name = "a" * 51  # Assuming max length is 50
        invalid_data = {"name": long_name, "color": "#FF5733"}

        response = await test_client.post("/api/v1/tags/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_description_length_validation(self, test_client: AsyncClient):
        """Test tag description length validation."""
        # Too long description
        long_description = "a" * 201  # Assuming max length is 200
        invalid_data = {
            "name": "test-tag",
            "color": "#FF5733",
            "description": long_description,
        }

        response = await test_client.post("/api/v1/tags/", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_whitespace_name_validation(self, test_client: AsyncClient):
        """Test that tag names with only whitespace are rejected."""
        invalid_data = {"name": "   ", "color": "#FF5733"}  # Only whitespace

        response = await test_client.post("/api/v1/tags/", json=invalid_data)

        assert response.status_code == 422


class TestTagAPIRelationships:
    """Test tag API with related entities."""

    @pytest.mark.asyncio
    async def test_get_tag_usage_statistics(self, test_client: AsyncClient):
        """Test getting tag usage statistics."""
        # Create a tag first
        tag_data = {"name": "stats-tag", "color": "#123456"}
        create_response = await test_client.post("/api/v1/tags/", json=tag_data)
        tag_id = create_response.json()["id"]

        response = await test_client.get(f"/api/v1/tags/{tag_id}/usage")

        assert response.status_code == 200
        data = response.json()
        assert "project_count" in data
        assert "issue_count" in data
        assert "total_usage" in data

    @pytest.mark.asyncio
    async def test_get_projects_with_tag(
        self, test_client: AsyncClient, sample_project
    ):
        """Test getting projects that have a specific tag."""
        # Create a tag and associate it with project
        tag_data = {"name": "project-tag", "color": "#654321"}
        tag_response = await test_client.post("/api/v1/tags/", json=tag_data)
        tag_id = tag_response.json()["id"]

        # Associate tag with project
        await test_client.post(f"/api/v1/projects/{sample_project.id}/tags/{tag_id}")

        # Get projects with this tag
        response = await test_client.get(f"/api/v1/tags/{tag_id}/projects")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_issues_with_tag(self, test_client: AsyncClient, sample_issue):
        """Test getting issues that have a specific tag."""
        # Create a tag and associate it with issue
        tag_data = {"name": "issue-tag", "color": "#789ABC"}
        tag_response = await test_client.post("/api/v1/tags/", json=tag_data)
        tag_id = tag_response.json()["id"]

        # Associate tag with issue
        await test_client.post(f"/api/v1/issues/{sample_issue.id}/tags/{tag_id}")

        # Get issues with this tag
        response = await test_client.get(f"/api/v1/tags/{tag_id}/issues")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_bulk_tag_operations(self, test_client: AsyncClient, sample_project):
        """Test bulk tag operations."""
        # Create multiple tags
        tag_ids = []
        for i in range(3):
            tag_data = {"name": f"bulk-tag-{i}", "color": f"#{i*111111:06X}"}
            response = await test_client.post("/api/v1/tags/", json=tag_data)
            tag_ids.append(response.json()["id"])

        # Bulk assign tags to project
        bulk_data = {"tag_ids": tag_ids}
        response = await test_client.post(
            f"/api/v1/projects/{sample_project.id}/tags/bulk-assign", json=bulk_data
        )

        assert response.status_code == 200

        # Bulk remove tags from project
        response = await test_client.post(
            f"/api/v1/projects/{sample_project.id}/tags/bulk-remove", json=bulk_data
        )

        assert response.status_code == 200
