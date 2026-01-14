"""NetworkContact service for business logic operations."""

from uuid import UUID

from turbo.core.repositories.company import CompanyRepository
from turbo.core.repositories.network_contact import NetworkContactRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.schemas.network_contact import (
    NetworkContactCreate,
    NetworkContactResponse,
    NetworkContactUpdate,
)
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import (
    NetworkContactNotFoundError,
)


class NetworkContactService:
    """Service for network contact business logic."""

    def __init__(
        self,
        network_contact_repository: NetworkContactRepository,
        company_repository: CompanyRepository,
        tag_repository: TagRepository,
    ) -> None:
        self._network_contact_repository = network_contact_repository
        self._company_repository = company_repository
        self._tag_repository = tag_repository

    async def create_network_contact(
        self, contact_data: NetworkContactCreate
    ) -> NetworkContactResponse:
        """Create a new network contact."""
        # Strip emojis from text fields
        if contact_data.first_name:
            contact_data.first_name = strip_emojis(contact_data.first_name)
        if contact_data.last_name:
            contact_data.last_name = strip_emojis(contact_data.last_name)
        if contact_data.how_we_met:
            contact_data.how_we_met = strip_emojis(contact_data.how_we_met)
        if contact_data.conversation_history:
            contact_data.conversation_history = strip_emojis(contact_data.conversation_history)
        if contact_data.notes:
            contact_data.notes = strip_emojis(contact_data.notes)

        # Extract association IDs before creating the contact
        tag_ids = contact_data.tag_ids

        # Create contact without association fields
        contact_dict = contact_data.model_dump(exclude={"tag_ids"})
        contact = await self._network_contact_repository.create(
            NetworkContactCreate(**contact_dict)
        )

        # Commit the contact first
        await self._network_contact_repository._session.commit()
        await self._network_contact_repository._session.refresh(contact)

        # Handle tag associations after commit
        if tag_ids:
            await self._network_contact_repository._session.refresh(contact, ["tags"])
            for tag_id in tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    contact.tags.append(tag)

            await self._network_contact_repository._session.commit()
            await self._network_contact_repository._session.refresh(contact)

        # Return response with counts
        response_dict = {
            "id": contact.id,
            "company_id": contact.company_id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "linkedin_url": contact.linkedin_url,
            "phone": contact.phone,
            "current_title": contact.current_title,
            "current_company": contact.current_company,
            "contact_type": contact.contact_type,
            "relationship_strength": contact.relationship_strength,
            "last_contact_date": contact.last_contact_date,
            "next_followup_date": contact.next_followup_date,
            "how_we_met": contact.how_we_met,
            "conversation_history": contact.conversation_history,
            "referral_status": contact.referral_status,
            "github_url": contact.github_url,
            "personal_website": contact.personal_website,
            "twitter_url": contact.twitter_url,
            "notes": contact.notes,
            "is_active": contact.is_active,
            "interaction_count": contact.interaction_count,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
            "tag_count": len(tag_ids) if tag_ids else 0,
        }
        return NetworkContactResponse(**response_dict)

    async def get_network_contact_by_id(self, contact_id: UUID) -> NetworkContactResponse:
        """Get network contact by ID."""
        contact = await self._network_contact_repository.get_with_all_relations(contact_id)
        if not contact:
            raise NetworkContactNotFoundError(contact_id)
        return self._to_response(contact)

    async def get_all_network_contacts(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[NetworkContactResponse]:
        """Get all network contacts with optional pagination."""
        contacts = await self._network_contact_repository.get_all(
            limit=limit, offset=offset
        )
        return [
            NetworkContactResponse(
                id=c.id,
                company_id=c.company_id,
                first_name=c.first_name,
                last_name=c.last_name,
                email=c.email,
                linkedin_url=c.linkedin_url,
                phone=c.phone,
                current_title=c.current_title,
                current_company=c.current_company,
                contact_type=c.contact_type,
                relationship_strength=c.relationship_strength,
                last_contact_date=c.last_contact_date,
                next_followup_date=c.next_followup_date,
                how_we_met=c.how_we_met,
                conversation_history=c.conversation_history,
                referral_status=c.referral_status,
                github_url=c.github_url,
                personal_website=c.personal_website,
                twitter_url=c.twitter_url,
                notes=c.notes,
                is_active=c.is_active,
                interaction_count=c.interaction_count,
                created_at=c.created_at,
                updated_at=c.updated_at,
                tag_count=0,
            )
            for c in contacts
        ]

    async def update_network_contact(
        self, contact_id: UUID, update_data: NetworkContactUpdate
    ) -> NetworkContactResponse:
        """Update a network contact."""
        # Strip emojis from text fields
        if update_data.first_name:
            update_data.first_name = strip_emojis(update_data.first_name)
        if update_data.last_name:
            update_data.last_name = strip_emojis(update_data.last_name)
        if update_data.how_we_met:
            update_data.how_we_met = strip_emojis(update_data.how_we_met)
        if update_data.conversation_history:
            update_data.conversation_history = strip_emojis(update_data.conversation_history)
        if update_data.notes:
            update_data.notes = strip_emojis(update_data.notes)

        contact = await self._network_contact_repository.get_by_id(contact_id)
        if not contact:
            raise NetworkContactNotFoundError(contact_id)

        # Update basic fields
        contact = await self._network_contact_repository.update(contact_id, update_data)
        if not contact:
            raise NetworkContactNotFoundError(contact_id)

        # Handle tag updates
        if update_data.tag_ids is not None:
            await self._network_contact_repository._session.refresh(contact, ["tags"])
            contact.tags.clear()
            for tag_id in update_data.tag_ids:
                tag = await self._tag_repository.get_by_id(tag_id)
                if tag:
                    contact.tags.append(tag)

        await self._network_contact_repository._session.commit()
        await self._network_contact_repository._session.refresh(contact)

        return self._to_response(contact)

    async def delete_network_contact(self, contact_id: UUID) -> bool:
        """Delete a network contact."""
        success = await self._network_contact_repository.delete(contact_id)
        if not success:
            raise NetworkContactNotFoundError(contact_id)
        return success

    async def get_contacts_by_type(self, contact_type: str) -> list[NetworkContactResponse]:
        """Get contacts by type."""
        contacts = await self._network_contact_repository.get_by_contact_type(contact_type)
        return [self._to_response(c) for c in contacts]

    async def get_contacts_by_company(self, company_id: UUID) -> list[NetworkContactResponse]:
        """Get contacts for a specific company."""
        contacts = await self._network_contact_repository.get_by_company(company_id)
        return [self._to_response(c) for c in contacts]

    async def get_warm_contacts(self) -> list[NetworkContactResponse]:
        """Get warm and hot contacts."""
        contacts = await self._network_contact_repository.get_warm_contacts()
        return [self._to_response(c) for c in contacts]

    async def get_contacts_needing_followup(self) -> list[NetworkContactResponse]:
        """Get contacts with upcoming or overdue follow-ups."""
        contacts = await self._network_contact_repository.get_contacts_needing_followup()
        return [self._to_response(c) for c in contacts]

    async def search_contacts(self, name_pattern: str) -> list[NetworkContactResponse]:
        """Search contacts by name."""
        contacts = await self._network_contact_repository.search_by_name(name_pattern)
        return [self._to_response(c) for c in contacts]

    def _to_response(self, contact) -> NetworkContactResponse:
        """Convert network contact model to response."""
        tag_count = len(contact.tags) if hasattr(contact, "tags") else 0

        response_dict = {
            "id": contact.id,
            "company_id": contact.company_id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "linkedin_url": contact.linkedin_url,
            "phone": contact.phone,
            "current_title": contact.current_title,
            "current_company": contact.current_company,
            "contact_type": contact.contact_type,
            "relationship_strength": contact.relationship_strength,
            "last_contact_date": contact.last_contact_date,
            "next_followup_date": contact.next_followup_date,
            "how_we_met": contact.how_we_met,
            "conversation_history": contact.conversation_history,
            "referral_status": contact.referral_status,
            "github_url": contact.github_url,
            "personal_website": contact.personal_website,
            "twitter_url": contact.twitter_url,
            "notes": contact.notes,
            "is_active": contact.is_active,
            "interaction_count": contact.interaction_count,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
            "tag_count": tag_count,
        }
        return NetworkContactResponse(**response_dict)
