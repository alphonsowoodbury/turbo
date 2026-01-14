"""Arbeitnow API integration for European tech jobs."""

import asyncio
from datetime import datetime
from typing import Optional

import aiohttp

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob


class ArbeitnowScraper(BaseScraper):
    """
    Scraper for Arbeitnow API.

    Arbeitnow focuses on tech jobs in Europe, especially Germany.
    Completely free, no API key required.
    API Docs: https://www.arbeitnow.com/api
    """

    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    def _get_source_name(self) -> str:
        return "arbeitnow"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search Arbeitnow for jobs matching criteria.

        Args:
            keywords: Search keywords (not supported by Arbeitnow, will filter locally)
            locations: Locations to search (not supported, will filter locally)
            remote_only: Only remote jobs
            limit: Max results

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # Arbeitnow endpoint - returns all jobs (simple API)
        url = self.BASE_URL

        query = " ".join(keywords).lower() if keywords else ""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Arbeitnow API error ({response.status}): {error_text}")
                        return jobs

                    data = await response.json()

                    # Parse results
                    all_jobs = data.get("data", [])

                    # Filter locally by keywords and remote
                    filtered_jobs = []
                    for job_data in all_jobs:
                        title = job_data.get("title", "").lower()
                        description = job_data.get("description", "").lower()
                        tags = " ".join(job_data.get("tags", [])).lower()
                        location = job_data.get("location", "").lower()
                        is_remote = "remote" in location or job_data.get("remote", False)

                        # Filter by remote
                        if remote_only and not is_remote:
                            continue

                        # Filter by keywords
                        if keywords:
                            text = f"{title} {description} {tags}"
                            if not any(kw.lower() in text for kw in keywords):
                                continue

                        # Filter by location
                        if locations and not remote_only:
                            if not any(loc.lower() in location for loc in locations):
                                continue

                        filtered_jobs.append(job_data)

                    print(f"Arbeitnow returned {len(filtered_jobs)} jobs matching criteria")

                    for job_data in filtered_jobs[:limit]:
                        job = self._parse_job_result(job_data)
                        if job:
                            jobs.append(job)

        except Exception as e:
            print(f"Error calling Arbeitnow API: {e}")

        return jobs

    def _parse_job_result(self, data: dict) -> Optional[ScrapedJob]:
        """Parse a single Arbeitnow job result."""
        try:
            # External ID (slug is unique identifier)
            slug = data.get("slug", "")
            if not slug:
                return None

            # URLs
            job_url = data.get("url", f"https://www.arbeitnow.com/view/{slug}")

            # Job details
            job_title = data.get("title", "Unknown Title")
            company_name = data.get("company_name", "Unknown Company")

            # Description
            job_description = data.get("description", "")

            # Location
            location = data.get("location", "")
            is_remote = data.get("remote", False) or "remote" in location.lower()

            # Remote policy
            remote_policy = "remote" if is_remote else "onsite"

            # Tags (skills/technologies)
            tags = data.get("tags", [])

            # Posted date
            created_at = data.get("created_at")
            posted_date = None
            if created_at:
                try:
                    # Unix timestamp
                    posted_date = datetime.fromtimestamp(created_at)
                except Exception:
                    pass

            # Job types
            job_types = data.get("job_types", [])

            return ScrapedJob(
                source=self.source_name,
                source_url=job_url,
                external_id=slug,
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location if location else "Europe",
                remote_policy=remote_policy,
                salary_min=None,  # Arbeitnow doesn't provide salary
                salary_max=None,
                salary_currency="EUR",
                required_skills=tags if tags else None,
                posted_date=posted_date,
                raw_data={
                    "job_types": job_types,
                    "is_remote": is_remote,
                    "slug": slug,
                },
            )

        except Exception as e:
            print(f"Error parsing Arbeitnow job result: {e}")
            return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        Arbeitnow's search endpoint returns full details.
        No separate detail endpoint needed.
        """
        return None
