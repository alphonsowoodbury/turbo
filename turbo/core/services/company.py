"""Company service for business logic operations."""

from uuid import UUID

from turbo.core.repositories.company import CompanyRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.schemas.company import (
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
)
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import (
    CompanyNotFoundError,
)


class CompanyService:
    """Service for company business logic."""

    def __init__(
        self,
        company_repository: CompanyRepository,
        tag_repository: TagRepository,
    ) -> None:
        self._company_repository = company_repository
        self._tag_repository = tag_repository

    async def create_company(self, company_data: CompanyCreate) -> CompanyResponse:
        """Create a new company."""
        # Strip emojis from text fields
        if company_data.name:
            company_data.name = strip_emojis(company_data.name)
        if company_data.research_notes:
            company_data.research_notes = strip_emojis(company_data.research_notes)
        if company_data.culture_notes:
            company_data.culture_notes = strip_emojis(company_data.culture_notes)

        # Extract association IDs before creating the company
        tag_ids = company_data.tag_ids

        # Create company without association fields
        company_dict = company_data.model_dump(exclude={"tag_ids"})
        company = await self._company_repository.create(CompanyCreate(**company_dict))

        # Commit the company first
        await self._company_repository._session.commit()
        await self._company_repository._session.refresh(company)

        # Handle tag associations after commit
        if tag_ids:
            await self._company_repository._session.refresh(company, ["tags"])
            for tag_id in tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    company.tags.append(tag)

            await self._company_repository._session.commit()
            await self._company_repository._session.refresh(company)

        # Return response with counts
        response_dict = {
            "id": company.id,
            "name": company.name,
            "website": company.website,
            "industry": company.industry,
            "size": company.size,
            "location": company.location,
            "remote_policy": company.remote_policy,
            "target_status": company.target_status,
            "research_notes": company.research_notes,
            "culture_notes": company.culture_notes,
            "tech_stack": company.tech_stack,
            "glassdoor_rating": company.glassdoor_rating,
            "linkedin_url": company.linkedin_url,
            "careers_page_url": company.careers_page_url,
            "application_count": company.application_count,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
            "tag_count": len(tag_ids) if tag_ids else 0,
            "contact_count": 0,
        }
        return CompanyResponse(**response_dict)

    async def get_company_by_id(self, company_id: UUID) -> CompanyResponse:
        """Get company by ID."""
        company = await self._company_repository.get_with_all_relations(company_id)
        if not company:
            raise CompanyNotFoundError(company_id)
        return self._to_response(company)

    async def get_all_companies(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[CompanyResponse]:
        """Get all companies with optional pagination."""
        companies = await self._company_repository.get_all(limit=limit, offset=offset)
        return [
            CompanyResponse(
                id=c.id,
                name=c.name,
                website=c.website,
                industry=c.industry,
                size=c.size,
                location=c.location,
                remote_policy=c.remote_policy,
                target_status=c.target_status,
                research_notes=c.research_notes,
                culture_notes=c.culture_notes,
                tech_stack=c.tech_stack,
                glassdoor_rating=c.glassdoor_rating,
                linkedin_url=c.linkedin_url,
                careers_page_url=c.careers_page_url,
                application_count=c.application_count,
                created_at=c.created_at,
                updated_at=c.updated_at,
                tag_count=0,
                contact_count=0,
            )
            for c in companies
        ]

    async def update_company(
        self, company_id: UUID, update_data: CompanyUpdate
    ) -> CompanyResponse:
        """Update a company."""
        # Strip emojis from text fields
        if update_data.name:
            update_data.name = strip_emojis(update_data.name)
        if update_data.research_notes:
            update_data.research_notes = strip_emojis(update_data.research_notes)
        if update_data.culture_notes:
            update_data.culture_notes = strip_emojis(update_data.culture_notes)

        company = await self._company_repository.get_by_id(company_id)
        if not company:
            raise CompanyNotFoundError(company_id)

        # Update basic fields
        company = await self._company_repository.update(company_id, update_data)
        if not company:
            raise CompanyNotFoundError(company_id)

        # Handle tag updates
        if update_data.tag_ids is not None:
            await self._company_repository._session.refresh(company, ["tags"])
            company.tags.clear()
            for tag_id in update_data.tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    company.tags.append(tag)

        await self._company_repository._session.commit()
        await self._company_repository._session.refresh(company)

        return self._to_response(company)

    async def delete_company(self, company_id: UUID) -> bool:
        """Delete a company."""
        success = await self._company_repository.delete(company_id)
        if not success:
            raise CompanyNotFoundError(company_id)
        return success

    async def get_companies_by_target_status(self, target_status: str) -> list[CompanyResponse]:
        """Get companies by target status."""
        companies = await self._company_repository.get_by_target_status(target_status)
        return [self._to_response(c) for c in companies]

    async def get_companies_by_industry(self, industry: str) -> list[CompanyResponse]:
        """Get companies by industry."""
        companies = await self._company_repository.get_by_industry(industry)
        return [self._to_response(c) for c in companies]

    async def search_companies(self, name_pattern: str) -> list[CompanyResponse]:
        """Search companies by name."""
        companies = await self._company_repository.search_by_name(name_pattern)
        return [self._to_response(c) for c in companies]

    def _to_response(self, company) -> CompanyResponse:
        """Convert company model to response."""
        tag_count = len(company.tags) if hasattr(company, 'tags') else 0
        contact_count = len(company.network_contacts) if hasattr(company, 'network_contacts') else 0

        response_dict = {
            "id": company.id,
            "name": company.name,
            "website": company.website,
            "industry": company.industry,
            "size": company.size,
            "location": company.location,
            "remote_policy": company.remote_policy,
            "target_status": company.target_status,
            "research_notes": company.research_notes,
            "culture_notes": company.culture_notes,
            "tech_stack": company.tech_stack,
            "glassdoor_rating": company.glassdoor_rating,
            "linkedin_url": company.linkedin_url,
            "careers_page_url": company.careers_page_url,
            "application_count": company.application_count,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
            "tag_count": tag_count,
            "contact_count": contact_count,
        }
        return CompanyResponse(**response_dict)
