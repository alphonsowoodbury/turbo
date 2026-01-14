"""Worktrees API endpoints."""

import os
import subprocess
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class WorktreeInfo(BaseModel):
    """Worktree information."""

    path: str
    branch: str
    commit_hash: str
    is_locked: bool
    issue_key: str | None = None


class WorktreeListResponse(BaseModel):
    """Response for listing worktrees."""

    worktrees: List[WorktreeInfo]
    total: int
    worktree_base_path: str


def get_worktree_base_path() -> Path:
    """Get the worktree base path from environment or default."""
    base_path = os.environ.get("WORKTREE_BASE_PATH")
    if not base_path:
        base_path = str(Path.home() / "worktrees")
    return Path(base_path)


def parse_worktree_info(worktree_path: str) -> WorktreeInfo | None:
    """Parse worktree information from path."""
    try:
        path = Path(worktree_path)

        # Get branch name
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
        )
        branch = result.stdout.strip() if result.returncode == 0 else "unknown"

        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
        )
        commit_hash = result.stdout.strip() if result.returncode == 0 else "unknown"

        # Check if locked
        lock_file = path / ".git" / "locked"
        is_locked = lock_file.exists() if (path / ".git").exists() else False

        # Extract issue key from directory name (e.g., turbo-code-platform-turbocode-121)
        dir_name = path.name
        issue_key = None
        if "-turbocode-" in dir_name.lower():
            parts = dir_name.lower().split("-turbocode-")
            if len(parts) == 2:
                issue_key = f"TURBOCODE-{parts[1]}"

        return WorktreeInfo(
            path=str(path),
            branch=branch,
            commit_hash=commit_hash,
            is_locked=is_locked,
            issue_key=issue_key,
        )
    except Exception:
        return None


@router.get("/", response_model=WorktreeListResponse)
async def list_worktrees():
    """
    List all git worktrees in the worktree base directory.

    Returns information about each worktree including:
    - Path
    - Branch name
    - Current commit hash
    - Lock status
    - Associated issue key (if applicable)
    """
    base_path = get_worktree_base_path()

    if not base_path.exists():
        return WorktreeListResponse(
            worktrees=[],
            total=0,
            worktree_base_path=str(base_path),
        )

    worktrees = []

    # List all directories in worktree base path
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            worktree_info = parse_worktree_info(str(item))
            if worktree_info:
                worktrees.append(worktree_info)

    # Sort by issue key or path
    worktrees.sort(key=lambda w: w.issue_key or w.path)

    return WorktreeListResponse(
        worktrees=worktrees,
        total=len(worktrees),
        worktree_base_path=str(base_path),
    )


@router.delete("/{issue_key}")
async def delete_worktree(issue_key: str):
    """
    Delete a worktree by issue key.

    This removes the worktree directory and prunes git references.
    """
    base_path = get_worktree_base_path()

    # Find worktree with matching issue key
    for item in base_path.iterdir():
        if item.is_dir() and issue_key.lower() in item.name.lower():
            worktree_path = item
            break
    else:
        raise HTTPException(status_code=404, detail=f"Worktree for {issue_key} not found")

    # Get git root from main project
    project_path = os.environ.get("TURBO_PROJECT_PATH", os.getcwd())

    try:
        # Remove worktree
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=project_path,
            capture_output=True,
            check=True,
        )

        # Prune worktree references
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=project_path,
            capture_output=True,
        )

        return {"status": "success", "message": f"Worktree for {issue_key} deleted"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete worktree: {e.stderr.decode()}"
        )
