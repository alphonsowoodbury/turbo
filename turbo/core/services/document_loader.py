"""
Document loader service that can parse various file types into text for Turbo Documents.

Supports: markdown, text, PDF, HTML, and more (extensible).
"""

import mimetypes
from pathlib import Path
from typing import Protocol


class DocumentParser(Protocol):
    """Protocol for document parsers."""

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the file."""
        ...

    def parse(self, file_path: Path) -> str:
        """Parse file and return text content."""
        ...


class MarkdownParser:
    """Parser for Markdown files."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".md", ".markdown"]

    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")


class TextParser:
    """Parser for plain text files."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".txt", ".text"]

    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")


class HTMLParser:
    """Parser for HTML files."""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".html", ".htm"]

    def parse(self, file_path: Path) -> str:
        # Basic HTML parsing - could be enhanced with BeautifulSoup
        content = file_path.read_text(encoding="utf-8")
        # For now, just return raw HTML (markdown renderer can handle some HTML)
        return content


class CodeParser:
    """Parser for code files (preserves as markdown code blocks)."""

    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".sh": "bash",
        ".sql": "sql",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".xml": "xml",
        ".css": "css",
        ".scss": "scss",
    }

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def parse(self, file_path: Path) -> str:
        """Parse code file and wrap in markdown code block."""
        content = file_path.read_text(encoding="utf-8")
        language = self.SUPPORTED_EXTENSIONS.get(file_path.suffix.lower(), "")

        # Wrap in markdown code block
        return f"```{language}\n{content}\n```"


class DocumentLoaderService:
    """Service to load various file types as Turbo Documents."""

    def __init__(self):
        # Register parsers in priority order
        self.parsers: list[DocumentParser] = [
            MarkdownParser(),
            TextParser(),
            HTMLParser(),
            CodeParser(),
        ]

    def add_parser(self, parser: DocumentParser) -> None:
        """Add a custom parser."""
        self.parsers.insert(0, parser)  # Add to front for priority

    def can_load(self, file_path: Path) -> bool:
        """Check if we can load this file."""
        if not file_path.exists():
            return False

        for parser in self.parsers:
            if parser.can_parse(file_path):
                return True

        return False

    def load(self, file_path: Path) -> str:
        """Load file and return text content."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Find appropriate parser
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser.parse(file_path)

        # No parser found
        raise ValueError(
            f"No parser available for file type: {file_path.suffix}. "
            f"Supported: .md, .txt, .html, code files"
        )

    def extract_title(self, content: str, filename: str) -> str:
        """Extract title from content or filename."""
        # Try to find H1 in markdown
        lines = content.split("\n")
        for line in lines[:10]:  # Check first 10 lines
            if line.strip().startswith("# "):
                return line.strip()[2:].strip()

        # Fallback to filename
        return filename.replace("_", " ").replace("-", " ").title()

    def determine_type(self, file_path: Path) -> str:
        """Determine document type based on file path and name."""
        path_str = str(file_path).lower()
        name = file_path.stem.lower()

        # Architecture documents
        if "architecture" in path_str or "plan" in name or "design" in name:
            return "design"

        # Specifications
        if "spec" in name or "prd" in name:
            return "specification"

        # Requirements
        if "requirements" in name or "roadmap" in name:
            return "requirements"

        # API docs
        if "api" in name:
            return "api_doc"

        # README/guides
        if "readme" in name or "guide" in name or "reference" in name:
            return "user_guide"

        # Code files
        if file_path.suffix.lower() in CodeParser.SUPPORTED_EXTENSIONS:
            return "code"

        # Default
        return "other"