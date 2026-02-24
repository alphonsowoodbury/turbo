"""SDK-native tools for Turbo operations.

Uses @tool decorator and create_sdk_mcp_server() to expose
Turbo's core operations as in-process tools for the Claude Agent SDK.

Each tool validates input with Pydantic, calls the Turbo API via the
pooled HTTP client, and returns error messages that guide the agent
toward corrective action.
"""

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field
from claude_agent_sdk import create_sdk_mcp_server, tool

from turbo.agent.http import TurboAPIError, get_http_client

logger = logging.getLogger("turbo.agent.tools")


# --- Response Formatting ---


def _text(content: Any) -> dict[str, Any]:
    """Wrap content in MCP tool response format."""
    text = json.dumps(content, indent=2) if isinstance(content, (dict, list)) else str(content)
    return {"content": [{"type": "text", "text": text}]}


def _error(message: str) -> dict[str, Any]:
    """Return a tool error response that teaches the agent what to do."""
    return {"content": [{"type": "text", "text": message}], "isError": True}


async def _safe_call(coro: Any, fallback_hint: str = "") -> dict[str, Any]:
    """Execute a tool coroutine with structured error handling."""
    try:
        result = await coro
        return _text(result)
    except TurboAPIError as exc:
        logger.warning("Tool API error: %s", exc)
        return _error(exc.agent_message())
    except Exception as exc:
        logger.error("Unexpected tool error: %s", exc, exc_info=True)
        msg = f"Error: Unexpected failure. {fallback_hint}" if fallback_hint else f"Error: {exc}"
        return _error(msg)


# --- Input Models ---


class ListProjectsInput(BaseModel):
    status: str | None = Field(None, description="Filter by project status")
    limit: int | None = Field(None, ge=1, le=100, description="Max results")


class ProjectIdInput(BaseModel):
    project_id: str = Field(..., min_length=1, description="UUID of the project")


class ProjectIssuesInput(BaseModel):
    project_id: str = Field(..., min_length=1, description="UUID of the project")
    status: str | None = Field(None, description="Filter by issue status")


class ListIssuesInput(BaseModel):
    status: str | None = Field(None, description="Filter by status")
    priority: str | None = Field(None, description="Filter by priority")
    project_id: str | None = Field(None, description="Filter by project UUID")
    limit: int | None = Field(None, ge=1, le=100, description="Max results")


class IssueIdInput(BaseModel):
    issue_id: str = Field(..., min_length=1, description="UUID or key (e.g. TURBO-1)")


class CreateIssueInput(BaseModel):
    project_id: str = Field(..., min_length=1, description="UUID of the project")
    title: str = Field(..., min_length=1, max_length=500, description="Issue title")
    description: str | None = Field(None, description="Detailed description")
    type: Literal["task", "bug", "feature", "improvement"] | None = Field(
        None, description="Issue type"
    )
    priority: Literal["critical", "high", "medium", "low"] | None = Field(
        None, description="Priority level"
    )


class UpdateIssueInput(BaseModel):
    issue_id: str = Field(..., min_length=1, description="UUID of the issue")
    status: str | None = Field(None, description="New status")
    priority: str | None = Field(None, description="New priority")
    title: str | None = Field(None, max_length=500, description="New title")
    description: str | None = Field(None, description="New description")


class OptionalProjectInput(BaseModel):
    project_id: str | None = Field(None, description="UUID of the project")


class LogWorkInput(BaseModel):
    issue_id: str = Field(..., min_length=1, description="UUID of the issue")
    summary: str = Field(..., min_length=1, description="Summary of work done")
    hours: float | None = Field(None, ge=0, description="Hours spent")


class StatusFilterInput(BaseModel):
    status: str | None = Field(None, description="Filter by status")


class CreateDecisionInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Decision title")
    description: str = Field(..., min_length=1, description="What was decided")
    decision_type: Literal["strategic", "tactical"] | None = Field(
        None, description="Decision category"
    )
    rationale: str | None = Field(None, description="Why this decision was made")


class AddCommentInput(BaseModel):
    entity_type: Literal["issue", "project", "initiative", "decision"] = Field(
        ..., description="Type of entity to comment on"
    )
    entity_id: str = Field(..., min_length=1, description="UUID of the entity")
    content: str = Field(..., min_length=1, description="Comment text")


# --- Validation Helper ---


def _validate(model_cls: type[BaseModel], args: dict[str, Any]) -> tuple[BaseModel | None, dict[str, Any] | None]:
    """Validate tool args against a Pydantic model.

    Returns (validated_model, None) on success, or (None, error_response) on failure.
    This pattern avoids exceptions for flow control and keeps tool functions clean.
    """
    try:
        return model_cls(**args), None
    except Exception as exc:
        return None, _error(
            f"Invalid input: {exc}. Check the tool's parameter descriptions and try again."
        )


# --- Project Tools ---


@tool(
    "list_projects",
    "List all projects in Turbo with their status and issue counts",
    ListProjectsInput.model_json_schema(),
)
async def list_projects(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(ListProjectsInput, args)
    if err:
        return err
    params = {k: v for k, v in validated.model_dump(exclude_none=True).items()}
    return await _safe_call(
        get_http_client().get("/projects", params=params),
        fallback_hint="Try: Check that the Turbo API is running.",
    )


@tool(
    "get_project",
    "Get detailed information about a specific project",
    ProjectIdInput.model_json_schema(),
)
async def get_project(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(ProjectIdInput, args)
    if err:
        return err
    return await _safe_call(
        get_http_client().get(f"/projects/{validated.project_id}"),
        fallback_hint="Try: Use list_projects to find valid project IDs.",
    )


@tool(
    "get_project_issues",
    "List all issues for a project, optionally filtered by status",
    ProjectIssuesInput.model_json_schema(),
)
async def get_project_issues(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(ProjectIssuesInput, args)
    if err:
        return err
    params = {}
    if validated.status:
        params["status"] = validated.status
    return await _safe_call(
        get_http_client().get(f"/projects/{validated.project_id}/issues", params=params),
        fallback_hint="Try: Use list_projects to verify the project exists.",
    )


# --- Issue Tools ---


@tool(
    "list_issues",
    "List issues across all projects with optional filtering",
    ListIssuesInput.model_json_schema(),
)
async def list_issues(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(ListIssuesInput, args)
    if err:
        return err
    params = {k: v for k, v in validated.model_dump(exclude_none=True).items()}
    return await _safe_call(get_http_client().get("/issues", params=params))


@tool(
    "get_issue",
    "Get detailed information about a specific issue by ID or key (e.g. TURBO-1)",
    IssueIdInput.model_json_schema(),
)
async def get_issue(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(IssueIdInput, args)
    if err:
        return err
    return await _safe_call(
        get_http_client().get(f"/issues/{validated.issue_id}"),
        fallback_hint="Try: Use list_issues to find valid issue IDs or keys.",
    )


@tool(
    "create_issue",
    "Create a new issue in a project",
    CreateIssueInput.model_json_schema(),
)
async def create_issue(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(CreateIssueInput, args)
    if err:
        return err
    return await _safe_call(
        get_http_client().post("/issues", validated.model_dump(exclude_none=True)),
        fallback_hint="Try: Use list_projects to verify the project_id.",
    )


@tool(
    "update_issue",
    "Update an existing issue's status, priority, title, or description",
    UpdateIssueInput.model_json_schema(),
)
async def update_issue(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(UpdateIssueInput, args)
    if err:
        return err
    issue_id = validated.issue_id
    data = validated.model_dump(exclude_none=True, exclude={"issue_id"})
    return await _safe_call(
        get_http_client().patch(f"/issues/{issue_id}", data),
        fallback_hint="Try: Use get_issue to check current issue state.",
    )


@tool(
    "start_issue_work",
    "Claim an issue and mark it as in_progress",
    IssueIdInput.model_json_schema(),
)
async def start_issue_work(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(IssueIdInput, args)
    if err:
        return err
    return await _safe_call(
        get_http_client().post(f"/issues/{validated.issue_id}/work", {}),
        fallback_hint="Try: Use get_issue to check the issue's current status.",
    )


# --- Work Queue Tools ---


@tool(
    "get_work_queue",
    "Get the prioritized work queue for a project",
    OptionalProjectInput.model_json_schema(),
)
async def get_work_queue(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(OptionalProjectInput, args)
    if err:
        return err
    params: dict[str, Any] = {"status": "queued"}
    if validated.project_id:
        params["project_id"] = validated.project_id
    return await _safe_call(get_http_client().get("/issues", params=params))


@tool(
    "get_next_issue",
    "Get the highest priority issue ready to work on",
    OptionalProjectInput.model_json_schema(),
)
async def get_next_issue(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(OptionalProjectInput, args)
    if err:
        return err
    params: dict[str, Any] = {"status": "ready", "limit": 1}
    if validated.project_id:
        params["project_id"] = validated.project_id
    return await _safe_call(get_http_client().get("/issues", params=params))


# --- Work Log Tools ---


@tool(
    "log_work",
    "Log a work session or progress update on an issue",
    LogWorkInput.model_json_schema(),
)
async def log_work(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(LogWorkInput, args)
    if err:
        return err
    return await _safe_call(
        get_http_client().post(
            f"/issues/{validated.issue_id}/work-logs",
            validated.model_dump(exclude_none=True),
        ),
        fallback_hint="Try: Use get_issue to verify the issue exists.",
    )


# --- Initiative Tools ---


@tool(
    "list_initiatives",
    "List all initiatives with their status and linked issues",
    StatusFilterInput.model_json_schema(),
)
async def list_initiatives(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(StatusFilterInput, args)
    if err:
        return err
    params = {k: v for k, v in validated.model_dump(exclude_none=True).items()}
    return await _safe_call(get_http_client().get("/initiatives", params=params))


# --- Decision Tools ---


@tool(
    "list_decisions",
    "List strategic decisions",
    StatusFilterInput.model_json_schema(),
)
async def list_decisions(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(StatusFilterInput, args)
    if err:
        return err
    params = {k: v for k, v in validated.model_dump(exclude_none=True).items()}
    return await _safe_call(get_http_client().get("/decisions", params=params))


@tool(
    "create_decision",
    "Record a strategic or tactical decision",
    CreateDecisionInput.model_json_schema(),
)
async def create_decision(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(CreateDecisionInput, args)
    if err:
        return err
    return await _safe_call(
        get_http_client().post("/decisions", validated.model_dump(exclude_none=True))
    )


# --- Comment Tools ---


@tool(
    "add_comment",
    "Add a comment to an issue or other entity",
    AddCommentInput.model_json_schema(),
)
async def add_comment(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(AddCommentInput, args)
    if err:
        return err
    return await _safe_call(
        get_http_client().post("/comments", validated.model_dump(exclude_none=True))
    )


# --- Status Summary Tool ---


@tool(
    "project_status_summary",
    "Get a high-level status summary of a project: open issues, blockers, recent activity",
    ProjectIdInput.model_json_schema(),
)
async def project_status_summary(args: dict[str, Any]) -> dict[str, Any]:
    validated, err = _validate(ProjectIdInput, args)
    if err:
        return err
    client = get_http_client()

    try:
        project = await client.get(f"/projects/{validated.project_id}")
        issues = await client.get(
            f"/projects/{validated.project_id}/issues",
            params={"limit": 100},
        )
    except TurboAPIError as exc:
        return _error(exc.agent_message())

    issue_list = issues if isinstance(issues, list) else issues.get("items", [])
    by_status: dict[str, int] = {}
    blockers: list[dict[str, Any]] = []

    for issue in issue_list:
        status = issue.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        if issue.get("priority") in ("critical", "high") and status not in (
            "closed",
            "done",
        ):
            blockers.append(
                {
                    "key": issue.get("issue_key"),
                    "title": issue.get("title"),
                    "priority": issue.get("priority"),
                    "status": status,
                }
            )

    return _text(
        {
            "project": project.get("name"),
            "total_issues": len(issue_list),
            "by_status": by_status,
            "high_priority_open": blockers,
        }
    )


# --- Server Factory ---

ALL_TOOLS = [
    list_projects,
    get_project,
    get_project_issues,
    list_issues,
    get_issue,
    create_issue,
    update_issue,
    start_issue_work,
    get_work_queue,
    get_next_issue,
    log_work,
    list_initiatives,
    list_decisions,
    create_decision,
    add_comment,
    project_status_summary,
]

# Tool name registry for validation and hook use
TOOL_NAMES = [
    "list_projects",
    "get_project",
    "get_project_issues",
    "list_issues",
    "get_issue",
    "create_issue",
    "update_issue",
    "start_issue_work",
    "get_work_queue",
    "get_next_issue",
    "log_work",
    "list_initiatives",
    "list_decisions",
    "create_decision",
    "add_comment",
    "project_status_summary",
]

# Tools that can modify data (write tools)
WRITE_TOOLS = {
    "create_issue",
    "update_issue",
    "start_issue_work",
    "log_work",
    "create_decision",
    "add_comment",
}

# Tools that only read data
READ_TOOLS = set(TOOL_NAMES) - WRITE_TOOLS


def create_turbo_tools_server() -> Any:
    """Create an in-process SDK MCP server with Turbo's core tools.

    Returns an SDK MCP server that can be passed to ClaudeAgentOptions.mcp_servers.
    """
    return create_sdk_mcp_server(
        name="turbo",
        version="1.0.0",
        tools=ALL_TOOLS,
    )
