"""Service for compiling workspace context for mentors."""

from datetime import datetime, timedelta
from uuid import UUID

from turbo.core.models.mentor import Mentor
from turbo.core.repositories.document import DocumentRepository
from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.repositories.company import CompanyRepository
from turbo.core.repositories.job_application import JobApplicationRepository
from turbo.core.repositories.network_contact import NetworkContactRepository
from turbo.core.repositories.resume import ResumeRepository


class MentorContextService:
    """Service for compiling rich workspace context for mentor conversations."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        issue_repository: IssueRepository,
        document_repository: DocumentRepository,
        company_repository: CompanyRepository | None = None,
        job_application_repository: JobApplicationRepository | None = None,
        network_contact_repository: NetworkContactRepository | None = None,
        resume_repository: ResumeRepository | None = None,
    ) -> None:
        self._project_repository = project_repository
        self._issue_repository = issue_repository
        self._document_repository = document_repository
        self._company_repository = company_repository
        self._job_application_repository = job_application_repository
        self._network_contact_repository = network_contact_repository
        self._resume_repository = resume_repository

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

        # Get job applications if enabled (career data)
        if prefs.get("include_applications", False) and self._job_application_repository:
            applications = await self._job_application_repository.get_all(limit=max_items)
            context["applications"] = [
                {
                    "id": str(a.id),
                    "position_title": a.position_title,
                    "company_name": a.company_name,
                    "status": a.status,
                    "application_date": a.application_date.isoformat() if a.application_date else None,
                    "notes": a.notes[:200] + "..." if a.notes and len(a.notes) > 200 else a.notes,
                }
                for a in applications
            ]

        # Get companies if enabled (career data)
        if prefs.get("include_companies", False) and self._company_repository:
            companies = await self._company_repository.get_all(limit=max_items)
            context["companies"] = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "industry": c.industry,
                    "size": c.size,
                    "notes": c.notes[:200] + "..." if c.notes and len(c.notes) > 200 else c.notes,
                }
                for c in companies
            ]

        # Get network contacts if enabled (career data)
        if prefs.get("include_contacts", False) and self._network_contact_repository:
            contacts = await self._network_contact_repository.get_all(limit=max_items)
            context["contacts"] = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "title": c.title,
                    "company": c.company,
                    "relationship": c.relationship,
                    "last_contact_date": c.last_contact_date.isoformat() if c.last_contact_date else None,
                }
                for c in contacts
            ]

        # Get resumes if enabled (career data)
        if prefs.get("include_resumes", False) and self._resume_repository:
            resumes = await self._resume_repository.get_all(limit=5)  # Limit resumes
            context["resumes"] = [
                {
                    "id": str(r.id),
                    "title": r.title,
                    "target_role": r.target_role,
                    "target_company": r.target_company,
                    "is_primary": r.is_primary,
                }
                for r in resumes
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

        # Job applications section (career data)
        if applications := context.get("applications"):
            md_lines.extend([
                "## Job Applications",
                ""
            ])
            for a in applications:
                md_lines.extend([
                    f"### {a['position_title']} at {a['company_name']}",
                    f"**Status:** {a['status']} | **Applied:** {a['application_date'] or 'N/A'}",
                    f"{a['notes'] or 'No notes'}",
                    ""
                ])

        # Companies section (career data)
        if companies := context.get("companies"):
            md_lines.extend([
                "## Target Companies",
                ""
            ])
            for c in companies:
                md_lines.extend([
                    f"### {c['name']}",
                    f"**Industry:** {c['industry'] or 'N/A'} | **Size:** {c['size'] or 'N/A'}",
                    f"{c['notes'] or 'No research notes'}",
                    ""
                ])

        # Network contacts section (career data)
        if contacts := context.get("contacts"):
            md_lines.extend([
                "## Network Contacts",
                ""
            ])
            for c in contacts:
                md_lines.extend([
                    f"### {c['name']} - {c['title'] or 'N/A'}",
                    f"**Company:** {c['company'] or 'N/A'} | **Relationship:** {c['relationship'] or 'N/A'}",
                    f"**Last Contact:** {c['last_contact_date'] or 'Never'}",
                    ""
                ])

        # Resumes section (career data)
        if resumes := context.get("resumes"):
            md_lines.extend([
                "## Resumes",
                ""
            ])
            for r in resumes:
                primary_marker = " (PRIMARY)" if r['is_primary'] else ""
                md_lines.extend([
                    f"### {r['title']}{primary_marker}",
                    f"**Target Role:** {r['target_role'] or 'General'} | **Target Company:** {r['target_company'] or 'Any'}",
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
