"""Action Approval Repository"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.action_approval import ActionApproval, ActionStatus, ActionRiskLevel
from turbo.core.schemas.action_approval import ActionApprovalCreate, ActionApprovalUpdate


class ActionApprovalRepository:
    """Repository for action approval operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = ActionApproval

    async def create(self, data: dict) -> ActionApproval:
        """Create a new action approval."""
        approval = ActionApproval(**data)
        self.session.add(approval)
        await self.session.commit()
        await self.session.refresh(approval)
        return approval

    async def get(self, approval_id: UUID) -> Optional[ActionApproval]:
        """Get an action approval by ID."""
        query = select(ActionApproval).where(ActionApproval.id == approval_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, approval_id: UUID, data: dict) -> Optional[ActionApproval]:
        """Update an action approval."""
        approval = await self.get(approval_id)
        if not approval:
            return None

        for key, value in data.items():
            if hasattr(approval, key):
                setattr(approval, key, value)

        await self.session.commit()
        await self.session.refresh(approval)
        return approval

    async def delete(self, approval_id: UUID) -> bool:
        """Delete an action approval."""
        approval = await self.get(approval_id)
        if not approval:
            return False

        await self.session.delete(approval)
        await self.session.commit()
        return True

    async def count(self) -> int:
        """Count total action approvals."""
        query = select(func.count(ActionApproval.id))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def count_pending(self) -> int:
        """Count pending action approvals."""
        query = select(func.count(ActionApproval.id)).where(
            ActionApproval.status == ActionStatus.PENDING
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_pending_approvals(
        self,
        limit: int = 100,
        offset: int = 0,
        entity_type: Optional[str] = None,
        risk_level: Optional[ActionRiskLevel] = None
    ) -> List[ActionApproval]:
        """
        Get pending action approvals.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            entity_type: Filter by entity type
            risk_level: Filter by risk level

        Returns:
            List of pending approvals
        """
        query = select(ActionApproval).where(ActionApproval.status == ActionStatus.PENDING)

        if entity_type:
            query = query.where(ActionApproval.entity_type == entity_type)

        if risk_level:
            query = query.where(ActionApproval.risk_level == risk_level)

        query = query.order_by(ActionApproval.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        status: Optional[ActionStatus] = None
    ) -> List[ActionApproval]:
        """
        Get action approvals for a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: UUID of entity
            status: Optional status filter

        Returns:
            List of action approvals
        """
        query = select(ActionApproval).where(
            and_(
                ActionApproval.entity_type == entity_type,
                ActionApproval.entity_id == entity_id
            )
        )

        if status:
            query = query.where(ActionApproval.status == status)

        query = query.order_by(ActionApproval.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: ActionStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActionApproval]:
        """
        Get action approvals by status.

        Args:
            status: Status to filter by
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of action approvals
        """
        query = (
            select(ActionApproval)
            .where(ActionApproval.status == status)
            .order_by(ActionApproval.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expired_pending(self) -> List[ActionApproval]:
        """
        Get expired pending approvals.

        Returns:
            List of expired pending approvals
        """
        now = datetime.utcnow()
        query = select(ActionApproval).where(
            and_(
                ActionApproval.status == ActionStatus.PENDING,
                ActionApproval.expires_at.isnot(None),
                ActionApproval.expires_at < now
            )
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_counts_by_status(self) -> dict:
        """
        Get counts of approvals by status.

        Returns:
            Dictionary of status counts
        """
        query = select(
            ActionApproval.status,
            func.count(ActionApproval.id)
        ).group_by(ActionApproval.status)

        result = await self.session.execute(query)
        counts = {status.value: count for status, count in result.all()}

        # Ensure all statuses are present
        for status in ActionStatus:
            if status.value not in counts:
                counts[status.value] = 0

        return counts

    async def approve(
        self,
        approval_id: UUID,
        approved_by: str
    ) -> Optional[ActionApproval]:
        """
        Approve an action.

        Args:
            approval_id: UUID of the approval
            approved_by: User who approved

        Returns:
            Updated approval or None if not found
        """
        approval = await self.get(approval_id)
        if not approval:
            return None

        approval.status = ActionStatus.APPROVED
        approval.approved_at = datetime.utcnow()
        approval.approved_by = approved_by
        approval.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(approval)

        return approval

    async def deny(
        self,
        approval_id: UUID,
        denied_by: str,
        denial_reason: Optional[str] = None
    ) -> Optional[ActionApproval]:
        """
        Deny an action.

        Args:
            approval_id: UUID of the approval
            denied_by: User who denied
            denial_reason: Reason for denial

        Returns:
            Updated approval or None if not found
        """
        approval = await self.get(approval_id)
        if not approval:
            return None

        approval.status = ActionStatus.DENIED
        approval.denied_at = datetime.utcnow()
        approval.denied_by = denied_by
        approval.denial_reason = denial_reason
        approval.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(approval)

        return approval

    async def mark_executed(
        self,
        approval_id: UUID,
        execution_result: Optional[dict] = None,
        execution_error: Optional[str] = None,
        executed_by_subagent: bool = False,
        subagent_name: Optional[str] = None
    ) -> Optional[ActionApproval]:
        """
        Mark an action as executed.

        Args:
            approval_id: UUID of the approval
            execution_result: Result data
            execution_error: Error message if failed
            executed_by_subagent: Whether a subagent executed it
            subagent_name: Name of subagent if used

        Returns:
            Updated approval or None if not found
        """
        approval = await self.get(approval_id)
        if not approval:
            return None

        if execution_error:
            approval.status = ActionStatus.FAILED
            approval.execution_error = execution_error
        else:
            approval.status = ActionStatus.EXECUTED
            approval.execution_result = execution_result

        approval.executed_at = datetime.utcnow()
        approval.executed_by_subagent = executed_by_subagent
        approval.subagent_name = subagent_name
        approval.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(approval)

        return approval
