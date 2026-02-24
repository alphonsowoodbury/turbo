"""API dependency injection."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.database import get_db_session
from turbo.core.repositories import (
    DocumentRepository,
    InitiativeRepository,
    IssueDependencyRepository,
    IssueRepository,
    MilestoneRepository,
    ProjectRepository,
    TagRepository,
)
from turbo.core.repositories.work_log import WorkLogRepository
from turbo.core.repositories.note import NoteRepository
from turbo.core.repositories.mentor import MentorRepository
from turbo.core.repositories.mentor_conversation import MentorConversationRepository
from turbo.core.repositories.staff import StaffRepository
from turbo.core.repositories.staff_conversation import StaffConversationRepository
from turbo.core.repositories.webhook import WebhookRepository
from turbo.core.services import (
    DocumentService,
    InitiativeService,
    IssueService,
    MilestoneService,
    ProjectService,
    TagService,
)
from turbo.core.services.note import NoteService
from turbo.core.services.mentor import MentorService
from turbo.core.services.mentor_context import MentorContextService
from turbo.core.services.staff import StaffService
from turbo.core.services.webhook_service import WebhookService
from turbo.core.services.key_generator import KeyGeneratorService
from turbo.core.services.git_worktree import GitWorktreeService


# Repository dependencies
def get_project_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRepository:
    """Get project repository."""
    return ProjectRepository(session)


def get_issue_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IssueRepository:
    """Get issue repository."""
    return IssueRepository(session)


def get_document_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DocumentRepository:
    """Get document repository."""
    return DocumentRepository(session)


def get_tag_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TagRepository:
    """Get tag repository."""
    return TagRepository(session)


def get_milestone_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MilestoneRepository:
    """Get milestone repository."""
    return MilestoneRepository(session)


def get_initiative_repository(
    session: AsyncSession = Depends(get_db_session),
) -> InitiativeRepository:
    """Get initiative repository."""
    return InitiativeRepository(session)


def get_issue_dependency_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IssueDependencyRepository:
    """Get issue dependency repository."""
    return IssueDependencyRepository(session)


def get_note_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NoteRepository:
    """Get note repository."""
    return NoteRepository(session)


def get_webhook_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WebhookRepository:
    """Get webhook repository."""
    return WebhookRepository(session)


def get_work_log_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WorkLogRepository:
    """Get work log repository."""
    return WorkLogRepository(session)


def get_key_generator_service(
    session: AsyncSession = Depends(get_db_session),
) -> KeyGeneratorService:
    """Get key generator service."""
    return KeyGeneratorService(session)


def get_git_worktree_service(
    issue_repo: IssueRepository = Depends(get_issue_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> GitWorktreeService:
    """Get git worktree service."""
    import os
    base_worktree_path = os.environ.get("WORKTREE_BASE_PATH", None)
    return GitWorktreeService(issue_repo, project_repo, base_worktree_path=base_worktree_path)


# Service dependencies
def get_project_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
    issue_repo: IssueRepository = Depends(get_issue_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    key_generator: KeyGeneratorService = Depends(get_key_generator_service),
) -> ProjectService:
    """Get project service."""
    return ProjectService(project_repo, issue_repo, document_repo, key_generator)


def get_issue_service(
    issue_repo: IssueRepository = Depends(get_issue_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    milestone_repo: MilestoneRepository = Depends(get_milestone_repository),
    dependency_repo: IssueDependencyRepository = Depends(get_issue_dependency_repository),
    work_log_repo: WorkLogRepository = Depends(get_work_log_repository),
    webhook_repo: WebhookRepository = Depends(get_webhook_repository),
    key_generator: KeyGeneratorService = Depends(get_key_generator_service),
    worktree_service: GitWorktreeService = Depends(get_git_worktree_service),
) -> IssueService:
    """Get issue service."""
    webhook_service = WebhookService(webhook_repo)
    return IssueService(issue_repo, project_repo, milestone_repo, dependency_repo, work_log_repo, webhook_service, key_generator, worktree_service)


def get_document_service(
    document_repo: DocumentRepository = Depends(get_document_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    key_generator: KeyGeneratorService = Depends(get_key_generator_service),
) -> DocumentService:
    """Get document service."""
    return DocumentService(document_repo, project_repo, key_generator)


def get_tag_service(
    tag_repo: TagRepository = Depends(get_tag_repository),
) -> TagService:
    """Get tag service."""
    return TagService(tag_repo)


def get_milestone_service(
    milestone_repo: MilestoneRepository = Depends(get_milestone_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    issue_repo: IssueRepository = Depends(get_issue_repository),
    tag_repo: TagRepository = Depends(get_tag_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    key_generator: KeyGeneratorService = Depends(get_key_generator_service),
) -> MilestoneService:
    """Get milestone service."""
    return MilestoneService(
        milestone_repo, project_repo, issue_repo, tag_repo, document_repo, key_generator
    )


def get_initiative_service(
    initiative_repo: InitiativeRepository = Depends(get_initiative_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    issue_repo: IssueRepository = Depends(get_issue_repository),
    tag_repo: TagRepository = Depends(get_tag_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    key_generator: KeyGeneratorService = Depends(get_key_generator_service),
) -> InitiativeService:
    """Get initiative service."""
    return InitiativeService(
        initiative_repo, project_repo, issue_repo, tag_repo, document_repo, key_generator
    )


def get_note_service(
    note_repo: NoteRepository = Depends(get_note_repository),
    tag_repo: TagRepository = Depends(get_tag_repository),
    webhook_repo: WebhookRepository = Depends(get_webhook_repository),
) -> NoteService:
    """Get note service."""
    webhook_service = WebhookService(webhook_repo)
    return NoteService(note_repo, tag_repo, webhook_service)


# Mentor repository dependencies
def get_mentor_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MentorRepository:
    """Get mentor repository."""
    return MentorRepository(session)


def get_mentor_conversation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MentorConversationRepository:
    """Get mentor conversation repository."""
    return MentorConversationRepository(session)


# Staff repository dependencies
def get_staff_repository(
    session: AsyncSession = Depends(get_db_session),
) -> StaffRepository:
    """Get staff repository."""
    return StaffRepository(session)


def get_staff_conversation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> StaffConversationRepository:
    """Get staff conversation repository."""
    return StaffConversationRepository(session)


# Staff service dependencies
def get_staff_service(
    staff_repo: StaffRepository = Depends(get_staff_repository),
    conversation_repo: StaffConversationRepository = Depends(get_staff_conversation_repository),
) -> StaffService:
    """Get staff service."""
    return StaffService(staff_repo, conversation_repo)


# Group discussion repository dependencies
def get_group_discussion_repository(
    session: AsyncSession = Depends(get_db_session),
):
    """Get group discussion repository."""
    from turbo.core.repositories.group_discussion import GroupDiscussionRepository
    return GroupDiscussionRepository(session)


def get_webhook_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WebhookRepository:
    """Get webhook repository."""
    return WebhookRepository(session)


# Group discussion service dependencies
def get_group_discussion_service(
    discussion_repo = Depends(get_group_discussion_repository),
    conversation_repo: StaffConversationRepository = Depends(get_staff_conversation_repository),
):
    """Get group discussion service."""
    from turbo.core.services.group_discussion import GroupDiscussionService
    return GroupDiscussionService(discussion_repo, conversation_repo)


# Mentor service dependencies
def get_mentor_context_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
    issue_repo: IssueRepository = Depends(get_issue_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> MentorContextService:
    """Get mentor context service."""
    return MentorContextService(
        project_repo,
        issue_repo,
        document_repo,
    )


def get_mentor_service(
    mentor_repo: MentorRepository = Depends(get_mentor_repository),
    conversation_repo: MentorConversationRepository = Depends(get_mentor_conversation_repository),
    context_service: MentorContextService = Depends(get_mentor_context_service),
) -> MentorService:
    """Get mentor service."""
    return MentorService(mentor_repo, conversation_repo, context_service)
