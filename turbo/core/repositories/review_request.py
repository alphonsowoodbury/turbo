"""Review request repository for data access operations."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.review_request import ReviewRequest
from turbo.core.repositories.base import BaseRepository


class ReviewRequestRepository(BaseRepository[ReviewRequest, dict, dict]):
    """Repository for ReviewRequest model with custom query methods."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ReviewRequest)

    async def get_pending_for_user(self) -> list[ReviewRequest]:
        """
        Get all pending review requests for the user (My Queue).

        Returns:
            List of pending review requests ordered by creation date (newest first)
        """
        stmt = (
            select(ReviewRequest)
            .where(ReviewRequest.status == "pending")
            .order_by(ReviewRequest.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_entity(
        self, entity_type: str, entity_id: UUID
    ) -> list[ReviewRequest]:
        """
        Get all review requests for a specific entity.

        Args:
            entity_type: Type of entity (issue, initiative, milestone, project)
            entity_id: UUID of the entity

        Returns:
            List of review requests for this entity
        """
        stmt = (
            select(ReviewRequest)
            .where(
                ReviewRequest.entity_type == entity_type,
                ReviewRequest.entity_id == entity_id,
            )
            .order_by(ReviewRequest.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_staff(
        self, staff_id: UUID, status: Optional[str] = None
    ) -> list[ReviewRequest]:
        """
        Get all review requests created by a specific staff member.

        Args:
            staff_id: UUID of the staff member
            status: Optional filter by status (pending, reviewed, dismissed)

        Returns:
            List of review requests from this staff member
        """
        stmt = select(ReviewRequest).where(ReviewRequest.staff_id == staff_id)

        if status:
            stmt = stmt.where(ReviewRequest.status == status)

        stmt = stmt.order_by(ReviewRequest.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_request_type(
        self, request_type: str, status: Optional[str] = None
    ) -> list[ReviewRequest]:
        """
        Get review requests by type.

        Args:
            request_type: Type of request (scope_validation, feedback, approval, etc.)
            status: Optional filter by status

        Returns:
            List of review requests of this type
        """
        stmt = select(ReviewRequest).where(ReviewRequest.request_type == request_type)

        if status:
            stmt = stmt.where(ReviewRequest.status == status)

        stmt = stmt.order_by(ReviewRequest.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_reviewed(self, review_request_id: UUID) -> Optional[ReviewRequest]:
        """
        Mark a review request as reviewed.

        Args:
            review_request_id: UUID of the review request

        Returns:
            Updated review request or None if not found
        """
        stmt = (
            update(ReviewRequest)
            .where(ReviewRequest.id == review_request_id)
            .values(status="reviewed", reviewed_at=datetime.utcnow())
            .returning(ReviewRequest)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one_or_none()

    async def mark_dismissed(self, review_request_id: UUID) -> Optional[ReviewRequest]:
        """
        Mark a review request as dismissed.

        Args:
            review_request_id: UUID of the review request

        Returns:
            Updated review request or None if not found
        """
        stmt = (
            update(ReviewRequest)
            .where(ReviewRequest.id == review_request_id)
            .values(status="dismissed", reviewed_at=datetime.utcnow())
            .returning(ReviewRequest)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one_or_none()

    async def count_pending(self) -> int:
        """
        Count total pending review requests.

        Returns:
            Number of pending review requests
        """
        stmt = select(ReviewRequest).where(ReviewRequest.status == "pending")
        result = await self._session.execute(stmt)
        return len(list(result.scalars().all()))

    async def get_pending_by_type_counts(self) -> dict[str, int]:
        """
        Get count of pending review requests grouped by type.

        Returns:
            Dictionary mapping request_type to count
        """
        stmt = select(ReviewRequest).where(ReviewRequest.status == "pending")
        result = await self._session.execute(stmt)
        requests = list(result.scalars().all())

        counts: dict[str, int] = {}
        for req in requests:
            counts[req.request_type] = counts.get(req.request_type, 0) + 1

        return counts
