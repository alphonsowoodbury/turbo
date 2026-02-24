"""Remotive API integration for remote jobs."""

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob

logger = logging.getLogger(__name__)


class RemotiveScraper(BaseScraper):
    """
    Scraper for Remotive.io API.

    Remotive specializes in remote jobs, especially tech positions.
    Completely free, no API key required.
    API Docs: https://remotive.com/api
    """

    BASE_URL = "https://remotive.com/api"

    def _get_source_name(self) -> str:
        return "remotive"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search Remotive for jobs matching criteria.

        Note: Remotive only has remote jobs, so remote_only is always True.

        Args:
            keywords: Search keywords (matched against title/description)
            locations: Ignored - Remotive is remote-only
            remote_only: Ignored - always True
            limit: Max results

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # Remotive has a jobs endpoint with optional category filter
        # Categories: software-dev, customer-support, design, etc.
        url = f"{self.BASE_URL}/remote-jobs"

        # Build query filter
        query = " ".join(keywords).lower() if keywords else "software"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning("Remotive API error (%d): %s", response.status, error_text)
                        return jobs

                    data = await response.json()

                    # Parse results
                    all_jobs = data.get("jobs", [])

                    # Filter by keywords (Remotive doesn't have search params)
                    filtered_jobs = []
                    for job_data in all_jobs:
                        title = job_data.get("title", "").lower()
                        description = job_data.get("description", "").lower()
                        category = job_data.get("category", "").lower()

                        # Check if any keyword matches title, description, or category
                        if any(kw.lower() in title or kw.lower() in description or kw.lower() in category
                               for kw in keywords) if keywords else True:
                            filtered_jobs.append(job_data)

                    logger.info("Remotive returned %d jobs matching: %s", len(filtered_jobs), query)

                    # Parse jobs and extract application URLs asynchronously
                    for job_data in filtered_jobs[:limit]:
                        job = self._parse_job_result(job_data)
                        if job:
                            # Try to extract application URL
                            try:
                                job.application_url = await self._extract_application_url(
                                    job.source_url,
                                    job_data
                                )
                            except Exception as e:
                                logger.warning("Failed to extract application URL for %s: %s", job.job_title, e)

                            jobs.append(job)

        except Exception as e:
            logger.error("Error calling Remotive API: %s", e)

        return jobs

    def _parse_job_result(self, data: dict) -> Optional[ScrapedJob]:
        """Parse a single Remotive job result."""
        try:
            # External ID
            job_id = data.get("id")
            if not job_id:
                return None

            # URLs
            job_url = data.get("url", f"https://remotive.com/remote-jobs/view/{job_id}")

            # Job details
            job_title = data.get("title", "Unknown Title")
            company_name = data.get("company_name", "Unknown Company")

            # Description
            job_description = data.get("description", "")

            # Location (always remote, but may specify region)
            candidate_location = data.get("candidate_required_location", "")
            location = f"Remote ({candidate_location})" if candidate_location else "Remote"

            # Remote policy (always remote)
            remote_policy = "remote"

            # Salary (Remotive provides salary as text field)
            salary_text = data.get("salary", "")
            salary_min, salary_max = None, None
            if salary_text:
                salary_min, salary_max = self.extract_salary(salary_text)

            # Tags (skills/technologies)
            tags = data.get("tags", [])

            # Posted date
            publication_date = data.get("publication_date")
            posted_date = None
            if publication_date:
                try:
                    posted_date = datetime.fromisoformat(publication_date.replace("Z", "+00:00"))
                except Exception:
                    pass

            # Category
            category = data.get("category", "")

            # Job type
            job_type = data.get("job_type", "")

            # Company info
            company_logo = data.get("company_logo", "")

            return ScrapedJob(
                source=self.source_name,
                source_url=job_url,
                external_id=str(job_id),
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location,
                remote_policy=remote_policy,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                required_skills=tags if tags else None,
                posted_date=posted_date,
                raw_data={
                    "category": category,
                    "job_type": job_type,
                    "company_logo": company_logo,
                    "candidate_location": candidate_location,
                    "salary_text": salary_text,
                },
            )

        except Exception as e:
            logger.error("Error parsing Remotive job result: %s", e)
            return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        Remotive's search endpoint returns full details.
        No separate detail endpoint needed.
        """
        return None

    async def _extract_application_url(self, remotive_url: str, api_data: dict) -> Optional[str]:
        """
        Extract the direct application URL from Remotive job page.

        First checks if the API provides an apply_url field, then falls back
        to parsing the job page HTML to find the "Apply for this position" button link.

        Args:
            remotive_url: URL of the Remotive listing page
            api_data: Raw API response data for this job

        Returns:
            Direct application URL or None if not found
        """
        # Check if API provides direct application URL
        if "apply_url" in api_data:
            return api_data["apply_url"]

        # Fallback: Parse the Remotive job page
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(remotive_url, timeout=10) as response:
                    if response.status != 200:
                        logger.warning("Failed to fetch Remotive page (%d): %s", response.status, remotive_url)
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Look for "Apply for this position" button/link
                    # Common patterns in Remotive pages:
                    # 1. <a class="apply-button" href="...">
                    # 2. <a>Apply for this position</a>
                    # 3. Button with data-url or onclick

                    # Try finding by text content
                    apply_link = soup.find('a', string=re.compile(r'Apply.*position', re.IGNORECASE))
                    if apply_link and apply_link.get('href'):
                        return apply_link['href']

                    # Try finding by class names (common patterns)
                    for class_name in ['apply-button', 'job-apply', 'apply-link', 'btn-apply']:
                        apply_link = soup.find('a', class_=re.compile(class_name, re.IGNORECASE))
                        if apply_link and apply_link.get('href'):
                            return apply_link['href']

                    # Try finding button with apply-related text
                    buttons = soup.find_all(['a', 'button'])
                    for btn in buttons:
                        text = btn.get_text().strip().lower()
                        if 'apply' in text and ('position' in text or 'job' in text or text == 'apply'):
                            if btn.name == 'a' and btn.get('href'):
                                return btn['href']
                            # For buttons, check parent or data attributes
                            parent = btn.find_parent('a')
                            if parent and parent.get('href'):
                                return parent['href']
                            if btn.get('data-url'):
                                return btn['data-url']

                    logger.debug("Could not find apply link in Remotive page: %s", remotive_url)
                    return None

        except Exception as e:
            logger.error("Error extracting application URL from Remotive page: %s", e)
            return None
