"""API v1 package."""

from fastapi import APIRouter

from turbo.api.v1.endpoints import (
    action_approvals,
    agents,
    blueprints,
    calendar,
    calendar_events,
    comments,
    decisions,
    dependencies,
    documents,
    favorites,
    forms,
    group_discussion,
    initiatives,
    issue_refinement,
    issues,
    mentors,
    milestones,
    my_queue,
    notes,
    projects,
    saved_filters,
    script_runs,
    settings,
    staff,
    tags,
    websocket,
    work_queue,
    worktrees,
)

# Create the main API router
router = APIRouter(prefix="/api/v1")

# Core PM
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(issues.router, prefix="/issues", tags=["issues"])
router.include_router(milestones.router, prefix="/milestones", tags=["milestones"])
router.include_router(initiatives.router, prefix="/initiatives", tags=["initiatives"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(tags.router, prefix="/tags", tags=["tags"])
router.include_router(comments.router, prefix="/comments", tags=["comments"])
router.include_router(decisions.router, prefix="/decisions", tags=["decisions"])
router.include_router(notes.router, prefix="/notes", tags=["notes"])
router.include_router(saved_filters.router, prefix="/saved-filters", tags=["saved-filters"])
router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])

# Work management
router.include_router(work_queue.router, prefix="/work-queue", tags=["work-queue"])
router.include_router(my_queue.router, tags=["my-queue"])  # has prefix
router.include_router(blueprints.router, prefix="/blueprints", tags=["blueprints"])
router.include_router(worktrees.router, prefix="/worktrees", tags=["worktrees"])
router.include_router(dependencies.router, tags=["dependencies"])  # has prefix
router.include_router(forms.router, tags=["forms"])  # has prefix

# Calendar
router.include_router(calendar.router, tags=["calendar"])  # has prefix — aggregated view
router.include_router(calendar_events.router, prefix="/calendar-events", tags=["calendar-events"])

# AI & Agents
router.include_router(agents.router, tags=["agents"])  # has prefix
router.include_router(staff.router, prefix="/staff", tags=["staff"])
router.include_router(mentors.router, prefix="/mentors", tags=["mentors"])
router.include_router(group_discussion.router, prefix="/group-discussions", tags=["group-discussions"])
router.include_router(action_approvals.router, tags=["action-approvals"])  # has prefix
router.include_router(issue_refinement.router, tags=["issue-refinement"])  # has prefix
router.include_router(script_runs.router, prefix="/scripts", tags=["scripts"])

# Settings & Infrastructure
router.include_router(settings.router, tags=["settings"])  # has prefix

# WebSocket (no prefix — routes define their own paths)
router.include_router(websocket.router)
