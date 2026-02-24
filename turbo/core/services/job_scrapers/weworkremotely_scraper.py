"""We Work Remotely API integration for remote jobs."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import aiohttp

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob

logger = logging.getLogger(__name__)


class WeWorkRemotelyScraper(BaseScraper):
    """
    Scraper for We Work Remotely API.

    We Work Remotely is a premium remote job board.
    Free tier: 1000 requests per day with API token
    API Docs: https://weworkremotely.com/api
    Note: Requires contacting support@weworkremotely.com for API token
    """

    BASE_URL = "https://weworkremotely.com/api/v1"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize We Work Remotely scraper.

        Args:
            api_token: WWR API token (or set WWR_API_TOKEN env var)
                     Contact [email protected] to get token
        """
        super().__init__()

        import os
        self.api_token = api_token or os.getenv("WWR_API_TOKEN", "")

    def _get_source_name(self) -> str:
        return "weworkremotely"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search We Work Remotely for jobs matching criteria.

        Note: All WWR jobs are remote by default.

        Args:
            keywords: Search keywords (filtered client-side)
            locations: Ignored - all jobs are remote
            remote_only: Ignored - always True
            limit: Max results

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # We Work Remotely endpoint
        url = f"{self.BASE_URL}/remote-jobs.json"

        # Build keyword filter for client-side filtering
        query = " ".join(keywords).lower() if keywords else ""

        # Headers with API token
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning("We Work Remotely API error (%d): %s", response.status, error_text)
                        return jobs

                    data = await response.json()

                    # WWR returns jobs grouped by category
                    all_jobs = []

                    # Extract jobs from different categories
                    for category_key in data.keys():
                        category_data = data[category_key]
                        if isinstance(category_data, list):
                            all_jobs.extend(category_data)

                    # Filter by keywords if provided
                    filtered_jobs = []
                    for job_data in all_jobs:
                        if isinstance(job_data, dict):
                            title = job_data.get("title", "").lower()
                            company = job_data.get("company", "").lower()
                            description = job_data.get("description", "").lower()
                            category = job_data.get("category", "").lower()

                            # Filter by keywords
                            if keywords:
                                text = f"{title} {company} {description} {category}"
                                if any(kw.lower() in text for kw in keywords):
                                    filtered_jobs.append(job_data)
                            else:
                                filtered_jobs.append(job_data)

                    logger.info("We Work Remotely returned %d jobs matching criteria", len(filtered_jobs))

                    for job_data in filtered_jobs[:limit]:
                        job = self._parse_job_result(job_data)
                        if job:
                            jobs.append(job)

        except Exception as e:
            logger.error("Error calling We Work Remotely API: %s", e)

        return jobs

    def _parse_job_result(self, data: dict) -> Optional[ScrapedJob]:
        """Parse a single We Work Remotely job result."""
        try:
            # External ID
            job_id = data.get("id")
            if not job_id:
                return None

            # URLs
            url = data.get("url", "")
            job_url = url if url.startswith("http") else f"https://weworkremotely.com{url}"

            # Job details
            job_title = data.get("title", "Unknown Title")
            company_name = data.get("company", "Unknown Company")

            # Description
            job_description = data.get("description", "")

            # Location (always remote, but may specify region)
            region = data.get("region", "")
            location = f"Remote ({region})" if region else "Remote (Worldwide)"

            # Remote policy (always remote)
            remote_policy = "remote"

            # Category (job type/field)
            category = data.get("category", "")

            # Tags
            tags = data.get("tags", [])

            # Posted date
            created_at = data.get("created_at")
            posted_date = None
            if created_at:
                try:
                    # WWR uses ISO format
                    posted_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except Exception:
                    pass

            # Company logo
            company_logo = data.get("company_logo", "")

            # Job type (full-time, contract, etc.)
            job_type = data.get("job_type", "")

            return ScrapedJob(
                source=self.source_name,
                source_url=job_url,
                external_id=str(job_id),
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location,
                remote_policy=remote_policy,
                salary_min=None,  # WWR doesn't provide salary via API
                salary_max=None,
                salary_currency="USD",
                required_skills=tags if tags else None,
                posted_date=posted_date,
                raw_data={
                    "category": category,
                    "region": region,
                    "job_type": job_type,
                    "company_logo": company_logo,
                    "tags": tags,
                },
            )

        except Exception as e:
            logger.error("Error parsing We Work Remotely job result: %s", e)
            return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        We Work Remotely's search endpoint returns full details.
        No separate detail endpoint needed.
        """
        return None
