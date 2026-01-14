"""AI-powered resume data extraction service using Claude API."""

import json
from typing import Any

from anthropic import Anthropic

from turbo.core.schemas.resume import ParsedResumeData
from turbo.utils.config import get_settings
from turbo.utils.exceptions import ValidationError


class ResumeAIExtractorService:
    """Service for AI-powered extraction of structured data from resume text."""

    def __init__(self, api_key: str | None = None):
        """Initialize AI extractor service.

        Args:
            api_key: Anthropic API key (optional, will use config if not provided)
        """
        settings = get_settings()

        if not api_key:
            api_key = settings.anthropic.api_key

        if not api_key:
            raise ValidationError(
                "Anthropic API key not configured. "
                "Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = Anthropic(api_key=api_key)
        self.model = settings.anthropic.model
        self.max_tokens = settings.anthropic.max_tokens
        self.temperature = settings.anthropic.temperature

    async def extract_structured_data(
        self,
        resume_text: str,
        sections: list[dict[str, Any]] | None = None,
    ) -> ParsedResumeData:
        """Extract structured data from resume text using Claude API.

        Args:
            resume_text: Full resume text
            sections: Pre-parsed sections (optional)

        Returns:
            Parsed resume data in structured format

        Raises:
            ValidationError: If extraction fails
        """
        try:
            # Build context from sections if available
            context = self._build_context(resume_text, sections)

            # Create extraction prompt
            prompt = self._create_extraction_prompt(context)

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract response text
            response_text = response.content[0].text

            # Parse JSON response
            parsed_data = self._parse_response(response_text)

            # Validate and convert to ParsedResumeData
            return ParsedResumeData(**parsed_data)

        except Exception as e:
            raise ValidationError(f"Failed to extract resume data: {str(e)}") from e

    def _build_context(
        self, resume_text: str, sections: list[dict[str, Any]] | None
    ) -> str:
        """Build context from resume text and sections.

        Args:
            resume_text: Full resume text
            sections: Pre-parsed sections

        Returns:
            Formatted context string
        """
        if not sections:
            return resume_text

        # Build structured context with sections
        context_parts = ["# Resume Content\n"]

        for section in sections:
            section_type = section.get("type", "unknown")
            title = section.get("title", "")
            content = section.get("content", "")

            context_parts.append(f"\n## {title} ({section_type})\n")
            context_parts.append(content)

        return "\n".join(context_parts)

    def _create_extraction_prompt(self, context: str) -> str:
        """Create extraction prompt for Claude API.

        Args:
            context: Resume context

        Returns:
            Formatted prompt
        """
        return f"""You are a resume parsing expert. Extract structured data from the following resume content.

{context}

Please extract and return the following information in JSON format:

{{
  "personal": {{
    "name": "Full name",
    "email": "Email address",
    "phone": "Phone number",
    "linkedin": "LinkedIn URL",
    "github": "GitHub URL",
    "website": "Personal website",
    "location": "City, State/Country"
  }},
  "summary": "Professional summary or objective statement (single paragraph)",
  "experience": [
    {{
      "company": "Company name",
      "title": "Job title",
      "location": "Location",
      "start_date": "Start date (YYYY-MM or YYYY)",
      "end_date": "End date (YYYY-MM or YYYY or 'Present')",
      "description": "Job description and key achievements (bullet points as newline-separated text)",
      "technologies": ["Tech1", "Tech2"]
    }}
  ],
  "education": [
    {{
      "institution": "School/University name",
      "degree": "Degree type and field",
      "location": "Location",
      "graduation_date": "Graduation date (YYYY or YYYY-MM)",
      "gpa": "GPA (if mentioned)",
      "honors": "Any honors or distinctions"
    }}
  ],
  "skills": ["Skill1", "Skill2", "Skill3"],
  "projects": [
    {{
      "name": "Project name",
      "description": "Project description",
      "technologies": ["Tech1", "Tech2"],
      "url": "Project URL (if available)",
      "date": "Project date or date range"
    }}
  ],
  "other": {{
    "certifications": ["Cert1", "Cert2"],
    "awards": ["Award1", "Award2"],
    "publications": ["Publication1"],
    "languages": ["Language: Proficiency"],
    "volunteer": ["Volunteer experience"]
  }}
}}

Important:
- If a field is not found, use null for strings, [] for arrays, or {{}} for objects
- For dates, use consistent formats (YYYY-MM or YYYY)
- For experience and projects, extract all relevant details
- For skills, extract both technical and soft skills mentioned
- Return ONLY valid JSON, no additional text

JSON:"""

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        """Parse JSON response from Claude API.

        Args:
            response_text: Response text from Claude

        Returns:
            Parsed data dictionary

        Raises:
            ValidationError: If response cannot be parsed
        """
        try:
            # Remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            cleaned_text = cleaned_text.strip()

            # Parse JSON
            data = json.loads(cleaned_text)

            # Ensure all required fields exist with defaults
            return {
                "personal": data.get("personal", {}),
                "summary": data.get("summary"),
                "experience": data.get("experience", []),
                "education": data.get("education", []),
                "skills": data.get("skills", []),
                "projects": data.get("projects", []),
                "other": data.get("other", {}),
            }

        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Failed to parse AI response as JSON: {str(e)}"
            ) from e

    def enhance_sections(
        self, sections: list[dict[str, Any]], parsed_data: ParsedResumeData
    ) -> list[dict[str, Any]]:
        """Enhance parsed sections with AI-extracted metadata.

        Args:
            sections: Pre-parsed sections
            parsed_data: AI-extracted data

        Returns:
            Enhanced sections with metadata
        """
        enhanced_sections = []

        for section in sections:
            section_type = section.get("type", "other")
            enhanced_section = section.copy()

            # Add relevant metadata based on section type
            if section_type == "experience" and parsed_data.experience:
                enhanced_section["metadata"] = {
                    "experiences": parsed_data.experience,
                }
            elif section_type == "education" and parsed_data.education:
                enhanced_section["metadata"] = {
                    "education": parsed_data.education,
                }
            elif section_type == "skills" and parsed_data.skills:
                enhanced_section["metadata"] = {
                    "skills": parsed_data.skills,
                }
            elif section_type == "projects" and parsed_data.projects:
                enhanced_section["metadata"] = {
                    "projects": parsed_data.projects,
                }
            elif section_type == "summary":
                enhanced_section["metadata"] = {
                    "summary": parsed_data.summary,
                }
            else:
                enhanced_section["metadata"] = {}

            enhanced_sections.append(enhanced_section)

        return enhanced_sections
