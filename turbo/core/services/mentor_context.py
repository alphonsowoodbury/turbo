"""Service for compiling workspace context for mentors."""

from datetime import datetime, timedelta
from uuid import UUID

from turbo.core.models.mentor import Mentor
from turbo.core.repositories.document import DocumentRepository
from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.project import ProjectRepository


class MentorContextService:
    """Service for compiling rich workspace context for mentor conversations."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        issue_repository: IssueRepository,
        document_repository: DocumentRepository,
    ) -> None:
        self._project_repository = project_repository
        self._issue_repository = issue_repository
        self._document_repository = document_repository

    async def compile_workspace_context(
        self, mentor: Mentor
    ) -> dict:
        """Compile comprehensive workspace context for a mentor."""
        prefs = mentor.context_preferences
        max_items = prefs.get("max_items", 10)

        context = {
            "workspace": mentor.workspace,
            "work_company": mentor.work_company,
            "compiled_at": datetime.utcnow().isoformat(),
        }

        # Get projects if enabled
        if prefs.get("include_projects", True):
            projects = await self._get_workspace_projects(
                mentor.workspace, mentor.work_company, limit=max_items
            )
            context["projects"] = [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "description": p.description,
                    "status": p.status,
                    "priority": p.priority,
                    "completion": p.completion_percentage,
                }
                for p in projects
            ]

        # Get issues if enabled
        if prefs.get("include_issues", True):
            issues = await self._get_workspace_issues(
                mentor.workspace, mentor.work_company, limit=max_items * 2
            )
            context["issues"] = [
                {
                    "id": str(i.id),
                    "title": i.title,
                    "description": i.description[:200] + "..." if len(i.description) > 200 else i.description,
                    "type": i.type,
                    "status": i.status,
                    "priority": i.priority,
                    "assignee": i.assignee,
                }
                for i in issues
            ]

        # Get documents if enabled
        if prefs.get("include_documents", True):
            documents = await self._get_workspace_documents(
                mentor.workspace, mentor.work_company, limit=max_items
            )
            context["documents"] = [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "type": d.type,
                    "summary": d.content[:150] + "..." if len(d.content) > 150 else d.content,
                }
                for d in documents
            ]

        return context

    async def format_context_as_markdown(self, context: dict) -> str:
        """Format context as markdown for Claude Code."""
        md_lines = [
            "# Workspace Context",
            "",
            f"**Workspace:** {context['workspace']}",
        ]

        if context.get("work_company"):
            md_lines.append(f"**Company:** {context['work_company']}")

        md_lines.append(f"**Compiled at:** {context['compiled_at']}")
        md_lines.append("")

        # Projects section
        if projects := context.get("projects"):
            md_lines.extend([
                "## Active Projects",
                ""
            ])
            for p in projects:
                md_lines.extend([
                    f"### {p['name']} ({p['status']})",
                    f"**Priority:** {p['priority']} | **Completion:** {p['completion']}%",
                    f"{p['description'][:200]}",
                    ""
                ])

        # Issues section
        if issues := context.get("issues"):
            md_lines.extend([
                "## Recent Issues",
                ""
            ])
            for i in issues[:10]:  # Limit to 10 most relevant
                md_lines.extend([
                    f"### [{i['status']}] {i['title']}",
                    f"**Type:** {i['type']} | **Priority:** {i['priority']}",
                    f"{i['description']}",
                    ""
                ])

        # Documents section
        if documents := context.get("documents"):
            md_lines.extend([
                "## Key Documents",
                ""
            ])
            for d in documents[:5]:  # Limit to 5 most relevant
                md_lines.extend([
                    f"### {d['title']} ({d['type']})",
                    f"{d['summary']}",
                    ""
                ])

        return "\n".join(md_lines)

    async def _get_workspace_projects(
        self, workspace: str, work_company: str | None, limit: int
    ) -> list:
        """Get projects for workspace."""
        return await self._project_repository.get_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
        )

    async def _get_workspace_issues(
        self, workspace: str, work_company: str | None, limit: int
    ) -> list:
        """Get issues for workspace."""
        return await self._issue_repository.get_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
        )

    async def _get_workspace_documents(
        self, workspace: str, work_company: str | None, limit: int
    ) -> list:
        """Get documents for workspace."""
        return await self._document_repository.get_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
        )
