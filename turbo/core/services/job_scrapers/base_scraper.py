"""Base scraper interface for job boards."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ScrapedJob:
    """Data class for scraped job information."""

    # Required fields
    source: str  # e.g., "indeed", "linkedin"
    source_url: str
    external_id: str
    company_name: str
    job_title: str

    # Optional fields
    application_url: Optional[str] = None  # Direct application URL (company's page)
    job_description: Optional[str] = None
    location: Optional[str] = None
    remote_policy: Optional[str] = None  # "remote", "hybrid", "onsite", "unknown"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    posted_date: Optional[datetime] = None
    raw_data: Optional[dict] = None


class BaseScraper(ABC):
    """Abstract base class for job board scrapers."""

    def __init__(self, rate_limit_delay: float = 1.0):
        """
        Initialize the scraper.

        Args:
            rate_limit_delay: Delay between requests in seconds
        """
        self.rate_limit_delay = rate_limit_delay
        self.source_name = self._get_source_name()

    @abstractmethod
    def _get_source_name(self) -> str:
        """Return the source name (e.g., 'indeed', 'linkedin')."""
        pass

    @abstractmethod
    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search for jobs matching the given criteria.

        Args:
            keywords: Keywords to search for (job titles, skills, etc.)
            locations: Locations to search in
            remote_only: Only return remote jobs
            limit: Maximum number of jobs to return

        Returns:
            List of ScrapedJob objects
        """
        pass

    @abstractmethod
    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        Get detailed information about a specific job.

        Args:
            job_url: URL of the job posting

        Returns:
            ScrapedJob object or None if not found
        """
        pass

    def normalize_remote_policy(self, raw_value: Optional[str]) -> str:
        """
        Normalize remote policy from various formats to standard values.

        Args:
            raw_value: Raw remote policy string from job posting

        Returns:
            One of: "remote", "hybrid", "onsite", "unknown"
        """
        if not raw_value:
            return "unknown"

        raw_lower = raw_value.lower()

        remote_keywords = ["remote", "work from home", "wfh", "telecommute", "distributed"]
        hybrid_keywords = ["hybrid", "flexible", "optional remote"]
        onsite_keywords = ["on-site", "onsite", "in-office", "office-based"]

        if any(keyword in raw_lower for keyword in remote_keywords):
            return "remote"
        elif any(keyword in raw_lower for keyword in hybrid_keywords):
            return "hybrid"
        elif any(keyword in raw_lower for keyword in onsite_keywords):
            return "onsite"

        return "unknown"

    def extract_salary(self, salary_text: Optional[str]) -> tuple[Optional[int], Optional[int]]:
        """
        Extract min and max salary from text.

        Args:
            salary_text: Raw salary string (e.g., "$100k - $150k", "$120,000")

        Returns:
            Tuple of (min_salary, max_salary) or (None, None)
        """
        if not salary_text:
            return None, None

        import re

        # Remove common salary text
        salary_text = salary_text.lower().replace("per year", "").replace("per annum", "")
        salary_text = salary_text.replace("a year", "").replace("/yr", "").replace("/year", "")

        # Find all numbers (with k/K for thousands)
        numbers = []
        patterns = [
            r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*k",  # 100k, 100.5k
            r"\$?\s*(\d{1,3}(?:,\d{3})+)",  # 100,000
        ]

        for pattern in patterns:
            matches = re.findall(pattern, salary_text, re.IGNORECASE)
            for match in matches:
                num_str = match.replace(",", "")
                if "k" in salary_text.lower():
                    numbers.append(int(float(num_str) * 1000))
                else:
                    numbers.append(int(float(num_str)))

        if not numbers:
            return None, None

        if len(numbers) == 1:
            # Single salary, use as min
            return numbers[0], None
        else:
            # Range, use min and max
            return min(numbers), max(numbers)
