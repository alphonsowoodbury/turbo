"""Service for Podcast business logic."""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import feedparser
import httpx

from turbo.core.models.podcast import PodcastShow, PodcastEpisode
from turbo.core.repositories.podcast import PodcastShowRepository, PodcastEpisodeRepository
from turbo.core.schemas.podcast import (
    PodcastShowCreate,
    PodcastShowUpdate,
    PodcastEpisodeCreate,
    PodcastEpisodeUpdate,
    PlayProgress,
)


class PodcastService:
    """Service for Podcast operations."""

    def __init__(
        self,
        show_repository: PodcastShowRepository,
        episode_repository: PodcastEpisodeRepository,
    ):
        """Initialize service."""
        self.show_repo = show_repository
        self.episode_repo = episode_repository

    # Show operations
    async def create_show(self, show_data: PodcastShowCreate) -> PodcastShow:
        """Create new podcast show."""
        return await self.show_repo.create(show_data)

    async def get_show(self, show_id: UUID) -> Optional[PodcastShow]:
        """Get podcast show by ID."""
        return await self.show_repo.get_by_id(show_id)

    async def get_all_shows(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastShow]:
        """Get all podcast shows."""
        return await self.show_repo.get_all(limit=limit, offset=offset)

    async def get_subscribed_shows(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastShow]:
        """Get subscribed podcast shows."""
        return await self.show_repo.get_subscribed(limit, offset)

    async def get_favorite_shows(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastShow]:
        """Get favorite podcast shows."""
        return await self.show_repo.get_favorites(limit, offset)

    async def update_show(
        self,
        show_id: UUID,
        show_data: PodcastShowUpdate,
    ) -> Optional[PodcastShow]:
        """Update podcast show."""
        return await self.show_repo.update(show_id, show_data)

    async def delete_show(self, show_id: UUID) -> bool:
        """Delete podcast show."""
        return await self.show_repo.delete(show_id)

    async def toggle_show_favorite(self, show_id: UUID) -> Optional[PodcastShow]:
        """Toggle show favorite status."""
        return await self.show_repo.toggle_favorite(show_id)

    async def toggle_show_subscription(self, show_id: UUID) -> Optional[PodcastShow]:
        """Toggle show subscription status."""
        return await self.show_repo.toggle_subscription(show_id)

    # Episode operations
    async def create_episode(self, episode_data: PodcastEpisodeCreate) -> PodcastEpisode:
        """Create new podcast episode."""
        episode = await self.episode_repo.create(episode_data)
        # Update show stats
        await self.show_repo.update_episode_stats(episode_data.show_id)
        return episode

    async def get_episode(self, episode_id: UUID) -> Optional[PodcastEpisode]:
        """Get podcast episode by ID."""
        return await self.episode_repo.get_by_id(episode_id)

    async def get_episodes_by_show(
        self,
        show_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastEpisode]:
        """Get episodes by show."""
        return await self.episode_repo.get_by_show(show_id, limit, offset)

    async def get_unplayed_episodes(
        self,
        show_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastEpisode]:
        """Get unplayed episodes."""
        return await self.episode_repo.get_unplayed(show_id, limit, offset)

    async def get_favorite_episodes(
        self,
        show_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PodcastEpisode]:
        """Get favorite episodes."""
        return await self.episode_repo.get_favorites(show_id, limit, offset)

    async def update_episode(
        self,
        episode_id: UUID,
        episode_data: PodcastEpisodeUpdate,
    ) -> Optional[PodcastEpisode]:
        """Update podcast episode."""
        return await self.episode_repo.update(episode_id, episode_data)

    async def delete_episode(self, episode_id: UUID) -> bool:
        """Delete podcast episode."""
        episode = await self.episode_repo.get_by_id(episode_id)
        if episode:
            deleted = await self.episode_repo.delete(episode_id)
            if deleted:
                # Update show stats
                await self.show_repo.update_episode_stats(episode.show_id)
            return deleted
        return False

    async def mark_episode_played(self, episode_id: UUID) -> Optional[PodcastEpisode]:
        """Mark episode as played."""
        episode = await self.episode_repo.mark_as_played(episode_id)
        if episode:
            # Update show stats
            await self.show_repo.update_episode_stats(episode.show_id)
        return episode

    async def toggle_episode_favorite(self, episode_id: UUID) -> Optional[PodcastEpisode]:
        """Toggle episode favorite status."""
        return await self.episode_repo.toggle_favorite(episode_id)

    async def update_play_progress(
        self,
        episode_id: UUID,
        progress: PlayProgress,
    ) -> Optional[PodcastEpisode]:
        """Update episode play progress."""
        episode = await self.episode_repo.update_play_progress(
            episode_id,
            progress.play_position,
            progress.completed,
        )
        if episode and progress.completed:
            # Update show stats if episode was completed
            await self.show_repo.update_episode_stats(episode.show_id)
        return episode

    async def add_transcript(
        self,
        episode_id: UUID,
        transcript: str,
    ) -> Optional[PodcastEpisode]:
        """Add transcript to episode."""
        return await self.episode_repo.add_transcript(episode_id, transcript)

    # RSS Feed operations
    async def subscribe_to_feed(self, feed_url: str) -> PodcastShow:
        """Subscribe to a podcast feed."""
        # Check if show already exists
        existing = await self.show_repo.get_by_feed_url(feed_url)
        if existing:
            return existing

        # Fetch and parse feed
        feed_data = await self._fetch_feed_metadata(feed_url)

        # Create show
        show_create = PodcastShowCreate(
            title=feed_data["title"],
            description=feed_data.get("description"),
            author=feed_data.get("author"),
            publisher=feed_data.get("publisher"),
            feed_url=feed_url,
            website_url=feed_data.get("website_url"),
            image_url=feed_data.get("image_url"),
            language=feed_data.get("language"),
            categories=feed_data.get("categories"),
            explicit=feed_data.get("explicit", False),
            is_subscribed=True,
            auto_fetch=False,
        )

        return await self.show_repo.create(show_create)

    async def fetch_episodes_from_feed(
        self,
        show_id: UUID,
        limit: Optional[int] = None,
    ) -> list[PodcastEpisode]:
        """Fetch episodes from podcast RSS feed."""
        show = await self.show_repo.get_by_id(show_id)
        if not show:
            raise ValueError(f"Show {show_id} not found")

        # Fetch and parse feed
        episodes_data = await self._fetch_feed_episodes(show.feed_url, limit)

        created_episodes = []
        for episode_data in episodes_data:
            # Check if episode already exists by GUID
            if episode_data.get("guid"):
                existing = await self.episode_repo.get_by_guid(episode_data["guid"])
                if existing:
                    continue

            # Create episode
            try:
                episode_create = PodcastEpisodeCreate(
                    show_id=show_id,
                    **episode_data,
                )
                episode = await self.episode_repo.create(episode_create)
                created_episodes.append(episode)
            except Exception:
                # Skip episodes that fail to create
                continue

        # Update show stats and last_fetched_at
        await self.show_repo.update(
            show_id,
            PodcastShowUpdate(last_fetched_at=datetime.now(timezone.utc)),
        )
        await self.show_repo.update_episode_stats(show_id)

        return created_episodes

    async def _fetch_feed_metadata(self, feed_url: str) -> dict:
        """Fetch and parse podcast feed metadata."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(feed_url)
            response.raise_for_status()

        feed = feedparser.parse(response.text)

        # Extract podcast-specific metadata
        channel = feed.feed

        return {
            "title": channel.get("title", "Unknown Podcast"),
            "description": channel.get("subtitle") or channel.get("description", ""),
            "author": channel.get("author") or channel.get("itunes_author", ""),
            "publisher": channel.get("publisher") or channel.get("itunes_author", ""),
            "website_url": channel.get("link"),
            "image_url": self._extract_image_url(channel),
            "language": channel.get("language"),
            "categories": self._extract_categories(channel),
            "explicit": channel.get("itunes_explicit") == "yes",
        }

    async def _fetch_feed_episodes(
        self,
        feed_url: str,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Fetch and parse podcast episodes from feed."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(feed_url)
            response.raise_for_status()

        feed = feedparser.parse(response.text)
        episodes = []

        entries = feed.entries if not limit else feed.entries[:limit]

        for entry in entries:
            episode = self._parse_episode(entry)
            if episode:
                episodes.append(episode)

        return episodes

    def _parse_episode(self, entry: dict) -> Optional[dict]:
        """Parse episode data from feed entry."""
        # Get audio enclosure
        audio_url = None
        duration = None
        file_size = None
        mime_type = None

        for enclosure in entry.get("enclosures", []):
            if enclosure.get("type", "").startswith("audio/"):
                audio_url = enclosure.get("href") or enclosure.get("url")
                file_size = self._parse_int(enclosure.get("length"))
                mime_type = enclosure.get("type")
                break

        if not audio_url:
            # Try media:content
            media_content = entry.get("media_content", [])
            for media in media_content:
                if media.get("type", "").startswith("audio/"):
                    audio_url = media.get("url")
                    mime_type = media.get("type")
                    break

        if not audio_url:
            return None

        # Parse duration
        itunes_duration = entry.get("itunes_duration")
        if itunes_duration:
            duration = self._parse_duration(itunes_duration)

        # Extract episode/season numbers
        episode_num = self._extract_episode_number(entry)
        season_num = self._extract_season_number(entry)

        return {
            "title": entry.get("title", "Untitled Episode"),
            "description": entry.get("description") or entry.get("summary", ""),
            "summary": entry.get("summary") or entry.get("description", ""),
            "episode_number": episode_num,
            "season_number": season_num,
            "audio_url": audio_url,
            "duration": duration,
            "file_size": file_size,
            "mime_type": mime_type,
            "published_at": self._parse_date(entry),
            "guid": entry.get("id") or entry.get("guid"),
            "image_url": self._extract_episode_image(entry),
        }

    def _extract_image_url(self, channel: dict) -> Optional[str]:
        """Extract image URL from feed."""
        # Try itunes:image
        if "image" in channel and isinstance(channel["image"], dict):
            return channel["image"].get("href")

        # Try image tag
        if "image" in channel and isinstance(channel["image"], str):
            return channel["image"]

        return None

    def _extract_episode_image(self, entry: dict) -> Optional[str]:
        """Extract episode image URL."""
        # Try itunes:image
        itunes_image = entry.get("itunes_image")
        if itunes_image:
            if isinstance(itunes_image, dict):
                return itunes_image.get("href")
            return itunes_image

        # Try media:thumbnail
        media_thumbnail = entry.get("media_thumbnail")
        if media_thumbnail and isinstance(media_thumbnail, list):
            return media_thumbnail[0].get("url")

        return None

    def _extract_categories(self, channel: dict) -> Optional[str]:
        """Extract categories as comma-separated string."""
        categories = []

        # Try itunes_category
        if "tags" in channel:
            categories.extend([tag.term for tag in channel["tags"]])

        return ", ".join(categories) if categories else None

    def _extract_episode_number(self, entry: dict) -> Optional[int]:
        """Extract episode number from entry."""
        # Try itunes:episode
        episode = entry.get("itunes_episode")
        if episode:
            return self._parse_int(episode)

        # Try to parse from title
        title = entry.get("title", "")
        match = re.search(r"#(\d+)|episode\s*(\d+)|ep\.?\s*(\d+)", title, re.I)
        if match:
            for group in match.groups():
                if group:
                    return int(group)

        return None

    def _extract_season_number(self, entry: dict) -> Optional[int]:
        """Extract season number from entry."""
        # Try itunes:season
        season = entry.get("itunes_season")
        if season:
            return self._parse_int(season)

        # Try to parse from title
        title = entry.get("title", "")
        match = re.search(r"season\s*(\d+)|s(\d+)", title, re.I)
        if match:
            for group in match.groups():
                if group:
                    return int(group)

        return None

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string to seconds."""
        if isinstance(duration_str, int):
            return duration_str

        try:
            # Handle HH:MM:SS or MM:SS format
            parts = duration_str.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(duration_str)
        except (ValueError, AttributeError):
            return None

    def _parse_date(self, entry: dict) -> Optional[datetime]:
        """Parse date from feed entry."""
        try:
            time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if time_struct:
                return datetime(*time_struct[:6], tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass

        return None

    def _parse_int(self, value) -> Optional[int]:
        """Safely parse integer value."""
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return None