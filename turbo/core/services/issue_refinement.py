"""Issue Refinement Service - AI-powered issue hygiene and maintenance."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.issue_dependency import IssueDependencyRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.schemas.issue import IssueUpdate


class IssueRefinementService:
    """
    Service for analyzing and refining issues.

    Provides hybrid human-in-loop refinement:
    - SAFE changes: Auto-applied (typos, tags, formatting)
    - REQUIRES_APPROVAL: Manual approval needed (status, dependencies, links)
    """

    def __init__(
        self,
        session: AsyncSession,
        issue_repo: IssueRepository,
        dependency_repo: IssueDependencyRepository,
        project_repo: ProjectRepository,
        tag_repo: TagRepository,
    ):
        self.session = session
        self.issue_repo = issue_repo
        self.dependency_repo = dependency_repo
        self.project_repo = project_repo
        self.tag_repo = tag_repo

    async def analyze_issues(
        self,
        project_id: UUID | None = None,
        include_safe: bool = True,
        include_approval_needed: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze issues and generate refinement plan.

        Args:
            project_id: Optional project to scope analysis to
            include_safe: Include safe auto-apply changes
            include_approval_needed: Include changes requiring approval

        Returns:
            Dictionary with safe_changes and approval_needed arrays
        """
        # Get issues to analyze with relationships eagerly loaded
        if project_id:
            issues = await self.issue_repo.get_by_project_with_relationships(project_id)
        else:
            issues = await self.issue_repo.get_all_with_relationships()

        safe_changes = []
        approval_needed = []

        # Analyze each issue
        for issue in issues:
            # 1. Check for missing tags (SAFE)
            if include_safe:
                suggested_tags = await self._suggest_tags(issue)
                if suggested_tags:
                    safe_changes.append({
                        "type": "add_tags",
                        "issue_id": str(issue.id),
                        "issue_title": issue.title,
                        "action": f"Add tags: {', '.join(suggested_tags)}",
                        "tags": suggested_tags,
                        "reason": "Content-based tag suggestion",
                    })

            # 2. Check for stale status (REQUIRES_APPROVAL)
            if include_approval_needed:
                if await self._is_stale_status(issue):
                    approval_needed.append({
                        "type": "update_status",
                        "issue_id": str(issue.id),
                        "issue_title": issue.title,
                        "current_status": issue.status,
                        "proposed_status": "open",
                        "action": f"Reset stale '{issue.status}' → 'open'",
                        "reason": f"No updates in 30+ days while marked as '{issue.status}'",
                        "last_updated": issue.updated_at.isoformat(),
                    })

            # 3. Check for missing dependencies (REQUIRES_APPROVAL)
            if include_approval_needed:
                suggested_deps = await self._suggest_dependencies(issue, issues)
                for dep in suggested_deps:
                    approval_needed.append({
                        "type": "add_dependency",
                        "issue_id": str(issue.id),
                        "issue_title": issue.title,
                        "blocking_issue_id": str(dep["blocking_id"]),
                        "blocking_issue_title": dep["blocking_title"],
                        "action": f"Add blocker: '{dep['blocking_title']}' blocks this issue",
                        "reason": dep["reason"],
                    })

            # 4. Check for missing documentation (SAFE - add template)
            if include_safe:
                if not issue.description or len(issue.description.strip()) < 20:
                    safe_changes.append({
                        "type": "add_description_template",
                        "issue_id": str(issue.id),
                        "issue_title": issue.title,
                        "action": "Add description template",
                        "template": self._get_description_template(issue.type),
                        "reason": "Missing or very short description",
                    })

            # 5. Check for orphaned issues (REQUIRES_APPROVAL)
            if include_approval_needed:
                if await self._is_orphaned(issue):
                    approval_needed.append({
                        "type": "flag_orphaned",
                        "issue_id": str(issue.id),
                        "issue_title": issue.title,
                        "action": "Flag as orphaned (no project/assignee/tags/milestone)",
                        "reason": "Issue lacks context - needs project, assignee, or milestone",
                        "missing": self._get_missing_context(issue),
                    })

        return {
            "summary": {
                "total_issues_analyzed": len(issues),
                "safe_changes_count": len(safe_changes),
                "approval_needed_count": len(approval_needed),
                "project_id": str(project_id) if project_id else "all",
            },
            "safe_changes": safe_changes,
            "approval_needed": approval_needed,
        }

    async def execute_safe_changes(
        self, safe_changes: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Execute all safe changes automatically.

        Args:
            safe_changes: List of safe changes from analyze_issues

        Returns:
            Execution results
        """
        results = {"success": [], "failed": []}

        for change in safe_changes:
            try:
                if change["type"] == "add_tags":
                    # Note: Tag addition would need tag IDs
                    # For now, just record intent
                    results["success"].append({
                        "issue_id": change["issue_id"],
                        "action": change["action"],
                        "status": "tags_suggested",
                    })

                elif change["type"] == "add_description_template":
                    issue_id = UUID(change["issue_id"])
                    issue = await self.issue_repo.get_by_id(issue_id)
                    if issue and (not issue.description or len(issue.description.strip()) < 20):
                        # Append template to existing description
                        new_desc = (issue.description or "").strip() + "\n\n" + change["template"]
                        update = IssueUpdate(description=new_desc)
                        await self.issue_repo.update(issue_id, update)
                        await self.session.commit()
                        results["success"].append({
                            "issue_id": change["issue_id"],
                            "action": change["action"],
                            "status": "completed",
                        })

            except Exception as e:
                results["failed"].append({
                    "issue_id": change.get("issue_id"),
                    "action": change.get("action"),
                    "error": str(e),
                })

        return results

    async def execute_approved_changes(
        self, approved_changes: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Execute changes that have been approved by user.

        Args:
            approved_changes: List of approved changes from approval_needed

        Returns:
            Execution results
        """
        results = {"success": [], "failed": []}

        for change in approved_changes:
            try:
                if change["type"] == "update_status":
                    issue_id = UUID(change["issue_id"])
                    update = IssueUpdate(status=change["proposed_status"])
                    await self.issue_repo.update(issue_id, update)
                    await self.session.commit()
                    results["success"].append({
                        "issue_id": change["issue_id"],
                        "action": change["action"],
                        "status": "completed",
                    })

                elif change["type"] == "add_dependency":
                    blocking_id = UUID(change["blocking_issue_id"])
                    blocked_id = UUID(change["issue_id"])
                    await self.dependency_repo.create_dependency(
                        blocking_id, blocked_id, "blocks"
                    )
                    await self.session.commit()
                    results["success"].append({
                        "issue_id": change["issue_id"],
                        "action": change["action"],
                        "status": "completed",
                    })

                elif change["type"] == "flag_orphaned":
                    # Could add a "needs_review" tag or update priority
                    results["success"].append({
                        "issue_id": change["issue_id"],
                        "action": change["action"],
                        "status": "flagged",
                    })

            except Exception as e:
                results["failed"].append({
                    "issue_id": change.get("issue_id"),
                    "action": change.get("action"),
                    "error": str(e),
                })

        return results

    # --- Analysis Helper Methods ---

    async def _suggest_tags(self, issue) -> list[str]:
        """Suggest tags based on issue content."""
        suggested = []
        content = (issue.title + " " + (issue.description or "")).lower()

        # Common patterns
        patterns = {
            "frontend": ["ui", "frontend", "react", "component", "css"],
            "backend": ["api", "backend", "server", "database", "endpoint"],
            "bug": ["bug", "error", "crash", "broken", "fix"],
            "documentation": ["docs", "documentation", "readme", "guide"],
            "testing": ["test", "testing", "qa", "coverage"],
            "performance": ["performance", "slow", "optimize", "speed"],
        }

        for tag_name, keywords in patterns.items():
            if any(kw in content for kw in keywords):
                suggested.append(tag_name)

        return suggested[:3]  # Max 3 suggestions

    async def _is_stale_status(self, issue) -> bool:
        """Check if issue has stale status."""
        if issue.status not in ["in_progress", "review", "testing"]:
            return False

        # Check if no updates in 30 days
        stale_threshold = datetime.now(timezone.utc) - timedelta(days=30)

        # Handle both timezone-aware and naive datetimes
        issue_updated = issue.updated_at
        if issue_updated.tzinfo is None:
            issue_updated = issue_updated.replace(tzinfo=timezone.utc)

        return issue_updated < stale_threshold

    async def _suggest_dependencies(self, issue, all_issues: list) -> list[dict]:
        """Suggest dependencies by analyzing issue descriptions."""
        suggestions = []
        desc = issue.description or ""

        # Look for patterns like "blocked by #123" or "depends on Issue-456"
        patterns = [
            r"blocked by.*?#(\d+)",
            r"depends on.*?#(\d+)",
            r"requires.*?#(\d+)",
            r"needs.*?issue[- ](\d+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, desc, re.IGNORECASE)
            for match in matches:
                # Try to find issue by number (would need issue number field)
                # For now, just note the pattern was found
                suggestions.append({
                    "blocking_id": issue.id,  # Placeholder
                    "blocking_title": f"Issue #{match}",
                    "reason": f"Mentioned in description: '{match}'",
                })

        return suggestions[:5]  # Max 5 suggestions

    async def _is_orphaned(self, issue) -> bool:
        """Check if issue is orphaned (lacks context)."""
        return (
            not issue.project_id
            and not issue.assignee
            and not issue.milestones
            and issue.status == "open"
        )

    def _get_missing_context(self, issue) -> list[str]:
        """Get list of missing context fields."""
        missing = []
        if not issue.project_id:
            missing.append("project")
        if not issue.assignee:
            missing.append("assignee")
        if not issue.milestones:
            missing.append("milestone")
        return missing

    def _get_description_template(self, issue_type: str) -> str:
        """Get description template based on issue type."""
        templates = {
            "bug": """
## Bug Description
<!-- Describe the bug -->

## Steps to Reproduce
1.
2.
3.

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens -->
""",
            "feature": """
## Feature Description
<!-- Describe the feature -->

## User Story
As a [user type], I want [goal] so that [benefit].

## Acceptance Criteria
- [ ]
- [ ]
- [ ]
""",
            "task": """
## Task Description
<!-- Describe what needs to be done -->

## Checklist
- [ ]
- [ ]
- [ ]
""",
        }
        return templates.get(issue_type, templates["task"])
