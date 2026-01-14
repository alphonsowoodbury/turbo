"""JobApplication service for business logic operations."""

from uuid import UUID

from turbo.core.repositories.company import CompanyRepository
from turbo.core.repositories.job_application import JobApplicationRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.repositories.resume import ResumeRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
)
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import (
    JobApplicationNotFoundError,
)


class JobApplicationService:
    """Service for job application business logic."""

    def __init__(
        self,
        job_application_repository: JobApplicationRepository,
        company_repository: CompanyRepository,
        resume_repository: ResumeRepository,
        project_repository: ProjectRepository,
        tag_repository: TagRepository,
    ) -> None:
        self._job_application_repository = job_application_repository
        self._company_repository = company_repository
        self._resume_repository = resume_repository
        self._project_repository = project_repository
        self._tag_repository = tag_repository

    async def create_job_application(
        self, application_data: JobApplicationCreate
    ) -> JobApplicationResponse:
        """Create a new job application."""
        # Strip emojis from text fields
        if application_data.job_title:
            application_data.job_title = strip_emojis(application_data.job_title)
        if application_data.job_description:
            application_data.job_description = strip_emojis(application_data.job_description)
        if application_data.interview_notes:
            application_data.interview_notes = strip_emojis(application_data.interview_notes)
        if application_data.notes:
            application_data.notes = strip_emojis(application_data.notes)

        # Extract association IDs before creating the application
        tag_ids = application_data.tag_ids

        # Create application without association fields
        application_dict = application_data.model_dump(exclude={"tag_ids"})
        application = await self._job_application_repository.create(
            JobApplicationCreate(**application_dict)
        )

        # Commit the application first
        await self._job_application_repository._session.commit()
        await self._job_application_repository._session.refresh(application)

        # Handle tag associations after commit
        if tag_ids:
            await self._job_application_repository._session.refresh(application, ["tags"])
            for tag_id in tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    application.tags.append(tag)

            await self._job_application_repository._session.commit()
            await self._job_application_repository._session.refresh(application)

        # Return response with counts
        response_dict = {
            "id": application.id,
            "company_id": application.company_id,
            "resume_id": application.resume_id,
            "project_id": application.project_id,
            "cover_letter_id": application.cover_letter_id,
            "referrer_contact_id": application.referrer_contact_id,
            "job_title": application.job_title,
            "job_description": application.job_description,
            "job_url": application.job_url,
            "salary_min": application.salary_min,
            "salary_max": application.salary_max,
            "location": application.location,
            "remote_policy": application.remote_policy,
            "status": application.status,
            "application_date": application.application_date,
            "last_contact_date": application.last_contact_date,
            "next_followup_date": application.next_followup_date,
            "resume_version": application.resume_version,
            "source": application.source,
            "interview_notes": application.interview_notes,
            "rejection_reason": application.rejection_reason,
            "notes": application.notes,
            "interview_count": application.interview_count,
            "response_time_hours": application.response_time_hours,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
            "tag_count": len(tag_ids) if tag_ids else 0,
        }
        return JobApplicationResponse(**response_dict)

    async def get_job_application_by_id(
        self, application_id: UUID
    ) -> JobApplicationResponse:
        """Get job application by ID."""
        application = await self._job_application_repository.get_with_all_relations(
            application_id
        )
        if not application:
            raise JobApplicationNotFoundError(application_id)
        return self._to_response(application)

    async def get_all_job_applications(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[JobApplicationResponse]:
        """Get all job applications with optional pagination."""
        applications = await self._job_application_repository.get_all(
            limit=limit, offset=offset
        )
        return [
            JobApplicationResponse(
                id=a.id,
                company_id=a.company_id,
                resume_id=a.resume_id,
                project_id=a.project_id,
                cover_letter_id=a.cover_letter_id,
                referrer_contact_id=a.referrer_contact_id,
                job_title=a.job_title,
                job_description=a.job_description,
                job_url=a.job_url,
                salary_min=a.salary_min,
                salary_max=a.salary_max,
                location=a.location,
                remote_policy=a.remote_policy,
                status=a.status,
                application_date=a.application_date,
                last_contact_date=a.last_contact_date,
                next_followup_date=a.next_followup_date,
                resume_version=a.resume_version,
                source=a.source,
                interview_notes=a.interview_notes,
                rejection_reason=a.rejection_reason,
                notes=a.notes,
                interview_count=a.interview_count,
                response_time_hours=a.response_time_hours,
                created_at=a.created_at,
                updated_at=a.updated_at,
                tag_count=0,
            )
            for a in applications
        ]

    async def update_job_application(
        self, application_id: UUID, update_data: JobApplicationUpdate
    ) -> JobApplicationResponse:
        """Update a job application."""
        # Strip emojis from text fields
        if update_data.job_title:
            update_data.job_title = strip_emojis(update_data.job_title)
        if update_data.job_description:
            update_data.job_description = strip_emojis(update_data.job_description)
        if update_data.interview_notes:
            update_data.interview_notes = strip_emojis(update_data.interview_notes)
        if update_data.notes:
            update_data.notes = strip_emojis(update_data.notes)

        application = await self._job_application_repository.get_by_id(application_id)
        if not application:
            raise JobApplicationNotFoundError(application_id)

        # Update basic fields
        application = await self._job_application_repository.update(
            application_id, update_data
        )
        if not application:
            raise JobApplicationNotFoundError(application_id)

        # Handle tag updates
        if update_data.tag_ids is not None:
            await self._job_application_repository._session.refresh(application, ["tags"])
            application.tags.clear()
            for tag_id in update_data.tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    application.tags.append(tag)

        await self._job_application_repository._session.commit()
        await self._job_application_repository._session.refresh(application)

        return self._to_response(application)

    async def delete_job_application(self, application_id: UUID) -> bool:
        """Delete a job application."""
        success = await self._job_application_repository.delete(application_id)
        if not success:
            raise JobApplicationNotFoundError(application_id)
        return success

    async def get_applications_by_status(
        self, status: str
    ) -> list[JobApplicationResponse]:
        """Get applications by status."""
        applications = await self._job_application_repository.get_by_status(status)
        return [self._to_response(a) for a in applications]

    async def get_applications_by_company(
        self, company_id: UUID
    ) -> list[JobApplicationResponse]:
        """Get applications for a specific company."""
        applications = await self._job_application_repository.get_by_company(company_id)
        return [self._to_response(a) for a in applications]

    async def get_active_applications(self) -> list[JobApplicationResponse]:
        """Get all active applications."""
        applications = await self._job_application_repository.get_active_applications()
        return [self._to_response(a) for a in applications]

    async def get_applications_needing_followup(self) -> list[JobApplicationResponse]:
        """Get applications with upcoming or overdue follow-ups."""
        applications = (
            await self._job_application_repository.get_applications_needing_followup()
        )
        return [self._to_response(a) for a in applications]

    def _to_response(self, application) -> JobApplicationResponse:
        """Convert job application model to response."""
        tag_count = len(application.tags) if hasattr(application, "tags") else 0

        response_dict = {
            "id": application.id,
            "company_id": application.company_id,
            "resume_id": application.resume_id,
            "project_id": application.project_id,
            "cover_letter_id": application.cover_letter_id,
            "referrer_contact_id": application.referrer_contact_id,
            "job_title": application.job_title,
            "job_description": application.job_description,
            "job_url": application.job_url,
            "salary_min": application.salary_min,
            "salary_max": application.salary_max,
            "location": application.location,
            "remote_policy": application.remote_policy,
            "status": application.status,
            "application_date": application.application_date,
            "last_contact_date": application.last_contact_date,
            "next_followup_date": application.next_followup_date,
            "resume_version": application.resume_version,
            "source": application.source,
            "interview_notes": application.interview_notes,
            "rejection_reason": application.rejection_reason,
            "notes": application.notes,
            "interview_count": application.interview_count,
            "response_time_hours": application.response_time_hours,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
            "tag_count": tag_count,
        }
        return JobApplicationResponse(**response_dict)
