"""Service for mentor business logic and file-based communication with Claude Code."""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from uuid import UUID

import aiofiles

from turbo.core.models.mentor import Mentor
from turbo.core.models.mentor_conversation import MentorConversation
from turbo.core.repositories.mentor import MentorRepository
from turbo.core.repositories.mentor_conversation import MentorConversationRepository
from turbo.core.schemas.mentor import MentorCreate, MentorResponse, MentorUpdate
from turbo.core.schemas.mentor_conversation import (
    ConversationHistoryResponse,
    MentorConversationCreate,
    MentorConversationResponse,
    SendMessageResponse,
)
from turbo.core.services.mentor_context import MentorContextService
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import MentorNotFoundError


class MentorService:
    """Service for mentor operations and Claude Code integration."""

    def __init__(
        self,
        mentor_repository: MentorRepository,
        conversation_repository: MentorConversationRepository,
        context_service: MentorContextService,
        mentors_dir: str = ".turbo/mentors",
    ) -> None:
        self._mentor_repository = mentor_repository
        self._conversation_repository = conversation_repository
        self._context_service = context_service
        self._mentors_dir = Path(mentors_dir)

    async def create_mentor(self, mentor_data: MentorCreate) -> MentorResponse:
        """Create a new mentor."""
        # Strip emojis from text fields
        if mentor_data.name:
            mentor_data.name = strip_emojis(mentor_data.name)
        if mentor_data.description:
            mentor_data.description = strip_emojis(mentor_data.description)
        if mentor_data.persona:
            mentor_data.persona = strip_emojis(mentor_data.persona)

        mentor = await self._mentor_repository.create(mentor_data)

        # Create mentor directory structure
        await self._initialize_mentor_directory(mentor)

        return MentorResponse.model_validate(mentor)

    async def get_mentor(self, mentor_id: UUID) -> MentorResponse:
        """Get mentor by ID."""
        mentor = await self._mentor_repository.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundError(mentor_id)

        # Add message count
        message_count = await self._conversation_repository.count_messages(mentor_id)
        response = MentorResponse.model_validate(mentor)
        response.message_count = message_count
        return response

    async def get_all_mentors(
        self,
        is_active: bool | None = True,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[MentorResponse]:
        """Get all mentors regardless of workspace."""
        mentors = await self._mentor_repository.get_active_mentors(
            limit=limit,
            offset=offset,
        ) if is_active else await self._mentor_repository.get_all(
            limit=limit,
            offset=offset,
        )

        responses = []
        for mentor in mentors:
            message_count = await self._conversation_repository.count_messages(mentor.id)
            response = MentorResponse.model_validate(mentor)
            response.message_count = message_count
            responses.append(response)

        return responses

    async def get_mentors_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        is_active: bool | None = True,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[MentorResponse]:
        """Get mentors by workspace."""
        mentors = await self._mentor_repository.get_by_workspace(
            workspace=workspace,
            work_company=work_company,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        responses = []
        for mentor in mentors:
            message_count = await self._conversation_repository.count_messages(mentor.id)
            response = MentorResponse.model_validate(mentor)
            response.message_count = message_count
            responses.append(response)

        return responses

    async def update_mentor(
        self, mentor_id: UUID, mentor_data: MentorUpdate
    ) -> MentorResponse:
        """Update a mentor."""
        # Strip emojis from text fields
        if mentor_data.name:
            mentor_data.name = strip_emojis(mentor_data.name)
        if mentor_data.description:
            mentor_data.description = strip_emojis(mentor_data.description)
        if mentor_data.persona:
            mentor_data.persona = strip_emojis(mentor_data.persona)

        mentor = await self._mentor_repository.update(mentor_id, mentor_data)
        if not mentor:
            raise MentorNotFoundError(mentor_id)

        # Update persona file if persona changed
        if mentor_data.persona:
            await self._write_persona_file(mentor)

        return MentorResponse.model_validate(mentor)

    async def delete_mentor(self, mentor_id: UUID) -> bool:
        """Delete a mentor."""
        success = await self._mentor_repository.delete(mentor_id)
        if not success:
            raise MentorNotFoundError(mentor_id)

        # Clean up mentor directory
        await self._cleanup_mentor_directory(mentor_id)

        return success

    async def send_message(
        self, mentor_id: UUID, content: str
    ) -> SendMessageResponse:
        """Send a message to a mentor (response generated async via webhook)."""
        mentor = await self._mentor_repository.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundError(mentor_id)

        try:
            # 1. Compile workspace context
            context = await self._context_service.compile_workspace_context(mentor)

            # 2. Save user message
            user_message_data = MentorConversationCreate(
                mentor_id=mentor_id,
                role="user",
                content=content,
                context_snapshot=context,
            )
            user_message = await self._conversation_repository.create(user_message_data)

            # 3. Return immediately - webhook will generate response asynchronously
            return SendMessageResponse(
                user_message=MentorConversationResponse.model_validate(user_message),
                assistant_message=None,
                status="pending",
                error=None,
            )

        except Exception as e:
            return SendMessageResponse(
                user_message=None,
                assistant_message=None,
                status="error",
                error=str(e),
            )

    async def add_assistant_message(
        self, mentor_id: UUID, content: str
    ) -> MentorConversationResponse:
        """Add an assistant message (called by webhook after generation)."""
        mentor = await self._mentor_repository.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundError(mentor_id)

        # Compile context for snapshot
        context = await self._context_service.compile_workspace_context(mentor)

        # Save assistant message
        assistant_message_data = MentorConversationCreate(
            mentor_id=mentor_id,
            role="assistant",
            content=content,
            context_snapshot=context,
        )
        assistant_message = await self._conversation_repository.create(
            assistant_message_data
        )

        return MentorConversationResponse.model_validate(assistant_message)

    async def get_conversation(
        self, mentor_id: UUID, limit: int | None = None, offset: int | None = None
    ) -> ConversationHistoryResponse:
        """Get conversation history for a mentor."""
        mentor = await self._mentor_repository.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundError(mentor_id)

        messages = await self._conversation_repository.get_by_mentor(
            mentor_id, limit=limit, offset=offset
        )
        total = await self._conversation_repository.count_messages(mentor_id)

        return ConversationHistoryResponse(
            messages=[MentorConversationResponse.model_validate(m) for m in messages],
            total=total,
            mentor_id=mentor_id,
        )

    async def update_message(
        self, mentor_id: UUID, message_id: UUID, content: str
    ) -> MentorConversationResponse:
        """Update a message in the conversation."""
        mentor = await self._mentor_repository.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundError(mentor_id)

        # Get the message to verify it belongs to this mentor and is from user
        message = await self._conversation_repository.get_by_id(message_id)
        if not message:
            raise ValueError(f"Message with id {message_id} not found")

        if message.mentor_id != mentor_id:
            raise ValueError(f"Message {message_id} does not belong to mentor {mentor_id}")

        if message.role != "user":
            raise ValueError("Only user messages can be edited")

        # Update the message content
        from turbo.core.schemas.mentor_conversation import MentorConversationUpdate
        update_data = MentorConversationUpdate(content=content)
        updated_message = await self._conversation_repository.update(message_id, update_data)

        if not updated_message:
            raise ValueError(f"Failed to update message {message_id}")

        return MentorConversationResponse.model_validate(updated_message)

    async def clear_conversation(self, mentor_id: UUID) -> int:
        """Clear all conversation messages for a mentor."""
        mentor = await self._mentor_repository.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundError(mentor_id)

        deleted_count = await self._conversation_repository.clear_conversation(mentor_id)

        # Clean up conversation file
        await self._clear_conversation_file(mentor_id)

        return deleted_count

    async def delete_message(self, mentor_id: UUID, message_id: UUID) -> bool:
        """Delete a specific message from the conversation."""
        mentor = await self._mentor_repository.get_by_id(mentor_id)
        if not mentor:
            raise MentorNotFoundError(mentor_id)

        success = await self._conversation_repository.delete_message(mentor_id, message_id)
        if not success:
            raise ValueError(f"Message {message_id} not found or does not belong to mentor {mentor_id}")

        return success

    # File-based communication helpers

    async def _initialize_mentor_directory(self, mentor: Mentor) -> None:
        """Initialize directory structure for a mentor."""
        mentor_dir = self._mentors_dir / str(mentor.id)
        mentor_dir.mkdir(parents=True, exist_ok=True)

        # Write persona file
        await self._write_persona_file(mentor)

        # Create empty conversation file
        conversation_file = mentor_dir / "conversation.md"
        async with aiofiles.open(conversation_file, "w") as f:
            await f.write(f"# Conversation with {mentor.name}\n\n")

    async def _write_persona_file(self, mentor: Mentor) -> None:
        """Write mentor persona to file."""
        mentor_dir = self._mentors_dir / str(mentor.id)
        mentor_dir.mkdir(parents=True, exist_ok=True)

        persona_file = mentor_dir / "persona.md"
        async with aiofiles.open(persona_file, "w") as f:
            await f.write(f"# {mentor.name}\n\n")
            await f.write(f"## Description\n{mentor.description}\n\n")
            await f.write(f"## Persona\n{mentor.persona}\n\n")
            await f.write(f"## Workspace\n{mentor.workspace}")
            if mentor.work_company:
                await f.write(f" ({mentor.work_company})")
            await f.write("\n")

    async def _write_request_file(
        self, mentor: Mentor, user_message: str, context: dict
    ) -> None:
        """Write request file for Claude Code to process."""
        mentor_dir = self._mentors_dir / str(mentor.id)
        request_file = mentor_dir / "request.md"

        # Format context as markdown
        context_md = await self._context_service.format_context_as_markdown(context)

        # Get recent conversation history
        recent_messages = await self._conversation_repository.get_recent_messages(
            mentor.id, limit=10
        )
        conversation_md = self._format_conversation_history(recent_messages)

        # Build request content
        request_content = [
            f"# Mentor Request: {mentor.name}",
            "",
            "## Your Persona",
            mentor.persona,
            "",
            "## Workspace Context",
            context_md,
            "",
            "## Recent Conversation",
            conversation_md if conversation_md else "_No previous conversation_",
            "",
            "## User's New Message",
            user_message,
            "",
            "## Instructions",
            "Respond to the user's message as the mentor defined above. Use the workspace context to provide specific, actionable guidance. Reference projects, issues, or documents when relevant. Focus on guidance and feedback rather than code generation.",
            "",
            "## Response Requirements",
            "- Write your response in a natural, conversational tone",
            "- Be specific and actionable",
            "- Reference workspace context when relevant",
            "- Provide examples or suggestions based on their actual work",
            "- Ask clarifying questions if needed",
            "",
            "---",
            "",
            "**Write your response below:**",
            "",
        ]

        async with aiofiles.open(request_file, "w") as f:
            await f.write("\n".join(request_content))

    async def _wait_for_response(
        self, mentor_id: UUID, timeout: int = 60
    ) -> str:
        """Wait for Claude Code to write response file."""
        mentor_dir = self._mentors_dir / str(mentor.id)
        response_file = mentor_dir / "response.md"

        # Delete old response file if exists
        if response_file.exists():
            response_file.unlink()

        # Poll for response file
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if response_file.exists():
                # Read response
                async with aiofiles.open(response_file, "r") as f:
                    content = await f.read()

                # Clean up response file
                response_file.unlink()

                return content.strip()

            await asyncio.sleep(1)

        raise asyncio.TimeoutError("Claude Code response timeout")

    async def _clear_conversation_file(self, mentor_id: UUID) -> None:
        """Clear conversation history file."""
        mentor_dir = self._mentors_dir / str(mentor_id)
        conversation_file = mentor_dir / "conversation.md"

        if conversation_file.exists():
            async with aiofiles.open(conversation_file, "w") as f:
                await f.write("# Conversation\n\n_Conversation cleared_\n")

    async def _cleanup_mentor_directory(self, mentor_id: UUID) -> None:
        """Clean up mentor directory."""
        mentor_dir = self._mentors_dir / str(mentor_id)
        if mentor_dir.exists():
            import shutil
            shutil.rmtree(mentor_dir)

    def _format_conversation_history(
        self, messages: list[MentorConversation]
    ) -> str:
        """Format conversation history as markdown."""
        if not messages:
            return ""

        lines = []
        for msg in messages:
            role_label = "**You:**" if msg.role == "user" else "**Mentor:**"
            lines.append(f"{role_label} {msg.content}\n")

        return "\n".join(lines)
