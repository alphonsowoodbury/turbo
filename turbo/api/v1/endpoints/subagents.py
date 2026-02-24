"""
Subagent API endpoints.

Allows invoking Turbo AI subagents via the Claude service.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subagents", tags=["subagents"])

# Claude service URL (claude-code container)
CLAUDE_SERVICE_URL = "http://turbo-claude-code:9000"


class SubagentRequest(BaseModel):
    """Request to invoke a subagent."""

    agent: str = Field(..., description="Name of the subagent to invoke")
    prompt: str = Field(..., description="User prompt/request")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Context data for the subagent"
    )
    agent_set: str = Field(
        default="turbo", description="Agent set: 'turbo' or 'turbodev'"
    )


class SubagentAction(BaseModel):
    """Action suggested by the subagent."""

    type: str
    params: Optional[Dict[str, Any]] = None


class SubagentResponse(BaseModel):
    """Response from a subagent."""

    agent: str
    response: str
    actions: Optional[List[SubagentAction]] = None
    error: Optional[str] = None


class Subagent(BaseModel):
    """Subagent metadata."""

    name: str
    description: str
    capabilities: List[str]
    agent_set: str


@router.post("/invoke", response_model=SubagentResponse)
async def invoke_subagent(request: SubagentRequest) -> SubagentResponse:
    """
    Invoke a Turbo AI subagent.

    Args:
        request: Subagent invocation request

    Returns:
        SubagentResponse with the agent's analysis and recommendations
    """
    try:
        # Forward request to Claude service
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{CLAUDE_SERVICE_URL}/api/v1/subagents/invoke",
                json={
                    "agent": request.agent,
                    "prompt": request.prompt,
                    "context": request.context or {},
                    "agent_set": request.agent_set,
                },
            )

            if response.status_code != 200:
                logger.error(
                    "Claude service error: %s - %s", response.status_code, response.text
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Claude service error",
                )

            result = response.json()

            return SubagentResponse(
                agent=request.agent,
                response=result.get("response", ""),
                actions=result.get("actions"),
                error=result.get("error"),
            )

    except httpx.ConnectError:
        logger.error("Failed to connect to Claude service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claude service is unavailable",
        )
    except httpx.TimeoutException:
        logger.error("Claude service request timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Claude service request timed out",
        )
    except Exception:
        logger.exception("Unexpected error invoking subagent")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


class SubagentListResponse(BaseModel):
    """Response containing list of subagents."""

    agent_set: str
    subagents: List[Subagent]


@router.get("/list", response_model=SubagentListResponse)
async def list_subagents(agent_set: str = "turbo") -> SubagentListResponse:
    """
    List available subagents.

    Args:
        agent_set: Filter by agent set ('turbo' or 'turbodev')

    Returns:
        SubagentListResponse with agent_set and list of available subagents
    """
    try:
        # Forward request to Claude service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{CLAUDE_SERVICE_URL}/api/v1/subagents/list", params={"agent_set": agent_set}
            )

            if response.status_code != 200:
                logger.error(
                    "Claude service error: %s - %s", response.status_code, response.text
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Claude service error",
                )

            data = response.json()
            return SubagentListResponse(**data)

    except httpx.ConnectError:
        logger.error("Failed to connect to Claude service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claude service is unavailable",
        )
    except httpx.TimeoutException:
        logger.error("Claude service request timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Claude service request timed out",
        )
    except Exception:
        logger.exception("Unexpected error listing subagents")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
