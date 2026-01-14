"""Resume generation service for creating resumes in multiple formats."""

import io
from datetime import datetime
from pathlib import Path
from uuid import UUID

from turbo.core.repositories.resume import ResumeRepository, ResumeSectionRepository
from turbo.core.repositories.job_application import JobApplicationRepository
from turbo.core.schemas.resume import ResumeCreate, ResumeSectionCreate, ResumeUpdate
from turbo.core.services.resume_tailoring import ResumeTailoringService
from turbo.core.services.pdf_generator import PDFGeneratorService
from turbo.utils.exceptions import ValidationError


class ResumeGenerationService:
    """Service for generating resumes in multiple formats."""

    def __init__(
        self,
        resume_repository: ResumeRepository,
        section_repository: ResumeSectionRepository,
        tailoring_service: ResumeTailoringService,
        job_application_repository: JobApplicationRepository | None = None,
        pdf_generator: PDFGeneratorService | None = None,
    ) -> None:
        self._resume_repo = resume_repository
        self._section_repo = section_repository
        self._tailoring_service = tailoring_service
        self._job_app_repo = job_application_repository
        self._pdf_generator = pdf_generator or PDFGeneratorService()

    async def generate_tailored_resume(
        self,
        base_resume_id: UUID,
        job_description: str,
        job_title: str | None = None,
        company_name: str | None = None,
        job_application_id: UUID | None = None,
        output_format: str = "markdown",
    ) -> dict:
        """
        Generate a tailored resume for a specific job.

        Args:
            base_resume_id: UUID of the base resume to customize
            job_description: Full job description text
            job_title: Title of the job position
            company_name: Name of the company
            job_application_id: Optional UUID to link tailored resume
            output_format: Output format (markdown, pdf, docx)

        Returns:
            Dict with resume_id, file_path, match_score, and suggestions
        """
        # Step 1: Tailor the resume content
        tailored_data = await self._tailoring_service.tailor_resume(
            base_resume_id=base_resume_id,
            job_description=job_description,
            job_title=job_title,
            company_name=company_name,
            job_application_id=job_application_id,
        )

        # Step 2: Create resume record
        resume = await self._create_resume_record(
            tailored_data, job_application_id
        )

        # Step 3: Create resume sections
        await self._create_resume_sections(resume.id, tailored_data["sections"])

        # Step 4: Generate file in requested format
        file_path = await self._generate_file(
            resume.id, output_format, tailored_data
        )

        # Step 5: Update resume with file path
        resume.file_path = str(file_path)
        await self._resume_repo.update(
            resume.id, ResumeUpdate(file_path=str(file_path))
        )

        # Step 6: Link to job application if provided
        if job_application_id and self._job_app_repo:
            await self._link_to_application(job_application_id, resume.id)

        return {
            "resume_id": str(resume.id),
            "file_path": str(file_path),
            "match_score": tailored_data["match_score"],
            "suggestions": tailored_data["suggestions"],
            "title": tailored_data["title"],
            "format": output_format,
        }

    async def _create_resume_record(
        self, tailored_data: dict, job_application_id: UUID | None = None
    ) -> "Resume":
        """Create a new Resume record from tailored data."""
        resume_create = ResumeCreate(
            title=tailored_data["title"],
            file_type=tailored_data.get("format", "markdown"),
            file_path=None,  # Will be set after file generation
            target_role=tailored_data.get("target_role"),
            target_company=tailored_data.get("target_company"),
            parsed_data=tailored_data["parsed_data"],
            is_primary=False,
        )

        resume = await self._resume_repo.create(resume_create)
        return resume

    async def _create_resume_sections(
        self, resume_id: UUID, sections: list[dict]
    ) -> None:
        """Create resume sections from tailored data."""
        for section_data in sections:
            section_create = ResumeSectionCreate(
                resume_id=resume_id,
                section_type=section_data["section_type"],
                title=section_data["title"],
                content=section_data["content"],
                order=section_data["order"],
                is_active=section_data.get("is_active", True),
                section_metadata=section_data.get("section_metadata", {}),
            )
            await self._section_repo.create(section_create)

    async def _generate_file(
        self, resume_id: UUID, output_format: str, tailored_data: dict
    ) -> Path:
        """Generate resume file in specified format."""
        # Get resume with sections
        resume = await self._resume_repo.get_with_sections(resume_id)
        if not resume:
            raise ValidationError(f"Resume {resume_id} not found")

        # Create output directory
        output_dir = Path.home() / "Documents" / "Resumes"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(
            c if c.isalnum() or c in " -_" else "_" for c in resume.title
        )
        filename = f"{safe_title}_{timestamp}.{output_format}"
        file_path = output_dir / filename

        # Generate based on format
        if output_format == "markdown":
            content = self._generate_markdown(resume, tailored_data)
            file_path.write_text(content, encoding="utf-8")
        elif output_format == "pdf":
            # Generate markdown first
            content = self._generate_markdown(resume, tailored_data)

            # Save markdown for reference
            md_path = output_dir / f"{safe_title}_{timestamp}.md"
            md_path.write_text(content, encoding="utf-8")

            # Convert to PDF
            try:
                pdf_path = output_dir / f"{safe_title}_{timestamp}.pdf"
                self._pdf_generator.markdown_to_pdf(
                    content, pdf_path, template="professional"
                )
                file_path = pdf_path
            except ImportError:
                # WeasyPrint not installed, return markdown
                file_path = md_path
        elif output_format == "docx":
            # DOCX generation requires python-docx
            # For now, generate markdown
            content = self._generate_markdown(resume, tailored_data)
            md_path = output_dir / f"{safe_title}_{timestamp}.md"
            md_path.write_text(content, encoding="utf-8")
            file_path = md_path
            # TODO: Implement DOCX conversion using python-docx
        else:
            raise ValidationError(f"Unsupported format: {output_format}")

        return file_path

    def _generate_markdown(self, resume: "Resume", tailored_data: dict) -> str:
        """Generate resume in Markdown format."""
        lines = []

        # Header with name (from parsed_data)
        personal_info = resume.parsed_data.get("personal_info", {})
        name = personal_info.get("name", "Resume")
        lines.append(f"# {name}")

        # Contact information on one line
        contact_parts = []
        if location := personal_info.get("location"):
            contact_parts.append(location)
        if phone := personal_info.get("phone"):
            contact_parts.append(phone)
        if email := personal_info.get("email"):
            contact_parts.append(email)
        if github := personal_info.get("github"):
            contact_parts.append(f"[GitHub]({github})")
        if linkedin := personal_info.get("linkedin"):
            contact_parts.append(f"[LinkedIn]({linkedin})")

        if contact_parts:
            lines.append(" | ".join(contact_parts))
        lines.append("")

        # Job title/target role
        if target_role := resume.target_role:
            lines.append(f"## {target_role}")
        lines.append("")

        # Custom summary if available
        if custom_summary := tailored_data["parsed_data"].get("custom_summary"):
            lines.append(f"*{custom_summary}*")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Sections (already ordered by relevance)
        for section in resume.sections:
            if not section.is_active:
                continue

            # Section title
            lines.append(f"## {section.title}")
            lines.append("")

            # Section content - preserve original formatting
            lines.append(section.content)
            lines.append("")

            # Section metadata (for experience, education, etc.)
            metadata = section.section_metadata
            if metadata:
                meta_parts = []
                if company := metadata.get("company"):
                    meta_parts.append(f"**{company}**")
                if title := metadata.get("title"):
                    meta_parts.append(title)
                if dates := metadata.get("dates"):
                    meta_parts.append(f"*{dates}*")
                if location := metadata.get("location"):
                    meta_parts.append(location)

                if meta_parts:
                    lines.append(" | ".join(meta_parts))
                    lines.append("")

        # Footer with generation info
        lines.append("---")
        lines.append("")
        lines.append(
            f"*Resume generated on {datetime.utcnow().strftime('%B %d, %Y')}*"
        )
        if match_score := tailored_data.get("match_score"):
            lines.append(f"*Match Score: {match_score}%*")

        return "\n".join(lines)

    async def _link_to_application(
        self, job_application_id: UUID, resume_id: UUID
    ) -> None:
        """Link resume to job application."""
        if self._job_app_repo:
            application = await self._job_app_repo.get_by_id(job_application_id)
            if application:
                await self._job_app_repo.update(
                    job_application_id, {"resume_id": resume_id}
                )

    async def generate_from_application(
        self,
        job_application_id: UUID,
        base_resume_id: UUID | None = None,
        output_format: str = "markdown",
    ) -> dict:
        """
        Generate resume directly from a job application.

        Args:
            job_application_id: UUID of the job application
            base_resume_id: Optional base resume (uses primary if not provided)
            output_format: Output format (markdown, pdf, docx)

        Returns:
            Dict with resume_id, file_path, match_score, and suggestions
        """
        if not self._job_app_repo:
            raise ValidationError("Job application repository not available")

        # Get application
        application = await self._job_app_repo.get_by_id(job_application_id)
        if not application:
            raise ValidationError(
                f"Job application {job_application_id} not found"
            )

        # Use primary resume if base not specified
        if not base_resume_id:
            primary_resume = await self._resume_repo.get_primary()
            if not primary_resume:
                raise ValidationError("No primary resume found")
            base_resume_id = primary_resume.id

        # Generate resume
        return await self.generate_tailored_resume(
            base_resume_id=base_resume_id,
            job_description=application.job_description or "",
            job_title=application.position_title,
            company_name=application.company_name,
            job_application_id=job_application_id,
            output_format=output_format,
        )

    async def batch_generate_resumes(
        self,
        base_resume_id: UUID,
        applications: list[UUID],
        output_format: str = "markdown",
    ) -> list[dict]:
        """
        Generate resumes for multiple applications.

        Args:
            base_resume_id: Base resume to customize
            applications: List of job application UUIDs
            output_format: Output format

        Returns:
            List of generation results
        """
        results = []
        for app_id in applications:
            try:
                result = await self.generate_from_application(
                    job_application_id=app_id,
                    base_resume_id=base_resume_id,
                    output_format=output_format,
                )
                results.append(
                    {
                        "application_id": str(app_id),
                        "success": True,
                        **result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "application_id": str(app_id),
                        "success": False,
                        "error": str(e),
                    }
                )
        return results
