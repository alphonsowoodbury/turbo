"""PDF parsing service for extracting text from resume PDFs."""

import re
from pathlib import Path
from typing import Any

import pdfplumber

from turbo.utils.exceptions import ValidationError


class PDFParserService:
    """Service for parsing PDF files and extracting structured text."""

    def __init__(self):
        """Initialize PDF parser service."""
        pass

    def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse PDF file and extract text content.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary containing parsed content:
            {
                "text": str,           # Raw text from PDF
                "pages": List[str],   # Text per page
                "metadata": dict,     # PDF metadata
                "sections": List[dict] # Detected sections
            }

        Raises:
            ValidationError: If file cannot be parsed
        """
        path = Path(file_path)

        if not path.exists():
            raise ValidationError(f"File not found: {file_path}")

        if not path.suffix.lower() == ".pdf":
            raise ValidationError(f"Not a PDF file: {file_path}")

        try:
            with pdfplumber.open(path) as pdf:
                # Extract metadata
                metadata = self._extract_metadata(pdf)

                # Extract text from all pages
                pages_text = []
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages_text.append(text)

                # Combine all text
                full_text = "\n\n".join(pages_text)

                # Detect sections based on common resume patterns
                sections = self._detect_sections(full_text)

                return {
                    "text": full_text,
                    "pages": pages_text,
                    "metadata": metadata,
                    "sections": sections,
                }

        except Exception as e:
            raise ValidationError(f"Failed to parse PDF: {str(e)}") from e

    def _extract_metadata(self, pdf: pdfplumber.PDF) -> dict[str, Any]:
        """Extract metadata from PDF.

        Args:
            pdf: pdfplumber PDF object

        Returns:
            Dictionary with metadata
        """
        metadata = pdf.metadata or {}

        return {
            "title": metadata.get("Title", ""),
            "author": metadata.get("Author", ""),
            "subject": metadata.get("Subject", ""),
            "creator": metadata.get("Creator", ""),
            "producer": metadata.get("Producer", ""),
            "creation_date": metadata.get("CreationDate", ""),
            "modification_date": metadata.get("ModDate", ""),
            "page_count": len(pdf.pages),
        }

    def _detect_sections(self, text: str) -> list[dict[str, Any]]:
        """Detect common resume sections based on headings.

        Args:
            text: Full text content

        Returns:
            List of detected sections with type, title, and content
        """
        # Common resume section patterns
        section_patterns = [
            (r"(?i)^(summary|professional\s+summary|profile|objective)[\s:]*$", "summary"),
            (r"(?i)^(experience|work\s+experience|employment|employment\s+history)[\s:]*$", "experience"),
            (r"(?i)^(education|academic\s+background)[\s:]*$", "education"),
            (r"(?i)^(skills|technical\s+skills|core\s+competencies)[\s:]*$", "skills"),
            (r"(?i)^(projects|portfolio|selected\s+projects)[\s:]*$", "projects"),
            (r"(?i)^(certifications|certificates|licenses)[\s:]*$", "certifications"),
            (r"(?i)^(awards|honors|achievements)[\s:]*$", "awards"),
            (r"(?i)^(publications|papers)[\s:]*$", "publications"),
            (r"(?i)^(volunteer|volunteering|community\s+service)[\s:]*$", "volunteer"),
            (r"(?i)^(languages|language\s+proficiency)[\s:]*$", "languages"),
            (r"(?i)^(references)[\s:]*$", "references"),
        ]

        sections = []
        lines = text.split("\n")

        current_section = None
        current_content = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            # Check if line matches a section heading
            matched = False
            for pattern, section_type in section_patterns:
                if re.match(pattern, stripped):
                    # Save previous section if exists
                    if current_section:
                        sections.append({
                            "type": current_section["type"],
                            "title": current_section["title"],
                            "content": "\n".join(current_content).strip(),
                        })

                    # Start new section
                    current_section = {
                        "type": section_type,
                        "title": stripped,
                    }
                    current_content = []
                    matched = True
                    break

            if not matched and current_section:
                # Add to current section content
                current_content.append(line)

        # Add last section
        if current_section:
            sections.append({
                "type": current_section["type"],
                "title": current_section["title"],
                "content": "\n".join(current_content).strip(),
            })

        return sections

    def extract_contact_info(self, text: str) -> dict[str, str | None]:
        """Extract contact information from text.

        Args:
            text: Text content

        Returns:
            Dictionary with contact fields (email, phone, linkedin, etc.)
        """
        contact_info: dict[str, str | None] = {
            "email": None,
            "phone": None,
            "linkedin": None,
            "github": None,
            "website": None,
        }

        # Email pattern
        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        if email_match:
            contact_info["email"] = email_match.group(0)

        # Phone pattern (basic US format)
        phone_match = re.search(
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text
        )
        if phone_match:
            contact_info["phone"] = phone_match.group(0)

        # LinkedIn pattern
        linkedin_match = re.search(
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", text, re.IGNORECASE
        )
        if linkedin_match:
            contact_info["linkedin"] = linkedin_match.group(0)

        # GitHub pattern
        github_match = re.search(
            r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", text, re.IGNORECASE
        )
        if github_match:
            contact_info["github"] = github_match.group(0)

        # Website pattern (basic)
        website_match = re.search(
            r"(?:https?://)?(?:www\.)?[\w-]+\.[\w-]+(?:/[\w-]+)*", text
        )
        if website_match and not any([
            linkedin_match and website_match.group(0) in (linkedin_match.group(0) or ""),
            github_match and website_match.group(0) in (github_match.group(0) or ""),
        ]):
            contact_info["website"] = website_match.group(0)

        return contact_info

    def extract_name(self, text: str) -> str | None:
        """Extract name from resume text.

        Assumes name is in first few lines and is title-cased.

        Args:
            text: Text content

        Returns:
            Extracted name or None
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        if not lines:
            return None

        # Check first 5 lines for a name
        for line in lines[:5]:
            # Skip if line has email or phone
            if "@" in line or re.search(r"\d{3}[-.\s]\d{3}[-.\s]\d{4}", line):
                continue

            # Skip common headers
            if line.upper() in ["RESUME", "CV", "CURRICULUM VITAE"]:
                continue

            # Check if it looks like a name (2-4 words, title case)
            words = line.split()
            if 2 <= len(words) <= 4 and all(
                word[0].isupper() if word else False for word in words
            ):
                return line

        return None
