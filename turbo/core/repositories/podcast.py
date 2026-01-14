"""Repository for Podcast database operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.podcast import PodcastShow, PodcastEpisode
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.podcast import (
    PodcastShowCreate,
    PodcastShowUpdate,
    PodcastEpisodeCreate,
    PodcastEpisodeUpdate,
)


class PodcastShowRepository(BaseRepository[PodcastShow, PodcastShowCreate, PodcastShowUpdate]):
    """Repository for PodcastShow operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(session, PodcastShow)

    async def get_by_feed_url(self, feed_url: str) -> Optional[PodcastShow]:
        """Get podcast show by feed URL."""
        result = await self._session.execute(
            select(PodcastShow).where(PodcastShow.feed_url == feed_url)
        )
        return result.scalars().first()

    async def get_subscribed(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastShow]:
        """Get subscribed podcast shows."""
        result = await self._session.execute(
            select(PodcastShow)
            .where(PodcastShow.is_subscribed == True)  # noqa: E712
            .where(PodcastShow.is_archived == False)  # noqa: E712
            .order_by(PodcastShow.title)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_favorites(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastShow]:
        """Get favorite podcast shows."""
        result = await self._session.execute(
            select(PodcastShow)
            .where(PodcastShow.is_favorite == True)  # noqa: E712
            .order_by(PodcastShow.title)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_publisher(
        self,
        publisher: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastShow]:
        """Get podcast shows by publisher."""
        result = await self._session.execute(
            select(PodcastShow)
            .where(PodcastShow.publisher == publisher)
            .order_by(PodcastShow.title)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def toggle_favorite(self, show_id: UUID) -> Optional[PodcastShow]:
        """Toggle favorite status."""
        show = await self.get_by_id(show_id)
        if show:
            show.is_favorite = not show.is_favorite
            await self._session.commit()
            await self._session.refresh(show)
        return show

    async def toggle_subscription(self, show_id: UUID) -> Optional[PodcastShow]:
        """Toggle subscription status."""
        show = await self.get_by_id(show_id)
        if show:
            show.is_subscribed = not show.is_subscribed
            await self._session.commit()
            await self._session.refresh(show)
        return show

    async def update_episode_stats(self, show_id: UUID) -> Optional[PodcastShow]:
        """Update episode statistics for a show."""
        show = await self.get_by_id(show_id)
        if show:
            # Count total episodes
            total_result = await self._session.execute(
                select(func.count(PodcastEpisode.id)).where(
                    PodcastEpisode.show_id == show_id
                )
            )
            show.total_episodes = total_result.scalar() or 0

            # Count listened episodes
            listened_result = await self._session.execute(
                select(func.count(PodcastEpisode.id)).where(
                    and_(
                        PodcastEpisode.show_id == show_id,
                        PodcastEpisode.is_played == True  # noqa: E712
                    )
                )
            )
            show.listened_episodes = listened_result.scalar() or 0

            await self._session.commit()
            await self._session.refresh(show)
        return show


class PodcastEpisodeRepository(BaseRepository[PodcastEpisode, PodcastEpisodeCreate, PodcastEpisodeUpdate]):
    """Repository for PodcastEpisode operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(session, PodcastEpisode)

    async def get_by_show(
        self,
        show_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastEpisode]:
        """Get episodes by show."""
        result = await self._session.execute(
            select(PodcastEpisode)
            .where(PodcastEpisode.show_id == show_id)
            .order_by(PodcastEpisode.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_guid(self, guid: str) -> Optional[PodcastEpisode]:
        """Get episode by GUID."""
        result = await self._session.execute(
            select(PodcastEpisode).where(PodcastEpisode.guid == guid)
        )
        return result.scalars().first()

    async def get_by_season(
        self,
        show_id: UUID,
        season_number: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastEpisode]:
        """Get episodes by season."""
        result = await self._session.execute(
            select(PodcastEpisode)
            .where(
                and_(
                    PodcastEpisode.show_id == show_id,
                    PodcastEpisode.season_number == season_number,
                )
            )
            .order_by(PodcastEpisode.episode_number)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_unplayed(
        self,
        show_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastEpisode]:
        """Get unplayed episodes."""
        query = select(PodcastEpisode).where(
            and_(
                PodcastEpisode.is_played == False,  # noqa: E712
                PodcastEpisode.is_archived == False,  # noqa: E712
            )
        )

        if show_id:
            query = query.where(PodcastEpisode.show_id == show_id)

        query = query.order_by(PodcastEpisode.published_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_favorites(
        self,
        show_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastEpisode]:
        """Get favorite episodes."""
        query = select(PodcastEpisode).where(PodcastEpisode.is_favorite == True)  # noqa: E712

        if show_id:
            query = query.where(PodcastEpisode.show_id == show_id)

        query = query.order_by(PodcastEpisode.published_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_with_transcripts(
        self,
        show_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastEpisode]:
        """Get episodes with transcripts."""
        query = select(PodcastEpisode).where(
            PodcastEpisode.transcript_generated == True  # noqa: E712
        )

        if show_id:
            query = query.where(PodcastEpisode.show_id == show_id)

        query = query.order_by(PodcastEpisode.published_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def mark_as_played(self, episode_id: UUID) -> Optional[PodcastEpisode]:
        """Mark episode as played."""
        episode = await self.get_by_id(episode_id)
        if episode:
            episode.is_played = True
            episode.play_count += 1
            from datetime import datetime, timezone
            episode.last_played_at = datetime.now(timezone.utc)
            await self._session.commit()
            await self._session.refresh(episode)
        return episode

    async def toggle_favorite(self, episode_id: UUID) -> Optional[PodcastEpisode]:
        """Toggle favorite status."""
        episode = await self.get_by_id(episode_id)
        if episode:
            episode.is_favorite = not episode.is_favorite
            await self._session.commit()
            await self._session.refresh(episode)
        return episode

    async def update_play_progress(
        self,
        episode_id: UUID,
        play_position: int,
        completed: bool = False,
    ) -> Optional[PodcastEpisode]:
        """Update play progress."""
        episode = await self.get_by_id(episode_id)
        if episode:
            episode.play_position = play_position
            if completed:
                episode.is_played = True
                episode.play_count += 1
            from datetime import datetime, timezone
            episode.last_played_at = datetime.now(timezone.utc)
            await self._session.commit()
            await self._session.refresh(episode)
        return episode

    async def add_transcript(
        self,
        episode_id: UUID,
        transcript: str,
        transcript_data: Optional[dict] = None,
    ) -> Optional[PodcastEpisode]:
        """Add transcript and structured transcript data to episode."""
        episode = await self.get_by_id(episode_id)
        if episode:
            episode.transcript = transcript
            episode.transcript_data = transcript_data
            episode.transcript_generated = True
            from datetime import datetime, timezone
            episode.transcript_generated_at = datetime.now(timezone.utc)
            await self._session.commit()
            await self._session.refresh(episode)
        return episode

    async def list_all(self) -> list[PodcastEpisode]:
        """Get all episodes (for stats)."""
        result = await self._session.execute(select(PodcastEpisode))
        return list(result.scalars().all())