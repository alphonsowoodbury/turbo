"""Service for aggregating and deduplicating resume data across multiple resumes."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.resume import Resume


class ResumeAggregatorService:
    """Aggregate resume data from multiple resumes into a single profile."""

    def __init__(self, session: AsyncSession):
        """Initialize aggregator service.

        Args:
            session: Database session
        """
        self.session = session

    async def aggregate_all_resumes(self) -> dict[str, Any]:
        """Aggregate data from all resumes with deduplication.

        Returns:
            Aggregated profile with deduplicated data
        """
        # Fetch all resumes with parsed data
        stmt = select(Resume)
        result = await self.session.execute(stmt)
        resumes = result.scalars().all()

        # Initialize aggregated structure
        aggregated = {
            "personal": {},
            "summary": None,
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "awards": [],
            "publications": [],
            "languages": [],
            "volunteer": [],
            "metadata": {
                "total_resumes": len(resumes),
                "resume_ids": [str(r.id) for r in resumes],
            },
        }

        # Track seen items for deduplication
        seen_experiences = set()
        seen_education = set()
        seen_skills = set()
        seen_projects = set()
        seen_certifications = set()
        seen_awards = set()
        seen_publications = set()
        seen_languages = set()
        seen_volunteer = set()

        # Aggregate from each resume
        for resume in resumes:
            parsed_data = resume.parsed_data or {}

            # Personal info (merge, preferring non-null values)
            if personal := parsed_data.get("personal"):
                self._merge_personal_info(aggregated["personal"], personal)

            # Summary (use the longest/most complete one)
            if summary := parsed_data.get("summary"):
                if not aggregated["summary"] or len(summary) > len(
                    aggregated["summary"]
                ):
                    aggregated["summary"] = summary

            # Experience (deduplicate by company + title + dates)
            if experiences := parsed_data.get("experience"):
                for exp in experiences:
                    exp_key = self._experience_key(exp)
                    if exp_key not in seen_experiences:
                        seen_experiences.add(exp_key)
                        aggregated["experience"].append(exp)

            # Education (deduplicate by institution + degree)
            if education := parsed_data.get("education"):
                for edu in education:
                    edu_key = self._education_key(edu)
                    if edu_key not in seen_education:
                        seen_education.add(edu_key)
                        aggregated["education"].append(edu)

            # Skills (deduplicate by name, case-insensitive)
            if skills := parsed_data.get("skills"):
                for skill in skills:
                    skill_lower = skill.lower().strip()
                    if skill_lower not in seen_skills:
                        seen_skills.add(skill_lower)
                        aggregated["skills"].append(skill)

            # Projects (deduplicate by name)
            if projects := parsed_data.get("projects"):
                for project in projects:
                    project_key = self._project_key(project)
                    if project_key not in seen_projects:
                        seen_projects.add(project_key)
                        aggregated["projects"].append(project)

            # Other data
            if other := parsed_data.get("other"):
                # Certifications
                if certs := other.get("certifications"):
                    for cert in certs:
                        cert_lower = cert.lower().strip()
                        if cert_lower not in seen_certifications:
                            seen_certifications.add(cert_lower)
                            aggregated["certifications"].append(cert)

                # Awards
                if awards := other.get("awards"):
                    for award in awards:
                        award_lower = award.lower().strip()
                        if award_lower not in seen_awards:
                            seen_awards.add(award_lower)
                            aggregated["awards"].append(award)

                # Publications
                if pubs := other.get("publications"):
                    for pub in pubs:
                        pub_lower = pub.lower().strip()
                        if pub_lower not in seen_publications:
                            seen_publications.add(pub_lower)
                            aggregated["publications"].append(pub)

                # Languages
                if langs := other.get("languages"):
                    for lang in langs:
                        lang_lower = lang.lower().strip()
                        if lang_lower not in seen_languages:
                            seen_languages.add(lang_lower)
                            aggregated["languages"].append(lang)

                # Volunteer
                if vols := other.get("volunteer"):
                    for vol in vols:
                        vol_lower = vol.lower().strip()
                        if vol_lower not in seen_volunteer:
                            seen_volunteer.add(vol_lower)
                            aggregated["volunteer"].append(vol)

        # Sort experience by date (most recent first)
        aggregated["experience"] = self._sort_experiences(aggregated["experience"])

        # Sort education by graduation date (most recent first)
        aggregated["education"] = self._sort_education(aggregated["education"])

        # Sort skills alphabetically
        aggregated["skills"] = sorted(aggregated["skills"], key=str.lower)

        # Add statistics
        aggregated["metadata"]["stats"] = {
            "total_experience_count": len(aggregated["experience"]),
            "total_education_count": len(aggregated["education"]),
            "total_skills_count": len(aggregated["skills"]),
            "total_projects_count": len(aggregated["projects"]),
            "total_certifications_count": len(aggregated["certifications"]),
        }

        return aggregated

    def _merge_personal_info(
        self, target: dict[str, Any], source: dict[str, Any]
    ) -> None:
        """Merge personal info, preferring non-null values.

        Args:
            target: Target personal info dict to update
            source: Source personal info dict
        """
        for key, value in source.items():
            if value and (not target.get(key) or value != "null"):
                target[key] = value

    def _experience_key(self, exp: dict[str, Any]) -> str:
        """Generate deduplication key for experience.

        Args:
            exp: Experience dict

        Returns:
            Unique key for deduplication
        """
        company = exp.get("company", "").lower().strip()
        title = exp.get("title", "").lower().strip()
        start = exp.get("start_date", "").lower().strip()
        return f"{company}|{title}|{start}"

    def _education_key(self, edu: dict[str, Any]) -> str:
        """Generate deduplication key for education.

        Args:
            edu: Education dict

        Returns:
            Unique key for deduplication
        """
        institution = edu.get("institution", "").lower().strip()
        degree = edu.get("degree", "").lower().strip()
        return f"{institution}|{degree}"

    def _project_key(self, project: dict[str, Any]) -> str:
        """Generate deduplication key for project.

        Args:
            project: Project dict

        Returns:
            Unique key for deduplication
        """
        name = project.get("name", "").lower().strip()
        return name

    def _sort_experiences(
        self, experiences: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Sort experiences by date (most recent first).

        Args:
            experiences: List of experience dicts

        Returns:
            Sorted list
        """

        def get_sort_key(exp: dict[str, Any]) -> tuple[int, int]:
            """Get sort key from experience dates."""
            end_date = exp.get("end_date", "")

            # Present is most recent
            if end_date and end_date.lower() == "present":
                return (9999, 12)

            # Try to parse YYYY-MM or YYYY
            try:
                if "-" in end_date:
                    year, month = end_date.split("-")
                    return (int(year), int(month))
                elif end_date:
                    return (int(end_date), 12)
            except (ValueError, AttributeError):
                pass

            # Fallback to start date
            start_date = exp.get("start_date", "")
            try:
                if "-" in start_date:
                    year, month = start_date.split("-")
                    return (int(year), int(month))
                elif start_date:
                    return (int(start_date), 1)
            except (ValueError, AttributeError):
                pass

            return (0, 0)

        return sorted(experiences, key=get_sort_key, reverse=True)

    def _sort_education(self, education: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort education by graduation date (most recent first).

        Args:
            education: List of education dicts

        Returns:
            Sorted list
        """

        def get_sort_key(edu: dict[str, Any]) -> int:
            """Get sort key from graduation date."""
            grad_date = edu.get("graduation_date", "") or ""

            # Try to parse YYYY-MM or YYYY
            try:
                if grad_date and "-" in grad_date:
                    year, _ = grad_date.split("-")
                    return int(year)
                elif grad_date:
                    return int(grad_date)
            except (ValueError, AttributeError):
                pass

            return 0

        return sorted(education, key=get_sort_key, reverse=True)
