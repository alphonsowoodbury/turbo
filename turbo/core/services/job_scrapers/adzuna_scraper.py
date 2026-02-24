"""Adzuna job board API integration."""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

import aiohttp

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob

logger = logging.getLogger(__name__)


class AdzunaScraper(BaseScraper):
    """Scraper for Adzuna job search API."""

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    # Free tier credentials - get from https://developer.adzuna.com/
    # Users should set these as environment variables
    APP_ID = "YOUR_APP_ID"  # Set via ADZUNA_APP_ID env var
    APP_KEY = "YOUR_APP_KEY"  # Set via ADZUNA_APP_KEY env var

    def __init__(self, app_id: Optional[str] = None, app_key: Optional[str] = None):
        """
        Initialize Adzuna scraper.

        Args:
            app_id: Adzuna app ID (or set ADZUNA_APP_ID env var)
            app_key: Adzuna app key (or set ADZUNA_APP_KEY env var)
        """
        super().__init__()

        # Use provided credentials or environment variables
        import os
        self.app_id = app_id or os.getenv("ADZUNA_APP_ID", self.APP_ID)
        self.app_key = app_key or os.getenv("ADZUNA_APP_KEY", self.APP_KEY)

    def _get_source_name(self) -> str:
        return "adzuna"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search Adzuna for jobs matching criteria.

        Args:
            keywords: Search keywords
            locations: Locations to search (uses "US" if remote/empty)
            remote_only: Only remote jobs
            limit: Max results (max 50 per API call)

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # Build search query
        query_parts = []
        if keywords:
            query_parts.extend(keywords)
        if remote_only:
            query_parts.append("remote")

        query = " ".join(query_parts) if query_parts else "software engineer"

        # Adzuna uses country code (us, uk, etc.)
        country = "us"

        # Location (optional - Adzuna searches nationwide if omitted)
        location_str = locations[0] if locations and locations[0].lower() != "remote" else ""

        # API endpoint: /v1/api/jobs/{country}/search/{page}
        # Adzuna uses 1-based pagination
        page = 1
        results_per_page = min(limit, 50)  # Adzuna max is 50

        url = f"{self.BASE_URL}/{country}/search/{page}"

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": results_per_page,
            "what": query,
            "content-type": "application/json",
            "sort_by": "date",
        }

        # Add location if specified
        if location_str:
            params["where"] = location_str

        # Add remote filter if specified
        if remote_only:
            params["what"] += " remote"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning("Adzuna API error (%d): %s", response.status, error_text)
                        return jobs

                    data = await response.json()

                    # Parse results
                    results = data.get("results", [])
                    logger.info("Adzuna returned %d jobs for query: %s", len(results), query)

                    for job_data in results:
                        job = self._parse_job_result(job_data)
                        if job:
                            jobs.append(job)

        except Exception as e:
            logger.error("Error calling Adzuna API: %s", e)

        return jobs

    def _parse_job_result(self, data: dict) -> Optional[ScrapedJob]:
        """Parse a single Adzuna job result."""
        try:
            # External ID
            job_id = data.get("id", "")
            if not job_id:
                return None

            # URLs
            redirect_url = data.get("redirect_url", "")
            source_url = redirect_url or f"https://www.adzuna.com/details/{job_id}"

            # Job details
            job_title = data.get("title", "Unknown Title")
            company_name = data.get("company", {}).get("display_name", "Unknown Company")

            # Description
            job_description = data.get("description", "")

            # Location
            location_data = data.get("location", {})
            location_parts = []
            if location_data.get("area"):
                location_parts.append(location_data["area"][0] if isinstance(location_data["area"], list) else location_data["area"])
            if location_data.get("display_name"):
                location_parts.append(location_data["display_name"])

            location = ", ".join(location_parts) if location_parts else None

            # Remote policy (check if "remote" appears in title/description)
            remote_policy = self.normalize_remote_policy(
                f"{job_title} {job_description} {location or ''}"
            )

            # Salary
            salary_min = data.get("salary_min")
            salary_max = data.get("salary_max")

            # Adzuna provides salary_is_predicted boolean
            salary_predicted = data.get("salary_is_predicted", False)

            # Posted date
            created = data.get("created")
            posted_date = None
            if created:
                try:
                    posted_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except Exception:
                    pass

            # Category (job type)
            category = data.get("category", {}).get("label", "")

            return ScrapedJob(
                source=self.source_name,
                source_url=source_url,
                external_id=str(job_id),
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location,
                remote_policy=remote_policy,
                salary_min=int(salary_min) if salary_min else None,
                salary_max=int(salary_max) if salary_max else None,
                salary_currency="USD",
                posted_date=posted_date,
                raw_data={
                    "category": category,
                    "salary_predicted": salary_predicted,
                    "contract_time": data.get("contract_time"),
                    "contract_type": data.get("contract_type"),
                },
            )

        except Exception as e:
            logger.error("Error parsing Adzuna job result: %s", e)
            return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        Adzuna doesn't provide a separate detail endpoint.
        All details are in the search results.
        """
        # Not implemented - search results already contain full details
        return None
