"""Markdown parsing service for extracting structured data from markdown resumes."""

import re
from pathlib import Path
from typing import Any

from turbo.utils.exceptions import ValidationError


class MarkdownParserService:
    """Service for parsing Markdown files and extracting structured content."""

    def __init__(self):
        """Initialize Markdown parser service."""
        pass

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse Markdown file and extract structured content.

        Args:
            file_path: Path to Markdown file

        Returns:
            Dictionary containing parsed content:
            {
                "text": str,              # Raw markdown text
                "sections": List[dict],   # Detected sections with headings
                "metadata": dict,         # Extracted metadata (if present)
            }

        Raises:
            ValidationError: If file cannot be parsed
        """
        path = Path(file_path)

        if not path.exists():
            raise ValidationError(f"File not found: {file_path}")

        if path.suffix.lower() not in {".md", ".markdown"}:
            raise ValidationError(f"Not a Markdown file: {file_path}")

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Extract YAML frontmatter if present
            metadata = self._extract_frontmatter(content)

            # Remove frontmatter from content
            content_without_frontmatter = self._remove_frontmatter(content)

            # Extract sections based on headings
            sections = self._extract_sections(content_without_frontmatter)

            return {
                "text": content_without_frontmatter,
                "sections": sections,
                "metadata": metadata,
            }

        except Exception as e:
            raise ValidationError(f"Failed to parse Markdown: {str(e)}") from e

    def _extract_frontmatter(self, content: str) -> dict[str, Any]:
        """Extract YAML frontmatter from markdown content.

        Args:
            content: Markdown content

        Returns:
            Dictionary with frontmatter data
        """
        # Match YAML frontmatter (--- at start and end)
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

        if not match:
            return {}

        frontmatter_text = match.group(1)
        metadata: dict[str, Any] = {}

        # Simple key-value parsing (not full YAML parser)
        for line in frontmatter_text.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()

        return metadata

    def _remove_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from markdown content.

        Args:
            content: Markdown content

        Returns:
            Content without frontmatter
        """
        return re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)

    def _extract_sections(self, content: str) -> list[dict[str, Any]]:
        """Extract sections based on markdown headings.

        Args:
            content: Markdown content

        Returns:
            List of sections with type, title, level, and content
        """
        sections = []
        lines = content.split("\n")

        current_section: dict[str, Any] | None = None
        current_content: list[str] = []

        for line in lines:
            # Check for ATX-style headings (# Heading)
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            # Check for Setext-style headings (underlined with = or -)
            if not heading_match and len(current_content) > 0:
                setext_match = re.match(r"^[=\-]{3,}$", line.strip())
                if setext_match:
                    # Previous line is the heading
                    heading_text = current_content[-1].strip()
                    level = 1 if "=" in line else 2

                    # Save previous section
                    if current_section:
                        sections.append({
                            "type": self._determine_section_type(current_section["title"]),
                            "title": current_section["title"],
                            "level": current_section["level"],
                            "content": "\n".join(current_content[:-1]).strip(),
                        })

                    # Start new section
                    current_section = {
                        "title": heading_text,
                        "level": level,
                    }
                    current_content = []
                    continue

            if heading_match:
                # Save previous section
                if current_section:
                    sections.append({
                        "type": self._determine_section_type(current_section["title"]),
                        "title": current_section["title"],
                        "level": current_section["level"],
                        "content": "\n".join(current_content).strip(),
                    })

                # Start new section
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                current_section = {
                    "title": title,
                    "level": level,
                }
                current_content = []
            else:
                # Add to current section content
                if current_section:
                    current_content.append(line)

        # Add last section
        if current_section:
            sections.append({
                "type": self._determine_section_type(current_section["title"]),
                "title": current_section["title"],
                "level": current_section["level"],
                "content": "\n".join(current_content).strip(),
            })

        return sections

    def _determine_section_type(self, title: str) -> str:
        """Determine section type from title.

        Args:
            title: Section title

        Returns:
            Section type (summary, experience, education, etc.)
        """
        title_lower = title.lower()

        # Common resume section patterns
        type_patterns = [
            (["summary", "professional summary", "profile", "objective", "about"], "summary"),
            (["experience", "work experience", "employment", "employment history", "professional experience"], "experience"),
            (["education", "academic background", "academic", "degrees"], "education"),
            (["skills", "technical skills", "core competencies", "technologies", "expertise"], "skills"),
            (["projects", "portfolio", "selected projects", "notable projects"], "projects"),
            (["certifications", "certificates", "licenses", "credentials"], "certifications"),
            (["awards", "honors", "achievements", "recognition"], "awards"),
            (["publications", "papers", "research", "articles"], "publications"),
            (["volunteer", "volunteering", "community service", "community"], "volunteer"),
            (["languages", "language proficiency"], "languages"),
            (["references"], "references"),
            (["contact", "contact information"], "contact"),
        ]

        for keywords, section_type in type_patterns:
            if any(keyword in title_lower for keyword in keywords):
                return section_type

        return "other"

    def extract_contact_info(self, text: str) -> dict[str, str | None]:
        """Extract contact information from text.

        Args:
            text: Text content

        Returns:
            Dictionary with contact fields
        """
        contact_info: dict[str, str | None] = {
            "email": None,
            "phone": None,
            "linkedin": None,
            "github": None,
            "website": None,
            "location": None,
        }

        # Email pattern
        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        if email_match:
            contact_info["email"] = email_match.group(0)

        # Phone pattern
        phone_match = re.search(
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text
        )
        if phone_match:
            contact_info["phone"] = phone_match.group(0)

        # LinkedIn pattern (including markdown links)
        linkedin_match = re.search(
            r"(?:\[.*?\]\()?(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+(?:\))?",
            text,
            re.IGNORECASE,
        )
        if linkedin_match:
            # Extract URL from markdown link if present
            url_match = re.search(
                r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+",
                linkedin_match.group(0),
                re.IGNORECASE,
            )
            if url_match:
                contact_info["linkedin"] = url_match.group(0)

        # GitHub pattern (including markdown links)
        github_match = re.search(
            r"(?:\[.*?\]\()?(?:https?://)?(?:www\.)?github\.com/[\w-]+(?:\))?",
            text,
            re.IGNORECASE,
        )
        if github_match:
            # Extract URL from markdown link if present
            url_match = re.search(
                r"(?:https?://)?(?:www\.)?github\.com/[\w-]+",
                github_match.group(0),
                re.IGNORECASE,
            )
            if url_match:
                contact_info["github"] = url_match.group(0)

        # Location pattern (common formats)
        location_match = re.search(
            r"(?:Location|Address|Based in):\s*([A-Za-z\s,]+(?:,\s*[A-Z]{2})?)",
            text,
            re.IGNORECASE,
        )
        if location_match:
            contact_info["location"] = location_match.group(1).strip()

        return contact_info

    def extract_name_from_heading(self, content: str) -> str | None:
        """Extract name from first heading in markdown.

        Args:
            content: Markdown content

        Returns:
            Extracted name or None
        """
        lines = content.split("\n")

        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()

            # Check for ATX-style heading
            heading_match = re.match(r"^#\s+(.+)$", line)
            if heading_match:
                name = heading_match.group(1).strip()
                # Remove markdown formatting
                name = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", name)
                name = re.sub(r"[*_`]", "", name)
                return name.strip()

        return None
