"""
Job deduplication service for detecting duplicate job postings across sources.

This service provides fuzzy matching and fingerprinting to identify duplicate jobs
that may be posted on multiple platforms with slight variations.
"""

import hashlib
import re
from difflib import SequenceMatcher
from typing import Optional
from uuid import UUID

from turbo.core.models.job_posting import JobPosting
from turbo.core.repositories.job_posting import JobPostingRepository
from turbo.core.services.job_scrapers import ScrapedJob


class JobDeduplicationService:
    """Service for detecting and managing duplicate job postings."""

    # Similarity thresholds
    EXACT_MATCH_THRESHOLD = 0.95  # 95% similar = exact match
    LIKELY_DUPLICATE_THRESHOLD = 0.85  # 85% similar = likely duplicate
    POSSIBLE_DUPLICATE_THRESHOLD = 0.70  # 70% similar = possible duplicate

    def __init__(self, job_posting_repository: JobPostingRepository):
        self._job_posting_repo = job_posting_repository

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison by removing extra whitespace and converting to lowercase."""
        if not text:
            return ""
        # Remove extra whitespace, convert to lowercase, remove special chars
        text = re.sub(r'\s+', ' ', text.strip().lower())
        text = re.sub(r'[^\w\s-]', '', text)
        return text

    @staticmethod
    def normalize_company_name(company: str) -> str:
        """Normalize company name by removing common suffixes and variations."""
        if not company:
            return ""

        normalized = JobDeduplicationService.normalize_text(company)

        # Remove common company suffixes
        suffixes = ['inc', 'llc', 'ltd', 'limited', 'corporation', 'corp', 'co', 'gmbh', 'sa', 'ag']
        for suffix in suffixes:
            # Remove suffix at end of string
            if normalized.endswith(f' {suffix}'):
                normalized = normalized[:-len(suffix)-1].strip()

        return normalized

    @staticmethod
    def normalize_job_title(title: str) -> str:
        """Normalize job title by removing seniority levels and common variations."""
        if not title:
            return ""

        normalized = JobDeduplicationService.normalize_text(title)

        # Normalize seniority levels
        seniority_map = {
            'sr': 'senior',
            'jr': 'junior',
            'mid level': 'mid',
            'midlevel': 'mid',
        }

        for abbr, full in seniority_map.items():
            normalized = normalized.replace(abbr, full)

        return normalized

    @staticmethod
    def normalize_location(location: Optional[str]) -> str:
        """Normalize location for comparison."""
        if not location:
            return "remote"

        normalized = JobDeduplicationService.normalize_text(location)

        # Treat various remote indicators as the same
        remote_keywords = ['remote', 'worldwide', 'anywhere', 'global']
        for keyword in remote_keywords:
            if keyword in normalized:
                return "remote"

        return normalized

    @staticmethod
    def create_job_fingerprint(
        company_name: str,
        job_title: str,
        location: Optional[str] = None
    ) -> str:
        """
        Create a fingerprint hash for a job posting.

        This fingerprint is used for fast duplicate detection. Jobs with the same
        fingerprint are considered exact duplicates.
        """
        normalized_company = JobDeduplicationService.normalize_company_name(company_name)
        normalized_title = JobDeduplicationService.normalize_job_title(job_title)
        normalized_location = JobDeduplicationService.normalize_location(location)

        # Create fingerprint from normalized values
        fingerprint_string = f"{normalized_company}|{normalized_title}|{normalized_location}"

        # Create SHA256 hash
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity ratio between two text strings (0.0 to 1.0)."""
        if not text1 or not text2:
            return 0.0

        return SequenceMatcher(None, text1, text2).ratio()

    @staticmethod
    def calculate_job_similarity(job1_data: dict, job2_data: dict) -> float:
        """
        Calculate overall similarity between two jobs.

        Weighted similarity:
        - Company name: 40%
        - Job title: 40%
        - Location: 20%
        """
        company_sim = JobDeduplicationService.calculate_similarity(
            JobDeduplicationService.normalize_company_name(job1_data.get("company_name", "")),
            JobDeduplicationService.normalize_company_name(job2_data.get("company_name", ""))
        )

        title_sim = JobDeduplicationService.calculate_similarity(
            JobDeduplicationService.normalize_job_title(job1_data.get("job_title", "")),
            JobDeduplicationService.normalize_job_title(job2_data.get("job_title", ""))
        )

        location_sim = JobDeduplicationService.calculate_similarity(
            JobDeduplicationService.normalize_location(job1_data.get("location")),
            JobDeduplicationService.normalize_location(job2_data.get("location"))
        )

        # Weighted average
        overall_similarity = (
            company_sim * 0.4 +
            title_sim * 0.4 +
            location_sim * 0.2
        )

        return overall_similarity

    async def find_duplicate_by_fingerprint(
        self,
        company_name: str,
        job_title: str,
        location: Optional[str] = None
    ) -> Optional[JobPosting]:
        """
        Find an exact duplicate job by fingerprint hash.

        Returns the existing job posting if found, None otherwise.
        """
        fingerprint = self.create_job_fingerprint(company_name, job_title, location)

        # Query database for jobs with matching fingerprint
        # This would require adding a fingerprint column to the job_postings table
        # For now, we'll do fuzzy matching instead
        return None

    async def find_similar_jobs(
        self,
        scraped_job: ScrapedJob,
        limit: int = 10,
        min_similarity: float = POSSIBLE_DUPLICATE_THRESHOLD
    ) -> list[tuple[JobPosting, float]]:
        """
        Find similar jobs in the database using fuzzy matching.

        Returns list of (job, similarity_score) tuples, sorted by similarity.
        """
        # Get recent jobs from database (last 30 days)
        # We'll search through these for potential duplicates
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(days=30)

        # Get all jobs (we'll filter by date in memory for now)
        all_jobs = await self._job_posting_repo.get_all(limit=1000)

        # Filter to recent jobs
        recent_jobs = [
            job for job in all_jobs
            if job.created_at >= recent_cutoff
        ]

        # Calculate similarity for each job
        job_data = {
            "company_name": scraped_job.company_name,
            "job_title": scraped_job.job_title,
            "location": scraped_job.location,
        }

        similar_jobs = []
        for existing_job in recent_jobs:
            existing_data = {
                "company_name": existing_job.company_name,
                "job_title": existing_job.job_title,
                "location": existing_job.location,
            }

            similarity = self.calculate_job_similarity(job_data, existing_data)

            if similarity >= min_similarity:
                similar_jobs.append((existing_job, similarity))

        # Sort by similarity (highest first)
        similar_jobs.sort(key=lambda x: x[1], reverse=True)

        # Return top N matches
        return similar_jobs[:limit]

    async def is_duplicate(
        self,
        scraped_job: ScrapedJob,
        threshold: float = LIKELY_DUPLICATE_THRESHOLD
    ) -> tuple[bool, Optional[JobPosting], float]:
        """
        Check if a scraped job is a duplicate of an existing job.

        Returns:
            (is_duplicate, existing_job, similarity_score)
        """
        # First check by source + external_id (exact match)
        existing = await self._job_posting_repo.get_by_external_id(
            scraped_job.source,
            scraped_job.external_id
        )

        if existing:
            return (True, existing, 1.0)

        # Check for similar jobs using fuzzy matching
        similar_jobs = await self.find_similar_jobs(
            scraped_job,
            limit=1,
            min_similarity=threshold
        )

        if similar_jobs:
            best_match, similarity = similar_jobs[0]
            return (True, best_match, similarity)

        return (False, None, 0.0)

    async def get_deduplication_stats(
        self,
        scraped_jobs: list[ScrapedJob],
        threshold: float = LIKELY_DUPLICATE_THRESHOLD
    ) -> dict:
        """
        Get deduplication statistics for a list of scraped jobs.

        Returns stats about exact matches, likely duplicates, and unique jobs.
        """
        stats = {
            "total_jobs": len(scraped_jobs),
            "exact_matches": 0,
            "likely_duplicates": 0,
            "possible_duplicates": 0,
            "unique_jobs": 0,
            "duplicate_details": []
        }

        for scraped_job in scraped_jobs:
            is_dup, existing, similarity = await self.is_duplicate(
                scraped_job,
                threshold=self.POSSIBLE_DUPLICATE_THRESHOLD
            )

            if not is_dup:
                stats["unique_jobs"] += 1
            elif similarity >= self.EXACT_MATCH_THRESHOLD:
                stats["exact_matches"] += 1
                stats["duplicate_details"].append({
                    "job_title": scraped_job.job_title,
                    "company": scraped_job.company_name,
                    "similarity": similarity,
                    "existing_source": existing.source if existing else None
                })
            elif similarity >= self.LIKELY_DUPLICATE_THRESHOLD:
                stats["likely_duplicates"] += 1
                stats["duplicate_details"].append({
                    "job_title": scraped_job.job_title,
                    "company": scraped_job.company_name,
                    "similarity": similarity,
                    "existing_source": existing.source if existing else None
                })
            else:
                stats["possible_duplicates"] += 1

        return stats
