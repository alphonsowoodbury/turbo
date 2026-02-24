"""The Muse API integration for curated jobs with company culture info."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import aiohttp

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob

logger = logging.getLogger(__name__)


class TheMuseScraper(BaseScraper):
    """
    Scraper for The Muse API.

    The Muse focuses on company culture and curated job listings.
    Completely free, no API key required.
    API Docs: https://www.themuse.com/developers/api/v2
    """

    BASE_URL = "https://www.themuse.com/api/public"

    def _get_source_name(self) -> str:
        return "themuse"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search The Muse for jobs matching criteria.

        Args:
            keywords: Search keywords (category or level)
            locations: Locations to search
            remote_only: Only remote/flexible jobs
            limit: Max results (max 20 per page)

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # The Muse jobs endpoint
        url = f"{self.BASE_URL}/jobs"

        # Build parameters
        params = {
            "page": "0",
            "descending": "true",
        }

        # Add category filter (The Muse uses predefined categories)
        if keywords:
            # Map common keywords to Muse categories
            category_map = {
                "software": "Software Engineering",
                "engineer": "Software Engineering",
                "engineering": "Software Engineering",
                "data": "Data Science",
                "product": "Product Management",
                "design": "Design and UX",
                "marketing": "Marketing and PR",
            }

            for keyword in keywords:
                for key, category in category_map.items():
                    if key.lower() in keyword.lower():
                        params["category"] = category
                        break
                if "category" in params:
                    break

        # Location (The Muse has "Flexible / Remote" as a location)
        if remote_only or (locations and any("remote" in loc.lower() for loc in locations)):
            params["location"] = "Flexible / Remote"
        elif locations and locations[0].lower() != "remote":
            params["location"] = locations[0]

        # Level filter (Entry, Mid, Senior, etc.)
        if keywords:
            if any("senior" in kw.lower() for kw in keywords):
                params["level"] = "Senior Level"
            elif any("mid" in kw.lower() for kw in keywords):
                params["level"] = "Mid Level"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning("The Muse API error (%d): %s", response.status, error_text)
                        return jobs

                    data = await response.json()

                    # Parse results
                    results = data.get("results", [])
                    logger.info("The Muse returned %d jobs", len(results))

                    for job_data in results[:limit]:
                        job = self._parse_job_result(job_data)
                        if job:
                            jobs.append(job)

        except Exception as e:
            logger.error("Error calling The Muse API: %s", e)

        return jobs

    def _parse_job_result(self, data: dict) -> Optional[ScrapedJob]:
        """Parse a single The Muse job result."""
        try:
            # External ID
            job_id = data.get("id")
            if not job_id:
                return None

            # URLs
            landing_page = data.get("refs", {}).get("landing_page", "")
            job_url = landing_page or f"https://www.themuse.com/jobs/{job_id}"

            # Job details
            job_title = data.get("name", "Unknown Title")

            # Company info
            company_data = data.get("company", {})
            company_name = company_data.get("name", "Unknown Company")

            # Locations (The Muse provides structured location data)
            locations = data.get("locations", [])
            location_names = [loc.get("name", "") for loc in locations]
            location = ", ".join(location_names) if location_names else None

            # Remote policy
            remote_policy = "unknown"
            if location and any("remote" in loc.lower() or "flexible" in loc.lower() for loc in location_names):
                remote_policy = "remote"
            elif location:
                remote_policy = "onsite"

            # Categories (skills/departments)
            categories = data.get("categories", [])
            category_names = [cat.get("name", "") for cat in categories]

            # Levels
            levels = data.get("levels", [])
            level_names = [lvl.get("name", "") for lvl in levels]

            # Content/Description
            job_description = data.get("contents", "")

            # Posted date
            publication_date = data.get("publication_date")
            posted_date = None
            if publication_date:
                try:
                    # The Muse uses format: "2025-10-20T12:00:00.000-04:00"
                    dt = datetime.fromisoformat(publication_date)
                    # Convert to timezone-naive UTC for database compatibility
                    posted_date = dt.replace(tzinfo=None)
                except Exception:
                    pass

            # Model type (internal, external)
            model_type = data.get("model_type", "")

            return ScrapedJob(
                source=self.source_name,
                source_url=job_url,
                external_id=str(job_id),
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location,
                remote_policy=remote_policy,
                salary_min=None,  # The Muse doesn't provide salary in API
                salary_max=None,
                salary_currency="USD",
                required_skills=category_names if category_names else None,
                posted_date=posted_date,
                raw_data={
                    "levels": level_names,
                    "categories": category_names,
                    "company_short_name": company_data.get("short_name"),
                    "model_type": model_type,
                    "tags": data.get("tags", []),
                },
            )

        except Exception as e:
            logger.error("Error parsing The Muse job result: %s", e)
            return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        Get company culture and detailed job info.

        The Muse has a /companies/{id} endpoint with culture data.
        """
        # Could implement to fetch company culture/values
        return None
