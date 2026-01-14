"""
Transcription Service - Local audio-to-text transcription using Whisper.

This service handles on-device transcription of podcast episodes using
faster-whisper, a high-performance implementation of OpenAI's Whisper model,
with speaker diarization using pyannote.audio.
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import aiofiles
import httpx
from faster_whisper import WhisperModel
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from pyannote.audio import Pipeline
    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False
    logger.warning("pyannote.audio not available - speaker diarization disabled")

from turbo.core.repositories.podcast import PodcastEpisodeRepository
from turbo.core.models.podcast import PodcastEpisode

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Service for transcribing podcast episodes using local Whisper models.

    Supports multiple model sizes: tiny, base, small, medium, large
    - tiny: Fastest, lower quality (~1GB RAM)
    - base: Fast, decent quality (~1.5GB RAM)
    - small: Balanced speed/quality (~2GB RAM)
    - medium: High quality, slower (~5GB RAM)
    - large: Best quality, slowest (~10GB RAM)
    """

    def __init__(
        self,
        session: AsyncSession,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        enable_diarization: bool = True,
    ):
        """
        Initialize the transcription service.

        Args:
            session: Database session
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on ('cpu' or 'cuda')
            compute_type: Computation type for speed/accuracy tradeoff
                         Options: int8, int8_float16, float16, float32
            enable_diarization: Enable speaker diarization (requires pyannote.audio)
        """
        self.session = session
        self.repository = PodcastEpisodeRepository(session)
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.enable_diarization = enable_diarization and DIARIZATION_AVAILABLE
        self._model: Optional[WhisperModel] = None
        self._diarization_pipeline: Optional[Any] = None

    def _load_model(self) -> WhisperModel:
        """
        Lazy-load the Whisper model on first use.

        Returns:
            WhisperModel instance
        """
        if self._model is None:
            logger.info(
                f"Loading Whisper model: {self.model_size} "
                f"(device={self.device}, compute_type={self.compute_type})"
            )
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("Whisper model loaded successfully")
        return self._model

    def _load_diarization_pipeline(self) -> Optional[Any]:
        """
        Lazy-load the speaker diarization pipeline.

        Returns:
            Pipeline instance or None if not available
        """
        if not self.enable_diarization:
            return None

        if self._diarization_pipeline is None:
            try:
                logger.info("Loading speaker diarization pipeline...")
                # Using pyannote/speaker-diarization-3.1 model
                self._diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=os.getenv("HUGGINGFACE_TOKEN"),  # Optional
                )
                logger.info("Speaker diarization pipeline loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load diarization pipeline: {e}")
                self.enable_diarization = False
                return None

        return self._diarization_pipeline

    async def download_audio(
        self, audio_url: str, temp_dir: Path
    ) -> Path:
        """
        Download audio file from URL to temporary directory.

        Args:
            audio_url: URL of the audio file
            temp_dir: Temporary directory to save audio

        Returns:
            Path to downloaded audio file

        Raises:
            httpx.HTTPError: If download fails
        """
        logger.info(f"Downloading audio from: {audio_url}")

        # Extract filename from URL or use generic name
        filename = audio_url.split("/")[-1].split("?")[0] or "audio.mp3"
        audio_path = temp_dir / filename

        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
            response = await client.get(audio_url)
            response.raise_for_status()

            async with aiofiles.open(audio_path, "wb") as f:
                await f.write(response.content)

        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        logger.info(f"Audio downloaded: {audio_path} ({file_size_mb:.2f} MB)")
        return audio_path

    def transcribe_audio(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        beam_size: int = 5,
    ) -> tuple[str, dict[str, Any]]:
        """
        Transcribe audio file using Whisper model with speaker diarization.

        This is a CPU-bound operation and runs in executor to avoid
        blocking the async event loop.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es'), None for auto-detect
            beam_size: Beam size for decoding (higher = more accurate but slower)

        Returns:
            Tuple of (full_transcript_text, structured_transcript_data)
            structured_transcript_data format:
            {
                "segments": [
                    {
                        "start": 0.0,
                        "end": 5.2,
                        "text": "Hello, welcome to the show.",
                        "speaker": "SPEAKER_00"
                    },
                    ...
                ],
                "speakers": {
                    "SPEAKER_00": "Speaker 1",
                    "SPEAKER_01": "Speaker 2",
                    ...
                },
                "language": "en",
                "duration": 3600.0
            }
        """
        logger.info(f"Transcribing audio: {audio_path}")
        model = self._load_model()

        # Run transcription with word-level timestamps
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=beam_size,
            vad_filter=True,  # Voice activity detection to skip silence
            vad_parameters=dict(
                min_silence_duration_ms=500
            ),  # Skip 500ms+ silence
            word_timestamps=True,  # Enable word-level timestamps
        )

        # Detected language info
        detected_language = info.language if language is None else language
        if language is None:
            logger.info(
                f"Detected language: {detected_language} "
                f"(probability: {info.language_probability:.2f})"
            )

        # Collect transcript segments with timestamps
        transcript_segments = []
        transcript_parts = []
        duration = 0.0

        for segment in segments:
            transcript_parts.append(segment.text.strip())
            transcript_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "speaker": None,  # Will be filled by diarization if available
            })
            duration = max(duration, segment.end)

        full_transcript = " ".join(transcript_parts)

        # Perform speaker diarization if enabled
        speaker_labels = {}
        if self.enable_diarization:
            try:
                diarization_result = self._perform_diarization(audio_path)
                if diarization_result:
                    # Assign speakers to segments based on overlap
                    transcript_segments = self._assign_speakers_to_segments(
                        transcript_segments, diarization_result
                    )
                    speaker_labels = self._generate_speaker_labels(transcript_segments)
                    logger.info(f"Speaker diarization complete: {len(speaker_labels)} speakers detected")
            except Exception as e:
                logger.warning(f"Speaker diarization failed: {e}")

        # Build structured transcript data
        transcript_data = {
            "segments": transcript_segments,
            "speakers": speaker_labels,
            "language": detected_language,
            "duration": duration,
        }

        logger.info(f"Transcription complete: {len(full_transcript)} characters, {len(transcript_segments)} segments")
        return full_transcript, transcript_data

    def _perform_diarization(self, audio_path: Path) -> Optional[Any]:
        """
        Perform speaker diarization on audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Diarization result or None if failed
        """
        pipeline = self._load_diarization_pipeline()
        if not pipeline:
            return None

        logger.info("Running speaker diarization...")
        try:
            # Run diarization
            diarization = pipeline(str(audio_path))
            return diarization
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return None

    def _assign_speakers_to_segments(
        self,
        segments: list[dict[str, Any]],
        diarization: Any,
    ) -> list[dict[str, Any]]:
        """
        Assign speaker labels to transcript segments based on diarization results.

        Args:
            segments: List of transcript segments with timestamps
            diarization: Diarization result from pyannote

        Returns:
            Updated segments with speaker labels
        """
        # Convert diarization to list of (start, end, speaker) tuples
        speaker_segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker,
            })

        # Assign speakers to transcript segments based on overlap
        for segment in segments:
            segment_start = segment["start"]
            segment_end = segment["end"]
            segment_mid = (segment_start + segment_end) / 2

            # Find speaker with most overlap
            best_speaker = None
            best_overlap = 0.0

            for speaker_seg in speaker_segments:
                # Calculate overlap
                overlap_start = max(segment_start, speaker_seg["start"])
                overlap_end = min(segment_end, speaker_seg["end"])
                overlap = max(0, overlap_end - overlap_start)

                # Check if segment midpoint is in speaker segment
                if speaker_seg["start"] <= segment_mid <= speaker_seg["end"]:
                    best_speaker = speaker_seg["speaker"]
                    break

                # Otherwise use segment with most overlap
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = speaker_seg["speaker"]

            segment["speaker"] = best_speaker

        return segments

    def _generate_speaker_labels(
        self,
        segments: list[dict[str, Any]],
    ) -> dict[str, str]:
        """
        Generate human-readable speaker labels.

        Args:
            segments: List of segments with speaker IDs

        Returns:
            Dictionary mapping speaker IDs to labels
        """
        # Get unique speakers in order of first appearance
        speakers_seen = []
        for segment in segments:
            speaker = segment.get("speaker")
            if speaker and speaker not in speakers_seen:
                speakers_seen.append(speaker)

        # Generate labels
        speaker_labels = {}
        for idx, speaker in enumerate(speakers_seen, 1):
            speaker_labels[speaker] = f"Speaker {idx}"

        return speaker_labels

    async def transcribe_episode(
        self,
        episode_id: UUID,
        language: Optional[str] = None,
        beam_size: int = 5,
        force: bool = False,
    ) -> PodcastEpisode:
        """
        Transcribe a podcast episode and save to database.

        Args:
            episode_id: ID of the episode to transcribe
            language: Language code for transcription, None for auto-detect
            beam_size: Beam size for decoding quality
            force: Force re-transcription even if already exists

        Returns:
            Updated PodcastEpisode with transcript

        Raises:
            ValueError: If episode not found or no audio URL
            httpx.HTTPError: If audio download fails
        """
        # Get episode
        episode = await self.repository.get_by_id(episode_id)
        if not episode:
            raise ValueError(f"Episode not found: {episode_id}")

        if not episode.audio_url:
            raise ValueError(f"Episode has no audio URL: {episode_id}")

        # Check if already transcribed
        if episode.transcript_generated and not force:
            logger.info(
                f"Episode already transcribed: {episode.title}. Use force=True to re-transcribe."
            )
            return episode

        # Create temporary directory for audio
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Download audio
            audio_path = await self.download_audio(episode.audio_url, temp_path)

            # Transcribe in executor (CPU-bound operation)
            loop = asyncio.get_event_loop()
            transcript, transcript_data = await loop.run_in_executor(
                None,
                self.transcribe_audio,
                audio_path,
                language,
                beam_size,
            )

        # Save transcript and structured data to database
        updated_episode = await self.repository.add_transcript(
            episode_id, transcript, transcript_data
        )

        if not updated_episode:
            raise ValueError(f"Failed to save transcript for episode: {episode_id}")

        await self.session.commit()
        logger.info(f"Transcript saved for episode: {episode.title}")
        return updated_episode

    async def transcribe_multiple_episodes(
        self,
        episode_ids: list[UUID],
        language: Optional[str] = None,
        beam_size: int = 5,
        force: bool = False,
    ) -> dict[UUID, dict[str, any]]:
        """
        Transcribe multiple episodes sequentially.

        Args:
            episode_ids: List of episode IDs to transcribe
            language: Language code for transcription
            beam_size: Beam size for decoding quality
            force: Force re-transcription

        Returns:
            Dictionary mapping episode_id to result status
            {
                episode_id: {
                    "success": bool,
                    "episode": PodcastEpisode or None,
                    "error": str or None
                }
            }
        """
        results = {}

        for episode_id in episode_ids:
            try:
                episode = await self.transcribe_episode(
                    episode_id, language, beam_size, force
                )
                results[episode_id] = {
                    "success": True,
                    "episode": episode,
                    "error": None,
                }
                logger.info(f"Successfully transcribed episode: {episode_id}")
            except Exception as e:
                results[episode_id] = {
                    "success": False,
                    "episode": None,
                    "error": str(e),
                }
                logger.error(
                    f"Failed to transcribe episode {episode_id}: {str(e)}"
                )

        return results

    async def get_transcription_stats(self) -> dict[str, int]:
        """
        Get transcription statistics.

        Returns:
            Dictionary with transcription stats
        """
        # Get all episodes
        all_episodes = await self.repository.list_all()

        total_episodes = len(all_episodes)
        transcribed = sum(1 for ep in all_episodes if ep.transcript_generated)
        pending = total_episodes - transcribed

        return {
            "total_episodes": total_episodes,
            "transcribed": transcribed,
            "pending": pending,
            "completion_rate": (
                round((transcribed / total_episodes) * 100, 2)
                if total_episodes > 0
                else 0.0
            ),
        }


async def create_transcription_service(
    session: AsyncSession,
    model_size: str = "base",
    device: str = "cpu",
    compute_type: str = "int8",
) -> TranscriptionService:
    """
    Factory function to create transcription service.

    Args:
        session: Database session
        model_size: Whisper model size
        device: Device to run on
        compute_type: Computation type

    Returns:
        TranscriptionService instance
    """
    return TranscriptionService(session, model_size, device, compute_type)