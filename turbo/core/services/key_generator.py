"""Key generation service for entity keys."""

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.entity_counter import ProjectEntityCounter
from turbo.core.models.project import Project


class KeyGeneratorService:
    """Service for generating unique entity keys."""

    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def validate_project_key(key: str) -> tuple[bool, str | None]:
        """
        Validate a project key.

        Rules:
        - 2-10 characters
        - Uppercase letters and numbers only
        - Must start with a letter

        Returns:
            (is_valid, error_message)
        """
        if not key:
            return False, "Project key is required"

        if len(key) < 2 or len(key) > 10:
            return False, "Project key must be 2-10 characters"

        if not key.isupper():
            return False, "Project key must be uppercase"

        if not re.match(r"^[A-Z][A-Z0-9]*$", key):
            return False, "Project key must start with a letter and contain only letters and numbers"

        return True, None

    async def is_project_key_available(self, key: str) -> bool:
        """Check if a project key is available (not already used)."""
        stmt = select(Project).where(Project.project_key == key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is None

    async def generate_entity_key(
        self, project_id: UUID, entity_type: str
    ) -> tuple[str, int]:
        """
        Generate the next unique key for an entity.

        This method is atomic and concurrency-safe using SELECT FOR UPDATE.

        Args:
            project_id: The project UUID
            entity_type: One of: "issue", "milestone", "initiative", "document"

        Returns:
            tuple of (full_key, number)
            Example: ("CNTXT-42", 42) for an issue
                     ("CNTXT-M3", 3) for a milestone

        Raises:
            ValueError: If project doesn't exist or entity_type is invalid
        """
        # Validate entity type
        valid_types = ["issue", "milestone", "initiative", "document"]
        if entity_type not in valid_types:
            raise ValueError(f"Invalid entity_type. Must be one of: {valid_types}")

        # Get project key
        stmt = select(Project.project_key).where(Project.id == project_id)
        result = await self._session.execute(stmt)
        project_key = result.scalar_one_or_none()

        if not project_key:
            raise ValueError(f"Project with id {project_id} not found")

        # Get or create counter (with lock)
        stmt = (
            select(ProjectEntityCounter)
            .where(ProjectEntityCounter.project_id == project_id)
            .where(ProjectEntityCounter.entity_type == entity_type)
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        counter = result.scalar_one_or_none()

        if not counter:
            # Create counter if it doesn't exist
            counter = ProjectEntityCounter(
                project_id=project_id, entity_type=entity_type, next_number=1
            )
            self._session.add(counter)
            await self._session.flush()  # Get the counter object

        # Get the number to use
        number = counter.next_number

        # Increment counter
        counter.next_number += 1
        await self._session.flush()

        # Generate the full key
        prefix_map = {
            "issue": "",  # CNTXT-1
            "milestone": "M",  # CNTXT-M1
            "initiative": "I",  # CNTXT-I1
            "document": "D",  # CNTXT-D1
        }

        prefix = prefix_map[entity_type]
        full_key = f"{project_key}-{prefix}{number}"

        return full_key, number

    @staticmethod
    def generate_project_key_suggestion(project_name: str) -> str:
        """
        Generate a suggested project key from a project name.

        Examples:
            "Context App" -> "CNTXT"
            "Turbo Code Platform" -> "TURBO"
            "My Project" -> "MYPROJ"

        User can override this suggestion.
        """
        # Remove special characters, keep only letters and numbers
        clean_name = re.sub(r"[^a-zA-Z0-9 ]", "", project_name)

        # Try to create acronym from first letters of words
        words = clean_name.split()
        if len(words) >= 2:
            # Multi-word: take first letter of each word
            acronym = "".join(word[0].upper() for word in words if word)
            if 2 <= len(acronym) <= 10:
                return acronym

        # Single word or acronym too long: take first 5-6 chars
        key = clean_name.replace(" ", "")[:6].upper()

        # Ensure at least 2 chars
        if len(key) < 2:
            key = (key + "XX")[:2]  # Pad with X if too short

        return key

    async def resolve_entity_id(
        self, id_or_key: str, entity_type: str
    ) -> UUID | None:
        """
        Resolve an entity ID from either UUID or key.

        Args:
            id_or_key: Either a UUID string or entity key (e.g., "CNTXT-1")
            entity_type: "issue", "milestone", "initiative", or "document"

        Returns:
            UUID if found, None otherwise
        """
        # Try as UUID first
        try:
            return UUID(id_or_key)
        except (ValueError, AttributeError):
            pass

        # Try as key
        entity_model_map = {
            "issue": "issues",
            "milestone": "milestones",
            "initiative": "initiatives",
            "document": "documents",
        }

        table_name = entity_model_map.get(entity_type)
        if not table_name:
            return None

        # Import the appropriate model
        if entity_type == "issue":
            from turbo.core.models.issue import Issue

            stmt = select(Issue.id).where(Issue.issue_key == id_or_key)
        elif entity_type == "milestone":
            from turbo.core.models.milestone import Milestone

            stmt = select(Milestone.id).where(Milestone.milestone_key == id_or_key)
        elif entity_type == "initiative":
            from turbo.core.models.initiative import Initiative

            stmt = select(Initiative.id).where(Initiative.initiative_key == id_or_key)
        elif entity_type == "document":
            from turbo.core.models.document import Document

            stmt = select(Document.id).where(Document.document_key == id_or_key)
        else:
            return None

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
