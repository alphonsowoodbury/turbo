"""Resume tailoring service for AI-powered resume customization."""

import re
from collections import Counter
from datetime import datetime
from uuid import UUID

from turbo.core.repositories.resume import ResumeRepository
from turbo.core.repositories.job_application import JobApplicationRepository
from turbo.core.schemas.resume import ResumeCreate, ResumeSectionCreate
from turbo.utils.exceptions import ValidationError


class ResumeTailoringService:
    """Service for tailoring resumes based on job descriptions."""

    def __init__(
        self,
        resume_repository: ResumeRepository,
        job_application_repository: JobApplicationRepository | None = None,
    ) -> None:
        self._resume_repo = resume_repository
        self._job_app_repo = job_application_repository

    async def tailor_resume(
        self,
        base_resume_id: UUID,
        job_description: str,
        job_title: str | None = None,
        company_name: str | None = None,
        job_application_id: UUID | None = None,
    ) -> dict:
        """
        Tailor a resume based on a job description.

        Args:
            base_resume_id: UUID of the base resume to customize
            job_description: Full job description text
            job_title: Title of the job position
            company_name: Name of the company
            job_application_id: Optional UUID to link tailored resume

        Returns:
            Dict with tailored_resume data, match_score, and suggestions
        """
        # Load base resume with sections
        base_resume = await self._resume_repo.get_with_sections(base_resume_id)
        if not base_resume:
            raise ValidationError(f"Resume {base_resume_id} not found")

        # Analyze job description
        job_requirements = self.analyze_job_description(job_description)

        # Calculate fit score
        match_score = self.score_resume_fit(base_resume, job_requirements)

        # Generate tailored content
        tailored_sections = self._reorder_sections_by_relevance(
            base_resume.sections, job_requirements
        )

        # Generate custom summary
        custom_summary = self._generate_custom_summary(
            base_resume, job_requirements, job_title, company_name
        )

        # Prepare tailored resume data
        tailored_data = {
            "title": f"{base_resume.title} - {company_name or 'Tailored'}"
            if company_name
            else f"{base_resume.title} - Tailored",
            "file_type": base_resume.file_type,
            "target_role": job_title or base_resume.target_role,
            "target_company": company_name or base_resume.target_company,
            "parsed_data": {
                **base_resume.parsed_data,
                "base_resume_id": str(base_resume_id),
                "job_description_hash": hash(job_description),
                "match_score": match_score,
                "tailored_at": datetime.utcnow().isoformat(),
                "custom_summary": custom_summary,
                "job_keywords": job_requirements["keywords"],
                "required_skills": job_requirements["required_skills"],
                "preferred_skills": job_requirements["preferred_skills"],
            },
            "sections": tailored_sections,
            "match_score": match_score,
            "suggestions": self._generate_suggestions(
                base_resume, job_requirements, match_score
            ),
        }

        return tailored_data

    def analyze_job_description(self, job_text: str) -> dict:
        """
        Analyze job description to extract keywords and requirements.

        Args:
            job_text: Full job description text

        Returns:
            Dict with keywords, required_skills, preferred_skills, etc.
        """
        # Normalize text
        text_lower = job_text.lower()

        # Extract keywords (simple frequency-based approach)
        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "you",
            "your",
            "our",
            "we",
            "us",
        }

        # Extract words (alphanumeric with optional + for C++)
        words = re.findall(r"\b[\w+]+\b", text_lower)
        filtered_words = [
            w for w in words if len(w) > 2 and w not in stop_words and not w.isdigit()
        ]

        # Get most common keywords
        word_counts = Counter(filtered_words)
        top_keywords = [word for word, count in word_counts.most_common(30)]

        # Extract required skills (look for patterns like "required:", "must have:")
        required_pattern = r"(?:required|must have|must be|required skills?):([^\n.]*)"
        required_matches = re.findall(required_pattern, text_lower, re.IGNORECASE)
        required_skills = self._extract_skills_from_text(" ".join(required_matches))

        # Extract preferred/nice-to-have skills
        preferred_pattern = r"(?:preferred|nice to have|plus|bonus):([^\n.]*)"
        preferred_matches = re.findall(preferred_pattern, text_lower, re.IGNORECASE)
        preferred_skills = self._extract_skills_from_text(" ".join(preferred_matches))

        # Common tech skills to look for
        tech_skills = [
            "python",
            "javascript",
            "typescript",
            "react",
            "node",
            "java",
            "c++",
            "golang",
            "rust",
            "sql",
            "nosql",
            "mongodb",
            "postgresql",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "terraform",
            "ci/cd",
            "git",
            "agile",
            "scrum",
            "rest",
            "graphql",
            "microservices",
            "api",
            "machine learning",
            "ai",
            "data science",
            "tensorflow",
            "pytorch",
        ]

        mentioned_tech = [skill for skill in tech_skills if skill in text_lower]

        # Extract experience requirements (e.g., "5+ years")
        exp_pattern = r"(\d+)[\s\-+]*(?:years?|yrs?)"
        exp_matches = re.findall(exp_pattern, text_lower)
        years_required = int(exp_matches[0]) if exp_matches else None

        return {
            "keywords": top_keywords,
            "required_skills": required_skills if required_skills else mentioned_tech[: 10],
            "preferred_skills": preferred_skills,
            "mentioned_technologies": mentioned_tech,
            "years_experience": years_required,
            "text_length": len(job_text),
        }

    def _extract_skills_from_text(self, text: str) -> list[str]:
        """Extract skill keywords from text."""
        # Split by common delimiters
        skills = re.split(r"[,;•\n-]", text)
        # Clean and filter
        cleaned = []
        for skill in skills:
            skill = skill.strip()
            # Remove leading "and", "or"
            skill = re.sub(r"^(?:and|or)\s+", "", skill, flags=re.IGNORECASE)
            if len(skill) > 2 and len(skill) < 100:
                cleaned.append(skill.lower())
        return cleaned

    def score_resume_fit(self, resume, job_requirements: dict) -> float:
        """
        Calculate percentage match between resume and job requirements.

        Args:
            resume: Resume model with sections
            job_requirements: Dict from analyze_job_description

        Returns:
            Float between 0 and 100 representing match percentage
        """
        # Combine all resume text
        resume_text = " ".join([resume.title, resume.target_role or ""])
        if resume.parsed_data:
            resume_text += " " + str(resume.parsed_data)

        for section in resume.sections:
            resume_text += f" {section.title} {section.content}"

        resume_text_lower = resume_text.lower()

        # Score based on required skills presence
        required_skills = job_requirements.get("required_skills", [])
        if required_skills:
            required_matches = sum(
                1 for skill in required_skills if skill.lower() in resume_text_lower
            )
            required_score = (required_matches / len(required_skills)) * 60  # 60% weight
        else:
            required_score = 30  # Default if no required skills found

        # Score based on keyword presence
        keywords = job_requirements.get("keywords", [])
        if keywords:
            keyword_matches = sum(
                1 for keyword in keywords[:20] if keyword in resume_text_lower
            )
            keyword_score = (keyword_matches / min(len(keywords), 20)) * 30  # 30% weight
        else:
            keyword_score = 15

        # Score based on preferred skills (bonus)
        preferred_skills = job_requirements.get("preferred_skills", [])
        if preferred_skills:
            preferred_matches = sum(
                1 for skill in preferred_skills if skill.lower() in resume_text_lower
            )
            preferred_score = (
                preferred_matches / len(preferred_skills)
            ) * 10  # 10% weight
        else:
            preferred_score = 5

        total_score = required_score + keyword_score + preferred_score
        return min(round(total_score, 1), 100.0)

    def _reorder_sections_by_relevance(
        self, sections, job_requirements: dict
    ) -> list[dict]:
        """
        Reorder resume sections based on relevance to job.

        Args:
            sections: List of ResumeSection objects
            job_requirements: Job requirements dict

        Returns:
            List of section dicts with reordered content and relevance scores
        """
        keywords = job_requirements.get("keywords", [])
        required_skills = job_requirements.get("required_skills", [])
        all_terms = set(keywords + required_skills)

        scored_sections = []
        for section in sections:
            if not section.is_active:
                continue

            section_text = f"{section.title} {section.content}".lower()

            # Calculate relevance score
            matches = sum(1 for term in all_terms if term in section_text)
            relevance_score = matches / max(len(all_terms), 1)

            # Boost certain section types
            if section.section_type == "experience":
                relevance_score *= 1.3
            elif section.section_type == "skills":
                relevance_score *= 1.2
            elif section.section_type == "summary":
                relevance_score *= 1.1

            scored_sections.append(
                {
                    "section_type": section.section_type,
                    "title": section.title,
                    "content": section.content,
                    "order": section.order,
                    "relevance_score": relevance_score,
                    "is_active": section.is_active,
                    "section_metadata": section.section_metadata,
                }
            )

        # Sort by relevance score (descending), then original order
        scored_sections.sort(key=lambda s: (-s["relevance_score"], s["order"]))

        # Re-assign order
        for idx, section in enumerate(scored_sections):
            section["order"] = idx

        return scored_sections

    def _generate_custom_summary(
        self,
        resume,
        job_requirements: dict,
        job_title: str | None = None,
        company_name: str | None = None,
    ) -> str:
        """
        Generate a customized summary/objective for the job.

        Args:
            resume: Base resume
            job_requirements: Job requirements
            job_title: Target job title
            company_name: Target company

        Returns:
            Customized summary text
        """
        # Extract existing summary if available
        base_summary = ""
        for section in resume.sections:
            if section.section_type == "summary" and section.is_active:
                base_summary = section.content
                break

        # For now, use a template-based approach
        # TODO: Replace with AI/Claude-powered generation
        required_skills = job_requirements.get("required_skills", [])
        top_skills = required_skills[:3] if required_skills else ["software development"]

        role_phrase = f"for the {job_title} role" if job_title else "in this position"
        company_phrase = f" at {company_name}" if company_name else ""

        summary = f"Results-driven professional with expertise in {', '.join(top_skills)}. "
        summary += f"Seeking to leverage technical skills and experience {role_phrase}{company_phrase}. "

        if base_summary:
            # Incorporate part of base summary
            summary += base_summary[:200]

        return summary[:500]  # Limit length

    def _generate_suggestions(
        self, resume, job_requirements: dict, match_score: float
    ) -> list[str]:
        """
        Generate suggestions for improving resume fit.

        Args:
            resume: Resume object
            job_requirements: Job requirements
            match_score: Current match score

        Returns:
            List of suggestion strings
        """
        suggestions = []

        # Check for missing required skills
        required_skills = job_requirements.get("required_skills", [])
        resume_text = " ".join(
            [section.content for section in resume.sections]
        ).lower()

        missing_skills = [
            skill for skill in required_skills if skill.lower() not in resume_text
        ]

        if missing_skills:
            suggestions.append(
                f"Consider highlighting experience with: {', '.join(missing_skills[:5])}"
            )

        # Check for keyword density
        if match_score < 50:
            suggestions.append(
                "Low keyword match. Review job description and incorporate relevant terms."
            )

        # Check for preferred skills
        preferred_skills = job_requirements.get("preferred_skills", [])
        if preferred_skills:
            missing_preferred = [
                skill for skill in preferred_skills if skill.lower() not in resume_text
            ]
            if missing_preferred:
                suggestions.append(
                    f"Bonus: Add experience with {', '.join(missing_preferred[:3])} if applicable"
                )

        # General suggestions
        if match_score >= 80:
            suggestions.append("Strong match! Review and polish before submission.")
        elif match_score >= 60:
            suggestions.append(
                "Good match. Consider emphasizing relevant experience more prominently."
            )
        else:
            suggestions.append(
                "Match score is low. Ensure your most relevant experience is highlighted."
            )

        return suggestions

    async def create_tailored_resume_record(
        self, tailored_data: dict, job_application_id: UUID | None = None
    ) -> "Resume":
        """
        Create a new Resume record from tailored data.

        Args:
            tailored_data: Dict from tailor_resume()
            job_application_id: Optional job application to link

        Returns:
            Created Resume object
        """
        # Create resume record
        resume_create = ResumeCreate(
            title=tailored_data["title"],
            file_type=tailored_data["file_type"],
            file_path=None,  # No file yet
            target_role=tailored_data.get("target_role"),
            target_company=tailored_data.get("target_company"),
            parsed_data=tailored_data["parsed_data"],
            is_primary=False,
        )

        resume = await self._resume_repo.create(resume_create)

        # Create sections
        # Note: Sections need to be created separately via ResumeSectionRepository
        # This is handled by the resume generation workflow

        # Link to job application if provided
        if job_application_id and self._job_app_repo:
            application = await self._job_app_repo.get_by_id(job_application_id)
            if application:
                application.resume_id = resume.id
                await self._job_app_repo.update(
                    job_application_id, {"resume_id": resume.id}
                )

        return resume
