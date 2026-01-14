"""Reed.co.uk API integration for UK jobs."""

import asyncio
from datetime import datetime
from typing import Optional

import aiohttp

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob


class ReedScraper(BaseScraper):
    """
    Scraper for Reed.co.uk API (UK jobs).

    Reed.co.uk is one of the UK's largest job boards.
    Free tier: 1000 requests per day
    API Docs: https://www.reed.co.uk/developers/jobseeker
    """

    BASE_URL = "https://www.reed.co.uk/api/1.0"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Reed scraper.

        Args:
            api_key: Reed API key (or set REED_API_KEY env var)
        """
        super().__init__()

        import os
        self.api_key = api_key or os.getenv("REED_API_KEY", "")

    def _get_source_name(self) -> str:
        return "reed"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search Reed.co.uk for jobs matching criteria.

        Args:
            keywords: Search keywords
            locations: Locations to search (UK locations)
            remote_only: Only remote jobs
            limit: Max results (max 100 per request)

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # Build search query
        query = " ".join(keywords) if keywords else "software engineer"

        if remote_only:
            query += " remote"

        # Reed parameters
        params = {
            "keywords": query,
            "resultsToTake": min(limit, 100),  # Max 100 per request
            "resultsToSkip": 0,
        }

        # Location (Reed uses UK location names)
        if locations and locations[0].lower() != "remote":
            params["locationName"] = locations[0]

        # Basic auth with API key as username, empty password
        auth = aiohttp.BasicAuth(self.api_key, "")

        url = f"{self.BASE_URL}/search"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, auth=auth) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Reed API error ({response.status}): {error_text}")
                        return jobs

                    data = await response.json()

                    # Parse results
                    results = data.get("results", [])
                    print(f"Reed returned {len(results)} jobs for query: {query}")

                    for job_data in results[:limit]:
                        job = self._parse_job_result(job_data)
                        if job:
                            jobs.append(job)

        except Exception as e:
            print(f"Error calling Reed API: {e}")

        return jobs

    def _parse_job_result(self, data: dict) -> Optional[ScrapedJob]:
        """Parse a single Reed job result."""
        try:
            # External ID
            job_id = data.get("jobId")
            if not job_id:
                return None

            # URLs
            job_url = data.get("jobUrl", f"https://www.reed.co.uk/jobs/{job_id}")

            # Job details
            job_title = data.get("jobTitle", "Unknown Title")
            employer_name = data.get("employerName", "Unknown Company")

            # Description
            job_description = data.get("jobDescription", "")

            # Location
            location_name = data.get("locationName", "")

            # Remote policy - Reed doesn't have explicit remote field
            remote_policy = self.normalize_remote_policy(
                f"{job_title} {job_description} {location_name}"
            )

            # Salary
            minimum_salary = data.get("minimumSalary")
            maximum_salary = data.get("maximumSalary")

            # Convert to annual if needed (Reed sometimes provides monthly)
            salary_min = int(minimum_salary) if minimum_salary else None
            salary_max = int(maximum_salary) if maximum_salary else None

            # Currency (Reed is UK-based)
            currency = data.get("currency", "GBP")

            # Date posted
            date_posted = data.get("date")
            posted_date = None
            if date_posted:
                try:
                    # Reed uses format: "20/10/2025" or ISO
                    if "T" in date_posted:
                        posted_date = datetime.fromisoformat(date_posted.replace("Z", "+00:00"))
                    else:
                        # Try DD/MM/YYYY format
                        posted_date = datetime.strptime(date_posted, "%d/%m/%Y")
                except Exception:
                    pass

            # Employment type
            contract_type = data.get("contractType", "")
            full_time = data.get("fullTime", True)

            # Expiration date
            expiration_date_str = data.get("expirationDate")
            expires_date = None
            if expiration_date_str:
                try:
                    expires_date = datetime.fromisoformat(expiration_date_str.replace("Z", "+00:00"))
                except Exception:
                    pass

            # Applications
            applications = data.get("applications")

            return ScrapedJob(
                source=self.source_name,
                source_url=job_url,
                external_id=str(job_id),
                company_name=employer_name,
                job_title=job_title,
                job_description=job_description,
                location=location_name if location_name else "United Kingdom",
                remote_policy=remote_policy,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                posted_date=posted_date,
                raw_data={
                    "contract_type": contract_type,
                    "full_time": full_time,
                    "applications": applications,
                    "expiration_date": expires_date.isoformat() if expires_date else None,
                },
            )

        except Exception as e:
            print(f"Error parsing Reed job result: {e}")
            return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        Get detailed job information by job ID.

        Reed has a /jobs/{jobId} endpoint for full details.
        """
        try:
            # Extract job ID from URL
            import re
            match = re.search(r"/jobs/(\d+)", job_url)
            if not match:
                return None

            job_id = match.group(1)

            # Basic auth
            auth = aiohttp.BasicAuth(self.api_key, "")

            url = f"{self.BASE_URL}/jobs/{job_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=auth) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    return self._parse_job_result(data)

        except Exception as e:
            print(f"Error fetching Reed job details: {e}")
            return None
