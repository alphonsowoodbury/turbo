"""Resume service for orchestrating resume operations."""

from typing import Any, BinaryIO
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.resume import Resume, ResumeSection
from turbo.core.repositories.resume import ResumeSectionRepository, ResumeRepository
from turbo.core.schemas.resume import (
    ParsedResumeData,
    ResumeCreate,
    ResumeSectionCreate,
    ResumeSectionUpdate,
    ResumeUpdate,
    ResumeUploadResponse,
)
from turbo.core.services.file_upload import FileUploadService
from turbo.core.services.markdown_parser import MarkdownParserService
from turbo.core.services.pdf_parser import PDFParserService
from turbo.core.services.resume_ai_extractor import ResumeAIExtractorService
from turbo.utils.exceptions import ResumeNotFoundError, ResumeSectionNotFoundError, ValidationError


class ResumeService:
    """Service for resume operations."""

    def __init__(self, session: AsyncSession):
        """Initialize resume service.

        Args:
            session: Database session
        """
        self.session = session
        self.resume_repo = ResumeRepository(session)
        self.section_repo = ResumeSectionRepository(session)
        self.upload_service = FileUploadService()
        self.pdf_parser = PDFParserService()
        self.markdown_parser = MarkdownParserService()

    async def upload_and_parse_resume(
        self,
        file: BinaryIO,
        filename: str,
        title: str,
        target_role: str | None = None,
        target_company: str | None = None,
        use_ai_extraction: bool = True,
        content_type: str | None = None,
    ) -> ResumeUploadResponse:
        """Upload and parse a resume file.

        Args:
            file: File object (binary mode)
            filename: Original filename
            title: Resume title
            target_role: Target job role (optional)
            target_company: Target company (optional)
            use_ai_extraction: Whether to use AI for data extraction
            content_type: MIME type of file

        Returns:
            Upload response with resume ID and file path

        Raises:
            ValidationError: If file validation or parsing fails
        """
        # Upload file
        file_path = await self.upload_service.save_file(file, filename, content_type)

        # Get file type
        file_type = self.upload_service.get_file_type(filename)

        # Parse file based on type
        if file_type == "pdf":
            parsed_content = self.pdf_parser.parse_file(file_path)
        else:  # markdown
            parsed_content = self.markdown_parser.parse_file(file_path)

        # Extract structured data using AI if enabled and API key is available
        parsed_data: dict[str, Any] = {}
        if use_ai_extraction:
            try:
                from turbo.utils.config import get_settings
                settings = get_settings()

                # Only attempt AI extraction if API key is configured
                if settings.anthropic.api_key:
                    ai_extractor = ResumeAIExtractorService()
                    parsed_data_obj = await ai_extractor.extract_structured_data(
                        resume_text=parsed_content["text"],
                        sections=parsed_content.get("sections", []),
                    )
                    parsed_data = parsed_data_obj.model_dump()
            except Exception:
                # Silently skip AI extraction if it fails
                # The resume will still be saved with basic parsing
                pass

        # Create resume record
        resume_create = ResumeCreate(
            title=title,
            file_path=file_path,
            file_type=file_type,
            target_role=target_role,
            target_company=target_company,
            parsed_data=parsed_data,
        )

        resume = await self.resume_repo.create(resume_create)

        # Create resume sections from parsed content
        if parsed_content.get("sections"):
            await self._create_sections_from_parsed(
                resume.id, parsed_content["sections"], parsed_data
            )

        await self.session.commit()

        # Trigger webhook for AI extraction (asynchronous, non-blocking)
        if use_ai_extraction:
            try:
                from turbo.core.services.claude_webhook import get_webhook_service
                import asyncio

                webhook_service = get_webhook_service()
                # Trigger webhook in background (fire and forget)
                asyncio.create_task(
                    webhook_service.trigger_entity_response("resume", resume.id)
                )
            except Exception:
                # Silently fail if webhook service is unavailable
                # Resume is still saved with basic parsing
                pass

        return ResumeUploadResponse(
            resume_id=resume.id,
            file_path=file_path,
            message=f"Resume '{title}' uploaded and parsed successfully",
        )

    async def _create_sections_from_parsed(
        self,
        resume_id: UUID,
        sections: list[dict[str, Any]],
        parsed_data: dict[str, Any],
    ) -> None:
        """Create resume sections from parsed content.

        Args:
            resume_id: Resume ID
            sections: Parsed sections
            parsed_data: AI-extracted data
        """
        for idx, section in enumerate(sections):
            # Build section_metadata from parsed data
            section_metadata = section.get("metadata", {})
            section_type = section.get("type", "other")

            # Add relevant parsed data to section_metadata
            if section_type == "experience" and parsed_data.get("experience"):
                section_metadata["experiences"] = parsed_data["experience"]
            elif section_type == "education" and parsed_data.get("education"):
                section_metadata["education"] = parsed_data["education"]
            elif section_type == "skills" and parsed_data.get("skills"):
                section_metadata["skills"] = parsed_data["skills"]
            elif section_type == "projects" and parsed_data.get("projects"):
                section_metadata["projects"] = parsed_data["projects"]

            section_create = ResumeSectionCreate(
                resume_id=resume_id,
                section_type=section_type,
                title=section.get("title", ""),
                content=section.get("content", ""),
                order=idx,
                is_active=True,
                section_metadata=section_metadata,
            )

            await self.section_repo.create(section_create)

    async def get_resume(self, resume_id: UUID) -> Resume:
        """Get resume by ID with sections.

        Args:
            resume_id: Resume ID

        Returns:
            Resume with sections

        Raises:
            ResumeNotFoundError: If resume not found
        """
        resume = await self.resume_repo.get_with_sections(resume_id)
        if not resume:
            raise ResumeNotFoundError(resume_id)
        return resume

    async def list_resumes(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[Resume], int]:
        """List all resumes.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (resumes, total_count)
        """
        resumes = await self.resume_repo.get_all_with_sections(skip=skip, limit=limit)
        total = len(resumes)  # TODO: Add count method to repository
        return resumes, total

    async def get_resumes_by_role(self, target_role: str) -> list[Resume]:
        """Get resumes filtered by target role.

        Args:
            target_role: Target job role

        Returns:
            List of matching resumes
        """
        return await self.resume_repo.get_by_target_role(target_role)

    async def get_primary_resume(self) -> Resume | None:
        """Get the primary resume.

        Returns:
            Primary resume or None
        """
        return await self.resume_repo.get_primary()

    async def update_resume(
        self, resume_id: UUID, update_data: ResumeUpdate
    ) -> Resume:
        """Update resume.

        Args:
            resume_id: Resume ID
            update_data: Update data

        Returns:
            Updated resume

        Raises:
            ResumeNotFoundError: If resume not found
        """
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume:
            raise ResumeNotFoundError(resume_id)

        await self.resume_repo.update(resume_id, update_data)
        await self.session.commit()

        # Fetch with sections loaded
        return await self.resume_repo.get_with_sections(resume_id)

    async def set_primary_resume(self, resume_id: UUID) -> Resume:
        """Set a resume as primary.

        Args:
            resume_id: Resume ID

        Returns:
            Updated resume

        Raises:
            ResumeNotFoundError: If resume not found
        """
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume:
            raise ResumeNotFoundError(resume_id)

        await self.resume_repo.set_primary(resume_id)
        await self.session.commit()

        return await self.resume_repo.get(resume_id)

    async def delete_resume(self, resume_id: UUID) -> None:
        """Delete resume and associated file.

        Args:
            resume_id: Resume ID

        Raises:
            ResumeNotFoundError: If resume not found
        """
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume:
            raise ResumeNotFoundError(resume_id)

        # Delete file
        if resume.file_path:
            self.upload_service.delete_file(resume.file_path)

        # Delete resume (cascade deletes sections)
        await self.resume_repo.delete(resume_id)
        await self.session.commit()

    # Section operations

    async def get_resume_sections(
        self, resume_id: UUID, active_only: bool = False
    ) -> list[ResumeSection]:
        """Get sections for a resume.

        Args:
            resume_id: Resume ID
            active_only: Whether to return only active sections

        Returns:
            List of resume sections
        """
        if active_only:
            return await self.section_repo.get_active_sections(resume_id)
        return await self.section_repo.get_by_resume(resume_id)

    async def create_section(
        self, section_data: ResumeSectionCreate
    ) -> ResumeSection:
        """Create a new resume section.

        Args:
            section_data: Section data

        Returns:
            Created section
        """
        section = await self.section_repo.create(section_data)
        await self.session.commit()
        return section

    async def update_section(
        self, section_id: UUID, update_data: ResumeSectionUpdate
    ) -> ResumeSection:
        """Update resume section.

        Args:
            section_id: Section ID
            update_data: Update data

        Returns:
            Updated section

        Raises:
            ResumeSectionNotFoundError: If section not found
        """
        section = await self.section_repo.get_by_id(section_id)
        if not section:
            raise ResumeSectionNotFoundError(section_id)

        updated = await self.section_repo.update(section_id, update_data)
        await self.session.commit()
        return updated

    async def delete_section(self, section_id: UUID) -> None:
        """Delete resume section.

        Args:
            section_id: Section ID

        Raises:
            ResumeSectionNotFoundError: If section not found
        """
        section = await self.section_repo.get_by_id(section_id)
        if not section:
            raise ResumeSectionNotFoundError(section_id)

        await self.section_repo.delete(section_id)
        await self.session.commit()

    async def reorder_sections(
        self, resume_id: UUID, section_orders: dict[UUID, int]
    ) -> None:
        """Reorder sections within a resume.

        Args:
            resume_id: Resume ID
            section_orders: Dictionary mapping section IDs to new order values
        """
        await self.section_repo.reorder_sections(resume_id, section_orders)
        await self.session.commit()
