"""
Action Executor Service

Executes approved actions via direct backend API calls.
Minimizes AI/subagent usage and provides direct execution when possible.
"""

from typing import Dict, Any, Optional
from uuid import UUID
import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.repositories.action_approval_repository import ActionApprovalRepository
from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.models import Comment
from turbo.core.schemas.issue import IssueUpdate
from turbo.core.schemas.project import ProjectUpdate


class ActionExecutor:
    """
    Executes approved actions via direct backend operations.

    Prefers direct database updates over AI/subagent calls for safety and speed.
    Only uses subagents for complex operations that require AI reasoning.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.approval_repo = ActionApprovalRepository(session)

    async def execute_action(self, approval_id: UUID) -> Dict[str, Any]:
        """
        Execute an approved action.

        Args:
            approval_id: UUID of the action approval

        Returns:
            Result dictionary with success/error info
        """
        # Get approval
        approval = await self.approval_repo.get(approval_id)
        if not approval:
            return {"success": False, "error": "Approval not found"}

        action_type = approval.action_type
        action_params = approval.action_params
        entity_type = approval.entity_type
        entity_id = approval.entity_id

        # Execute based on action type
        try:
            if action_type == "add_comment":
                result = await self._add_comment(entity_type, entity_id, action_params)
            elif action_type == "add_tag":
                result = await self._add_tag(entity_type, entity_id, action_params)
            elif action_type == "update_status":
                result = await self._update_status(entity_type, entity_id, action_params)
            elif action_type == "update_priority":
                result = await self._update_priority(entity_type, entity_id, action_params)
            elif action_type == "update_description":
                result = await self._update_description(entity_type, entity_id, action_params)
            elif action_type == "update_title":
                result = await self._update_title(entity_type, entity_id, action_params)
            elif action_type == "add_assignee":
                result = await self._add_assignee(entity_type, entity_id, action_params)
            elif action_type == "close_issue":
                result = await self._close_issue(entity_id, action_params)
            elif action_type == "reopen_issue":
                result = await self._reopen_issue(entity_id, action_params)
            elif action_type == "add_dependency":
                result = await self._add_dependency(entity_id, action_params)
            elif action_type == "archive_project":
                result = await self._archive_project(entity_id, action_params)
            else:
                # Unknown action - use subagent
                result = await self._execute_via_subagent(approval)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_type": action_type
            }

    async def _add_comment(self, entity_type: str, entity_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a comment to an entity."""
        content = params.get("content", "")
        author_type = params.get("author_type", "ai")
        author_name = params.get("author_name", "Claude")

        comment = Comment(
            entity_type=entity_type,
            entity_id=entity_id,
            content=content,
            author_type=author_type,
            author_name=author_name,
        )
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)

        return {
            "success": True,
            "action": "add_comment",
            "comment_id": str(comment.id),
            "used_subagent": False,
        }

    async def _add_tag(self, entity_type: str, entity_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a tag to an entity."""
        tag_repo = TagRepository(self.session)

        tag_id = params.get("tag_id")
        if not tag_id:
            return {"success": False, "error": "tag_id is required"}

        # Add tag to entity
        if entity_type == "issue":
            issue_repo = IssueRepository(self.session)
            issue = await issue_repo.get(entity_id)
            if issue:
                await issue_repo.add_tag(entity_id, UUID(tag_id))
        elif entity_type == "project":
            project_repo = ProjectRepository(self.session)
            project = await project_repo.get(entity_id)
            if project:
                await project_repo.add_tag(entity_id, UUID(tag_id))
        else:
            return {"success": False, "error": f"Unsupported entity type: {entity_type}"}

        return {
            "success": True,
            "action": "add_tag",
            "used_subagent": False,
        }

    async def _update_status(self, entity_type: str, entity_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity status."""
        new_status = params.get("status")
        if not new_status:
            return {"success": False, "error": "status is required"}

        if entity_type == "issue":
            issue_repo = IssueRepository(self.session)
            update_data = IssueUpdate(status=new_status)
            issue = await issue_repo.update(entity_id, update_data)
            if not issue:
                return {"success": False, "error": "Issue not found"}
        elif entity_type == "project":
            project_repo = ProjectRepository(self.session)
            update_data = ProjectUpdate(status=new_status)
            project = await project_repo.update(entity_id, update_data)
            if not project:
                return {"success": False, "error": "Project not found"}
        else:
            return {"success": False, "error": f"Unsupported entity type: {entity_type}"}

        return {
            "success": True,
            "action": "update_status",
            "new_status": new_status,
            "used_subagent": False,
        }

    async def _update_priority(self, entity_type: str, entity_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity priority."""
        new_priority = params.get("priority")
        if not new_priority:
            return {"success": False, "error": "priority is required"}

        if entity_type == "issue":
            issue_repo = IssueRepository(self.session)
            update_data = IssueUpdate(priority=new_priority)
            issue = await issue_repo.update(entity_id, update_data)
            if not issue:
                return {"success": False, "error": "Issue not found"}
        elif entity_type == "project":
            project_repo = ProjectRepository(self.session)
            update_data = ProjectUpdate(priority=new_priority)
            project = await project_repo.update(entity_id, update_data)
            if not project:
                return {"success": False, "error": "Project not found"}
        else:
            return {"success": False, "error": f"Unsupported entity type: {entity_type}"}

        return {
            "success": True,
            "action": "update_priority",
            "new_priority": new_priority,
            "used_subagent": False,
        }

    async def _update_description(self, entity_type: str, entity_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity description."""
        new_description = params.get("description")
        if not new_description:
            return {"success": False, "error": "description is required"}

        if entity_type == "issue":
            issue_repo = IssueRepository(self.session)
            update_data = IssueUpdate(description=new_description)
            issue = await issue_repo.update(entity_id, update_data)
            if not issue:
                return {"success": False, "error": "Issue not found"}
        elif entity_type == "project":
            project_repo = ProjectRepository(self.session)
            update_data = ProjectUpdate(description=new_description)
            project = await project_repo.update(entity_id, update_data)
            if not project:
                return {"success": False, "error": "Project not found"}
        else:
            return {"success": False, "error": f"Unsupported entity type: {entity_type}"}

        return {
            "success": True,
            "action": "update_description",
            "used_subagent": False,
        }

    async def _update_title(self, entity_type: str, entity_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity title."""
        new_title = params.get("title")
        if not new_title:
            return {"success": False, "error": "title is required"}

        if entity_type == "issue":
            issue_repo = IssueRepository(self.session)
            update_data = IssueUpdate(title=new_title)
            issue = await issue_repo.update(entity_id, update_data)
            if not issue:
                return {"success": False, "error": "Issue not found"}
        elif entity_type == "project":
            project_repo = ProjectRepository(self.session)
            update_data = ProjectUpdate(name=new_title)  # Projects use 'name'
            project = await project_repo.update(entity_id, update_data)
            if not project:
                return {"success": False, "error": "Project not found"}
        else:
            return {"success": False, "error": f"Unsupported entity type: {entity_type}"}

        return {
            "success": True,
            "action": "update_title",
            "new_title": new_title,
            "used_subagent": False,
        }

    async def _add_assignee(self, entity_type: str, entity_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add assignee to an entity."""
        assignee = params.get("assignee")
        if not assignee:
            return {"success": False, "error": "assignee is required"}

        if entity_type == "issue":
            issue_repo = IssueRepository(self.session)
            update_data = IssueUpdate(assignee=assignee)
            issue = await issue_repo.update(entity_id, update_data)
            if not issue:
                return {"success": False, "error": "Issue not found"}
        else:
            return {"success": False, "error": f"Unsupported entity type: {entity_type}"}

        return {
            "success": True,
            "action": "add_assignee",
            "assignee": assignee,
            "used_subagent": False,
        }

    async def _close_issue(self, issue_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close an issue."""
        issue_repo = IssueRepository(self.session)
        update_data = IssueUpdate(status="closed")
        issue = await issue_repo.update(issue_id, update_data)

        if not issue:
            return {"success": False, "error": "Issue not found"}

        # Optionally add a closing comment
        if params.get("add_comment"):
            comment = Comment(
                entity_type="issue",
                entity_id=issue_id,
                content=params.get("comment_text", "Issue closed by AI."),
                author_type="ai",
                author_name="Claude",
            )
            self.session.add(comment)
            await self.session.commit()

        return {
            "success": True,
            "action": "close_issue",
            "used_subagent": False,
        }

    async def _reopen_issue(self, issue_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reopen a closed issue."""
        issue_repo = IssueRepository(self.session)
        update_data = IssueUpdate(status="open")
        issue = await issue_repo.update(issue_id, update_data)

        if not issue:
            return {"success": False, "error": "Issue not found"}

        return {
            "success": True,
            "action": "reopen_issue",
            "used_subagent": False,
        }

    async def _add_dependency(self, issue_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a blocking dependency to an issue."""
        blocking_issue_id = params.get("blocking_issue_id")
        if not blocking_issue_id:
            return {"success": False, "error": "blocking_issue_id is required"}

        issue_repo = IssueRepository(self.session)
        await issue_repo.add_blocker(UUID(blocking_issue_id), issue_id)

        return {
            "success": True,
            "action": "add_dependency",
            "blocking_issue_id": blocking_issue_id,
            "used_subagent": False,
        }

    async def _archive_project(self, project_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Archive a project."""
        project_repo = ProjectRepository(self.session)
        update_data = ProjectUpdate(status="archived")
        project = await project_repo.update(project_id, update_data)

        if not project:
            return {"success": False, "error": "Project not found"}

        return {
            "success": True,
            "action": "archive_project",
            "used_subagent": False,
        }

    async def _execute_via_subagent(self, approval) -> Dict[str, Any]:
        """
        Execute action via a subagent when direct execution isn't available.

        This is used for complex actions that require AI reasoning.
        Subagent usage is blocked by default unless explicitly allowed.
        """
        # Check if subagent usage is allowed
        # TODO: Implement subagent blocking/allowlist system

        return {
            "success": False,
            "error": "Subagent execution not yet implemented",
            "action_type": approval.action_type,
            "used_subagent": False,
        }
