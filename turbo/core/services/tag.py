"""Tag service for business logic operations."""

from uuid import UUID

from turbo.core.repositories.tag import TagRepository
from turbo.core.schemas.tag import TagCreate, TagResponse
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import DuplicateResourceError, TagNotFoundError


class TagService:
    """Service for tag business logic."""

    def __init__(self, tag_repository: TagRepository) -> None:
        self._tag_repository = tag_repository

    async def create_tag(self, tag_data: TagCreate) -> TagResponse:
        """Create a new tag."""
        # Strip emojis from text fields
        if tag_data.name:
            tag_data.name = strip_emojis(tag_data.name)
        if tag_data.description:
            tag_data.description = strip_emojis(tag_data.description)

        # Check if tag with same name already exists
        existing_tag = await self._tag_repository.get_by_name(tag_data.name)
        if existing_tag:
            raise DuplicateResourceError("Tag", f"name '{tag_data.name}'")

        tag = await self._tag_repository.create(tag_data)
        return TagResponse.model_validate(tag)

    async def get_tag_by_id(self, tag_id: UUID) -> TagResponse:
        """Get tag by ID."""
        tag = await self._tag_repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)
        return TagResponse.model_validate(tag)

    async def get_tag_by_name(self, name: str) -> TagResponse | None:
        """Get tag by name."""
        tag = await self._tag_repository.get_by_name(name)
        if tag:
            return TagResponse.model_validate(tag)
        return None

    async def get_all_tags(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[TagResponse]:
        """Get all tags with optional pagination."""
        tags = await self._tag_repository.get_all(limit=limit, offset=offset)
        return [TagResponse.model_validate(tag) for tag in tags]

    async def update_tag(self, tag_id: UUID, tag_data: TagCreate) -> TagResponse:
        """Update a tag."""
        # Strip emojis from text fields
        if tag_data.name:
            tag_data.name = strip_emojis(tag_data.name)
        if tag_data.description:
            tag_data.description = strip_emojis(tag_data.description)

        # Check if name is being changed to an existing name
        if tag_data.name:
            existing_tag = await self._tag_repository.get_by_name(tag_data.name)
            if existing_tag and existing_tag.id != tag_id:
                raise DuplicateResourceError("Tag", f"name '{tag_data.name}'")

        tag = await self._tag_repository.update(tag_id, tag_data)
        if not tag:
            raise TagNotFoundError(tag_id)
        return TagResponse.model_validate(tag)

    async def delete_tag(self, tag_id: UUID) -> bool:
        """Delete a tag."""
        success = await self._tag_repository.delete(tag_id)
        if not success:
            raise TagNotFoundError(tag_id)
        return success

    async def search_tags(self, name_pattern: str) -> list[TagResponse]:
        """Search tags by name pattern."""
        tags = await self._tag_repository.search_by_name(name_pattern)
        return [TagResponse.model_validate(tag) for tag in tags]

    async def get_tags_by_color(self, color: str) -> list[TagResponse]:
        """Get tags by color."""
        tags = await self._tag_repository.get_by_color(color)
        return [TagResponse.model_validate(tag) for tag in tags]

    async def get_popular_tags(self, limit: int = 10) -> list[TagResponse]:
        """Get most popular tags."""
        tags = await self._tag_repository.get_popular_tags(limit=limit)
        return [TagResponse.model_validate(tag) for tag in tags]

    async def get_unused_tags(self) -> list[TagResponse]:
        """Get tags that are not used by any projects or issues."""
        tags = await self._tag_repository.get_unused_tags()
        return [TagResponse.model_validate(tag) for tag in tags]
