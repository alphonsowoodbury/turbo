"""Tests for Turbo tool functions, input models, and response formatting."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from turbo.agent.http import TurboAPIError
from turbo.agent.tools import (
    ALL_TOOLS,
    TOOL_NAMES,
    WRITE_TOOLS,
    READ_TOOLS,
    AddCommentInput,
    CreateIssueInput,
    ListIssuesInput,
    ListProjectsInput,
    ProjectIdInput,
    UpdateIssueInput,
    _error,
    _safe_call,
    _text,
    _validate,
)


# --- Response Formatting ---


def test_text_formats_dict():
    result = _text({"key": "value"})
    assert result["content"][0]["type"] == "text"
    parsed = json.loads(result["content"][0]["text"])
    assert parsed == {"key": "value"}
    assert "isError" not in result


def test_text_formats_list():
    result = _text([1, 2, 3])
    parsed = json.loads(result["content"][0]["text"])
    assert parsed == [1, 2, 3]


def test_text_formats_string():
    result = _text("hello world")
    assert result["content"][0]["text"] == "hello world"


def test_error_formats_correctly():
    result = _error("something went wrong")
    assert result["isError"] is True
    assert result["content"][0]["text"] == "something went wrong"


# --- _safe_call ---


async def test_safe_call_success():
    coro = AsyncMock(return_value={"data": "ok"})()
    result = await _safe_call(coro)
    assert "isError" not in result
    parsed = json.loads(result["content"][0]["text"])
    assert parsed == {"data": "ok"}


async def test_safe_call_turbo_api_error():
    async def _raise():
        raise TurboAPIError("fail", endpoint="GET /x", status_code=404, body="")

    result = await _safe_call(_raise())
    assert result["isError"] is True
    assert "404" in result["content"][0]["text"]


async def test_safe_call_unexpected_error():
    async def _raise():
        raise RuntimeError("boom")

    result = await _safe_call(_raise(), fallback_hint="Try again")
    assert result["isError"] is True
    assert "Try again" in result["content"][0]["text"]


# --- _validate ---


def test_validate_success():
    model, err = _validate(ListProjectsInput, {"status": "active"})
    assert err is None
    assert model.status == "active"


def test_validate_failure():
    model, err = _validate(CreateIssueInput, {})  # Missing required fields
    assert model is None
    assert err is not None
    assert err["isError"] is True
    assert "Invalid input" in err["content"][0]["text"]


# --- Pydantic Input Models ---


def test_create_issue_input_valid():
    inp = CreateIssueInput(
        project_id="abc-123",
        title="Fix the bug",
        priority="high",
        type="bug",
    )
    assert inp.title == "Fix the bug"
    assert inp.priority == "high"


def test_create_issue_input_missing_required():
    with pytest.raises(ValidationError):
        CreateIssueInput(project_id="abc")  # Missing title


def test_create_issue_input_title_too_long():
    with pytest.raises(ValidationError):
        CreateIssueInput(project_id="abc", title="x" * 501)


def test_create_issue_input_invalid_priority():
    with pytest.raises(ValidationError):
        CreateIssueInput(project_id="abc", title="Ok title", priority="urgent")


def test_list_issues_input_negative_limit():
    with pytest.raises(ValidationError):
        ListIssuesInput(limit=-1)


def test_update_issue_input_no_changes():
    """Just issue_id with no other fields should be valid."""
    inp = UpdateIssueInput(issue_id="abc-123")
    assert inp.issue_id == "abc-123"
    assert inp.status is None


def test_add_comment_input_valid():
    inp = AddCommentInput(
        entity_type="issue",
        entity_id="abc-123",
        content="Looks good!",
    )
    assert inp.entity_type == "issue"


def test_add_comment_input_invalid_entity_type():
    with pytest.raises(ValidationError):
        AddCommentInput(
            entity_type="epic",  # Not in the Literal options
            entity_id="abc-123",
            content="Nope",
        )


def test_project_id_input_empty_fails():
    with pytest.raises(ValidationError):
        ProjectIdInput(project_id="")


# --- Tool Registry ---


def test_tool_names_match_all_tools():
    assert len(TOOL_NAMES) == len(ALL_TOOLS)


def test_write_tools_are_subset():
    assert WRITE_TOOLS.issubset(set(TOOL_NAMES))


def test_read_tools_no_overlap_with_write():
    assert READ_TOOLS & WRITE_TOOLS == set()


def test_read_plus_write_equals_all():
    assert READ_TOOLS | WRITE_TOOLS == set(TOOL_NAMES)


# --- Tool Functions via monkeypatched HTTP client ---


@pytest.fixture
def mock_turbo_client():
    """Create a mock HTTP client that returns canned responses."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value={"items": []})
    mock.post = AsyncMock(return_value={"id": "new-123", "created": True})
    mock.patch = AsyncMock(return_value={"id": "upd-123", "updated": True})
    return mock


@pytest.fixture
def patch_http_client(monkeypatch, mock_turbo_client):
    """Monkeypatch get_http_client to return the mock."""
    monkeypatch.setattr(
        "turbo.agent.tools.get_http_client",
        lambda: mock_turbo_client,
    )
    return mock_turbo_client


async def test_list_projects_no_filters(patch_http_client):
    from turbo.agent.tools import list_projects

    result = await list_projects.handler({})
    assert "isError" not in result
    patch_http_client.get.assert_awaited_once()


async def test_list_projects_with_status(patch_http_client):
    from turbo.agent.tools import list_projects

    result = await list_projects.handler({"status": "active"})
    assert "isError" not in result
    call_args = patch_http_client.get.call_args
    assert call_args[1]["params"]["status"] == "active" or "active" in str(call_args)


async def test_get_project_valid_id(patch_http_client):
    from turbo.agent.tools import get_project

    patch_http_client.get.return_value = {"id": "abc", "name": "Test"}
    result = await get_project.handler({"project_id": "abc-123"})
    assert "isError" not in result


async def test_get_project_empty_id_fails(patch_http_client):
    from turbo.agent.tools import get_project

    result = await get_project.handler({"project_id": ""})
    assert result.get("isError") is True


async def test_create_issue_valid(patch_http_client):
    from turbo.agent.tools import create_issue

    result = await create_issue.handler({
        "project_id": "proj-1",
        "title": "New issue",
        "type": "task",
        "priority": "medium",
    })
    assert "isError" not in result
    patch_http_client.post.assert_awaited_once()


async def test_create_issue_missing_title(patch_http_client):
    from turbo.agent.tools import create_issue

    result = await create_issue.handler({"project_id": "proj-1"})
    assert result.get("isError") is True


async def test_create_issue_invalid_priority(patch_http_client):
    from turbo.agent.tools import create_issue

    result = await create_issue.handler({
        "project_id": "proj-1",
        "title": "Test",
        "priority": "urgent",
    })
    assert result.get("isError") is True


async def test_update_issue_only_status(patch_http_client):
    from turbo.agent.tools import update_issue

    result = await update_issue.handler({"issue_id": "iss-1", "status": "closed"})
    assert "isError" not in result
    patch_http_client.patch.assert_awaited_once()


async def test_project_status_summary(patch_http_client, sample_issues_list):
    from turbo.agent.tools import project_status_summary

    patch_http_client.get.side_effect = [
        {"id": "proj-1", "name": "Test Project"},
        sample_issues_list,
    ]

    result = await project_status_summary.handler({"project_id": "proj-1"})
    assert "isError" not in result
    text = json.loads(result["content"][0]["text"])
    assert text["project"] == "Test Project"
    assert text["total_issues"] == 3
    assert "by_status" in text
    assert len(text["high_priority_open"]) >= 1  # critical + high items


# --- Handler Tests for Remaining Tools ---


async def test_get_project_issues_handler(patch_http_client):
    from turbo.agent.tools import get_project_issues

    result = await get_project_issues.handler({"project_id": "proj-1", "status": "open"})
    assert "isError" not in result
    patch_http_client.get.assert_awaited_once()


async def test_list_issues_handler(patch_http_client):
    from turbo.agent.tools import list_issues

    result = await list_issues.handler({"status": "open"})
    assert "isError" not in result
    patch_http_client.get.assert_awaited_once()


async def test_get_issue_handler(patch_http_client):
    from turbo.agent.tools import get_issue

    patch_http_client.get.return_value = {"id": "iss-1", "title": "Test"}
    result = await get_issue.handler({"issue_id": "iss-1"})
    assert "isError" not in result


async def test_start_issue_work_handler(patch_http_client):
    from turbo.agent.tools import start_issue_work

    result = await start_issue_work.handler({"issue_id": "iss-1"})
    assert "isError" not in result
    patch_http_client.post.assert_awaited_once()


async def test_get_work_queue_handler(patch_http_client):
    from turbo.agent.tools import get_work_queue

    result = await get_work_queue.handler({"project_id": "proj-1"})
    assert "isError" not in result
    patch_http_client.get.assert_awaited_once()


async def test_get_work_queue_no_project(patch_http_client):
    from turbo.agent.tools import get_work_queue

    result = await get_work_queue.handler({})
    assert "isError" not in result
    patch_http_client.get.assert_awaited_once()


async def test_get_next_issue_handler(patch_http_client):
    from turbo.agent.tools import get_next_issue

    result = await get_next_issue.handler({})
    assert "isError" not in result
    patch_http_client.get.assert_awaited_once()


async def test_log_work_handler(patch_http_client):
    from turbo.agent.tools import log_work

    result = await log_work.handler({"issue_id": "iss-1", "summary": "Fixed the bug"})
    assert "isError" not in result
    patch_http_client.post.assert_awaited_once()


async def test_list_initiatives_handler(patch_http_client):
    from turbo.agent.tools import list_initiatives

    result = await list_initiatives.handler({})
    assert "isError" not in result
    patch_http_client.get.assert_awaited_once()


async def test_list_decisions_handler(patch_http_client):
    from turbo.agent.tools import list_decisions

    result = await list_decisions.handler({})
    assert "isError" not in result
    patch_http_client.get.assert_awaited_once()


async def test_create_decision_handler(patch_http_client):
    from turbo.agent.tools import create_decision

    result = await create_decision.handler({"title": "Use PostgreSQL", "description": "We chose PG for reliability"})
    assert "isError" not in result
    patch_http_client.post.assert_awaited_once()


async def test_add_comment_handler(patch_http_client):
    from turbo.agent.tools import add_comment

    result = await add_comment.handler({"entity_type": "issue", "entity_id": "iss-1", "content": "Looks good!"})
    assert "isError" not in result
    patch_http_client.post.assert_awaited_once()


async def test_get_project_issues_no_status(patch_http_client):
    from turbo.agent.tools import get_project_issues

    result = await get_project_issues.handler({"project_id": "proj-1"})
    assert "isError" not in result


async def test_get_next_issue_with_project(patch_http_client):
    from turbo.agent.tools import get_next_issue

    result = await get_next_issue.handler({"project_id": "proj-1"})
    assert "isError" not in result


async def test_list_initiatives_with_status(patch_http_client):
    from turbo.agent.tools import list_initiatives

    result = await list_initiatives.handler({"status": "active"})
    assert "isError" not in result


async def test_list_decisions_with_status(patch_http_client):
    from turbo.agent.tools import list_decisions

    result = await list_decisions.handler({"status": "active"})
    assert "isError" not in result
