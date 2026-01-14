"""Repository for form operations."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.form import Form, FormResponse, FormResponseAudit


class FormRepository:
    """Repository for form database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create_form(self, form_data: dict[str, Any]) -> Form:
        """Create a new form."""
        form = Form(**form_data)
        self.session.add(form)
        await self.session.commit()
        await self.session.refresh(form)
        return form

    async def get_form(self, form_id: str) -> Form | None:
        """Get a form by ID."""
        stmt = select(Form).where(Form.id == form_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_forms_by_issue(self, issue_id: str) -> list[Form]:
        """Get all forms attached to an issue."""
        stmt = select(Form).where(Form.issue_id == issue_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_forms_by_document(self, document_id: str) -> list[Form]:
        """Get all forms attached to a document."""
        stmt = select(Form).where(Form.document_id == document_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_forms_by_project(self, project_id: str) -> list[Form]:
        """Get all forms attached to a project."""
        stmt = select(Form).where(Form.project_id == project_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_form(self, form_id: str, update_data: dict[str, Any]) -> Form | None:
        """Update a form."""
        form = await self.get_form(form_id)
        if not form:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(form, key, value)

        form.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(form)
        return form

    async def delete_form(self, form_id: str) -> bool:
        """Delete a form."""
        form = await self.get_form(form_id)
        if not form:
            return False

        await self.session.delete(form)
        await self.session.commit()
        return True


class FormResponseRepository:
    """Repository for form response operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create_response(self, response_data: dict[str, Any]) -> FormResponse:
        """Create a new form response."""
        response = FormResponse(**response_data)
        self.session.add(response)
        await self.session.commit()
        await self.session.refresh(response)
        return response

    async def get_response(self, response_id: str) -> FormResponse | None:
        """Get a form response by ID."""
        stmt = select(FormResponse).where(FormResponse.id == response_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_responses_by_form(self, form_id: str) -> list[FormResponse]:
        """Get all responses for a form."""
        stmt = select(FormResponse).where(FormResponse.form_id == form_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_response_by_user_and_form(
        self, form_id: str, user_id: str
    ) -> FormResponse | None:
        """Get a user's response to a specific form (single response model)."""
        stmt = select(FormResponse).where(
            FormResponse.form_id == form_id, FormResponse.responded_by == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_response(
        self,
        response_id: str,
        update_data: dict[str, Any],
        changed_by: str,
        changed_by_type: str = "user",
    ) -> FormResponse | None:
        """Update a form response and create audit log entries."""
        response = await self.get_response(response_id)
        if not response:
            return None

        # Get old responses for audit trail
        old_responses = response.responses.copy()
        new_responses = update_data.get("responses", {})

        # Update response
        for key, value in update_data.items():
            if value is not None:
                setattr(response, key, value)

        response.updated_at = datetime.utcnow()

        # Create audit entries for changed fields
        for field_id, new_value in new_responses.items():
            old_value = old_responses.get(field_id)
            if old_value != new_value:
                audit_entry = FormResponseAudit(
                    response_id=response_id,
                    field_id=field_id,
                    old_value={"value": old_value} if old_value is not None else None,
                    new_value={"value": new_value},
                    changed_by=changed_by,
                    changed_by_type=changed_by_type,
                )
                self.session.add(audit_entry)

        await self.session.commit()
        await self.session.refresh(response)
        return response

    async def delete_response(self, response_id: str) -> bool:
        """Delete a form response."""
        response = await self.get_response(response_id)
        if not response:
            return False

        await self.session.delete(response)
        await self.session.commit()
        return True

    async def get_audit_log(self, response_id: str) -> list[FormResponseAudit]:
        """Get audit log for a form response."""
        stmt = (
            select(FormResponseAudit)
            .where(FormResponseAudit.response_id == response_id)
            .order_by(FormResponseAudit.changed_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
