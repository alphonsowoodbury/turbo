"""JSearch API integration via RapidAPI (job aggregator)."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import aiohttp

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob

logger = logging.getLogger(__name__)


class JSearchScraper(BaseScraper):
    """
    Scraper for JSearch API via RapidAPI.

    JSearch aggregates jobs from Indeed, LinkedIn, Glassdoor, ZipRecruiter, etc.
    Free tier: 150 requests/month
    Sign up at: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
    """

    BASE_URL = "https://jsearch.p.rapidapi.com"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize JSearch scraper.

        Args:
            api_key: RapidAPI key (or set RAPIDAPI_KEY env var)
        """
        super().__init__()

        import os
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY", "")

    def _get_source_name(self) -> str:
        return "jsearch"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search JSearch for jobs matching criteria.

        Args:
            keywords: Search keywords
            locations: Locations to search
            remote_only: Only remote jobs
            limit: Max results (max 10 per page on free tier)

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # Build search query
        query_parts = []
        if keywords:
            query_parts.extend(keywords)

        query = " ".join(query_parts) if query_parts else "software engineer"

        # Add location to query
        if locations and locations[0].lower() != "remote":
            query += f" in {locations[0]}"

        if remote_only:
            query += " remote"

        # JSearch parameters
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "all",  # all, today, 3days, week, month
        }

        # Add remote filter if specified
        if remote_only:
            params["employment_types"] = "FULLTIME"
            params["remote_jobs_only"] = "true"

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

        url = f"{self.BASE_URL}/search"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning("JSearch API error (%d): %s", response.status, error_text)
                        return jobs

                    data = await response.json()

                    # Parse results
                    results = data.get("data", [])
                    logger.info("JSearch returned %d jobs for query: %s", len(results), query)

                    for job_data in results[:limit]:
                        job = self._parse_job_result(job_data)
                        if job:
                            jobs.append(job)

        except Exception as e:
            logger.error("Error calling JSearch API: %s", e)

        return jobs

    def _parse_job_result(self, data: dict) -> Optional[ScrapedJob]:
        """Parse a single JSearch job result."""
        try:
            # External ID
            job_id = data.get("job_id", "")
            if not job_id:
                return None

            # URLs
            apply_link = data.get("job_apply_link", "")
            job_url = data.get("job_google_link", apply_link)

            # Job details
            job_title = data.get("job_title", "Unknown Title")
            company_name = data.get("employer_name", "Unknown Company")

            # Description
            job_description = data.get("job_description", "")

            # Location
            city = data.get("job_city")
            state = data.get("job_state")
            country = data.get("job_country")

            location_parts = [p for p in [city, state, country] if p]
            location = ", ".join(location_parts) if location_parts else None

            # Remote policy
            is_remote = data.get("job_is_remote", False)
            remote_policy = "remote" if is_remote else self.normalize_remote_policy(
                f"{job_title} {job_description} {location or ''}"
            )

            # Salary (JSearch provides min/max salary and period)
            salary_min = data.get("job_min_salary")
            salary_max = data.get("job_max_salary")
            salary_period = data.get("job_salary_period")  # YEAR, MONTH, HOUR

            # Convert to annual if needed
            if salary_period == "MONTH":
                if salary_min:
                    salary_min = int(salary_min * 12)
                if salary_max:
                    salary_max = int(salary_max * 12)
            elif salary_period == "HOUR":
                # Assume 40hr/week, 52 weeks
                if salary_min:
                    salary_min = int(salary_min * 40 * 52)
                if salary_max:
                    salary_max = int(salary_max * 40 * 52)

            # Skills
            required_skills = data.get("job_required_skills", [])

            # Posted date
            posted_timestamp = data.get("job_posted_at_timestamp")
            posted_date = None
            if posted_timestamp:
                try:
                    posted_date = datetime.fromtimestamp(posted_timestamp)
                except Exception:
                    pass

            # Employment type
            employment_type = data.get("job_employment_type", "")

            # Publisher (original source: indeed, linkedin, etc)
            publisher = data.get("job_publisher", "")

            return ScrapedJob(
                source=self.source_name,
                source_url=job_url,
                external_id=str(job_id),
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location,
                remote_policy=remote_policy,
                salary_min=int(salary_min) if salary_min else None,
                salary_max=int(salary_max) if salary_max else None,
                salary_currency=data.get("job_salary_currency", "USD"),
                required_skills=required_skills if required_skills else None,
                posted_date=posted_date,
                raw_data={
                    "publisher": publisher,
                    "employment_type": employment_type,
                    "is_remote": is_remote,
                    "apply_link": apply_link,
                    "highlights": data.get("job_highlights", {}),
                    "benefits": data.get("job_benefits", []),
                },
            )

        except Exception as e:
            logger.error("Error parsing JSearch job result: %s", e)
            return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        Get detailed job information by job ID.

        JSearch provides a /job-details endpoint but requires job_id.
        """
        # Could implement if we store job_id separately
        return None
