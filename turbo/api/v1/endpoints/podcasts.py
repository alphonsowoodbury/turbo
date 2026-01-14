"""Podcast API endpoints."""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.database.connection import get_db_session
from turbo.core.repositories.podcast import PodcastShowRepository, PodcastEpisodeRepository
from turbo.core.schemas.podcast import (
    PodcastShowCreate,
    PodcastShowResponse,
    PodcastShowUpdate,
    PodcastShowWithEpisodes,
    PodcastEpisodeCreate,
    PodcastEpisodeResponse,
    PodcastEpisodeUpdate,
    PodcastFeedURL,
    PlayProgress,
)
from turbo.core.services.podcast import PodcastService

router = APIRouter(prefix="/podcasts", tags=["podcasts"])

# Check if transcription dependencies are available
def _check_transcription_available():
    """Check if transcription service can be imported."""
    try:
        from turbo.core.services.transcription import TranscriptionService
        return True, TranscriptionService
    except (ImportError, OSError):
        return False, None


def get_podcast_service(
    session: AsyncSession = Depends(get_db_session),
) -> PodcastService:
    """Get podcast service."""
    show_repository = PodcastShowRepository(session)
    episode_repository = PodcastEpisodeRepository(session)
    return PodcastService(show_repository, episode_repository)


def get_transcription_service(
    session: AsyncSession = Depends(get_db_session),
    model_size: str = Query("base", regex="^(tiny|base|small|medium|large)$"),
):
    """Get transcription service with configurable model size."""
    available, TranscriptionService = _check_transcription_available()
    if not available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service is not available. Missing required dependencies (torchaudio/pyannote).",
        )
    return TranscriptionService(session, model_size=model_size)


# Podcast Show Endpoints
@router.post("/shows", response_model=PodcastShowResponse, status_code=status.HTTP_201_CREATED)
async def create_show(
    show_data: PodcastShowCreate,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastShowResponse:
    """Create a new podcast show."""
    return await service.create_show(show_data)


@router.get("/shows", response_model=list[PodcastShowResponse])
async def list_shows(
    is_subscribed: Optional[bool] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: PodcastService = Depends(get_podcast_service),
) -> list[PodcastShowResponse]:
    """List podcast shows with optional filters."""
    if is_subscribed:
        return await service.get_subscribed_shows(limit, offset)
    elif is_favorite:
        return await service.get_favorite_shows(limit, offset)
    else:
        return await service.get_all_shows(limit, offset)


@router.get("/shows/{show_id}", response_model=PodcastShowResponse)
async def get_show(
    show_id: UUID,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastShowResponse:
    """Get podcast show by ID."""
    show = await service.get_show(show_id)
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found",
        )
    return show


@router.get("/shows/{show_id}/with-episodes", response_model=PodcastShowWithEpisodes)
async def get_show_with_episodes(
    show_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastShowWithEpisodes:
    """Get podcast show with episodes."""
    show = await service.get_show(show_id)
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found",
        )

    episodes = await service.get_episodes_by_show(show_id, limit, offset)

    # Convert to response with episodes
    show_dict = {
        "id": show.id,
        "title": show.title,
        "description": show.description,
        "author": show.author,
        "publisher": show.publisher,
        "feed_url": show.feed_url,
        "website_url": show.website_url,
        "image_url": show.image_url,
        "language": show.language,
        "categories": show.categories,
        "explicit": show.explicit,
        "is_subscribed": show.is_subscribed,
        "is_favorite": show.is_favorite,
        "is_archived": show.is_archived,
        "auto_fetch": show.auto_fetch,
        "last_fetched_at": show.last_fetched_at,
        "total_episodes": show.total_episodes,
        "listened_episodes": show.listened_episodes,
        "created_at": show.created_at,
        "updated_at": show.updated_at,
        "episodes": episodes,
    }
    return PodcastShowWithEpisodes(**show_dict)


@router.put("/shows/{show_id}", response_model=PodcastShowResponse)
async def update_show(
    show_id: UUID,
    show_data: PodcastShowUpdate,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastShowResponse:
    """Update podcast show."""
    show = await service.update_show(show_id, show_data)
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found",
        )
    return show


@router.delete("/shows/{show_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_show(
    show_id: UUID,
    service: PodcastService = Depends(get_podcast_service),
) -> None:
    """Delete podcast show."""
    deleted = await service.delete_show(show_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found",
        )


@router.post("/shows/{show_id}/favorite", response_model=PodcastShowResponse)
async def toggle_show_favorite(
    show_id: UUID,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastShowResponse:
    """Toggle show favorite status."""
    show = await service.toggle_show_favorite(show_id)
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found",
        )
    return show


@router.post("/shows/{show_id}/subscribe", response_model=PodcastShowResponse)
async def toggle_show_subscription(
    show_id: UUID,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastShowResponse:
    """Toggle show subscription status."""
    show = await service.toggle_show_subscription(show_id)
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show with id {show_id} not found",
        )
    return show


# Feed Operations
@router.post("/subscribe", response_model=PodcastShowResponse)
async def subscribe_to_feed(
    feed_data: PodcastFeedURL,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastShowResponse:
    """Subscribe to a podcast feed."""
    try:
        return await service.subscribe_to_feed(feed_data.url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to subscribe to feed: {str(e)}",
        )


@router.post("/shows/{show_id}/fetch-episodes", response_model=list[PodcastEpisodeResponse])
async def fetch_episodes(
    show_id: UUID,
    limit: Optional[int] = Query(None, ge=1, le=100),
    service: PodcastService = Depends(get_podcast_service),
) -> list[PodcastEpisodeResponse]:
    """Fetch episodes from show's RSS feed."""
    try:
        return await service.fetch_episodes_from_feed(show_id, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch episodes: {str(e)}",
        )


# Podcast Episode Endpoints
@router.post("/episodes", response_model=PodcastEpisodeResponse, status_code=status.HTTP_201_CREATED)
async def create_episode(
    episode_data: PodcastEpisodeCreate,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastEpisodeResponse:
    """Create a new podcast episode."""
    return await service.create_episode(episode_data)


@router.get("/episodes", response_model=list[PodcastEpisodeResponse])
async def list_episodes(
    show_id: Optional[UUID] = Query(None),
    is_played: Optional[bool] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: PodcastService = Depends(get_podcast_service),
) -> list[PodcastEpisodeResponse]:
    """List podcast episodes with optional filters."""
    if show_id and is_played is not None and not is_played:
        return await service.get_unplayed_episodes(show_id, limit, offset)
    elif show_id and is_favorite:
        return await service.get_favorite_episodes(show_id, limit, offset)
    elif show_id:
        return await service.get_episodes_by_show(show_id, limit, offset)
    elif is_played is not None and not is_played:
        return await service.get_unplayed_episodes(None, limit, offset)
    elif is_favorite:
        return await service.get_favorite_episodes(None, limit, offset)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide at least one filter parameter",
        )


@router.get("/shows/{show_id}/episodes", response_model=list[PodcastEpisodeResponse])
async def get_show_episodes(
    show_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: PodcastService = Depends(get_podcast_service),
) -> list[PodcastEpisodeResponse]:
    """Get episodes for a specific show."""
    return await service.get_episodes_by_show(show_id, limit, offset)


@router.get("/episodes/{episode_id}", response_model=PodcastEpisodeResponse)
async def get_episode(
    episode_id: UUID,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastEpisodeResponse:
    """Get podcast episode by ID."""
    episode = await service.get_episode(episode_id)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found",
        )
    return episode


@router.put("/episodes/{episode_id}", response_model=PodcastEpisodeResponse)
async def update_episode(
    episode_id: UUID,
    episode_data: PodcastEpisodeUpdate,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastEpisodeResponse:
    """Update podcast episode."""
    episode = await service.update_episode(episode_id, episode_data)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found",
        )
    return episode


@router.delete("/episodes/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: UUID,
    service: PodcastService = Depends(get_podcast_service),
) -> None:
    """Delete podcast episode."""
    deleted = await service.delete_episode(episode_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found",
        )


@router.post("/episodes/{episode_id}/played", response_model=PodcastEpisodeResponse)
async def mark_episode_played(
    episode_id: UUID,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastEpisodeResponse:
    """Mark episode as played."""
    episode = await service.mark_episode_played(episode_id)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found",
        )
    return episode


@router.post("/episodes/{episode_id}/favorite", response_model=PodcastEpisodeResponse)
async def toggle_episode_favorite(
    episode_id: UUID,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastEpisodeResponse:
    """Toggle episode favorite status."""
    episode = await service.toggle_episode_favorite(episode_id)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found",
        )
    return episode


@router.post("/episodes/{episode_id}/progress", response_model=PodcastEpisodeResponse)
async def update_episode_progress(
    episode_id: UUID,
    progress: PlayProgress,
    service: PodcastService = Depends(get_podcast_service),
) -> PodcastEpisodeResponse:
    """Update episode play progress."""
    episode = await service.update_play_progress(episode_id, progress)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found",
        )
    return episode


# Transcription Endpoints
@router.post("/episodes/{episode_id}/transcribe", response_model=PodcastEpisodeResponse)
async def transcribe_episode(
    episode_id: UUID,
    language: Optional[str] = Query(None, regex="^[a-z]{2}$"),
    beam_size: int = Query(5, ge=1, le=10),
    force: bool = Query(False),
    transcription_service = Depends(get_transcription_service),
) -> PodcastEpisodeResponse:
    """
    Transcribe a podcast episode using local Whisper model.

    Args:
        episode_id: ID of the episode to transcribe
        language: Language code (e.g., 'en', 'es'), None for auto-detect
        beam_size: Beam size for decoding (higher = more accurate but slower, 1-10)
        force: Force re-transcription even if already exists

    Model sizes available via query param:
        - tiny: Fastest, lower quality (~1GB RAM)
        - base: Fast, decent quality (~1.5GB RAM) [default]
        - small: Balanced speed/quality (~2GB RAM)
        - medium: High quality, slower (~5GB RAM)
        - large: Best quality, slowest (~10GB RAM)
    """
    try:
        episode = await transcription_service.transcribe_episode(
            episode_id, language, beam_size, force
        )
        return episode
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )


@router.post("/episodes/transcribe-batch")
async def transcribe_multiple_episodes(
    episode_ids: list[UUID],
    language: Optional[str] = Query(None, regex="^[a-z]{2}$"),
    beam_size: int = Query(5, ge=1, le=10),
    force: bool = Query(False),
    transcription_service = Depends(get_transcription_service),
) -> dict[str, Any]:
    """
    Transcribe multiple episodes in batch.

    Returns a summary of successful and failed transcriptions.
    """
    results = await transcription_service.transcribe_multiple_episodes(
        episode_ids, language, beam_size, force
    )

    # Convert UUID keys to strings for JSON serialization
    serialized_results = {
        str(episode_id): {
            "success": result["success"],
            "episode_id": str(episode_id),
            "error": result["error"],
        }
        for episode_id, result in results.items()
    }

    # Calculate summary
    total = len(results)
    successful = sum(1 for r in results.values() if r["success"])
    failed = total - successful

    return {
        "summary": {
            "total": total,
            "successful": successful,
            "failed": failed,
        },
        "results": serialized_results,
    }


@router.get("/transcription/stats")
async def get_transcription_stats(
    transcription_service = Depends(get_transcription_service),
) -> dict[str, Any]:
    """Get transcription statistics across all episodes."""
    return await transcription_service.get_transcription_stats()