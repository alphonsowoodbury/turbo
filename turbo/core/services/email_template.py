"""Email template service using Document model."""

import re
from typing import Any
from uuid import UUID

from turbo.core.repositories.document import DocumentRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from turbo.core.services.key_generator import KeyGeneratorService
from turbo.utils.exceptions import DocumentNotFoundError, ValidationError


class EmailTemplateService:
    """Service for managing email templates using Document entities."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        project_repo: ProjectRepository,
        key_generator: KeyGeneratorService,
    ):
        """Initialize email template service.

        Args:
            document_repo: Document repository for database operations
            project_repo: Project repository for validation
            key_generator: Service for generating document keys
        """
        self.document_repo = document_repo
        self.project_repo = project_repo
        self.key_generator = key_generator

    async def create_template(
        self,
        project_id: UUID,
        name: str,
        content: str,
        category: str,
        variables: list[str] | None = None,
        version: str = "1.0",
    ) -> DocumentResponse:
        """Create a new email template.

        Args:
            project_id: Project to associate template with
            name: Template name
            content: Template content with {{variable}} placeholders
            category: Template category (cover_letter, cold_outreach, followup, etc.)
            variables: List of variable names used in template
            version: Template version (default: 1.0)

        Returns:
            DocumentResponse with template data

        Raises:
            ValidationError: If template validation fails
        """
        # Extract variables from content if not provided
        if variables is None:
            variables = self._extract_variables(content)

        # Validate project exists
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found")

        # Validate category
        valid_categories = {
            "cover_letter",
            "cold_outreach",
            "followup",
            "thank_you",
            "networking",
            "referral_request",
            "status_check",
            "other",
        }
        if category not in valid_categories:
            raise ValidationError(
                f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
            )

        # Create document with email template metadata
        doc_data = DocumentCreate(
            title=name,
            content=content,
            project_id=project_id,
            type="email_template",
            format="text",
            version=version,
            status="draft",
            doc_metadata={
                "category": category,
                "variables": variables,
                "usage_count": 0,
                "response_count": 0,
                "response_rate": 0.0,
                "avg_response_time_hours": None,
                "a_b_test_variants": [],
            },
        )

        # Generate document key
        document_key, document_number = await self.key_generator.generate_entity_key(
            project_id, "document"
        )

        # Set document key and number on the model
        doc_data.document_key = document_key
        doc_data.document_number = document_number

        # Create document (pass Pydantic model, not dict)
        document = await self.document_repo.create(doc_data)

        return DocumentResponse.model_validate(document)

    async def get_template(self, template_id: UUID) -> DocumentResponse:
        """Get email template by ID.

        Args:
            template_id: Template UUID

        Returns:
            DocumentResponse

        Raises:
            DocumentNotFoundError: If template not found
        """
        document = await self.document_repo.get_by_id(template_id)
        if not document or document.type != "email_template":
            raise DocumentNotFoundError(f"Email template {template_id} not found")

        return DocumentResponse.model_validate(document)

    async def list_templates(
        self,
        project_id: UUID | None = None,
        category: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[DocumentResponse]:
        """List email templates with optional filtering.

        Args:
            project_id: Filter by project
            category: Filter by category
            status: Filter by status
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of DocumentResponse objects
        """
        # Get all email templates
        documents = await self.document_repo.get_by_type(
            "email_template", limit=limit, offset=offset
        )

        # Apply filters
        filtered = []
        for doc in documents:
            # Filter by project
            if project_id and doc.project_id != project_id:
                continue

            # Filter by category
            if category:
                doc_category = doc.doc_metadata.get("category") if doc.doc_metadata else None
                if doc_category != category:
                    continue

            # Filter by status
            if status and doc.status != status:
                continue

            filtered.append(DocumentResponse.model_validate(doc))

        return filtered

    async def update_template(
        self, template_id: UUID, update_data: dict[str, Any]
    ) -> DocumentResponse:
        """Update email template.

        Args:
            template_id: Template UUID
            update_data: Fields to update

        Returns:
            Updated DocumentResponse

        Raises:
            DocumentNotFoundError: If template not found
        """
        # Verify template exists
        document = await self.document_repo.get_by_id(template_id)
        if not document or document.type != "email_template":
            raise DocumentNotFoundError(f"Email template {template_id} not found")

        # If content is being updated, re-extract variables
        if "content" in update_data:
            new_variables = self._extract_variables(update_data["content"])
            if "doc_metadata" not in update_data:
                update_data["doc_metadata"] = document.doc_metadata or {}
            update_data["doc_metadata"]["variables"] = new_variables

        # Update document
        updated = await self.document_repo.update(template_id, update_data)
        return DocumentResponse.model_validate(updated)

    async def delete_template(self, template_id: UUID) -> None:
        """Delete email template.

        Args:
            template_id: Template UUID

        Raises:
            DocumentNotFoundError: If template not found
        """
        # Verify template exists
        document = await self.document_repo.get_by_id(template_id)
        if not document or document.type != "email_template":
            raise DocumentNotFoundError(f"Email template {template_id} not found")

        await self.document_repo.delete(template_id)

    async def render_template(
        self, template_id: UUID, variables: dict[str, str]
    ) -> str:
        """Render template with variable substitution.

        Args:
            template_id: Template UUID
            variables: Dictionary of variable names to values

        Returns:
            Rendered template content

        Raises:
            DocumentNotFoundError: If template not found
            ValidationError: If required variables are missing
        """
        template = await self.get_template(template_id)

        # Get required variables
        required_vars = template.doc_metadata.get("variables", []) if template.doc_metadata else []

        # Check for missing variables
        missing = [var for var in required_vars if var not in variables]
        if missing:
            raise ValidationError(
                f"Missing required variables: {', '.join(missing)}"
            )

        # Perform variable substitution
        content = template.content
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            content = content.replace(placeholder, var_value)

        return content

    async def track_usage(self, template_id: UUID) -> None:
        """Track template usage (increment usage counter).

        Args:
            template_id: Template UUID
        """
        document = await self.document_repo.get_by_id(template_id)
        if not document or document.type != "email_template":
            return

        metadata = document.doc_metadata or {}
        metadata["usage_count"] = metadata.get("usage_count", 0) + 1

        await self.document_repo.update(template_id, {"doc_metadata": metadata})

    async def track_response(
        self, template_id: UUID, response_time_hours: float | None = None
    ) -> None:
        """Track response to email sent using this template.

        Args:
            template_id: Template UUID
            response_time_hours: Time in hours until response (optional)
        """
        document = await self.document_repo.get_by_id(template_id)
        if not document or document.type != "email_template":
            return

        metadata = document.doc_metadata or {}
        response_count = metadata.get("response_count", 0) + 1
        usage_count = metadata.get("usage_count", 1)

        metadata["response_count"] = response_count
        metadata["response_rate"] = response_count / usage_count if usage_count > 0 else 0.0

        # Update average response time
        if response_time_hours is not None:
            current_avg = metadata.get("avg_response_time_hours")
            if current_avg is None:
                metadata["avg_response_time_hours"] = response_time_hours
            else:
                # Running average
                metadata["avg_response_time_hours"] = (
                    current_avg * (response_count - 1) + response_time_hours
                ) / response_count

        await self.document_repo.update(template_id, {"doc_metadata": metadata})

    async def create_ab_variant(
        self, template_id: UUID, variant_name: str, variant_content: str
    ) -> UUID:
        """Create A/B test variant of a template.

        Args:
            template_id: Original template UUID
            variant_name: Name for the variant
            variant_content: Modified content for variant

        Returns:
            UUID of the created variant template

        Raises:
            DocumentNotFoundError: If original template not found
        """
        # Get original template
        original = await self.get_template(template_id)

        # Create variant as new template
        variant_doc = DocumentCreate(
            title=f"{original.title} - {variant_name}",
            content=variant_content,
            project_id=original.project_id,
            type="email_template",
            format="text",
            version=original.version,
            status="draft",
            doc_metadata={
                "category": original.doc_metadata.get("category") if original.doc_metadata else "other",
                "variables": self._extract_variables(variant_content),
                "usage_count": 0,
                "response_count": 0,
                "response_rate": 0.0,
                "avg_response_time_hours": None,
                "a_b_test_variants": [],
                "original_template_id": str(template_id),
                "variant_name": variant_name,
            },
        )

        # Generate key for variant
        document_key, document_number = await self.key_generator.generate_entity_key(
            original.project_id, "document"
        )

        doc_dict = variant_doc.model_dump(exclude_unset=True)
        doc_dict["document_key"] = document_key
        doc_dict["document_number"] = document_number

        variant = await self.document_repo.create(doc_dict)

        # Update original template to track variant
        original_metadata = original.doc_metadata or {}
        variants = original_metadata.get("a_b_test_variants", [])
        variants.append({"variant_id": str(variant.id), "variant_name": variant_name})
        original_metadata["a_b_test_variants"] = variants

        await self.document_repo.update(template_id, {"doc_metadata": original_metadata})

        return variant.id

    def _extract_variables(self, content: str) -> list[str]:
        """Extract variable names from template content.

        Args:
            content: Template content with {{variable}} placeholders

        Returns:
            List of unique variable names
        """
        # Find all {{variable}} patterns
        pattern = r"\{\{(\w+)\}\}"
        matches = re.findall(pattern, content)
        return list(set(matches))  # Unique variables only
