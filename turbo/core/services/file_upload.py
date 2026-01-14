"""File upload service for handling resume file uploads."""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from turbo.utils.exceptions import ValidationError


class FileUploadService:
    """Service for handling file uploads with validation."""

    # Allowed file types
    ALLOWED_EXTENSIONS = {".pdf", ".md", ".markdown"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "text/markdown",
        "text/plain",  # Some markdown files are detected as plain text
    }

    # Size limits (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, upload_dir: str = "uploads/resumes"):
        """Initialize file upload service.

        Args:
            upload_dir: Directory to store uploaded files (relative to project root)
        """
        self.upload_dir = Path(upload_dir)
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        """Create upload directory if it doesn't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(
        self, filename: str, file_size: int, content_type: str | None = None
    ) -> None:
        """Validate file before upload.

        Args:
            filename: Name of the file
            file_size: Size of file in bytes
            content_type: MIME type of the file

        Raises:
            ValidationError: If file validation fails
        """
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Check MIME type if provided
        if content_type and content_type not in self.ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"Invalid content type: {content_type}. "
                f"Allowed types: {', '.join(self.ALLOWED_MIME_TYPES)}"
            )

        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(
                f"File size exceeds maximum allowed size of {max_size_mb:.1f} MB"
            )

        if file_size == 0:
            raise ValidationError("File is empty")

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename to avoid collisions.

        Args:
            original_filename: Original name of the uploaded file

        Returns:
            Unique filename with format: timestamp_uuid_originalname.ext
        """
        file_ext = Path(original_filename).suffix.lower()
        file_stem = Path(original_filename).stem

        # Clean filename (remove special characters)
        clean_stem = "".join(
            c for c in file_stem if c.isalnum() or c in ("-", "_")
        ).rstrip()

        # Generate unique identifier
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        return f"{timestamp}_{unique_id}_{clean_stem}{file_ext}"

    async def save_file(
        self, file: BinaryIO, filename: str, content_type: str | None = None
    ) -> str:
        """Save uploaded file to disk.

        Args:
            file: File object (binary mode)
            filename: Original filename
            content_type: MIME type of the file

        Returns:
            Relative path to saved file

        Raises:
            ValidationError: If file validation fails
        """
        # Read file content
        content = file.read()
        file_size = len(content)

        # Validate file
        self.validate_file(filename, file_size, content_type)

        # Generate unique filename
        unique_filename = self.generate_unique_filename(filename)
        file_path = self.upload_dir / unique_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        # Return relative path
        return str(file_path)

    def delete_file(self, file_path: str) -> None:
        """Delete uploaded file.

        Args:
            file_path: Path to file to delete
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
        except Exception as e:
            # Log error but don't raise - file deletion is not critical
            print(f"Warning: Failed to delete file {file_path}: {e}")

    def get_file_type(self, filename: str) -> str:
        """Determine file type from filename.

        Args:
            filename: Name of the file

        Returns:
            File type: 'pdf' or 'markdown'

        Raises:
            ValidationError: If file type is not supported
        """
        file_ext = Path(filename).suffix.lower()

        if file_ext == ".pdf":
            return "pdf"
        elif file_ext in {".md", ".markdown"}:
            return "markdown"
        else:
            raise ValidationError(f"Unsupported file type: {file_ext}")

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists at given path.

        Args:
            file_path: Path to file

        Returns:
            True if file exists, False otherwise
        """
        return Path(file_path).exists()
