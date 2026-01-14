"""Repository for managing issue dependencies."""

from datetime import datetime, timezone
from typing import Dict, List
from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.associations import issue_dependencies


class IssueDependencyRepository:
    """Repository for issue dependency operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create_dependency(
        self,
        blocking_issue_id: UUID,
        blocked_issue_id: UUID,
        dependency_type: str = "blocks",
    ) -> Dict:
        """Create a new issue dependency.

        Args:
            blocking_issue_id: ID of the blocking issue
            blocked_issue_id: ID of the blocked issue
            dependency_type: Type of dependency (default: "blocks")

        Returns:
            Created dependency as a dictionary

        Raises:
            ValueError: If creating this dependency would create a circular dependency
        """
        # Check for circular dependencies before creating
        if await self._would_create_cycle(blocking_issue_id, blocked_issue_id):
            raise ValueError(
                f"Cannot create dependency: would create circular dependency between "
                f"{blocking_issue_id} and {blocked_issue_id}"
            )

        stmt = insert(issue_dependencies).values(
            blocking_issue_id=blocking_issue_id,
            blocked_issue_id=blocked_issue_id,
            dependency_type=dependency_type,
            created_at=datetime.now(timezone.utc),
        )
        await self.session.execute(stmt)
        await self.session.flush()

        return {
            "blocking_issue_id": blocking_issue_id,
            "blocked_issue_id": blocked_issue_id,
            "dependency_type": dependency_type,
            "created_at": datetime.now(timezone.utc),
        }

    async def delete_dependency(
        self, blocking_issue_id: UUID, blocked_issue_id: UUID
    ) -> bool:
        """Delete an issue dependency.

        Args:
            blocking_issue_id: ID of the blocking issue
            blocked_issue_id: ID of the blocked issue

        Returns:
            True if dependency was deleted, False if not found
        """
        stmt = delete(issue_dependencies).where(
            issue_dependencies.c.blocking_issue_id == blocking_issue_id,
            issue_dependencies.c.blocked_issue_id == blocked_issue_id,
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_blocking_issues(self, issue_id: UUID) -> List[UUID]:
        """Get all issues that block the given issue.

        Args:
            issue_id: ID of the blocked issue

        Returns:
            List of UUIDs of issues that block this one
        """
        stmt = select(issue_dependencies.c.blocking_issue_id).where(
            issue_dependencies.c.blocked_issue_id == issue_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_blocked_issues(self, issue_id: UUID) -> List[UUID]:
        """Get all issues that are blocked by the given issue.

        Args:
            issue_id: ID of the blocking issue

        Returns:
            List of UUIDs of issues that are blocked by this one
        """
        stmt = select(issue_dependencies.c.blocked_issue_id).where(
            issue_dependencies.c.blocking_issue_id == issue_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_dependencies(self, issue_id: UUID) -> dict:
        """Get all dependencies for an issue (both blocking and blocked by).

        Args:
            issue_id: ID of the issue

        Returns:
            Dictionary with 'blocking' and 'blocked_by' lists
        """
        blocking = await self.get_blocking_issues(issue_id)
        blocked_by = await self.get_blocked_issues(issue_id)

        return {
            "blocking": blocking,  # Already UUIDs
            "blocked_by": blocked_by,  # Already UUIDs
        }

    async def _would_create_cycle(
        self, blocking_issue_id: UUID, blocked_issue_id: UUID
    ) -> bool:
        """Check if adding this dependency would create a circular dependency.

        Uses depth-first search to detect cycles.

        Args:
            blocking_issue_id: ID of the blocking issue
            blocked_issue_id: ID of the blocked issue

        Returns:
            True if adding this dependency would create a cycle, False otherwise
        """
        # If blocked_issue already blocks blocking_issue (directly or indirectly),
        # then adding this dependency would create a cycle
        visited = set()
        return await self._has_path(blocked_issue_id, blocking_issue_id, visited)

    async def _has_path(
        self, from_issue: UUID, to_issue: UUID, visited: set
    ) -> bool:
        """Check if there's a dependency path from from_issue to to_issue.

        Args:
            from_issue: Starting issue ID
            to_issue: Target issue ID
            visited: Set of visited issue IDs (to prevent infinite loops)

        Returns:
            True if there's a path, False otherwise
        """
        if from_issue == to_issue:
            return True

        if from_issue in visited:
            return False

        visited.add(from_issue)

        # Get all issues blocked by from_issue
        blocked_by_from = await self.get_blocked_issues(from_issue)

        # Recursively check if any of them lead to to_issue
        for blocked_issue_id in blocked_by_from:
            if await self._has_path(blocked_issue_id, to_issue, visited):
                return True

        return False

    async def get_dependency_chain(self, issue_id: UUID) -> List[UUID]:
        """Get the full dependency chain for an issue.

        Returns all issues that must be completed before this issue can start,
        in topological order.

        Args:
            issue_id: ID of the issue

        Returns:
            List of issue IDs in dependency order
        """
        chain = []
        visited = set()
        await self._build_chain(issue_id, chain, visited)
        return chain

    async def _build_chain(
        self, issue_id: UUID, chain: List[UUID], visited: set
    ) -> None:
        """Recursively build the dependency chain.

        Args:
            issue_id: Current issue ID
            chain: List to append dependencies to
            visited: Set of visited issue IDs
        """
        if issue_id in visited:
            return

        visited.add(issue_id)

        # Get all blocking issues
        blocking = await self.get_blocking_issues(issue_id)

        # Recursively add their dependencies first
        for blocking_issue_id in blocking:
            await self._build_chain(blocking_issue_id, chain, visited)

        # Then add this issue
        if issue_id not in chain:
            chain.append(issue_id)