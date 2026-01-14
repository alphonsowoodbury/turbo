"""Git worktree management service for parallel issue development."""

import os
import subprocess
from pathlib import Path
from typing import Optional
from uuid import UUID

from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.utils.exceptions import IssueNotFoundError, ProjectNotFoundError


class GitWorktreeService:
    """Service for managing git worktrees for parallel issue development."""

    def __init__(
        self,
        issue_repository: IssueRepository,
        project_repository: ProjectRepository,
        base_worktree_path: Optional[str] = None,
    ) -> None:
        """
        Initialize the git worktree service.

        Args:
            issue_repository: Repository for issue data access
            project_repository: Repository for project data access
            base_worktree_path: Base directory for worktrees (default: ~/worktrees/)
        """
        self._issue_repository = issue_repository
        self._project_repository = project_repository

        # Default worktree base path
        if base_worktree_path:
            self._base_path = Path(base_worktree_path).expanduser()
        else:
            self._base_path = Path.home() / "worktrees"

        # Ensure base path exists
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _get_git_root(self, project_path: str) -> Optional[Path]:
        """
        Find the git repository root for a project.

        Args:
            project_path: Path to the project directory

        Returns:
            Path to git root, or None if not a git repo
        """
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

    def _sanitize_branch_name(self, text: str) -> str:
        """
        Sanitize text for use in git branch names.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text safe for branch names
        """
        # Replace spaces and special chars with hyphens
        sanitized = text.lower()
        sanitized = "".join(c if c.isalnum() or c in "-_" else "-" for c in sanitized)
        # Remove consecutive hyphens
        while "--" in sanitized:
            sanitized = sanitized.replace("--", "-")
        # Trim hyphens from ends
        sanitized = sanitized.strip("-")
        # Limit length
        return sanitized[:50]

    async def create_worktree(
        self, issue_id: UUID, project_path: str, base_branch: str = "main"
    ) -> dict:
        """
        Create a git worktree for an issue.

        Args:
            issue_id: UUID of the issue
            project_path: Path to the main project repository
            base_branch: Base branch to create worktree from (default: main)

        Returns:
            Dictionary with worktree info:
            {
                "worktree_path": "/path/to/worktree",
                "branch_name": "CNTXT-1/fix-auth-bug",
                "issue_key": "CNTXT-1"
            }

        Raises:
            IssueNotFoundError: If issue doesn't exist
            ValueError: If not a git repository or worktree already exists
        """
        # Get issue details
        issue = await self._issue_repository.get_by_id(issue_id)
        if not issue:
            raise IssueNotFoundError(issue_id)

        # Ensure issue has a key
        if not issue.issue_key:
            raise ValueError(f"Issue {issue_id} does not have an issue_key. Only issues with keys can have worktrees.")

        # Get project to find repo path
        if not issue.project_id:
            raise ValueError("Issue must belong to a project to create a worktree")

        project = await self._project_repository.get_by_id(issue.project_id)
        if not project:
            raise ProjectNotFoundError(issue.project_id)

        # Verify project_path is a git repo
        git_root = self._get_git_root(project_path)
        if not git_root:
            raise ValueError(f"{project_path} is not a git repository")

        # Create branch name: CNTXT-1/fix-auth-bug
        sanitized_title = self._sanitize_branch_name(issue.title)
        branch_name = f"{issue.issue_key}/{sanitized_title}"

        # Create worktree path: ~/worktrees/ProjectName-CNTXT-1/
        worktree_name = f"{project.name}-{issue.issue_key}"
        worktree_name = self._sanitize_branch_name(worktree_name)
        worktree_path = self._base_path / worktree_name

        # Check if worktree already exists
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
            "issue_key": issue.issue_key,
            "git_root": str(git_root),
        }

    async def remove_worktree(self, issue_id: UUID, force: bool = False) -> bool:
        """
        Remove a git worktree for an issue.

        Args:
            issue_id: UUID of the issue
            force: Force removal even if there are uncommitted changes

        Returns:
            True if worktree was removed, False if it didn't exist

        Raises:
            IssueNotFoundError: If issue doesn't exist
            ValueError: If removal fails
        """
        # Get issue details
        issue = await self._issue_repository.get_by_id(issue_id)
        if not issue:
            raise IssueNotFoundError(issue_id)

        if not issue.issue_key:
            raise ValueError(f"Issue {issue_id} does not have an issue_key")

        # Get project
        if not issue.project_id:
            raise ValueError("Issue must belong to a project")

        project = await self._project_repository.get_by_id(issue.project_id)
        if not project:
            raise ProjectNotFoundError(issue.project_id)

        # Find worktree path
        worktree_name = f"{project.name}-{issue.issue_key}"
        worktree_name = self._sanitize_branch_name(worktree_name)
        worktree_path = self._base_path / worktree_name

        # Check if worktree exists
        if not worktree_path.exists():
            return False

        # Remove the worktree
        try:
            cmd = ["git", "worktree", "remove", str(worktree_path)]
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

    async def list_worktrees(self, project_path: str) -> list[dict]:
        """
        List all worktrees for a project.

        Args:
            project_path: Path to the main project repository

        Returns:
            List of worktree info dictionaries

        Raises:
            ValueError: If not a git repository
        """
        git_root = self._get_git_root(project_path)
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

            # Parse worktree list output
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

    async def get_worktree_status(self, worktree_path: str) -> dict:
        """
        Get the git status of a worktree.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Dictionary with status info:
            {
                "has_changes": bool,
                "uncommitted_files": int,
                "branch": str
            }

        Raises:
            ValueError: If path is not a git worktree
        """
        worktree_path = Path(worktree_path)
        if not worktree_path.exists():
            raise ValueError(f"Worktree does not exist at {worktree_path}")

        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                check=True,
            )
            branch = branch_result.stdout.strip()

            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                check=True,
            )

            uncommitted = [
                line for line in status_result.stdout.strip().split("\n") if line
            ]

            return {
                "has_changes": len(uncommitted) > 0,
                "uncommitted_files": len(uncommitted),
                "branch": branch,
                "path": str(worktree_path),
            }

        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to get worktree status: {e.stderr}")
