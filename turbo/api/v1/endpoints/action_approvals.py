"""
Action Approval API Endpoints

Manage AI action approval queue with human-in-the-loop control.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.models.action_approval import ActionStatus, ActionRiskLevel
from turbo.core.repositories.action_approval_repository import ActionApprovalRepository
from turbo.core.schemas.action_approval import (
    ActionApprovalCreate,
    ActionApprovalResponse,
    ActionApprovalListResponse,
    ApproveActionRequest,
    DenyActionRequest,
)
from turbo.core.services.action_executor import ActionExecutor

router = APIRouter(prefix="/action-approvals", tags=["action-approvals"])


@router.post("/", response_model=ActionApprovalResponse, status_code=201)
async def create_action_approval(
    data: ActionApprovalCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new action approval request.

    This is typically called by the AI system when it wants to perform an action.
    """
    repo = ActionApprovalRepository(db)

    approval = await repo.create({
        **data.model_dump(),
        "status": ActionStatus.PENDING,
    })

    # If auto_execute is True and it's a safe action, execute immediately
    if data.auto_execute and data.risk_level in [ActionRiskLevel.SAFE, ActionRiskLevel.LOW]:
        executor = ActionExecutor(db)
        try:
            result = await executor.execute_action(approval.id)
            if result.get("success"):
                approval = await repo.mark_executed(
                    approval.id,
                    execution_result=result,
                    executed_by_subagent=result.get("used_subagent", False),
                    subagent_name=result.get("subagent_name")
                )
                approval.status = ActionStatus.AUTO_EXECUTED
                approval.auto_executed_at = approval.executed_at
                await db.commit()
        except Exception as e:
            await repo.mark_executed(
                approval.id,
                execution_error=str(e)
            )

    return ActionApprovalResponse.model_validate(approval)


@router.get("/", response_model=ActionApprovalListResponse)
async def list_action_approvals(
    status: Optional[ActionStatus] = Query(None, description="Filter by status"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    risk_level: Optional[ActionRiskLevel] = Query(None, description="Filter by risk level"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List action approvals with filters.

    By default, returns pending approvals. Use status filter to get others.
    """
    repo = ActionApprovalRepository(db)

    if status:
        approvals = await repo.get_by_status(status, limit=limit, offset=offset)
    else:
        approvals = await repo.get_pending_approvals(
            limit=limit,
            offset=offset,
            entity_type=entity_type,
            risk_level=risk_level
        )

    # Get counts
    counts = await repo.get_counts_by_status()

    # Get total count
    total_count = await repo.count()

    return ActionApprovalListResponse(
        approvals=[ActionApprovalResponse.model_validate(a) for a in approvals],
        total=total_count,
        pending_count=counts.get(ActionStatus.PENDING.value, 0),
        approved_count=counts.get(ActionStatus.APPROVED.value, 0),
        denied_count=counts.get(ActionStatus.DENIED.value, 0),
        executed_count=counts.get(ActionStatus.EXECUTED.value, 0) + counts.get(ActionStatus.AUTO_EXECUTED.value, 0),
    )


@router.get("/pending", response_model=ActionApprovalListResponse)
async def get_pending_approvals(
    entity_type: Optional[str] = Query(None),
    risk_level: Optional[ActionRiskLevel] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get pending action approvals (shortcut endpoint).

    This is the primary endpoint for the approval queue UI.
    """
    repo = ActionApprovalRepository(db)

    approvals = await repo.get_pending_approvals(
        limit=limit,
        offset=offset,
        entity_type=entity_type,
        risk_level=risk_level
    )

    counts = await repo.get_counts_by_status()
    total_count = await repo.count()

    return ActionApprovalListResponse(
        approvals=[ActionApprovalResponse.model_validate(a) for a in approvals],
        total=total_count,
        pending_count=counts.get(ActionStatus.PENDING.value, 0),
        approved_count=counts.get(ActionStatus.APPROVED.value, 0),
        denied_count=counts.get(ActionStatus.DENIED.value, 0),
        executed_count=counts.get(ActionStatus.EXECUTED.value, 0) + counts.get(ActionStatus.AUTO_EXECUTED.value, 0),
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[ActionApprovalResponse])
async def get_entity_approvals(
    entity_type: str,
    entity_id: UUID,
    status: Optional[ActionStatus] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get action approvals for a specific entity.

    Useful for showing approval history on issue/project pages.
    """
    repo = ActionApprovalRepository(db)

    approvals = await repo.get_by_entity(entity_type, entity_id, status=status)

    return [ActionApprovalResponse.model_validate(a) for a in approvals]


@router.get("/{approval_id}", response_model=ActionApprovalResponse)
async def get_action_approval(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific action approval by ID."""
    repo = ActionApprovalRepository(db)

    approval = await repo.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Action approval not found")

    return ActionApprovalResponse.model_validate(approval)


@router.post("/{approval_id}/approve", response_model=ActionApprovalResponse)
async def approve_action(
    approval_id: UUID,
    request: ApproveActionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Approve an action and optionally execute it immediately.

    This is the primary endpoint for the "Approve" button in the UI.
    """
    repo = ActionApprovalRepository(db)

    # Check approval exists and is pending
    approval = await repo.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Action approval not found")

    if approval.status != ActionStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Action is already {approval.status.value}")

    # Approve
    approval = await repo.approve(approval_id, request.approved_by)

    # Execute if requested
    if request.execute_immediately:
        executor = ActionExecutor(db)
        try:
            result = await executor.execute_action(approval_id)
            if result.get("success"):
                approval = await repo.mark_executed(
                    approval_id,
                    execution_result=result,
                    executed_by_subagent=result.get("used_subagent", False),
                    subagent_name=result.get("subagent_name")
                )
            else:
                approval = await repo.mark_executed(
                    approval_id,
                    execution_error=result.get("error", "Unknown error")
                )
        except Exception as e:
            approval = await repo.mark_executed(
                approval_id,
                execution_error=str(e)
            )

    return ActionApprovalResponse.model_validate(approval)


@router.post("/{approval_id}/deny", response_model=ActionApprovalResponse)
async def deny_action(
    approval_id: UUID,
    request: DenyActionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Deny an action.

    This is the primary endpoint for the "Deny" button in the UI.
    """
    repo = ActionApprovalRepository(db)

    # Check approval exists and is pending
    approval = await repo.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Action approval not found")

    if approval.status != ActionStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Action is already {approval.status.value}")

    # Deny
    approval = await repo.deny(approval_id, request.denied_by, request.denial_reason)

    return ActionApprovalResponse.model_validate(approval)


@router.delete("/{approval_id}")
async def delete_action_approval(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete an action approval (admin only)."""
    repo = ActionApprovalRepository(db)

    approval = await repo.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Action approval not found")

    await repo.delete(approval_id)

    return {"success": True, "message": "Action approval deleted"}
