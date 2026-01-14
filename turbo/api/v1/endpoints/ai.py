"""AI execution endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import (
    get_db_session,
    get_issue_service,
    get_project_service,
    get_initiative_service,
    get_milestone_service,
)
from turbo.core.services.ai_executor import AIExecutorService
from turbo.core.services.issue import IssueService
from turbo.core.services.project import ProjectService
from turbo.core.services.initiative import InitiativeService
from turbo.core.services.milestone import MilestoneService

router = APIRouter()


class AIExecuteRequest(BaseModel):
    """Request to execute an AI task."""

    request: str = Field(..., description="Natural language request")
    context: dict[str, Any] | None = Field(None, description="Optional context (project_id, etc)")
    model: str | None = Field(None, description="Model to use (e.g., 'qwen2.5:14b', 'llama3.1:8b')")


class AIExecuteResponse(BaseModel):
    """Response from AI execution."""

    success: bool
    response: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


@router.post("/execute", response_model=AIExecuteResponse)
async def execute_ai_request(
    data: AIExecuteRequest,
    session: AsyncSession = Depends(get_db_session),
    issue_service: IssueService = Depends(get_issue_service),
    project_service: ProjectService = Depends(get_project_service),
    initiative_service: InitiativeService = Depends(get_initiative_service),
    milestone_service: MilestoneService = Depends(get_milestone_service),
) -> AIExecuteResponse:
    """
    Execute an AI-powered request.

    This endpoint accepts natural language requests and uses an LLM
    to execute them via tool calling.

    Example requests:
    - "Create a high priority bug for authentication issues"
    - "List all open issues in the project"
    - "Update issue #123 to in_progress"
    - "Show me all critical bugs"
    """
    try:
        ai_service = AIExecutorService(
            session=session,
            issue_service=issue_service,
            project_service=project_service,
            initiative_service=initiative_service,
            milestone_service=milestone_service,
        )

        result = await ai_service.execute(data.request, data.context, data.model)

        return AIExecuteResponse(
            success=result["success"],
            response=result.get("response", ""),
            tool_calls=result.get("tool_calls", []),
            error=result.get("error")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models(
    session: AsyncSession = Depends(get_db_session),
    issue_service: IssueService = Depends(get_issue_service),
    project_service: ProjectService = Depends(get_project_service),
    initiative_service: InitiativeService = Depends(get_initiative_service),
    milestone_service: MilestoneService = Depends(get_milestone_service),
) -> dict[str, Any]:
    """
    List all available LLM models.

    Returns a list of models that can be used with the /execute endpoint.
    """
    ai_service = AIExecutorService(
        session=session,
        issue_service=issue_service,
        project_service=project_service,
        initiative_service=initiative_service,
        milestone_service=milestone_service,
    )

    models = ai_service.list_available_models()
    return {
        "models": models,
        "default": "qwen2.5:7b"
    }


@router.get("/health")
async def ai_health_check() -> dict[str, str]:
    """Check if AI service is available."""
    import ollama
    from turbo.utils.config import get_settings

    settings = get_settings()
    try:
        client = ollama.Client(host=settings.llm.base_url)
        # Try to list models
        client.list()
        return {"status": "healthy", "service": "ollama"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
