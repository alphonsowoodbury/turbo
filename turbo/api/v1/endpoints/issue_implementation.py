"""Issue implementation request endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from turbo.api.dependencies import get_issue_service
from turbo.core.services.issue import IssueService
from turbo.utils.exceptions import IssueNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/issues", tags=["issue-implementation"])


class ImplementationRequest(BaseModel):
    """Request for autonomous implementation."""

    notes: str | None = None
    priority_override: str | None = None


class ImplementationResponse(BaseModel):
    """Response from implementation request."""

    success: bool
    message: str
    issue_id: UUID


@router.post("/{issue_id}/request-implementation", response_model=ImplementationResponse)
async def request_implementation(
    issue_id: UUID,
    request: ImplementationRequest | None = None,
    issue_service: IssueService = Depends(get_issue_service),
):
    """
    Request autonomous implementation of an issue via Claude Code.

    This triggers a webhook event that Claude Code listens for.
    The issue can be assigned to staff for management while Claude Code handles implementation.
    """
    try:
        # Verify issue exists
        issue = await issue_service.get_issue_by_id(issue_id)

        # Emit webhook event for implementation request
        if issue_service._webhook_service:
            payload = {
                "issue": issue.model_dump(mode="json"),
                "request_notes": request.notes if request else None,
                "priority_override": request.priority_override if request else None,
            }
            await issue_service._webhook_service.emit_event(
                "issue.implementation_requested",
                payload
            )
            logger.info(f"Emitted implementation request for issue {issue_id}")

        return ImplementationResponse(
            success=True,
            message=f"Implementation requested for issue: {issue.title}",
            issue_id=issue_id
        )

    except IssueNotFoundError:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    except Exception as e:
        logger.error(f"Error requesting implementation for issue {issue_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
