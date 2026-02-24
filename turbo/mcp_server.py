#!/usr/bin/env python3
"""Turbo MCP Server - Exposes Turbo functionality to Claude Code via Model Context Protocol."""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("turbo")

# Turbo API base URL
TURBO_API_URL = os.getenv("TURBO_API_URL", "http://localhost:8001/api/v1")

# Project-scoped access control (optional)
# Set TURBO_ALLOWED_PROJECT_IDS env var to comma-separated UUIDs to restrict access
ALLOWED_PROJECT_IDS = None
if os.getenv("TURBO_ALLOWED_PROJECT_IDS"):
    ALLOWED_PROJECT_IDS = set(
        pid.strip() for pid in os.getenv("TURBO_ALLOWED_PROJECT_IDS", "").split(",") if pid.strip()
    )


def is_project_allowed(project_id: str) -> bool:
    """Check if project access is allowed based on ALLOWED_PROJECT_IDS."""
    if ALLOWED_PROJECT_IDS is None:
        return True  # No restrictions
    return project_id in ALLOWED_PROJECT_IDS


def filter_projects(projects: list) -> list:
    """Filter projects list to only allowed projects."""
    if ALLOWED_PROJECT_IDS is None:
        return projects
    return [p for p in projects if p.get("id") in ALLOWED_PROJECT_IDS]


def filter_entities_by_project(entities: list, project_id_field: str = "project_id") -> list:
    """Filter entities list to only those in allowed projects."""
    if ALLOWED_PROJECT_IDS is None:
        return entities
    return [e for e in entities if e.get(project_id_field) in ALLOWED_PROJECT_IDS]


# Git Worktree Helper Functions (run locally, not in API container)

def get_git_root(project_path: str) -> Path | None:
    """Find the git repository root for a project."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def sanitize_branch_name(text: str) -> str:
    """Sanitize text for use in git branch names."""
    sanitized = text.lower()
    sanitized = "".join(c if c.isalnum() or c in "-_" else "-" for c in sanitized)
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    sanitized = sanitized.strip("-")
    return sanitized[:50]


def create_worktree_local(issue_key: str, issue_title: str, project_name: str, project_path: str, base_branch: str = "main") -> dict:
    """
    Create a git worktree locally.

    Args:
        issue_key: Issue key (e.g., "TURBOCODE-1")
        issue_title: Issue title for branch name
        project_name: Project name for worktree directory
        project_path: Path to the main project repository
        base_branch: Base branch to create worktree from

    Returns:
        Dictionary with worktree info

    Raises:
        ValueError: If not a git repository or worktree creation fails
    """
    git_root = get_git_root(project_path)
    if not git_root:
        raise ValueError(f"{project_path} is not a git repository")

    # Create branch name: TURBOCODE-1/fix-auth-bug
    sanitized_title = sanitize_branch_name(issue_title)
    branch_name = f"{issue_key}/{sanitized_title}"

    # Create worktree path: ~/worktrees/ProjectName-TURBOCODE-1/
    base_path = Path.home() / "worktrees"
    base_path.mkdir(parents=True, exist_ok=True)

    worktree_name = f"{project_name}-{issue_key}"
    worktree_name = sanitize_branch_name(worktree_name)
    worktree_path = base_path / worktree_name

    if worktree_path.exists():
        raise ValueError(f"Worktree already exists at {worktree_path}")

    # Create the worktree
    try:
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_branch],
            cwd=str(git_root),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to create worktree: {e.stderr}")

    return {
        "worktree_path": str(worktree_path),
        "branch_name": branch_name,
        "issue_key": issue_key,
        "git_root": str(git_root),
    }


def remove_worktree_local(worktree_path: str, force: bool = False) -> bool:
    """
    Remove a git worktree locally.

    Args:
        worktree_path: Path to the worktree directory
        force: Force removal even if there are uncommitted changes

    Returns:
        True if worktree was removed, False if it didn't exist

    Raises:
        ValueError: If removal fails
    """
    path = Path(worktree_path)
    if not path.exists():
        return False

    try:
        cmd = ["git", "worktree", "remove", str(path)]
        if force:
            cmd.append("--force")

        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to remove worktree: {e.stderr}")


def list_worktrees_local(project_path: str) -> list[dict]:
    """List all worktrees for a project locally."""
    git_root = get_git_root(project_path)
    if not git_root:
        raise ValueError(f"{project_path} is not a git repository")

    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(git_root),
            capture_output=True,
            text=True,
            check=True,
        )

        worktrees = []
        current = {}

        for line in result.stdout.strip().split("\n"):
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line.split(" ", 1)[1]}
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1]
            elif line.startswith("HEAD "):
                current["commit"] = line.split(" ", 1)[1]
            elif line == "":
                if current:
                    worktrees.append(current)
                    current = {}

        if current:
            worktrees.append(current)

        return worktrees
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to list worktrees: {e.stderr}")


def get_worktree_status_local(worktree_path: str) -> dict:
    """Get the git status of a worktree locally."""
    path = Path(worktree_path).expanduser()
    if not path.exists():
        raise ValueError(f"Worktree does not exist at {worktree_path}")

    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(path),
            capture_output=True,
            text=True,
            check=True,
        )
        branch = branch_result.stdout.strip()

        # Get status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(path),
            capture_output=True,
            text=True,
            check=True,
        )

        uncommitted = [line for line in status_result.stdout.strip().split("\n") if line]

        return {
            "has_changes": len(uncommitted) > 0,
            "uncommitted_files": len(uncommitted),
            "branch": branch,
            "path": str(path),
        }
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to get worktree status: {e.stderr}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Turbo tools."""
    return [
        # Project Management Tools
        Tool(
            name="list_projects",
            description="Get all projects with optional filtering. Returns project list with id, name, status, priority, completion percentage, and issue counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "on_hold", "completed", "archived"],
                        "description": "Filter projects by status",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of projects to return",
                    },
                },
            },
        ),
        Tool(
            name="get_project",
            description="Get detailed information about a specific project including stats (total issues, open issues, closed issues, completion rate).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "UUID of the project",
                    }
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_project_issues",
            description="Get all issues for a specific project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "UUID of the project",
                    }
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="update_project",
            description="Update a project's details. Only include fields you want to change. Returns the updated project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "UUID of the project to update"},
                    "name": {"type": "string", "description": "Project name"},
                    "description": {"type": "string", "description": "Project description (supports Markdown)"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "on_hold", "completed", "archived"],
                        "description": "Project status",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Priority level",
                    },
                    "completion_percentage": {
                        "type": "number",
                        "description": "Completion percentage (0-100)",
                        "minimum": 0,
                        "maximum": 100,
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="delete_project",
            description="Delete a project permanently. Use with caution as this is irreversible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "UUID of the project to delete",
                    }
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="archive_project",
            description="Archive a project (soft delete). Archived projects can be restored later.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "UUID of the project to archive",
                    }
                },
                "required": ["project_id"],
            },
        ),
        # Issue Management Tools
        Tool(
            name="list_issues",
            description="Get all issues with optional filtering. Can filter by project, status, priority, type, assignee. Returns issue list with all details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Filter by project UUID"},
                    "status": {
                        "type": "string",
                        "enum": ["open", "ready", "in_progress", "review", "testing", "closed"],
                        "description": "Filter by issue status",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by priority level",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["feature", "bug", "task", "enhancement", "documentation", "discovery"],
                        "description": "Filter by issue type",
                    },
                    "assignee": {"type": "string", "description": "Filter by assignee name"},
                    "limit": {"type": "integer", "description": "Maximum number of issues to return"},
                },
            },
        ),
        Tool(
            name="get_issue",
            description="Get detailed information about a specific issue including title, description, status, priority, type, assignee, discovery_status, and timestamps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue",
                    }
                },
                "required": ["issue_id"],
            },
        ),
        Tool(
            name="create_issue",
            description="Create a new issue. Returns the created issue with generated ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Issue title"},
                    "description": {"type": "string", "description": "Issue description (supports Markdown)"},
                    "type": {
                        "type": "string",
                        "enum": ["feature", "bug", "task", "enhancement", "documentation", "discovery"],
                        "description": "Issue type",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "ready", "in_progress", "review", "testing", "closed"],
                        "description": "Issue status (default: open)",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Priority level",
                    },
                    "project_id": {"type": "string", "description": "Project UUID (optional for discovery issues)"},
                    "assignee": {"type": "string", "description": "Assignee name (optional)"},
                    "discovery_status": {
                        "type": "string",
                        "enum": ["proposed", "researching", "findings_ready", "approved", "parked", "declined"],
                        "description": "Discovery status (only for discovery issues)",
                    },
                },
                "required": ["title", "description", "type", "priority"],
            },
        ),
        Tool(
            name="update_issue",
            description="Update an issue's details. Only include fields you want to change. Returns the updated issue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "UUID of the issue to update"},
                    "title": {"type": "string"},
                    "description": {"type": "string", "description": "Updated description (supports Markdown)"},
                    "status": {
                        "type": "string",
                        "enum": ["open", "ready", "in_progress", "review", "testing", "closed"],
                    },
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "type": {
                        "type": "string",
                        "enum": ["feature", "bug", "task", "enhancement", "documentation", "discovery"],
                    },
                    "assignee": {"type": "string", "description": "Assignee name"},
                    "discovery_status": {
                        "type": "string",
                        "enum": ["proposed", "researching", "findings_ready", "approved", "parked", "declined"],
                    },
                },
                "required": ["issue_id"],
            },
        ),
        # Work Queue Tools
        Tool(
            name="get_next_issue",
            description="Get THE next issue to work on. Returns the highest-ranked issue (work_rank=1) that is open or in_progress. Use this when the user asks 'work the next issue' or 'what should I work on next'. Returns null if no ranked issues exist.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_work_queue",
            description="Get all issues in the work queue, sorted by priority rank. Lower rank number = higher priority (rank 1 is most important). Only returns issues that have been explicitly ranked.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["open", "ready", "in_progress", "review", "testing", "closed"],
                        "description": "Filter by status",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by priority",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to return (default 100)",
                    },
                },
            },
        ),
        Tool(
            name="set_issue_rank",
            description="Set the work queue rank for an issue. Rank 1 is highest priority. Use this to manually prioritize issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "UUID of the issue"},
                    "work_rank": {
                        "type": "integer",
                        "description": "Rank position (1=highest priority)",
                        "minimum": 1,
                    },
                },
                "required": ["issue_id", "work_rank"],
            },
        ),
        Tool(
            name="auto_rank_issues",
            description="Automatically rank all open/in_progress issues using intelligent scoring based on priority, age, blockers, and dependencies. This will overwrite existing ranks.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Workflow Tools
        Tool(
            name="start_issue_work",
            description="Start work on an issue (ready -> in_progress). Creates work log and adds automatic comment. Can ONLY be used on issues with status='ready'. Cannot be used to mark issues as 'ready'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "UUID of the issue"},
                    "started_by": {
                        "type": "string",
                        "description": "Who is starting work (e.g., 'ai:context', 'ai:turbo', 'user')",
                    },
                },
                "required": ["issue_id", "started_by"],
            },
        ),
        Tool(
            name="submit_issue_for_review",
            description="Submit an issue for review (in_progress -> review). Ends work log with commit URL and adds automatic comment. Can ONLY be used on issues with status='in_progress'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "UUID of the issue"},
                    "commit_url": {
                        "type": "string",
                        "description": "Git commit URL for the completed work",
                    },
                },
                "required": ["issue_id", "commit_url"],
            },
        ),
        # Discovery Tools
        Tool(
            name="list_discoveries",
            description="Get all discovery issues (type=discovery). Includes discovery status. Useful for finding research topics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "discovery_status": {
                        "type": "string",
                        "enum": ["proposed", "researching", "findings_ready", "approved", "parked", "declined"],
                        "description": "Filter by discovery status",
                    }
                },
            },
        ),
        # Initiative Tools
        Tool(
            name="create_initiative",
            description="Create a new initiative. Returns the created initiative with generated ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Initiative name"},
                    "description": {"type": "string", "description": "Initiative description"},
                    "status": {
                        "type": "string",
                        "enum": ["planning", "in_progress", "on_hold", "completed", "cancelled"],
                        "description": "Initiative status (default: planning)",
                    },
                    "project_id": {"type": "string", "description": "Associated project UUID (optional)"},
                    "start_date": {"type": "string", "description": "Start date (ISO format, optional)"},
                    "target_date": {"type": "string", "description": "Target completion date (ISO format, optional)"},
                },
                "required": ["name", "description"],
            },
        ),
        Tool(
            name="list_initiatives",
            description="Get all initiatives (feature/technology-based groupings). Returns initiative list with status, dates, and counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["planning", "in_progress", "on_hold", "completed", "cancelled"],
                        "description": "Filter by initiative status",
                    },
                    "project_id": {"type": "string", "description": "Filter by project UUID"},
                },
            },
        ),
        Tool(
            name="get_initiative",
            description="Get detailed information about a specific initiative including name, description, status, dates, and counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "initiative_id": {
                        "type": "string",
                        "description": "UUID of the initiative",
                    }
                },
                "required": ["initiative_id"],
            },
        ),
        Tool(
            name="get_initiative_issues",
            description="Get all issues associated with an initiative. Useful for understanding what work is part of a feature/technology initiative.",
            inputSchema={
                "type": "object",
                "properties": {
                    "initiative_id": {
                        "type": "string",
                        "description": "UUID of the initiative",
                    }
                },
                "required": ["initiative_id"],
            },
        ),
        Tool(
            name="update_initiative",
            description="Update an initiative's details. Only include fields you want to change. Returns the updated initiative.",
            inputSchema={
                "type": "object",
                "properties": {
                    "initiative_id": {"type": "string", "description": "UUID of the initiative to update"},
                    "name": {"type": "string", "description": "Initiative name"},
                    "description": {"type": "string", "description": "Initiative description (supports Markdown)"},
                    "status": {
                        "type": "string",
                        "enum": ["planning", "in_progress", "on_hold", "completed", "cancelled"],
                        "description": "Initiative status",
                    },
                    "start_date": {"type": "string", "description": "Start date (ISO format)"},
                    "target_date": {"type": "string", "description": "Target completion date (ISO format)"},
                    "project_id": {"type": "string", "description": "Associated project UUID"},
                },
                "required": ["initiative_id"],
            },
        ),
        Tool(
            name="delete_initiative",
            description="Delete an initiative permanently. Use with caution as this is irreversible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "initiative_id": {
                        "type": "string",
                        "description": "UUID of the initiative to delete",
                    }
                },
                "required": ["initiative_id"],
            },
        ),
        Tool(
            name="link_issue_to_initiative",
            description="Associate an issue with an initiative. Adds the issue to the initiative's issue list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue",
                    },
                    "initiative_id": {
                        "type": "string",
                        "description": "UUID of the initiative to link",
                    }
                },
                "required": ["issue_id", "initiative_id"],
            },
        ),
        Tool(
            name="unlink_issue_from_initiative",
            description="Remove an issue from an initiative. Removes the issue from the initiative's issue list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue",
                    },
                    "initiative_id": {
                        "type": "string",
                        "description": "UUID of the initiative to unlink",
                    }
                },
                "required": ["issue_id", "initiative_id"],
            },
        ),
        # Milestone Tools
        Tool(
            name="create_milestone",
            description="Create a new milestone. Returns the created milestone with generated ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Milestone name"},
                    "description": {"type": "string", "description": "Milestone description"},
                    "project_id": {"type": "string", "description": "Project UUID"},
                    "status": {
                        "type": "string",
                        "enum": ["planned", "in_progress", "completed", "cancelled"],
                        "description": "Milestone status (default: planned)",
                    },
                    "start_date": {"type": "string", "description": "Start date (ISO format, optional)"},
                    "due_date": {"type": "string", "description": "Due date (ISO format, required)"},
                },
                "required": ["name", "description", "project_id", "due_date"],
            },
        ),
        Tool(
            name="list_milestones",
            description="Get all milestones (time/release-based groupings). Returns milestone list with status, dates, and counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["planned", "in_progress", "completed", "cancelled"],
                        "description": "Filter by milestone status",
                    },
                    "project_id": {"type": "string", "description": "Filter by project UUID"},
                },
            },
        ),
        Tool(
            name="get_milestone",
            description="Get detailed information about a specific milestone including name, description, status, dates, and counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "milestone_id": {
                        "type": "string",
                        "description": "UUID of the milestone",
                    }
                },
                "required": ["milestone_id"],
            },
        ),
        Tool(
            name="get_milestone_issues",
            description="Get all issues associated with a milestone. Useful for tracking what needs to be done for a release.",
            inputSchema={
                "type": "object",
                "properties": {
                    "milestone_id": {
                        "type": "string",
                        "description": "UUID of the milestone",
                    }
                },
                "required": ["milestone_id"],
            },
        ),
        Tool(
            name="update_milestone",
            description="Update a milestone's details. Only include fields you want to change. Returns the updated milestone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "milestone_id": {"type": "string", "description": "UUID of the milestone to update"},
                    "name": {"type": "string", "description": "Milestone name"},
                    "description": {"type": "string", "description": "Milestone description (supports Markdown)"},
                    "status": {
                        "type": "string",
                        "enum": ["planned", "in_progress", "completed", "cancelled"],
                        "description": "Milestone status",
                    },
                    "start_date": {"type": "string", "description": "Start date (ISO format)"},
                    "due_date": {"type": "string", "description": "Due date (ISO format)"},
                },
                "required": ["milestone_id"],
            },
        ),
        Tool(
            name="delete_milestone",
            description="Delete a milestone permanently. Use with caution as this is irreversible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "milestone_id": {
                        "type": "string",
                        "description": "UUID of the milestone to delete",
                    }
                },
                "required": ["milestone_id"],
            },
        ),
        Tool(
            name="link_issue_to_milestone",
            description="Associate an issue with a milestone. Adds the milestone to the issue's milestone list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue",
                    },
                    "milestone_id": {
                        "type": "string",
                        "description": "UUID of the milestone to link",
                    }
                },
                "required": ["issue_id", "milestone_id"],
            },
        ),
        Tool(
            name="unlink_issue_from_milestone",
            description="Remove an issue from a milestone. Removes the milestone from the issue's milestone list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue",
                    },
                    "milestone_id": {
                        "type": "string",
                        "description": "UUID of the milestone to unlink",
                    }
                },
                "required": ["issue_id", "milestone_id"],
            },
        ),
        # Comment Tools
        Tool(
            name="add_comment",
            description="Add a comment to any entity (issue, project, milestone, initiative, literature, blueprint). Use author_type='ai' for Claude responses and author_type='user' for user comments. Can use either issue_id (legacy) or entity_type + entity_id (polymorphic).",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to comment on (legacy, use entity_type + entity_id instead)",
                    },
                    "entity_type": {
                        "type": "string",
                        "enum": ["issue", "project", "milestone", "initiative", "literature", "blueprint"],
                        "description": "Type of entity to comment on",
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the entity to comment on",
                    },
                    "content": {
                        "type": "string",
                        "description": "Comment content (supports Markdown)",
                    },
                    "author_name": {
                        "type": "string",
                        "description": "Author name (default: 'Claude' for AI)",
                        "default": "Claude",
                    },
                    "author_type": {
                        "type": "string",
                        "enum": ["user", "ai"],
                        "description": "Author type: 'user' or 'ai' (default: 'ai')",
                        "default": "ai",
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="get_entity_comments",
            description="Get all comments for any entity (issue, project, milestone, initiative, literature, blueprint), ordered chronologically. Returns conversation thread between user and AI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["issue", "project", "milestone", "initiative", "literature", "blueprint"],
                        "description": "Type of entity",
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the entity",
                    }
                },
                "required": ["entity_type", "entity_id"],
            },
        ),
        Tool(
            name="get_issue_comments",
            description="Get all comments for an issue, ordered chronologically. Returns conversation thread between user and AI. (Legacy - use get_entity_comments instead)",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue",
                    }
                },
                "required": ["issue_id"],
            },
        ),
        # Mentor Tools
        Tool(
            name="get_mentor",
            description="Get detailed information about a mentor including name, description, persona, workspace, and context preferences.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mentor_id": {
                        "type": "string",
                        "description": "UUID of the mentor",
                    }
                },
                "required": ["mentor_id"],
            },
        ),
        Tool(
            name="get_mentor_messages",
            description="Get conversation history with a mentor. Returns all messages between user and mentor, ordered chronologically.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mentor_id": {
                        "type": "string",
                        "description": "UUID of the mentor",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of messages to return",
                    },
                },
                "required": ["mentor_id"],
            },
        ),
        Tool(
            name="add_mentor_message",
            description="Add an assistant message to a mentor conversation. Use this to respond to the user's message.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mentor_id": {
                        "type": "string",
                        "description": "UUID of the mentor",
                    },
                    "content": {
                        "type": "string",
                        "description": "The mentor's response message content",
                    },
                },
                "required": ["mentor_id", "content"],
            },
        ),
        # Staff Tools
        Tool(
            name="list_staff",
            description="Get all staff members with optional filtering. Staff are AI domain experts that can be @ mentioned in comments for execution and guidance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "role_type": {
                        "type": "string",
                        "enum": ["leadership", "domain_expert"],
                        "description": "Filter by role type (leadership = universal permissions, domain_expert = assigned only)",
                    },
                    "is_active": {
                        "type": "boolean",
                        "description": "Filter by active status (default: true)",
                    },
                },
            },
        ),
        Tool(
            name="get_staff",
            description="Get detailed information about a specific staff member including handle, role, persona, monitoring scope, and capabilities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "staff_id": {
                        "type": "string",
                        "description": "UUID of the staff member",
                    }
                },
                "required": ["staff_id"],
            },
        ),
        Tool(
            name="get_staff_by_handle",
            description="Get staff member by handle (for @ mention resolution). Example: get_staff_by_handle('ChiefOfStaff') or get_staff_by_handle('AgilityLead')",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Staff handle without @ prefix (e.g., 'ChiefOfStaff', 'ProductManager', 'AgilityLead', 'EngineeringManager')",
                    }
                },
                "required": ["handle"],
            },
        ),
        Tool(
            name="get_staff_conversation",
            description="Get conversation history with a staff member. Returns all messages ordered chronologically.",
            inputSchema={
                "type": "object",
                "properties": {
                    "staff_id": {
                        "type": "string",
                        "description": "UUID of the staff member",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of messages to return (default: 50)",
                    },
                },
                "required": ["staff_id"],
            },
        ),
        Tool(
            name="add_staff_message",
            description="Add an assistant message to staff conversation (called by webhook after staff response generation). Use this when staff @ mentioned in comments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "staff_id": {
                        "type": "string",
                        "description": "UUID of the staff member",
                    },
                    "content": {
                        "type": "string",
                        "description": "The staff's response message content",
                    },
                },
                "required": ["staff_id", "content"],
            },
        ),
        Tool(
            name="get_my_queue",
            description="Get the unified My Queue with all pending work: action approvals, assigned tasks (issues/initiatives/milestones), and review requests from staff.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max items per section (default: 50)",
                    },
                },
            },
        ),
        # Literature Tools
        Tool(
            name="list_literature",
            description="Get all literature (articles, podcasts, books, papers) with optional filtering. Returns list with title, type, url, author, source, read status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["article", "podcast", "book", "research_paper"],
                        "description": "Filter by literature type",
                    },
                    "source": {"type": "string", "description": "Filter by source name"},
                    "is_read": {"type": "boolean", "description": "Filter by read status"},
                    "is_favorite": {"type": "boolean", "description": "Filter by favorite status"},
                    "is_archived": {"type": "boolean", "description": "Filter by archived status"},
                    "limit": {"type": "integer", "description": "Maximum number of items to return (default: 100)"},
                    "offset": {"type": "integer", "description": "Number of items to skip (default: 0)"},
                },
            },
        ),
        Tool(
            name="get_literature",
            description="Get detailed information about a specific literature item including full content, metadata, and reading status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "literature_id": {
                        "type": "string",
                        "description": "UUID of the literature item",
                    }
                },
                "required": ["literature_id"],
            },
        ),
        Tool(
            name="fetch_article",
            description="Fetch and save an article from a URL. Uses Reader View technology to extract clean content without ads. Returns the saved article.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the article to fetch",
                    }
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="fetch_rss_feed",
            description="Fetch multiple articles from an RSS feed URL. Extracts all articles and saves them to your literature collection.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_url": {
                        "type": "string",
                        "description": "URL of the RSS feed",
                    }
                },
                "required": ["feed_url"],
            },
        ),
        Tool(
            name="mark_literature_read",
            description="Mark a literature item as read. Useful for tracking reading progress.",
            inputSchema={
                "type": "object",
                "properties": {
                    "literature_id": {
                        "type": "string",
                        "description": "UUID of the literature item",
                    }
                },
                "required": ["literature_id"],
            },
        ),
        Tool(
            name="toggle_literature_favorite",
            description="Toggle favorite status of a literature item. Use to save important articles for later.",
            inputSchema={
                "type": "object",
                "properties": {
                    "literature_id": {
                        "type": "string",
                        "description": "UUID of the literature item",
                    }
                },
                "required": ["literature_id"],
            },
        ),
        Tool(
            name="update_literature",
            description="Update a literature item's details. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "literature_id": {"type": "string", "description": "UUID of the literature item"},
                    "title": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["article", "podcast", "book", "research_paper"],
                    },
                    "tags": {"type": "string", "description": "Comma-separated tags"},
                    "is_archived": {"type": "boolean"},
                    "progress": {"type": "integer", "description": "Reading/listening progress percentage"},
                },
                "required": ["literature_id"],
            },
        ),
        Tool(
            name="delete_literature",
            description="Delete a literature item permanently. Use with caution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "literature_id": {
                        "type": "string",
                        "description": "UUID of the literature item",
                    }
                },
                "required": ["literature_id"],
            },
        ),
        # Document Tools
        Tool(
            name="load_document",
            description="Load a file (markdown, text, code, HTML, etc.) as a Turbo Document. Automatically detects file type and extracts title. Supports .md, .txt, .html, .py, .js, .ts, and many code files. When used with project-scoped MCP (turbo-context), automatically associates with allowed project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file to load",
                    },
                    "title": {
                        "type": "string",
                        "description": "Document title (optional - auto-detected from file content or filename)",
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Document type (optional - auto-detected from file path)",
                        "enum": ["design", "specification", "requirements", "api_doc", "user_guide", "code", "changelog", "adr", "other"],
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project UUID to associate document with (takes precedence over project_name)",
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Project name to associate document with (fuzzy matched, ignored if project_id provided)",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="list_documents",
            description="Get all documents with optional filtering by type, format, or project. Returns list of documents with metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["specification", "user_guide", "api_doc", "readme", "changelog", "requirements", "design", "other"],
                        "description": "Filter by document type",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "html", "text", "pdf", "docx"],
                        "description": "Filter by document format",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Filter by project UUID",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of documents to return (1-100)",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of documents to skip",
                    },
                },
            },
        ),
        Tool(
            name="get_document",
            description="Get detailed information about a specific document including full content, metadata, version, and author.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "UUID of the document",
                    }
                },
                "required": ["document_id"],
            },
        ),
        Tool(
            name="update_document",
            description="Update a document's details. Only include fields you want to change. Returns the updated document.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "UUID of the document to update"},
                    "title": {"type": "string", "description": "Document title"},
                    "content": {"type": "string", "description": "Document content (supports Markdown)"},
                    "type": {
                        "type": "string",
                        "enum": ["specification", "user_guide", "api_doc", "readme", "changelog", "requirements", "design", "other"],
                        "description": "Document type",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "html", "text", "pdf", "docx"],
                        "description": "Document format",
                    },
                    "version": {"type": "string", "description": "Document version"},
                    "author": {"type": "string", "description": "Author email"},
                },
                "required": ["document_id"],
            },
        ),
        Tool(
            name="delete_document",
            description="Delete a document permanently. Use with caution as this is irreversible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "UUID of the document to delete",
                    }
                },
                "required": ["document_id"],
            },
        ),
        Tool(
            name="search_documents",
            description="Search documents by title and content. Returns matching documents.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to match against document title and content",
                    }
                },
                "required": ["query"],
            },
        ),
        # Skills Tools
        Tool(
            name="create_skill",
            description="Create a new skill to track technical abilities, soft skills, tools, languages, or certifications.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name (max 200 characters)"},
                    "category": {
                        "type": "string",
                        "enum": ["technical", "soft_skills", "tools", "languages", "certifications", "other"],
                        "description": "Skill category (default: technical)",
                    },
                    "proficiency_level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced", "expert"],
                        "description": "Proficiency level (default: intermediate)",
                    },
                    "description": {"type": "string", "description": "Skill description (max 1000 characters)"},
                    "years_of_experience": {"type": "integer", "description": "Years of experience (0-100)"},
                    "is_endorsed": {"type": "boolean", "description": "Whether skill is endorsed"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="list_skills",
            description="List all skills with optional filtering by category, proficiency, or endorsement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["technical", "soft_skills", "tools", "languages", "certifications", "other"],
                        "description": "Filter by category",
                    },
                    "proficiency_level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced", "expert"],
                        "description": "Filter by proficiency level",
                    },
                    "is_endorsed": {"type": "boolean", "description": "Filter by endorsement status"},
                    "limit": {"type": "integer", "description": "Maximum number to return (1-500, default: 100)"},
                    "offset": {"type": "integer", "description": "Offset for pagination (default: 0)"},
                },
            },
        ),
        Tool(
            name="update_skill",
            description="Update a skill's details. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_id": {"type": "string", "description": "UUID of the skill to update"},
                    "name": {"type": "string", "description": "Skill name"},
                    "category": {
                        "type": "string",
                        "enum": ["technical", "soft_skills", "tools", "languages", "certifications", "other"],
                    },
                    "proficiency_level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced", "expert"],
                    },
                    "description": {"type": "string", "description": "Skill description"},
                    "years_of_experience": {"type": "integer", "description": "Years of experience"},
                    "is_endorsed": {"type": "boolean", "description": "Endorsement status"},
                },
                "required": ["skill_id"],
            },
        ),
        Tool(
            name="delete_skill",
            description="Delete a skill permanently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_id": {"type": "string", "description": "UUID of the skill to delete"},
                },
                "required": ["skill_id"],
            },
        ),
        # Resume Tools
        Tool(
            name="upload_resume",
            description="Upload and parse a resume file (PDF or Markdown). Returns resume ID and parsed data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path to resume file"},
                    "title": {"type": "string", "description": "Resume title"},
                    "target_role": {"type": "string", "description": "Target job role (optional)"},
                    "target_company": {"type": "string", "description": "Target company (optional)"},
                    "use_ai_extraction": {
                        "type": "boolean",
                        "description": "Use AI to extract structured data (default: true)",
                    },
                },
                "required": ["file_path", "title"],
            },
        ),
        Tool(
            name="list_resumes",
            description="List all resumes with their metadata and sections.",
            inputSchema={
                "type": "object",
                "properties": {
                    "skip": {"type": "integer", "description": "Number to skip (pagination)"},
                    "limit": {"type": "integer", "description": "Maximum number to return"},
                },
            },
        ),
        Tool(
            name="get_resume",
            description="Get detailed resume information including all sections and parsed data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_id": {"type": "string", "description": "UUID of the resume"},
                },
                "required": ["resume_id"],
            },
        ),
        Tool(
            name="update_resume",
            description="Update resume details. Only include fields you want to change. Use parsed_data to save extracted structured information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_id": {"type": "string", "description": "UUID of the resume to update"},
                    "title": {"type": "string", "description": "Resume title"},
                    "target_role": {"type": "string", "description": "Target job role"},
                    "target_company": {"type": "string", "description": "Target company"},
                    "is_primary": {"type": "boolean", "description": "Set as primary resume"},
                    "parsed_data": {
                        "type": "object",
                        "description": "Structured data extracted from resume (personal info, experience, education, skills, projects, etc.)"
                    },
                },
                "required": ["resume_id"],
            },
        ),
        Tool(
            name="delete_resume",
            description="Delete a resume permanently including its file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_id": {"type": "string", "description": "UUID of the resume to delete"},
                },
                "required": ["resume_id"],
            },
        ),
        Tool(
            name="get_resume_sections",
            description="Get all sections for a resume.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_id": {"type": "string", "description": "UUID of the resume"},
                    "active_only": {
                        "type": "boolean",
                        "description": "Only return active sections (default: false)",
                    },
                },
                "required": ["resume_id"],
            },
        ),
        # Career Management - Company Tools
        Tool(
            name="create_company",
            description="Create a new company for career tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Company name (max 200 characters)"},
                    "description": {"type": "string", "description": "Company description (optional)"},
                    "industry": {"type": "string", "description": "Industry (max 100 characters, optional)"},
                    "size": {"type": "string", "description": "Company size (max 50 characters, optional)"},
                    "location": {"type": "string", "description": "Location (max 200 characters, optional)"},
                    "website": {"type": "string", "description": "Website URL (optional)"},
                    "linkedin_url": {"type": "string", "description": "LinkedIn URL (optional)"},
                    "glassdoor_url": {"type": "string", "description": "Glassdoor URL (optional)"},
                    "target_status": {
                        "type": "string",
                        "enum": ["researching", "interested", "applying", "interviewing", "offer", "not_interested"],
                        "description": "Target status (default: researching)",
                    },
                    "notes": {"type": "string", "description": "Notes (optional)"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="list_companies",
            description="Get all companies with optional filtering by target status, industry, or search query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_status": {
                        "type": "string",
                        "enum": ["researching", "interested", "applying", "interviewing", "offer", "not_interested"],
                        "description": "Filter by target status",
                    },
                    "industry": {"type": "string", "description": "Filter by industry"},
                    "search": {"type": "string", "description": "Search by company name"},
                    "limit": {"type": "integer", "description": "Maximum number to return (1-100)"},
                    "offset": {"type": "integer", "description": "Offset for pagination (default: 0)"},
                },
            },
        ),
        Tool(
            name="get_company",
            description="Get detailed information about a specific company.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "UUID of the company"},
                },
                "required": ["company_id"],
            },
        ),
        Tool(
            name="update_company",
            description="Update a company's details. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "UUID of the company to update"},
                    "name": {"type": "string", "description": "Company name"},
                    "description": {"type": "string", "description": "Company description"},
                    "industry": {"type": "string", "description": "Industry"},
                    "size": {"type": "string", "description": "Company size"},
                    "location": {"type": "string", "description": "Location"},
                    "website": {"type": "string", "description": "Website URL"},
                    "linkedin_url": {"type": "string", "description": "LinkedIn URL"},
                    "glassdoor_url": {"type": "string", "description": "Glassdoor URL"},
                    "target_status": {
                        "type": "string",
                        "enum": ["researching", "interested", "applying", "interviewing", "offer", "not_interested"],
                        "description": "Target status",
                    },
                    "notes": {"type": "string", "description": "Notes"},
                },
                "required": ["company_id"],
            },
        ),
        Tool(
            name="delete_company",
            description="Delete a company permanently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "UUID of the company to delete"},
                },
                "required": ["company_id"],
            },
        ),
        # Career Management - Job Application Tools
        Tool(
            name="create_job_application",
            description="Create a new job application to track application progress.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string", "description": "UUID of the company"},
                    "job_title": {"type": "string", "description": "Job title (max 200 characters)"},
                    "description": {"type": "string", "description": "Job description (optional)"},
                    "job_url": {"type": "string", "description": "Job posting URL (optional)"},
                    "location": {"type": "string", "description": "Job location (max 200 characters, optional)"},
                    "salary_range": {"type": "string", "description": "Salary range (max 100 characters, optional)"},
                    "status": {
                        "type": "string",
                        "enum": ["researching", "preparing", "applied", "screening", "interviewing", "offer", "rejected", "withdrawn", "accepted"],
                        "description": "Application status (default: researching)",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Priority level (default: medium)",
                    },
                    "applied_date": {"type": "string", "description": "Application date (ISO format, optional)"},
                    "deadline": {"type": "string", "description": "Application deadline (ISO format, optional)"},
                    "next_followup": {"type": "string", "description": "Next follow-up date (ISO format, optional)"},
                    "resume_id": {"type": "string", "description": "UUID of resume used (optional)"},
                    "cover_letter_project_id": {"type": "string", "description": "UUID of cover letter project (optional)"},
                    "notes": {"type": "string", "description": "Notes (optional)"},
                },
                "required": ["company_id", "job_title"],
            },
        ),
        Tool(
            name="list_job_applications",
            description="Get all job applications with optional filtering by status, company, or active status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["researching", "preparing", "applied", "screening", "interviewing", "offer", "rejected", "withdrawn", "accepted"],
                        "description": "Filter by status",
                    },
                    "company_id": {"type": "string", "description": "Filter by company UUID"},
                    "active_only": {"type": "boolean", "description": "Filter for active applications only (default: false)"},
                    "limit": {"type": "integer", "description": "Maximum number to return (1-100)"},
                    "offset": {"type": "integer", "description": "Offset for pagination (default: 0)"},
                },
            },
        ),
        Tool(
            name="get_job_application",
            description="Get detailed information about a specific job application.",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {"type": "string", "description": "UUID of the job application"},
                },
                "required": ["application_id"],
            },
        ),
        Tool(
            name="update_job_application",
            description="Update a job application's details. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {"type": "string", "description": "UUID of the application to update"},
                    "job_title": {"type": "string", "description": "Job title"},
                    "description": {"type": "string", "description": "Job description"},
                    "job_url": {"type": "string", "description": "Job posting URL"},
                    "location": {"type": "string", "description": "Job location"},
                    "salary_range": {"type": "string", "description": "Salary range"},
                    "status": {
                        "type": "string",
                        "enum": ["researching", "preparing", "applied", "screening", "interviewing", "offer", "rejected", "withdrawn", "accepted"],
                        "description": "Application status",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Priority level",
                    },
                    "applied_date": {"type": "string", "description": "Application date (ISO format)"},
                    "deadline": {"type": "string", "description": "Application deadline (ISO format)"},
                    "next_followup": {"type": "string", "description": "Next follow-up date (ISO format)"},
                    "notes": {"type": "string", "description": "Notes"},
                },
                "required": ["application_id"],
            },
        ),
        Tool(
            name="delete_job_application",
            description="Delete a job application permanently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {"type": "string", "description": "UUID of the application to delete"},
                },
                "required": ["application_id"],
            },
        ),
        Tool(
            name="get_applications_needing_followup",
            description="Get job applications with upcoming or overdue follow-ups.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Career Management - Network Contact Tools
        Tool(
            name="create_network_contact",
            description="Create a new network contact for relationship tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "first_name": {"type": "string", "description": "First name (max 100 characters)"},
                    "last_name": {"type": "string", "description": "Last name (max 100 characters)"},
                    "email": {"type": "string", "description": "Email address (optional)"},
                    "phone": {"type": "string", "description": "Phone number (max 50 characters, optional)"},
                    "company_id": {"type": "string", "description": "UUID of associated company (optional)"},
                    "current_title": {"type": "string", "description": "Current job title (max 255 characters, optional)"},
                    "current_company": {"type": "string", "description": "Current company name (max 255 characters, optional)"},
                    "linkedin_url": {"type": "string", "description": "LinkedIn URL (optional)"},
                    "contact_type": {
                        "type": "string",
                        "enum": ["recruiter_internal", "recruiter_external", "hiring_manager", "peer", "referrer", "mentor", "former_colleague"],
                        "description": "Contact type (optional)",
                    },
                    "relationship_strength": {
                        "type": "string",
                        "enum": ["cold", "warm", "hot"],
                        "description": "Relationship strength (default: cold)",
                    },
                    "last_contact_date": {"type": "string", "description": "Last contact date (ISO format, optional)"},
                    "next_followup_date": {"type": "string", "description": "Next follow-up date (ISO format, optional)"},
                    "how_we_met": {"type": "string", "description": "How we met (optional)"},
                    "referral_status": {
                        "type": "string",
                        "enum": ["none", "requested", "agreed", "completed"],
                        "description": "Referral status (optional)",
                    },
                    "notes": {"type": "string", "description": "Notes (optional)"},
                },
                "required": ["first_name", "last_name"],
            },
        ),
        Tool(
            name="list_network_contacts",
            description="Get all network contacts with optional filtering by type, company, or relationship strength.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_type": {
                        "type": "string",
                        "enum": ["recruiter_internal", "recruiter_external", "hiring_manager", "peer", "referrer", "mentor", "former_colleague"],
                        "description": "Filter by contact type",
                    },
                    "company_id": {"type": "string", "description": "Filter by company UUID"},
                    "warm_only": {"type": "boolean", "description": "Filter for warm/hot contacts only (default: false)"},
                    "search": {"type": "string", "description": "Search by name"},
                    "limit": {"type": "integer", "description": "Maximum number to return (1-100)"},
                    "offset": {"type": "integer", "description": "Offset for pagination (default: 0)"},
                },
            },
        ),
        Tool(
            name="get_network_contact",
            description="Get detailed information about a specific network contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "UUID of the network contact"},
                },
                "required": ["contact_id"],
            },
        ),
        Tool(
            name="update_network_contact",
            description="Update a network contact's details. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "UUID of the contact to update"},
                    "first_name": {"type": "string", "description": "First name"},
                    "last_name": {"type": "string", "description": "Last name"},
                    "email": {"type": "string", "description": "Email address"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "current_title": {"type": "string", "description": "Current job title"},
                    "current_company": {"type": "string", "description": "Current company name"},
                    "linkedin_url": {"type": "string", "description": "LinkedIn URL"},
                    "contact_type": {
                        "type": "string",
                        "enum": ["recruiter_internal", "recruiter_external", "hiring_manager", "peer", "referrer", "mentor", "former_colleague"],
                        "description": "Contact type",
                    },
                    "relationship_strength": {
                        "type": "string",
                        "enum": ["cold", "warm", "hot"],
                        "description": "Relationship strength",
                    },
                    "last_contact_date": {"type": "string", "description": "Last contact date (ISO format)"},
                    "next_followup_date": {"type": "string", "description": "Next follow-up date (ISO format)"},
                    "how_we_met": {"type": "string", "description": "How we met"},
                    "referral_status": {
                        "type": "string",
                        "enum": ["none", "requested", "agreed", "completed"],
                        "description": "Referral status",
                    },
                    "notes": {"type": "string", "description": "Notes"},
                },
                "required": ["contact_id"],
            },
        ),
        Tool(
            name="delete_network_contact",
            description="Delete a network contact permanently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "UUID of the contact to delete"},
                },
                "required": ["contact_id"],
            },
        ),
        Tool(
            name="get_contacts_needing_followup",
            description="Get network contacts with upcoming or overdue follow-ups.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Email Template Tools
        Tool(
            name="create_email_template",
            description="Create a new email template with variable substitution support.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "UUID of the project"},
                    "name": {"type": "string", "description": "Template name"},
                    "content": {"type": "string", "description": "Template content with {{variable}} placeholders"},
                    "category": {
                        "type": "string",
                        "enum": ["cover_letter", "cold_outreach", "followup", "thank_you", "networking", "referral_request", "status_check", "other"],
                        "description": "Template category",
                    },
                    "variables": {"type": "array", "items": {"type": "string"}, "description": "List of variable names (optional, auto-detected if not provided)"},
                    "version": {"type": "string", "description": "Template version (default: 1.0)"},
                },
                "required": ["project_id", "name", "content", "category"],
            },
        ),
        Tool(
            name="list_email_templates",
            description="List email templates with optional filtering by project, category, or status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Filter by project UUID"},
                    "category": {
                        "type": "string",
                        "enum": ["cover_letter", "cold_outreach", "followup", "thank_you", "networking", "referral_request", "status_check", "other"],
                        "description": "Filter by category",
                    },
                    "status": {"type": "string", "description": "Filter by status"},
                    "limit": {"type": "integer", "description": "Maximum number to return (1-100)"},
                    "offset": {"type": "integer", "description": "Offset for pagination"},
                },
            },
        ),
        Tool(
            name="get_email_template",
            description="Get a specific email template by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string", "description": "UUID of the template"},
                },
                "required": ["template_id"],
            },
        ),
        Tool(
            name="render_email_template",
            description="Render an email template with variable substitution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string", "description": "UUID of the template"},
                    "variables": {
                        "type": "object",
                        "description": "Dictionary of variable names to values (e.g., {'company': 'Acme', 'role': 'Engineer'})",
                    },
                },
                "required": ["template_id", "variables"],
            },
        ),
        Tool(
            name="update_email_template",
            description="Update an email template. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string", "description": "UUID of the template to update"},
                    "name": {"type": "string", "description": "Template name"},
                    "content": {"type": "string", "description": "Template content"},
                    "category": {
                        "type": "string",
                        "enum": ["cover_letter", "cold_outreach", "followup", "thank_you", "networking", "referral_request", "status_check", "other"],
                        "description": "Template category",
                    },
                    "status": {"type": "string", "description": "Template status"},
                },
                "required": ["template_id"],
            },
        ),
        Tool(
            name="delete_email_template",
            description="Delete an email template permanently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string", "description": "UUID of the template to delete"},
                },
                "required": ["template_id"],
            },
        ),
        # Resume Generation Tools
        Tool(
            name="generate_tailored_resume",
            description="Generate a tailored resume for a specific job. Analyzes job description, customizes content, reorders sections by relevance, and creates resume file in requested format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_resume_id": {"type": "string", "description": "UUID of the base resume to customize"},
                    "job_description": {"type": "string", "description": "Full job description text"},
                    "job_title": {"type": "string", "description": "Job title (optional)"},
                    "company_name": {"type": "string", "description": "Company name (optional)"},
                    "job_application_id": {"type": "string", "description": "Job application UUID to link (optional)"},
                    "output_format": {
                        "type": "string",
                        "enum": ["markdown", "pdf", "docx"],
                        "description": "Output format (default: markdown)",
                    },
                },
                "required": ["base_resume_id", "job_description"],
            },
        ),
        Tool(
            name="generate_resume_from_application",
            description="Generate resume directly from a job application. Uses application's job description, title, and company. If no base resume provided, uses primary resume.",
            inputSchema={
                "type": "object",
                "properties": {
                    "application_id": {"type": "string", "description": "UUID of the job application"},
                    "base_resume_id": {"type": "string", "description": "UUID of base resume (optional, uses primary if not provided)"},
                    "output_format": {
                        "type": "string",
                        "enum": ["markdown", "pdf", "docx"],
                        "description": "Output format (default: markdown)",
                    },
                },
                "required": ["application_id"],
            },
        ),
        Tool(
            name="batch_generate_resumes",
            description="Generate resumes for multiple job applications in one operation. Useful for bulk resume generation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_resume_id": {"type": "string", "description": "UUID of the base resume to customize"},
                    "application_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of job application UUIDs",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["markdown", "pdf", "docx"],
                        "description": "Output format (default: markdown)",
                    },
                },
                "required": ["base_resume_id", "application_ids"],
            },
        ),
        # Forms Tools
        Tool(
            name="create_form",
            description="Create a new form that can be attached to an issue, document, or project. Forms collect structured data with custom fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Form title (max 255 characters)"},
                    "description": {"type": "string", "description": "Form description (optional)"},
                    "schema": {
                        "type": "object",
                        "description": "Form schema defining fields (JSON object with field definitions)",
                    },
                    "issue_id": {"type": "string", "description": "UUID of issue to attach form to (optional)"},
                    "document_id": {"type": "string", "description": "UUID of document to attach form to (optional)"},
                    "project_id": {"type": "string", "description": "UUID of project to attach form to (optional)"},
                    "created_by": {"type": "string", "description": "Creator name (default: 'system')"},
                    "created_by_type": {
                        "type": "string",
                        "enum": ["user", "ai"],
                        "description": "Creator type (default: 'ai')",
                    },
                    "on_submit": {
                        "type": "object",
                        "description": "Workflow configuration for form submission (optional JSON object)",
                    },
                },
                "required": ["title", "schema"],
            },
        ),
        Tool(
            name="list_forms",
            description="List forms attached to a specific entity (issue, document, or project).",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["issue", "document", "project"],
                        "description": "Type of entity to list forms for",
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the entity",
                    },
                },
                "required": ["entity_type", "entity_id"],
            },
        ),
        Tool(
            name="update_form",
            description="Update a form's details. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "form_id": {"type": "string", "description": "UUID of the form to update"},
                    "title": {"type": "string", "description": "Form title"},
                    "description": {"type": "string", "description": "Form description"},
                    "schema": {"type": "object", "description": "Form schema (field definitions)"},
                    "status": {"type": "string", "description": "Form status"},
                    "on_submit": {"type": "object", "description": "Workflow configuration"},
                },
                "required": ["form_id"],
            },
        ),
        Tool(
            name="delete_form",
            description="Delete a form permanently. This also deletes all responses to the form.",
            inputSchema={
                "type": "object",
                "properties": {
                    "form_id": {"type": "string", "description": "UUID of the form to delete"},
                },
                "required": ["form_id"],
            },
        ),
        # Calendar Events Tools
        Tool(
            name="create_event",
            description="Create a new calendar event. Supports recurring events, reminders, and various categories.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title (max 255 characters)"},
                    "description": {"type": "string", "description": "Event description (optional)"},
                    "start_date": {"type": "string", "description": "Start date/time (ISO format)"},
                    "end_date": {"type": "string", "description": "End date/time (ISO format, optional)"},
                    "all_day": {"type": "boolean", "description": "Whether event is all-day (default: false)"},
                    "location": {"type": "string", "description": "Event location (optional, max 255 characters)"},
                    "category": {
                        "type": "string",
                        "enum": ["personal", "work", "meeting", "deadline", "appointment", "reminder", "holiday", "other"],
                        "description": "Event category (default: 'other')",
                    },
                    "color": {"type": "string", "description": "Hex color code (format: #RRGGBB)"},
                    "is_recurring": {"type": "boolean", "description": "Whether event recurs (default: false)"},
                    "recurrence_rule": {"type": "string", "description": "Recurrence rule (optional, max 255 characters)"},
                    "reminder_minutes": {"type": "integer", "description": "Minutes before event to remind (optional)"},
                },
                "required": ["title", "start_date"],
            },
        ),
        Tool(
            name="list_events",
            description="List calendar events with optional filtering by category, date range, or upcoming events.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["personal", "work", "meeting", "deadline", "appointment", "reminder", "holiday", "other"],
                        "description": "Filter by category",
                    },
                    "start_date": {"type": "string", "description": "Start date for date range filter (ISO format)"},
                    "end_date": {"type": "string", "description": "End date for date range filter (ISO format)"},
                    "upcoming": {"type": "boolean", "description": "Filter for upcoming events only (default: false)"},
                    "include_completed": {"type": "boolean", "description": "Include completed events (default: false)"},
                    "include_cancelled": {"type": "boolean", "description": "Include cancelled events (default: false)"},
                    "limit": {"type": "integer", "description": "Maximum number to return (1-500, default: 100)"},
                    "offset": {"type": "integer", "description": "Offset for pagination (default: 0)"},
                },
            },
        ),
        Tool(
            name="get_event",
            description="Get detailed information about a specific calendar event.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "UUID of the event"},
                },
                "required": ["event_id"],
            },
        ),
        Tool(
            name="update_event",
            description="Update a calendar event's details. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "UUID of the event to update"},
                    "title": {"type": "string", "description": "Event title"},
                    "description": {"type": "string", "description": "Event description"},
                    "start_date": {"type": "string", "description": "Start date/time (ISO format)"},
                    "end_date": {"type": "string", "description": "End date/time (ISO format)"},
                    "all_day": {"type": "boolean", "description": "Whether event is all-day"},
                    "location": {"type": "string", "description": "Event location"},
                    "category": {
                        "type": "string",
                        "enum": ["personal", "work", "meeting", "deadline", "appointment", "reminder", "holiday", "other"],
                    },
                    "color": {"type": "string", "description": "Hex color code"},
                    "is_recurring": {"type": "boolean", "description": "Whether event recurs"},
                    "recurrence_rule": {"type": "string", "description": "Recurrence rule"},
                    "reminder_minutes": {"type": "integer", "description": "Minutes before event to remind"},
                    "is_completed": {"type": "boolean", "description": "Whether event is completed"},
                    "is_cancelled": {"type": "boolean", "description": "Whether event is cancelled"},
                },
                "required": ["event_id"],
            },
        ),
        Tool(
            name="delete_event",
            description="Delete a calendar event permanently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "UUID of the event to delete"},
                },
                "required": ["event_id"],
            },
        ),
        # Favorites Tools
        Tool(
            name="add_favorite",
            description="Add an item to favorites. Supports issues, documents, tags, blueprints, and projects.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_type": {
                        "type": "string",
                        "enum": ["issue", "document", "tag", "blueprint", "project"],
                        "description": "Type of item to favorite",
                    },
                    "item_id": {"type": "string", "description": "UUID of the item to favorite"},
                },
                "required": ["item_type", "item_id"],
            },
        ),
        Tool(
            name="remove_favorite",
            description="Remove an item from favorites.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_type": {
                        "type": "string",
                        "enum": ["issue", "document", "tag", "blueprint", "project"],
                        "description": "Type of item to unfavorite",
                    },
                    "item_id": {"type": "string", "description": "UUID of the item to unfavorite"},
                },
                "required": ["item_type", "item_id"],
            },
        ),
        # Issue Refinement Tools (AI-powered hygiene)
        Tool(
            name="refine_issues_analyze",
            description=(
                "Analyze issues and generate refinement plan with AI-powered suggestions. "
                "Returns SAFE changes (auto-applicable) and APPROVAL_NEEDED changes (require user review). "
                "Use this to identify stale issues, missing dependencies, orphaned issues, and documentation gaps."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Optional: Scope analysis to specific project UUID",
                    },
                    "include_safe": {
                        "type": "boolean",
                        "description": "Include safe auto-apply changes (tags, templates). Default: true",
                    },
                    "include_approval": {
                        "type": "boolean",
                        "description": "Include changes requiring approval (status, dependencies). Default: true",
                    },
                },
            },
        ),
        Tool(
            name="refine_issues_execute",
            description=(
                "Execute issue refinement changes. Supports two modes: "
                "1. Auto-execute SAFE changes (add tags, templates) "
                "2. Execute APPROVED changes after user review (update status, add dependencies). "
                "Pass the changes array from refine_issues_analyze results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["safe", "approved"],
                        "description": "Execution mode: 'safe' for auto-apply or 'approved' for user-approved changes",
                    },
                    "changes": {
                        "type": "array",
                        "description": "Array of changes to execute (from analyze results)",
                        "items": {"type": "object"},
                    },
                },
                "required": ["mode", "changes"],
            },
        ),
        # Graph/Knowledge Base Tools
        Tool(
            name="get_related_entities",
            description="Find entities semantically related to a specific entity using vector similarity in the knowledge graph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the source entity",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Type of the entity (issue, project, milestone, initiative, document, etc.)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of related entities to return (1-100, default: 10)",
                        "default": 10,
                    }
                },
                "required": ["entity_id", "entity_type"],
            },
        ),
        Tool(
            name="search_knowledge_graph",
            description="Perform semantic search across the knowledge graph to find entities by meaning, not just keywords.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text",
                    },
                    "entity_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by entity types (issue, project, milestone, initiative, document, etc.)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                    },
                    "min_relevance": {
                        "type": "number",
                        "description": "Minimum relevance score (0.0-1.0, default: 0.7)",
                        "default": 0.7,
                    }
                },
                "required": ["query"],
            },
        ),
        # Podcast Tools
        Tool(
            name="subscribe_to_podcast",
            description="Subscribe to a podcast feed by URL. Fetches show metadata and creates subscription.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "RSS feed URL of the podcast"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="list_podcast_shows",
            description="List podcast shows with optional filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "is_subscribed": {"type": "boolean", "description": "Filter by subscription status"},
                    "is_favorite": {"type": "boolean", "description": "Filter by favorite status"},
                    "limit": {"type": "integer", "description": "Maximum number to return (default: 100)"},
                    "offset": {"type": "integer", "description": "Offset for pagination (default: 0)"},
                },
            },
        ),
        Tool(
            name="get_podcast_show",
            description="Get detailed information about a podcast show.",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "UUID of the podcast show"},
                },
                "required": ["show_id"],
            },
        ),
        Tool(
            name="update_podcast_show",
            description="Update a podcast show's details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "UUID of the show to update"},
                    "is_subscribed": {"type": "boolean", "description": "Subscription status"},
                    "is_favorite": {"type": "boolean", "description": "Favorite status"},
                    "is_archived": {"type": "boolean", "description": "Archived status"},
                    "auto_fetch": {"type": "boolean", "description": "Auto-fetch new episodes"},
                },
                "required": ["show_id"],
            },
        ),
        Tool(
            name="delete_podcast_show",
            description="Delete a podcast show and all its episodes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "UUID of the show to delete"},
                },
                "required": ["show_id"],
            },
        ),
        Tool(
            name="toggle_podcast_subscription",
            description="Toggle subscription status for a podcast show.",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "UUID of the podcast show"},
                },
                "required": ["show_id"],
            },
        ),
        Tool(
            name="fetch_podcast_episodes",
            description="Sync/fetch new episodes from a podcast show's RSS feed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "UUID of the podcast show"},
                    "limit": {"type": "integer", "description": "Maximum episodes to fetch (1-100)"},
                },
                "required": ["show_id"],
            },
        ),
        Tool(
            name="list_podcast_episodes",
            description="List podcast episodes with optional filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "Filter by show UUID"},
                    "is_played": {"type": "boolean", "description": "Filter by played status"},
                    "is_favorite": {"type": "boolean", "description": "Filter by favorite status"},
                    "limit": {"type": "integer", "description": "Maximum number to return (default: 100)"},
                    "offset": {"type": "integer", "description": "Offset for pagination (default: 0)"},
                },
            },
        ),
        # Saved Filters Tools
        Tool(
            name="create_saved_filter",
            description="Create a new saved filter for a project. Filters store query parameters to quickly find specific issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Filter name (max 100 characters)"},
                    "description": {"type": "string", "description": "Filter description (optional, max 255 characters)"},
                    "filter_config": {
                        "type": "string",
                        "description": "Filter configuration as JSON string (e.g., '{\"status\": \"open\", \"priority\": \"high\"}')",
                    },
                    "project_id": {"type": "string", "description": "UUID of the project this filter belongs to"},
                },
                "required": ["name", "filter_config", "project_id"],
            },
        ),
        Tool(
            name="list_saved_filters",
            description="Get all saved filters for a specific project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "UUID of the project",
                    }
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_saved_filter",
            description="Get detailed information about a specific saved filter.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_id": {
                        "type": "string",
                        "description": "UUID of the saved filter",
                    }
                },
                "required": ["filter_id"],
            },
        ),
        Tool(
            name="update_saved_filter",
            description="Update a saved filter's details. Only include fields you want to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_id": {"type": "string", "description": "UUID of the filter to update"},
                    "name": {"type": "string", "description": "Filter name"},
                    "description": {"type": "string", "description": "Filter description"},
                    "filter_config": {"type": "string", "description": "Filter configuration as JSON string"},
                },
                "required": ["filter_id"],
            },
        ),
        Tool(
            name="delete_saved_filter",
            description="Delete a saved filter permanently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_id": {
                        "type": "string",
                        "description": "UUID of the filter to delete",
                    }
                },
                "required": ["filter_id"],
            },
        ),
        # Issue Dependencies Tools
        Tool(
            name="add_blocker",
            description="Add a blocking dependency between issues. The blocking issue must be completed before the blocked issue can start.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blocking_issue_id": {
                        "type": "string",
                        "description": "UUID of the issue that blocks (must be completed first)",
                    },
                    "blocked_issue_id": {
                        "type": "string",
                        "description": "UUID of the issue that is blocked (depends on blocking issue)",
                    },
                    "dependency_type": {
                        "type": "string",
                        "description": "Type of dependency (default: 'blocks')",
                        "default": "blocks",
                    }
                },
                "required": ["blocking_issue_id", "blocked_issue_id"],
            },
        ),
        Tool(
            name="remove_blocker",
            description="Remove a blocking dependency between issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blocking_issue_id": {
                        "type": "string",
                        "description": "UUID of the blocking issue",
                    },
                    "blocked_issue_id": {
                        "type": "string",
                        "description": "UUID of the blocked issue",
                    }
                },
                "required": ["blocking_issue_id", "blocked_issue_id"],
            },
        ),
        Tool(
            name="get_blocking_issues",
            description="Get all issues that block a given issue (dependencies that must be completed first).",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue",
                    }
                },
                "required": ["issue_id"],
            },
        ),
        Tool(
            name="get_blocked_issues",
            description="Get all issues that are blocked by a given issue (issues that depend on this one).",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue",
                    }
                },
                "required": ["issue_id"],
            },
        ),
        # Tag Tools
        Tool(
            name="create_tag",
            description="Create a new tag. Tags are used to categorize and organize projects, issues, and other entities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Tag name (max 50 characters)"},
                    "color": {"type": "string", "description": "Hex color code (format: #RRGGBB)", "pattern": "^#[0-9A-Fa-f]{6}$"},
                    "description": {"type": "string", "description": "Optional tag description (max 200 characters)"},
                },
                "required": ["name", "color"],
            },
        ),
        Tool(
            name="list_tags",
            description="Get all tags with optional filtering by color. Returns list of tags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "color": {"type": "string", "description": "Filter by hex color code"},
                    "limit": {"type": "integer", "description": "Maximum number of tags to return (1-100)"},
                    "offset": {"type": "integer", "description": "Number of tags to skip"},
                },
            },
        ),
        Tool(
            name="get_tag",
            description="Get detailed information about a specific tag including name, color, and description.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {
                        "type": "string",
                        "description": "UUID of the tag",
                    }
                },
                "required": ["tag_id"],
            },
        ),
        Tool(
            name="update_tag",
            description="Update a tag's details. All fields must be provided (full replacement, not partial update).",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {"type": "string", "description": "UUID of the tag to update"},
                    "name": {"type": "string", "description": "Tag name (max 50 characters)"},
                    "color": {"type": "string", "description": "Hex color code (format: #RRGGBB)", "pattern": "^#[0-9A-Fa-f]{6}$"},
                    "description": {"type": "string", "description": "Tag description (max 200 characters)"},
                },
                "required": ["tag_id", "name", "color"],
            },
        ),
        Tool(
            name="delete_tag",
            description="Delete a tag permanently. This removes the tag from all entities that use it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {
                        "type": "string",
                        "description": "UUID of the tag to delete",
                    }
                },
                "required": ["tag_id"],
            },
        ),
        Tool(
            name="add_tag_to_entity",
            description="Add a tag to an entity (project or issue). Associates the tag with the specified entity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["project", "issue"],
                        "description": "Type of entity to tag",
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the entity",
                    },
                    "tag_id": {
                        "type": "string",
                        "description": "UUID of the tag to add",
                    }
                },
                "required": ["entity_type", "entity_id", "tag_id"],
            },
        ),
        Tool(
            name="remove_tag_from_entity",
            description="Remove a tag from an entity (project or issue). Disassociates the tag from the specified entity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["project", "issue"],
                        "description": "Type of entity",
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "UUID of the entity",
                    },
                    "tag_id": {
                        "type": "string",
                        "description": "UUID of the tag to remove",
                    }
                },
                "required": ["entity_type", "entity_id", "tag_id"],
            },
        ),
        # Blueprint Tools
        Tool(
            name="list_blueprints",
            description="Get all blueprints with optional filtering. Blueprints define architecture patterns, coding standards, and project templates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category (architecture, testing, styling, database, api, deployment, custom)",
                    },
                    "is_active": {
                        "type": "boolean",
                        "description": "Filter by active status",
                    },
                },
            },
        ),
        Tool(
            name="get_blueprint",
            description="Get detailed information about a specific blueprint including content (patterns, standards, rules, templates).",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "UUID of the blueprint",
                    }
                },
                "required": ["blueprint_id"],
            },
        ),
        Tool(
            name="create_blueprint",
            description="Create a new blueprint. Blueprints define architecture patterns, coding standards, rules, and templates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Blueprint name (max 200 characters)"},
                    "description": {"type": "string", "description": "Blueprint description"},
                    "category": {
                        "type": "string",
                        "description": "Blueprint category",
                        "enum": ["architecture", "testing", "styling", "database", "api", "deployment", "custom"],
                    },
                    "content": {
                        "type": "object",
                        "description": "Blueprint content (patterns, standards, rules, templates) as JSON object",
                    },
                    "version": {"type": "string", "description": "Blueprint version (max 50 characters)"},
                    "is_active": {"type": "boolean", "description": "Whether blueprint is active (default: true)"},
                },
                "required": ["name", "description", "category", "version"],
            },
        ),
        Tool(
            name="update_blueprint",
            description="Update a blueprint's details. Only include fields you want to change. Returns the updated blueprint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {"type": "string", "description": "UUID of the blueprint to update"},
                    "name": {"type": "string", "description": "Blueprint name"},
                    "description": {"type": "string", "description": "Blueprint description"},
                    "category": {
                        "type": "string",
                        "description": "Blueprint category",
                        "enum": ["architecture", "testing", "styling", "database", "api", "deployment", "custom"],
                    },
                    "content": {
                        "type": "object",
                        "description": "Blueprint content (patterns, standards, rules, templates) as JSON object",
                    },
                    "version": {"type": "string", "description": "Blueprint version"},
                    "is_active": {"type": "boolean", "description": "Whether blueprint is active"},
                },
                "required": ["blueprint_id"],
            },
        ),
        Tool(
            name="delete_blueprint",
            description="Delete a blueprint permanently. Use with caution as this is irreversible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "UUID of the blueprint to delete",
                    }
                },
                "required": ["blueprint_id"],
            },
        ),
        Tool(
            name="activate_blueprint",
            description="Activate a blueprint, making it available for use in projects.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "UUID of the blueprint to activate",
                    }
                },
                "required": ["blueprint_id"],
            },
        ),
        Tool(
            name="deactivate_blueprint",
            description="Deactivate a blueprint, making it unavailable for use in projects without deleting it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "UUID of the blueprint to deactivate",
                    }
                },
                "required": ["blueprint_id"],
            },
        ),
        # Git Worktree Management Tools
        Tool(
            name="start_work_on_issue",
            description="Start work on an issue. Creates a git worktree at ~/worktrees/ProjectName-ISSUEKEY/ with a branch ISSUEKEY/title. Updates issue status to 'in_progress', creates work log, and tracks worktree path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to start work on",
                    },
                    "started_by": {
                        "type": "string",
                        "description": "Who is starting work (e.g., 'user', 'ai:context', 'ai:turbo')",
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project git repository (e.g., '/path/to/turboCode'). Optional - if not provided, worktree creation is skipped.",
                    },
                },
                "required": ["issue_id", "started_by"],
            },
        ),
        Tool(
            name="submit_issue_with_worktree",
            description="Submit an issue for review after completing work. Cleans up git worktree, updates issue status to 'review', ends work log with commit URL, and adds automatic comment with time spent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to submit for review",
                    },
                    "commit_url": {
                        "type": "string",
                        "description": "Git commit URL for the completed work (e.g., 'https://github.com/org/repo/commit/abc123')",
                    },
                    "cleanup_worktree": {
                        "type": "boolean",
                        "description": "Whether to remove the git worktree after submission (default: true)",
                    },
                },
                "required": ["issue_id", "commit_url"],
            },
        ),
        Tool(
            name="list_worktrees",
            description="List all git worktrees for a project repository. Returns worktree paths, branches, and commit hashes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project git repository",
                    }
                },
                "required": ["project_path"],
            },
        ),
        Tool(
            name="get_worktree_status",
            description="Get the git status of a worktree. Returns information about uncommitted files, current branch, and whether there are changes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "worktree_path": {
                        "type": "string",
                        "description": "Path to the worktree directory (e.g., '~/worktrees/Project-KEY-1')",
                    }
                },
                "required": ["worktree_path"],
            },
        ),
        # Job Search Tools
        Tool(
            name="create_search_criteria",
            description="Create job search criteria to automatically find job postings. Define your preferences for job titles, locations, salary, keywords, and more.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name for this search (e.g., 'Senior Data Engineer Remote')"},
                    "description": {"type": "string", "description": "Optional description"},
                    "job_titles": {"type": "array", "items": {"type": "string"}, "description": "Target job titles"},
                    "locations": {"type": "array", "items": {"type": "string"}, "description": "Preferred locations"},
                    "excluded_states": {"type": "array", "items": {"type": "string"}, "description": "States to exclude"},
                    "remote_policies": {"type": "array", "items": {"type": "string"}, "description": "remote, hybrid, onsite"},
                    "exclude_onsite": {"type": "boolean", "description": "Exclude on-site only jobs"},
                    "salary_minimum": {"type": "integer", "description": "Minimum acceptable salary"},
                    "salary_target": {"type": "integer", "description": "Target salary"},
                    "required_keywords": {"type": "array", "items": {"type": "string"}, "description": "Must have these keywords"},
                    "preferred_keywords": {"type": "array", "items": {"type": "string"}, "description": "Nice to have keywords"},
                    "excluded_keywords": {"type": "array", "items": {"type": "string"}, "description": "Exclude jobs with these"},
                    "enabled_sources": {"type": "array", "items": {"type": "string"}, "description": "Job boards to search (indeed, linkedin, etc.)"},
                    "auto_search_enabled": {"type": "boolean", "description": "Enable automatic searches"},
                    "search_frequency_hours": {"type": "integer", "description": "How often to search (hours)"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="list_search_criteria",
            description="List all job search criteria.",
            inputSchema={
                "type": "object",
                "properties": {
                    "is_active": {"type": "boolean", "description": "Filter by active status"},
                    "limit": {"type": "integer", "description": "Max results"},
                },
            },
        ),
        Tool(
            name="get_search_criteria",
            description="Get detailed information about a search criteria.",
            inputSchema={
                "type": "object",
                "properties": {
                    "criteria_id": {"type": "string", "description": "UUID of search criteria"}
                },
                "required": ["criteria_id"],
            },
        ),
        Tool(
            name="update_search_criteria",
            description="Update job search criteria settings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "criteria_id": {"type": "string", "description": "UUID of search criteria"},
                    "name": {"type": "string"},
                    "is_active": {"type": "boolean"},
                    "job_titles": {"type": "array", "items": {"type": "string"}},
                    "salary_minimum": {"type": "integer"},
                    "auto_search_enabled": {"type": "boolean"},
                },
                "required": ["criteria_id"],
            },
        ),
        Tool(
            name="execute_job_search",
            description="Execute a job search based on search criteria. Searches configured job boards, scores matches, and stores results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "criteria_id": {"type": "string", "description": "UUID of search criteria"},
                    "sources": {"type": "array", "items": {"type": "string"}, "description": "Optional: override sources (indeed, linkedin, etc.)"},
                },
                "required": ["criteria_id"],
            },
        ),
        Tool(
            name="list_job_postings",
            description="List discovered job postings with optional filters. Shows new jobs found through automated searches.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["new", "interested", "not_interested", "applied", "expired"], "description": "Filter by status"},
                    "source": {"type": "string", "description": "Filter by job board (indeed, linkedin, etc.)"},
                    "min_score": {"type": "number", "description": "Minimum match score (0-100)"},
                    "limit": {"type": "integer", "description": "Max results (default 100)"},
                },
            },
        ),
        Tool(
            name="get_job_posting",
            description="Get detailed information about a job posting including full description and match reasons.",
            inputSchema={
                "type": "object",
                "properties": {
                    "posting_id": {"type": "string", "description": "UUID of job posting"}
                },
                "required": ["posting_id"],
            },
        ),
        Tool(
            name="update_job_posting",
            description="Update a job posting (e.g., mark as interested, not interested, or applied).",
            inputSchema={
                "type": "object",
                "properties": {
                    "posting_id": {"type": "string", "description": "UUID of job posting"},
                    "status": {"type": "string", "enum": ["new", "interested", "not_interested", "applied", "expired"]},
                },
                "required": ["posting_id"],
            },
        ),
        Tool(
            name="get_job_search_history",
            description="Get history of job search executions with results stats.",
            inputSchema={
                "type": "object",
                "properties": {
                    "criteria_id": {"type": "string", "description": "Optional: filter by criteria UUID"},
                    "limit": {"type": "integer", "description": "Max results (default 50)"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a Turbo tool by calling the Turbo API."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Project Management
            if name == "list_projects":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/projects/", params=params)
                response.raise_for_status()
                # Filter to allowed projects
                projects = response.json()
                filtered = filter_projects(projects)
                return [TextContent(type="text", text=json.dumps(filtered))]

            elif name == "get_project":
                project_id = arguments["project_id"]
                # Check access
                if not is_project_allowed(project_id):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to project {project_id}"
                    }))]
                response = await client.get(f"{TURBO_API_URL}/projects/{project_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_project_issues":
                project_id = arguments["project_id"]
                # Check access
                if not is_project_allowed(project_id):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to project {project_id}"
                    }))]
                # Use the filtered issues endpoint instead of the broken project endpoint
                response = await client.get(f"{TURBO_API_URL}/issues/", params={"project_id": project_id})
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_project":
                project_id = arguments.get("project_id")
                # Check access
                if not is_project_allowed(project_id):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to modify project {project_id}"
                    }))]
                arguments.pop("project_id")
                response = await client.put(f"{TURBO_API_URL}/projects/{project_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_project":
                project_id = arguments["project_id"]
                # Check access
                if not is_project_allowed(project_id):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to delete project {project_id}"
                    }))]
                response = await client.delete(f"{TURBO_API_URL}/projects/{project_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Project deleted successfully")]

            elif name == "archive_project":
                project_id = arguments["project_id"]
                # Check access
                if not is_project_allowed(project_id):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to archive project {project_id}"
                    }))]
                response = await client.post(f"{TURBO_API_URL}/projects/{project_id}/archive")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Issue Management
            elif name == "list_issues":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/issues/", params=params)
                response.raise_for_status()
                # Filter to issues in allowed projects
                issues = response.json()
                filtered = filter_entities_by_project(issues)
                return [TextContent(type="text", text=json.dumps(filtered))]

            elif name == "get_issue":
                issue_id = arguments["issue_id"]
                response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                response.raise_for_status()
                # Check if issue is in allowed project
                issue = response.json()
                if not is_project_allowed(issue.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to this issue's project"
                    }))]
                return [TextContent(type="text", text=response.text)]

            elif name == "create_issue":
                # Check if creating in allowed project
                project_id = arguments.get("project_id")
                if project_id and not is_project_allowed(project_id):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You can only create issues in allowed projects"
                    }))]
                response = await client.post(f"{TURBO_API_URL}/issues/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_issue":
                issue_id = arguments.get("issue_id")
                # First get the issue to check project
                get_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                get_response.raise_for_status()
                issue = get_response.json()
                if not is_project_allowed(issue.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to modify this issue"
                    }))]
                arguments.pop("issue_id")
                response = await client.put(f"{TURBO_API_URL}/issues/{issue_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Work Queue
            elif name == "get_next_issue":
                response = await client.get(f"{TURBO_API_URL}/work-queue/next")
                response.raise_for_status()
                # Check if next issue is in allowed project
                issue = response.json()
                if issue and not is_project_allowed(issue.get("project_id")):
                    # Skip to next allowed issue
                    return [TextContent(type="text", text=json.dumps({
                        "message": "Next issue is not in allowed projects"
                    }))]
                return [TextContent(type="text", text=response.text)]

            elif name == "get_work_queue":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/work-queue/", params=params)
                response.raise_for_status()
                # Filter to issues in allowed projects
                queue = response.json()
                filtered = filter_entities_by_project(queue)
                return [TextContent(type="text", text=json.dumps(filtered))]

            elif name == "set_issue_rank":
                issue_id = arguments["issue_id"]
                work_rank = arguments["work_rank"]
                # Check if issue is in allowed project
                get_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                get_response.raise_for_status()
                issue = get_response.json()
                if not is_project_allowed(issue.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to modify this issue's rank"
                    }))]
                response = await client.post(
                    f"{TURBO_API_URL}/work-queue/{issue_id}/rank",
                    json={"work_rank": work_rank}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "auto_rank_issues":
                # This ranks all issues - only allow if no project filter
                if ALLOWED_PROJECT_IDS is not None:
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Not allowed",
                        "message": "Auto-ranking all issues is not permitted with project restrictions"
                    }))]
                response = await client.post(f"{TURBO_API_URL}/work-queue/auto-rank")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "start_issue_work":
                issue_id = arguments.get("issue_id")
                started_by = arguments.get("started_by")

                # Check project access
                issue_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                issue_response.raise_for_status()
                issue = issue_response.json()

                if issue.get("project_id") and not is_project_allowed(issue["project_id"]):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": "You do not have access to start work on this issue"
                    }))]

                # Call the API endpoint
                response = await client.post(
                    f"{TURBO_API_URL}/issues/{issue_id}/start-work",
                    json={"started_by": started_by}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "submit_issue_for_review":
                issue_id = arguments.get("issue_id")
                commit_url = arguments.get("commit_url")

                # Check project access
                issue_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                issue_response.raise_for_status()
                issue = issue_response.json()

                if issue.get("project_id") and not is_project_allowed(issue["project_id"]):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": "You do not have access to submit this issue for review"
                    }))]

                # Call the API endpoint
                response = await client.post(
                    f"{TURBO_API_URL}/issues/{issue_id}/submit-review",
                    json={"commit_url": commit_url}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Discovery
            elif name == "list_discoveries":
                params = {**arguments, "type": "discovery"}
                response = await client.get(f"{TURBO_API_URL}/issues/", params=params)
                response.raise_for_status()
                # Filter to discoveries in allowed projects
                discoveries = response.json()
                filtered = filter_entities_by_project(discoveries)
                return [TextContent(type="text", text=json.dumps(filtered))]

            # Initiatives
            elif name == "create_initiative":
                # Check if creating in allowed project
                project_id = arguments.get("project_id")
                if project_id and not is_project_allowed(project_id):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You can only create initiatives in allowed projects"
                    }))]
                response = await client.post(f"{TURBO_API_URL}/initiatives/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_initiatives":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/initiatives/", params=params)
                response.raise_for_status()
                # Filter to initiatives in allowed projects
                initiatives = response.json()
                filtered = filter_entities_by_project(initiatives)
                return [TextContent(type="text", text=json.dumps(filtered))]

            elif name == "get_initiative":
                initiative_id = arguments["initiative_id"]
                response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}")
                response.raise_for_status()
                # Check if initiative is in allowed project
                initiative = response.json()
                if not is_project_allowed(initiative.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to this initiative's project"
                    }))]
                return [TextContent(type="text", text=response.text)]

            elif name == "get_initiative_issues":
                initiative_id = arguments["initiative_id"]
                # First check if initiative is allowed
                init_response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}")
                init_response.raise_for_status()
                initiative = init_response.json()
                if not is_project_allowed(initiative.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to this initiative's project"
                    }))]
                response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}/issues")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_initiative":
                initiative_id = arguments.get("initiative_id")
                # First get the initiative to check project
                get_response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}")
                get_response.raise_for_status()
                initiative = get_response.json()
                if not is_project_allowed(initiative.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to modify this initiative"
                    }))]
                arguments.pop("initiative_id")
                response = await client.put(f"{TURBO_API_URL}/initiatives/{initiative_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_initiative":
                initiative_id = arguments["initiative_id"]
                # First get the initiative to check project
                get_response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}")
                get_response.raise_for_status()
                initiative = get_response.json()
                if not is_project_allowed(initiative.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to delete this initiative"
                    }))]
                response = await client.delete(f"{TURBO_API_URL}/initiatives/{initiative_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Initiative deleted successfully")]

            elif name == "link_issue_to_initiative":
                issue_id = arguments["issue_id"]
                initiative_id = arguments["initiative_id"]

                # Get current initiative to retrieve existing issue_ids
                initiative_response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}")
                initiative_response.raise_for_status()
                initiative_data = initiative_response.json()

                # Get current issues from the initiative
                issues_response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}/issues")
                issues_response.raise_for_status()
                current_issues = issues_response.json()
                current_issue_ids = [issue["id"] for issue in current_issues]

                # Add issue if not already present
                if issue_id not in current_issue_ids:
                    current_issue_ids.append(issue_id)
                    update_response = await client.put(
                        f"{TURBO_API_URL}/initiatives/{initiative_id}",
                        json={"issue_ids": current_issue_ids}
                    )
                    update_response.raise_for_status()
                    return [TextContent(type="text", text=f"Issue {issue_id} linked to initiative {initiative_id}")]
                else:
                    return [TextContent(type="text", text=f"Issue {issue_id} already linked to initiative {initiative_id}")]

            elif name == "unlink_issue_from_initiative":
                issue_id = arguments["issue_id"]
                initiative_id = arguments["initiative_id"]

                # Get current initiative to retrieve existing issue_ids
                initiative_response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}")
                initiative_response.raise_for_status()
                initiative_data = initiative_response.json()

                # Get current issues from the initiative
                issues_response = await client.get(f"{TURBO_API_URL}/initiatives/{initiative_id}/issues")
                issues_response.raise_for_status()
                current_issues = issues_response.json()
                current_issue_ids = [issue["id"] for issue in current_issues]

                # Remove issue if present
                if issue_id in current_issue_ids:
                    current_issue_ids.remove(issue_id)
                    update_response = await client.put(
                        f"{TURBO_API_URL}/initiatives/{initiative_id}",
                        json={"issue_ids": current_issue_ids}
                    )
                    update_response.raise_for_status()
                    return [TextContent(type="text", text=f"Issue {issue_id} unlinked from initiative {initiative_id}")]
                else:
                    return [TextContent(type="text", text=f"Issue {issue_id} was not linked to initiative {initiative_id}")]

            # Milestones
            elif name == "create_milestone":
                # Check if creating in allowed project (milestones require project_id)
                project_id = arguments.get("project_id")
                if not is_project_allowed(project_id):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You can only create milestones in allowed projects"
                    }))]
                response = await client.post(f"{TURBO_API_URL}/milestones/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_milestones":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/milestones/", params=params)
                response.raise_for_status()
                # Filter to milestones in allowed projects
                milestones = response.json()
                filtered = filter_entities_by_project(milestones)
                return [TextContent(type="text", text=json.dumps(filtered))]

            elif name == "get_milestone":
                milestone_id = arguments["milestone_id"]
                response = await client.get(f"{TURBO_API_URL}/milestones/{milestone_id}")
                response.raise_for_status()
                # Check if milestone is in allowed project
                milestone = response.json()
                if not is_project_allowed(milestone.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to this milestone's project"
                    }))]
                return [TextContent(type="text", text=response.text)]

            elif name == "get_milestone_issues":
                milestone_id = arguments["milestone_id"]
                # First check if milestone is allowed
                ms_response = await client.get(f"{TURBO_API_URL}/milestones/{milestone_id}")
                ms_response.raise_for_status()
                milestone = ms_response.json()
                if not is_project_allowed(milestone.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to this milestone's project"
                    }))]
                response = await client.get(f"{TURBO_API_URL}/milestones/{milestone_id}/issues")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_milestone":
                milestone_id = arguments.get("milestone_id")
                # First get the milestone to check project
                get_response = await client.get(f"{TURBO_API_URL}/milestones/{milestone_id}")
                get_response.raise_for_status()
                milestone = get_response.json()
                if not is_project_allowed(milestone.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to modify this milestone"
                    }))]
                arguments.pop("milestone_id")
                response = await client.put(f"{TURBO_API_URL}/milestones/{milestone_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_milestone":
                milestone_id = arguments["milestone_id"]
                # First get the milestone to check project
                get_response = await client.get(f"{TURBO_API_URL}/milestones/{milestone_id}")
                get_response.raise_for_status()
                milestone = get_response.json()
                if not is_project_allowed(milestone.get("project_id")):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied",
                        "message": f"You do not have access to delete this milestone"
                    }))]
                response = await client.delete(f"{TURBO_API_URL}/milestones/{milestone_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Milestone deleted successfully")]

            elif name == "link_issue_to_milestone":
                issue_id = arguments["issue_id"]
                milestone_id = arguments["milestone_id"]

                # Get current issue to retrieve existing milestone_ids
                issue_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                issue_response.raise_for_status()
                issue_data = issue_response.json()

                # Add milestone if not already present
                current_milestones = issue_data.get("milestone_ids", [])
                if milestone_id not in current_milestones:
                    current_milestones.append(milestone_id)
                    update_response = await client.put(
                        f"{TURBO_API_URL}/issues/{issue_id}",
                        json={"milestone_ids": current_milestones}
                    )
                    update_response.raise_for_status()
                    return [TextContent(type="text", text=f"Issue {issue_id} linked to milestone {milestone_id}")]
                else:
                    return [TextContent(type="text", text=f"Issue {issue_id} already linked to milestone {milestone_id}")]

            elif name == "unlink_issue_from_milestone":
                issue_id = arguments["issue_id"]
                milestone_id = arguments["milestone_id"]

                # Get current issue to retrieve existing milestone_ids
                issue_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                issue_response.raise_for_status()
                issue_data = issue_response.json()

                # Remove milestone if present
                current_milestones = issue_data.get("milestone_ids", [])
                if milestone_id in current_milestones:
                    current_milestones.remove(milestone_id)
                    update_response = await client.put(
                        f"{TURBO_API_URL}/issues/{issue_id}",
                        json={"milestone_ids": current_milestones}
                    )
                    update_response.raise_for_status()
                    return [TextContent(type="text", text=f"Issue {issue_id} unlinked from milestone {milestone_id}")]
                else:
                    return [TextContent(type="text", text=f"Issue {issue_id} was not linked to milestone {milestone_id}")]

            # Comments
            elif name == "add_comment":
                # Set defaults for author_name and author_type
                if "author_name" not in arguments:
                    arguments["author_name"] = "Claude"
                if "author_type" not in arguments:
                    arguments["author_type"] = "ai"

                # Handle legacy issue_id format
                if "issue_id" in arguments and "entity_type" not in arguments:
                    arguments["entity_type"] = "issue"
                    arguments["entity_id"] = arguments.pop("issue_id")

                response = await client.post(f"{TURBO_API_URL}/comments/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_entity_comments":
                entity_type = arguments["entity_type"]
                entity_id = arguments["entity_id"]
                response = await client.get(f"{TURBO_API_URL}/comments/entity/{entity_type}/{entity_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_issue_comments":
                # Legacy support - convert to entity_type/entity_id
                issue_id = arguments["issue_id"]
                response = await client.get(f"{TURBO_API_URL}/comments/entity/issue/{issue_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Mentors
            elif name == "get_mentor":
                mentor_id = arguments["mentor_id"]
                response = await client.get(f"{TURBO_API_URL}/mentors/{mentor_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_mentor_messages":
                mentor_id = arguments["mentor_id"]
                params = {}
                if "limit" in arguments:
                    params["limit"] = arguments["limit"]
                response = await client.get(f"{TURBO_API_URL}/mentors/{mentor_id}/messages", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "add_mentor_message":
                mentor_id = arguments["mentor_id"]
                content = arguments["content"]
                response = await client.post(
                    f"{TURBO_API_URL}/mentors/{mentor_id}/assistant-message",
                    json={"content": content}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Staff
            elif name == "list_staff":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/staff/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_staff":
                staff_id = arguments["staff_id"]
                response = await client.get(f"{TURBO_API_URL}/staff/{staff_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_staff_by_handle":
                handle = arguments["handle"]
                response = await client.get(f"{TURBO_API_URL}/staff/handle/{handle}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_staff_conversation":
                staff_id = arguments["staff_id"]
                params = {}
                if "limit" in arguments:
                    params["limit"] = arguments["limit"]
                response = await client.get(f"{TURBO_API_URL}/staff/{staff_id}/messages", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "add_staff_message":
                staff_id = arguments["staff_id"]
                content = arguments["content"]
                response = await client.post(
                    f"{TURBO_API_URL}/staff/{staff_id}/assistant-message",
                    json={"content": content}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_my_queue":
                params = {}
                if "limit" in arguments:
                    params["limit"] = arguments["limit"]
                response = await client.get(f"{TURBO_API_URL}/my-queue/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Literature
            elif name == "list_literature":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/literature/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_literature":
                literature_id = arguments["literature_id"]
                response = await client.get(f"{TURBO_API_URL}/literature/{literature_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "fetch_article":
                url = arguments["url"]
                response = await client.post(
                    f"{TURBO_API_URL}/literature/fetch-url",
                    json={"url": url},
                    timeout=60.0,  # Longer timeout for content extraction
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "fetch_rss_feed":
                feed_url = arguments["feed_url"]
                response = await client.post(
                    f"{TURBO_API_URL}/literature/fetch-feed",
                    json={"url": feed_url},
                    timeout=120.0,  # Longer timeout for multiple articles
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "mark_literature_read":
                literature_id = arguments["literature_id"]
                response = await client.post(f"{TURBO_API_URL}/literature/{literature_id}/read")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "toggle_literature_favorite":
                literature_id = arguments["literature_id"]
                response = await client.post(f"{TURBO_API_URL}/literature/{literature_id}/favorite")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_literature":
                literature_id = arguments.pop("literature_id")
                response = await client.put(f"{TURBO_API_URL}/literature/{literature_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_literature":
                literature_id = arguments["literature_id"]
                response = await client.delete(f"{TURBO_API_URL}/literature/{literature_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Literature item deleted successfully")]

            # Document Loading
            elif name == "load_document":
                from pathlib import Path
                from turbo.core.services.document_loader import DocumentLoaderService

                file_path = Path(arguments["file_path"]).resolve()

                # Path traversal protection: block sensitive system paths
                _blocked_prefixes = ("/etc/", "/var/", "/root/", "/proc/", "/sys/")
                if any(str(file_path).startswith(p) for p in _blocked_prefixes):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied: file path is outside allowed directories",
                    }))]
                title = arguments.get("title")
                doc_type = arguments.get("doc_type")
                project_id = arguments.get("project_id")
                project_name = arguments.get("project_name")

                # Load and parse file
                loader = DocumentLoaderService()

                if not loader.can_load(file_path):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Unsupported file type",
                        "file_type": file_path.suffix
                    }))]

                try:
                    content = loader.load(file_path)

                    # Extract metadata
                    if not title:
                        title = loader.extract_title(content, file_path.stem)

                    if not doc_type:
                        doc_type = loader.determine_type(file_path)

                    # Determine target project
                    target_project_id = None

                    # Priority 1: Use project_id if provided
                    if project_id:
                        target_project_id = project_id

                    # Priority 2: If project scoping is active and only one project allowed, use that
                    elif ALLOWED_PROJECT_IDS and len(ALLOWED_PROJECT_IDS) == 1:
                        target_project_id = list(ALLOWED_PROJECT_IDS)[0]

                    # Priority 3: Search by project name via API
                    elif project_name:
                        projects_response = await client.get(f"{TURBO_API_URL}/projects/")
                        projects_response.raise_for_status()
                        projects = projects_response.json()

                        # Filter to allowed projects
                        projects = filter_projects(projects)

                        for project in projects:
                            if project_name.lower() in project["name"].lower():
                                target_project_id = project["id"]
                                break

                    # Default: Get first allowed project
                    else:
                        projects_response = await client.get(f"{TURBO_API_URL}/projects/")
                        projects_response.raise_for_status()
                        projects = projects_response.json()

                        # Filter to allowed projects
                        projects = filter_projects(projects)

                        if projects:
                            # Try to find "Turbo" project or use first
                            for project in projects:
                                if "turbo" in project["name"].lower():
                                    target_project_id = project["id"]
                                    break

                            if not target_project_id:
                                target_project_id = projects[0]["id"]

                    if not target_project_id:
                        return [TextContent(type="text", text=json.dumps({
                            "error": "No project found",
                            "message": "Could not determine target project. Specify project_id or project_name."
                        }))]

                    # Check access
                    if not is_project_allowed(target_project_id):
                        return [TextContent(type="text", text=json.dumps({
                            "error": "Access denied",
                            "message": f"You do not have access to create documents in this project"
                        }))]

                    # Create document via API
                    doc_data = {
                        "title": title,
                        "content": content,
                        "type": doc_type,
                        "format": "markdown",
                        "project_id": target_project_id,
                    }

                    response = await client.post(f"{TURBO_API_URL}/documents/", json=doc_data)
                    response.raise_for_status()
                    doc = response.json()

                    return [TextContent(type="text", text=json.dumps({
                        "success": True,
                        "message": "Document loaded successfully!",
                        "document": {
                            "id": doc["id"],
                            "title": doc["title"],
                            "type": doc["type"],
                            "project_id": doc["project_id"],
                        }
                    }))]

                except Exception:
                    logger.exception("Failed to load document")
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Failed to load document",
                    }))]

            elif name == "list_documents":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/documents/", params=params)
                response.raise_for_status()

                # Strip content field to reduce token usage
                documents = response.json()
                # Filter to allowed projects
                documents = filter_entities_by_project(documents)

                # Return only metadata (exclude full content)
                metadata_only = []
                for doc in documents:
                    metadata = {k: v for k, v in doc.items() if k != 'content'}
                    # Add content length indicator instead of full content
                    if 'content' in doc and doc['content']:
                        metadata['content_length'] = len(doc['content'])
                        metadata['content_preview'] = doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content']
                    metadata_only.append(metadata)

                return [TextContent(type="text", text=json.dumps(metadata_only))]

            elif name == "get_document":
                document_id = arguments["document_id"]
                response = await client.get(f"{TURBO_API_URL}/documents/{document_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_document":
                document_id = arguments.pop("document_id")
                response = await client.put(f"{TURBO_API_URL}/documents/{document_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_document":
                document_id = arguments["document_id"]
                response = await client.delete(f"{TURBO_API_URL}/documents/{document_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Document deleted successfully")]

            elif name == "search_documents":
                query = arguments["query"]
                response = await client.get(f"{TURBO_API_URL}/documents/search", params={"query": query})
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Skills
            elif name == "create_skill":
                response = await client.post(f"{TURBO_API_URL}/skills/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_skills":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/skills/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_skill":
                skill_id = arguments.pop("skill_id")
                response = await client.put(f"{TURBO_API_URL}/skills/{skill_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_skill":
                skill_id = arguments["skill_id"]
                response = await client.delete(f"{TURBO_API_URL}/skills/{skill_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Skill deleted successfully")]

            # Resumes
            elif name == "upload_resume":
                from pathlib import Path as _Path
                file_path = str(_Path(arguments["file_path"]).resolve())

                # Path traversal protection
                _blocked = ("/etc/", "/var/", "/root/", "/proc/", "/sys/")
                if any(file_path.startswith(p) for p in _blocked):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Access denied: file path is outside allowed directories",
                    }))]
                title = arguments["title"]
                target_role = arguments.get("target_role")
                target_company = arguments.get("target_company")
                use_ai_extraction = arguments.get("use_ai_extraction", True)

                # Prepare multipart form data
                with open(file_path, "rb") as f:
                    files = {"file": (file_path.split("/")[-1], f)}
                    data = {
                        "title": title,
                        "use_ai_extraction": str(use_ai_extraction).lower(),
                    }
                    if target_role:
                        data["target_role"] = target_role
                    if target_company:
                        data["target_company"] = target_company

                    response = await client.post(
                        f"{TURBO_API_URL}/resumes/upload",
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    return [TextContent(type="text", text=response.text)]

            elif name == "list_resumes":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/resumes/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_resume":
                resume_id = arguments["resume_id"]
                response = await client.get(f"{TURBO_API_URL}/resumes/{resume_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_resume":
                resume_id = arguments.pop("resume_id")
                response = await client.put(f"{TURBO_API_URL}/resumes/{resume_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_resume":
                resume_id = arguments["resume_id"]
                response = await client.delete(f"{TURBO_API_URL}/resumes/{resume_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Resume deleted successfully")]

            elif name == "get_resume_sections":
                resume_id = arguments["resume_id"]
                active_only = arguments.get("active_only", False)
                params = {"active_only": active_only}
                response = await client.get(f"{TURBO_API_URL}/resumes/{resume_id}/sections", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Career Management - Companies
            elif name == "create_company":
                response = await client.post(f"{TURBO_API_URL}/companies/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_companies":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/companies/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_company":
                company_id = arguments["company_id"]
                response = await client.get(f"{TURBO_API_URL}/companies/{company_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_company":
                company_id = arguments.pop("company_id")
                response = await client.put(f"{TURBO_API_URL}/companies/{company_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_company":
                company_id = arguments["company_id"]
                response = await client.delete(f"{TURBO_API_URL}/companies/{company_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Company deleted successfully")]

            # Career Management - Job Applications
            elif name == "create_job_application":
                response = await client.post(f"{TURBO_API_URL}/job-applications/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_job_applications":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/job-applications/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_job_application":
                application_id = arguments["application_id"]
                response = await client.get(f"{TURBO_API_URL}/job-applications/{application_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_job_application":
                application_id = arguments.pop("application_id")
                response = await client.put(f"{TURBO_API_URL}/job-applications/{application_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_job_application":
                application_id = arguments["application_id"]
                response = await client.delete(f"{TURBO_API_URL}/job-applications/{application_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Job application deleted successfully")]

            elif name == "get_applications_needing_followup":
                response = await client.get(f"{TURBO_API_URL}/job-applications/followups/pending")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Career Management - Network Contacts
            elif name == "create_network_contact":
                response = await client.post(f"{TURBO_API_URL}/network-contacts/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_network_contacts":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/network-contacts/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_network_contact":
                contact_id = arguments["contact_id"]
                response = await client.get(f"{TURBO_API_URL}/network-contacts/{contact_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_network_contact":
                contact_id = arguments.pop("contact_id")
                response = await client.put(f"{TURBO_API_URL}/network-contacts/{contact_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_network_contact":
                contact_id = arguments["contact_id"]
                response = await client.delete(f"{TURBO_API_URL}/network-contacts/{contact_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Network contact deleted successfully")]

            elif name == "get_contacts_needing_followup":
                response = await client.get(f"{TURBO_API_URL}/network-contacts/followups/pending")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Email Templates
            elif name == "create_email_template":
                params = {
                    "project_id": arguments["project_id"],
                    "name": arguments["name"],
                    "content": arguments["content"],
                    "category": arguments["category"],
                }
                if "variables" in arguments:
                    params["variables"] = arguments["variables"]
                if "version" in arguments:
                    params["version"] = arguments["version"]
                response = await client.post(f"{TURBO_API_URL}/email-templates/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_email_templates":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/email-templates/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_email_template":
                template_id = arguments["template_id"]
                response = await client.get(f"{TURBO_API_URL}/email-templates/{template_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "render_email_template":
                template_id = arguments["template_id"]
                variables = arguments["variables"]
                response = await client.post(
                    f"{TURBO_API_URL}/email-templates/{template_id}/render",
                    json={"variables": variables}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_email_template":
                template_id = arguments.pop("template_id")
                response = await client.put(
                    f"{TURBO_API_URL}/email-templates/{template_id}",
                    json=arguments
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_email_template":
                template_id = arguments["template_id"]
                response = await client.delete(f"{TURBO_API_URL}/email-templates/{template_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Email template deleted successfully")]

            # Resume Generation
            elif name == "generate_tailored_resume":
                payload = {
                    "base_resume_id": arguments["base_resume_id"],
                    "job_description": arguments["job_description"],
                }
                if "job_title" in arguments:
                    payload["job_title"] = arguments["job_title"]
                if "company_name" in arguments:
                    payload["company_name"] = arguments["company_name"]
                if "job_application_id" in arguments:
                    payload["job_application_id"] = arguments["job_application_id"]
                if "output_format" in arguments:
                    payload["output_format"] = arguments["output_format"]
                else:
                    payload["output_format"] = "markdown"

                response = await client.post(
                    f"{TURBO_API_URL}/resume-generation/generate",
                    json=payload
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "generate_resume_from_application":
                application_id = arguments["application_id"]
                payload = {}
                if "base_resume_id" in arguments:
                    payload["base_resume_id"] = arguments["base_resume_id"]
                if "output_format" in arguments:
                    payload["output_format"] = arguments["output_format"]
                else:
                    payload["output_format"] = "markdown"

                response = await client.post(
                    f"{TURBO_API_URL}/resume-generation/generate/application/{application_id}",
                    json=payload
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "batch_generate_resumes":
                payload = {
                    "base_resume_id": arguments["base_resume_id"],
                    "application_ids": arguments["application_ids"],
                }
                if "output_format" in arguments:
                    payload["output_format"] = arguments["output_format"]
                else:
                    payload["output_format"] = "markdown"

                response = await client.post(
                    f"{TURBO_API_URL}/resume-generation/generate/batch",
                    json=payload
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Forms
            elif name == "create_form":
                response = await client.post(f"{TURBO_API_URL}/forms/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_forms":
                entity_type = arguments["entity_type"]
                entity_id = arguments["entity_id"]
                # Map to plural form for API endpoint
                entity_plural = f"{entity_type}s"
                response = await client.get(f"{TURBO_API_URL}/forms/{entity_plural}/{entity_id}/forms")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_form":
                form_id = arguments.pop("form_id")
                response = await client.put(f"{TURBO_API_URL}/forms/{form_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_form":
                form_id = arguments["form_id"]
                response = await client.delete(f"{TURBO_API_URL}/forms/{form_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Form deleted successfully")]

            # Calendar Events
            elif name == "create_event":
                response = await client.post(f"{TURBO_API_URL}/calendar-events/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_events":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/calendar-events/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_event":
                event_id = arguments["event_id"]
                response = await client.get(f"{TURBO_API_URL}/calendar-events/{event_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_event":
                event_id = arguments.pop("event_id")
                response = await client.put(f"{TURBO_API_URL}/calendar-events/{event_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_event":
                event_id = arguments["event_id"]
                response = await client.delete(f"{TURBO_API_URL}/calendar-events/{event_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Calendar event deleted successfully")]

            # Favorites
            elif name == "add_favorite":
                response = await client.post(f"{TURBO_API_URL}/favorites/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=f"Added {arguments['item_type']} {arguments['item_id']} to favorites")]

            elif name == "remove_favorite":
                item_type = arguments["item_type"]
                item_id = arguments["item_id"]
                response = await client.delete(f"{TURBO_API_URL}/favorites/by-item/{item_type}/{item_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=f"Removed {item_type} {item_id} from favorites")]

            # Issue Refinement
            elif name == "refine_issues_analyze":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.post(
                    f"{TURBO_API_URL}/issue-refinement/analyze",
                    params=params,
                    timeout=60.0  # Longer timeout for analysis
                )
                response.raise_for_status()
                result = response.json()

                # Format response for better readability
                summary = result.get("summary", {})
                safe_count = summary.get("safe_changes_count", 0)
                approval_count = summary.get("approval_needed_count", 0)

                formatted_response = f"""
# Issue Refinement Analysis

**Summary:**
- Issues analyzed: {summary.get('total_issues_analyzed', 0)}
- Safe changes (auto-apply): {safe_count}
- Approval needed: {approval_count}

"""
                if safe_count > 0:
                    formatted_response += "\n**SAFE CHANGES (Auto-applicable):**\n"
                    for change in result.get("safe_changes", [])[:5]:  # Show first 5
                        formatted_response += f"- [{change['type']}] {change['issue_title']}: {change['action']}\n"
                    if safe_count > 5:
                        formatted_response += f"... and {safe_count - 5} more\n"

                if approval_count > 0:
                    formatted_response += "\n**REQUIRES APPROVAL:**\n"
                    for change in result.get("approval_needed", [])[:5]:  # Show first 5
                        formatted_response += f"- [{change['type']}] {change['issue_title']}: {change['action']}\n"
                        formatted_response += f"  Reason: {change['reason']}\n"
                    if approval_count > 5:
                        formatted_response += f"... and {approval_count - 5} more\n"

                formatted_response += f"\n\nFull results: {json.dumps(result, indent=2)}"

                return [TextContent(type="text", text=formatted_response)]

            elif name == "refine_issues_execute":
                mode = arguments["mode"]
                changes = arguments["changes"]

                if mode == "safe":
                    endpoint = "/issue-refinement/execute-safe"
                else:
                    endpoint = "/issue-refinement/execute-approved"

                response = await client.post(
                    f"{TURBO_API_URL}{endpoint}",
                    json=changes,
                    timeout=120.0  # Longer timeout for execution
                )
                response.raise_for_status()
                result = response.json()

                # Format results
                success_count = len(result.get("success", []))
                failed_count = len(result.get("failed", []))

                formatted_response = f"""
# Refinement Execution Results ({mode} mode)

**Summary:**
- Successfully applied: {success_count}
- Failed: {failed_count}

"""
                if success_count > 0:
                    formatted_response += "\n**Successful changes:**\n"
                    for item in result.get("success", []):
                        formatted_response += f"- {item.get('action', 'Unknown')} (Issue: {item.get('issue_id')})\n"

                if failed_count > 0:
                    formatted_response += "\n**Failed changes:**\n"
                    for item in result.get("failed", []):
                        formatted_response += f"- {item.get('action', 'Unknown')}: {item.get('error', 'Unknown error')}\n"

                return [TextContent(type="text", text=formatted_response)]

            # Graph/Knowledge Base
            elif name == "get_related_entities":
                entity_id = arguments["entity_id"]
                entity_type = arguments["entity_type"]
                limit = arguments.get("limit", 10)
                params = {"entity_type": entity_type, "limit": limit}
                response = await client.get(f"{TURBO_API_URL}/graph/related/{entity_id}", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "search_knowledge_graph":
                response = await client.post(f"{TURBO_API_URL}/graph/search", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Podcasts
            elif name == "subscribe_to_podcast":
                url = arguments["url"]
                response = await client.post(
                    f"{TURBO_API_URL}/podcasts/subscribe",
                    json={"url": url}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_podcast_shows":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/podcasts/shows", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_podcast_show":
                show_id = arguments["show_id"]
                response = await client.get(f"{TURBO_API_URL}/podcasts/shows/{show_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_podcast_show":
                show_id = arguments.pop("show_id")
                response = await client.put(f"{TURBO_API_URL}/podcasts/shows/{show_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_podcast_show":
                show_id = arguments["show_id"]
                response = await client.delete(f"{TURBO_API_URL}/podcasts/shows/{show_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Podcast show deleted successfully")]

            elif name == "toggle_podcast_subscription":
                show_id = arguments["show_id"]
                response = await client.post(f"{TURBO_API_URL}/podcasts/shows/{show_id}/subscribe")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "fetch_podcast_episodes":
                show_id = arguments["show_id"]
                params = {}
                if "limit" in arguments:
                    params["limit"] = arguments["limit"]
                response = await client.post(
                    f"{TURBO_API_URL}/podcasts/shows/{show_id}/fetch-episodes",
                    params=params
                )
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_podcast_episodes":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/podcasts/episodes", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            # Saved Filters
            elif name == "create_saved_filter":
                response = await client.post(f"{TURBO_API_URL}/saved-filters/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_saved_filters":
                project_id = arguments["project_id"]
                response = await client.get(f"{TURBO_API_URL}/saved-filters/project/{project_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_saved_filter":
                filter_id = arguments["filter_id"]
                response = await client.get(f"{TURBO_API_URL}/saved-filters/{filter_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_saved_filter":
                filter_id = arguments.pop("filter_id")
                response = await client.put(f"{TURBO_API_URL}/saved-filters/{filter_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_saved_filter":
                filter_id = arguments["filter_id"]
                response = await client.delete(f"{TURBO_API_URL}/saved-filters/{filter_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Saved filter deleted successfully")]

            # Issue Dependencies
            elif name == "add_blocker":
                from uuid import UUID as PyUUID
                from turbo.core.database.connection import get_db_session
                from turbo.core.repositories.issue_dependency import IssueDependencyRepository

                blocking_issue_id = PyUUID(arguments["blocking_issue_id"])
                blocked_issue_id = PyUUID(arguments["blocked_issue_id"])
                dependency_type = arguments.get("dependency_type", "blocks")

                try:
                    async for session in get_db_session():
                        dep_repo = IssueDependencyRepository(session)
                        result = await dep_repo.create_dependency(
                            blocking_issue_id, blocked_issue_id, dependency_type
                        )
                        await session.commit()
                        return [TextContent(
                            type="text",
                            text=f"Dependency created: Issue {blocking_issue_id} blocks issue {blocked_issue_id}"
                        )]
                except ValueError as e:
                    return [TextContent(type="text", text=f"Error: {str(e)}")]
                except Exception:
                    logger.exception("Error creating dependency")
                    return [TextContent(type="text", text="Error creating dependency")]

            elif name == "remove_blocker":
                from uuid import UUID as PyUUID
                from turbo.core.database.connection import get_db_session
                from turbo.core.repositories.issue_dependency import IssueDependencyRepository

                blocking_issue_id = PyUUID(arguments["blocking_issue_id"])
                blocked_issue_id = PyUUID(arguments["blocked_issue_id"])

                try:
                    async for session in get_db_session():
                        dep_repo = IssueDependencyRepository(session)
                        success = await dep_repo.delete_dependency(blocking_issue_id, blocked_issue_id)
                        await session.commit()
                        if success:
                            return [TextContent(
                                type="text",
                                text=f"Dependency removed: Issue {blocking_issue_id} no longer blocks issue {blocked_issue_id}"
                            )]
                        else:
                            return [TextContent(type="text", text="Dependency not found")]
                except Exception:
                    logger.exception("Error removing dependency")
                    return [TextContent(type="text", text="Error removing dependency")]

            elif name == "get_blocking_issues":
                from uuid import UUID as PyUUID
                from turbo.core.database.connection import get_db_session
                from turbo.core.repositories.issue_dependency import IssueDependencyRepository

                issue_id = PyUUID(arguments["issue_id"])

                try:
                    async for session in get_db_session():
                        dep_repo = IssueDependencyRepository(session)
                        blocking_issues = await dep_repo.get_blocking_issues(issue_id)
                        return [TextContent(
                            type="text",
                            text=json.dumps({
                                "issue_id": str(issue_id),
                                "blocking_issues": [str(id) for id in blocking_issues],
                                "count": len(blocking_issues)
                            }, indent=2)
                        )]
                except Exception:
                    logger.exception("Error getting blocking issues")
                    return [TextContent(type="text", text="Error getting blocking issues")]

            elif name == "get_blocked_issues":
                from uuid import UUID as PyUUID
                from turbo.core.database.connection import get_db_session
                from turbo.core.repositories.issue_dependency import IssueDependencyRepository

                issue_id = PyUUID(arguments["issue_id"])

                try:
                    async for session in get_db_session():
                        dep_repo = IssueDependencyRepository(session)
                        blocked_issues = await dep_repo.get_blocked_issues(issue_id)
                        return [TextContent(
                            type="text",
                            text=json.dumps({
                                "issue_id": str(issue_id),
                                "blocked_issues": [str(id) for id in blocked_issues],
                                "count": len(blocked_issues)
                            }, indent=2)
                        )]
                except Exception:
                    logger.exception("Error getting blocked issues")
                    return [TextContent(type="text", text="Error getting blocked issues")]

            # Tags
            elif name == "create_tag":
                response = await client.post(f"{TURBO_API_URL}/tags/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "list_tags":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/tags/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_tag":
                tag_id = arguments["tag_id"]
                response = await client.get(f"{TURBO_API_URL}/tags/{tag_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_tag":
                tag_id = arguments.pop("tag_id")
                response = await client.put(f"{TURBO_API_URL}/tags/{tag_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_tag":
                tag_id = arguments["tag_id"]
                response = await client.delete(f"{TURBO_API_URL}/tags/{tag_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Tag deleted successfully")]

            elif name == "add_tag_to_entity":
                entity_type = arguments["entity_type"]
                entity_id = arguments["entity_id"]
                tag_id = arguments["tag_id"]

                if entity_type == "project":
                    response = await client.post(f"{TURBO_API_URL}/projects/{entity_id}/tags/{tag_id}")
                elif entity_type == "issue":
                    response = await client.post(f"{TURBO_API_URL}/issues/{entity_id}/tags/{tag_id}")
                else:
                    return [TextContent(type="text", text=f"Unsupported entity type: {entity_type}")]

                response.raise_for_status()
                return [TextContent(type="text", text=f"Tag {tag_id} added to {entity_type} {entity_id}")]

            elif name == "remove_tag_from_entity":
                entity_type = arguments["entity_type"]
                entity_id = arguments["entity_id"]
                tag_id = arguments["tag_id"]

                if entity_type == "project":
                    response = await client.delete(f"{TURBO_API_URL}/projects/{entity_id}/tags/{tag_id}")
                elif entity_type == "issue":
                    response = await client.delete(f"{TURBO_API_URL}/issues/{entity_id}/tags/{tag_id}")
                else:
                    return [TextContent(type="text", text=f"Unsupported entity type: {entity_type}")]

                response.raise_for_status()
                return [TextContent(type="text", text=f"Tag {tag_id} removed from {entity_type} {entity_id}")]

            # Blueprints
            elif name == "list_blueprints":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/blueprints/", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "get_blueprint":
                blueprint_id = arguments["blueprint_id"]
                response = await client.get(f"{TURBO_API_URL}/blueprints/{blueprint_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "create_blueprint":
                response = await client.post(f"{TURBO_API_URL}/blueprints/", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "update_blueprint":
                blueprint_id = arguments.pop("blueprint_id")
                response = await client.put(f"{TURBO_API_URL}/blueprints/{blueprint_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=response.text)]

            elif name == "delete_blueprint":
                blueprint_id = arguments["blueprint_id"]
                response = await client.delete(f"{TURBO_API_URL}/blueprints/{blueprint_id}")
                response.raise_for_status()
                return [TextContent(type="text", text="Blueprint deleted successfully")]

            elif name == "activate_blueprint":
                blueprint_id = arguments["blueprint_id"]
                response = await client.put(
                    f"{TURBO_API_URL}/blueprints/{blueprint_id}",
                    json={"is_active": True}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=f"Blueprint {blueprint_id} activated")]

            elif name == "deactivate_blueprint":
                blueprint_id = arguments["blueprint_id"]
                response = await client.put(
                    f"{TURBO_API_URL}/blueprints/{blueprint_id}",
                    json={"is_active": False}
                )
                response.raise_for_status()
                return [TextContent(type="text", text=f"Blueprint {blueprint_id} deactivated")]

            # Git Worktree Management (runs locally, not via API)
            elif name == "start_work_on_issue":
                issue_id = arguments["issue_id"]
                started_by = arguments["started_by"]
                project_path = arguments.get("project_path")

                # Get issue details first
                issue_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                issue_response.raise_for_status()
                issue_data = issue_response.json()

                # Get project details
                project_response = await client.get(f"{TURBO_API_URL}/projects/{issue_data['project_id']}")
                project_response.raise_for_status()
                project_data = project_response.json()

                # Create worktree locally if project_path provided
                worktree_info = None
                if project_path:
                    try:
                        worktree_info = create_worktree_local(
                            issue_key=issue_data["issue_key"],
                            issue_title=issue_data["title"],
                            project_name=project_data["name"],
                            project_path=project_path,
                            base_branch="main"
                        )
                    except Exception:
                        logger.exception("Failed to create worktree")
                        return [TextContent(type="text", text="Failed to create worktree")]

                # Update issue via API (status change, work log creation)
                payload = {
                    "started_by": started_by,
                }
                if worktree_info:
                    payload["project_path"] = worktree_info["worktree_path"]

                response = await client.post(
                    f"{TURBO_API_URL}/issues/{issue_id}/start-work",
                    json=payload
                )
                response.raise_for_status()

                # Return combined response
                api_result = response.json()
                if worktree_info:
                    api_result["worktree"] = worktree_info

                return [TextContent(type="text", text=json.dumps(api_result, indent=2))]

            elif name == "submit_issue_with_worktree":
                issue_id = arguments["issue_id"]
                commit_url = arguments["commit_url"]
                cleanup_worktree = arguments.get("cleanup_worktree", True)

                # Get issue details to find worktree path
                issue_response = await client.get(f"{TURBO_API_URL}/issues/{issue_id}")
                issue_response.raise_for_status()
                issue_data = issue_response.json()

                # Update issue via API first (status change, end work log)
                response = await client.post(
                    f"{TURBO_API_URL}/issues/{issue_id}/submit-review",
                    json={"commit_url": commit_url, "cleanup_worktree": False}  # We'll handle cleanup locally
                )
                response.raise_for_status()
                api_result = response.json()

                # Clean up worktree locally if requested
                worktree_removed = False
                if cleanup_worktree:
                    # Try to get worktree path from work logs
                    work_logs = issue_data.get("work_logs", [])
                    if work_logs:
                        latest_log = work_logs[-1]
                        worktree_path = latest_log.get("worktree_path")
                        if worktree_path:
                            try:
                                # Check for uncommitted changes first
                                status = get_worktree_status_local(worktree_path)
                                if status["has_changes"]:
                                    return [TextContent(type="text", text=f"Warning: Worktree at {worktree_path} has {status['uncommitted_files']} uncommitted files. Please commit or stash changes before submitting for review.")]

                                # Remove worktree
                                worktree_removed = remove_worktree_local(worktree_path, force=False)
                                api_result["worktree_removed"] = worktree_removed
                            except Exception:
                                logger.exception("Worktree cleanup failed")
                                api_result["worktree_cleanup_error"] = "Cleanup failed"

                return [TextContent(type="text", text=json.dumps(api_result, indent=2))]

            elif name == "list_worktrees":
                project_path = arguments["project_path"]
                try:
                    worktrees = list_worktrees_local(project_path)
                    return [TextContent(type="text", text=json.dumps(worktrees, indent=2))]
                except Exception:
                    logger.exception("Error listing worktrees")
                    return [TextContent(type="text", text="Error listing worktrees")]

            elif name == "get_worktree_status":
                worktree_path = arguments["worktree_path"]
                try:
                    status = get_worktree_status_local(worktree_path)
                    return [TextContent(type="text", text=json.dumps(status, indent=2))]
                except Exception:
                    logger.exception("Error getting worktree status")
                    return [TextContent(type="text", text="Error getting worktree status")]

            # Job Search Tools
            elif name == "create_search_criteria":
                response = await client.post(f"{TURBO_API_URL}/job-search/criteria", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            elif name == "list_search_criteria":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/job-search/criteria", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            elif name == "get_search_criteria":
                criteria_id = arguments["criteria_id"]
                response = await client.get(f"{TURBO_API_URL}/job-search/criteria/{criteria_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            elif name == "update_search_criteria":
                criteria_id = arguments.pop("criteria_id")
                response = await client.put(f"{TURBO_API_URL}/job-search/criteria/{criteria_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            elif name == "execute_job_search":
                criteria_id = arguments["criteria_id"]
                sources = arguments.get("sources")
                params = {"sources": sources} if sources else {}
                response = await client.post(f"{TURBO_API_URL}/job-search/execute/{criteria_id}", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            elif name == "list_job_postings":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/job-search/postings", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            elif name == "get_job_posting":
                posting_id = arguments["posting_id"]
                response = await client.get(f"{TURBO_API_URL}/job-search/postings/{posting_id}")
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            elif name == "update_job_posting":
                posting_id = arguments.pop("posting_id")
                response = await client.put(f"{TURBO_API_URL}/job-search/postings/{posting_id}", json=arguments)
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            elif name == "get_job_search_history":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{TURBO_API_URL}/job-search/history", params=params)
                response.raise_for_status()
                return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except httpx.HTTPError as e:
            logger.exception("Error calling Turbo API")
            error_msg = "Error calling Turbo API"
            if hasattr(e, "response") and e.response is not None:
                error_msg = f"API Error (HTTP {e.response.status_code})"
            return [TextContent(type="text", text=error_msg)]
        except Exception:
            logger.exception("Unexpected error in MCP tool handler")
            return [TextContent(type="text", text="Unexpected error processing request")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
