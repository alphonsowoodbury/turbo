"""USAJobs API integration for US federal government jobs."""

import asyncio
from datetime import datetime
from typing import Optional

import aiohttp

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob


class USAJobsScraper(BaseScraper):
    """
    Scraper for USAJobs.gov API (US federal government jobs).

    USAJobs provides access to all federal job openings.
    Completely free with API key (unlimited requests)
    API Docs: https://developer.usajobs.gov/
    """

    BASE_URL = "https://data.usajobs.gov/api"

    def __init__(self, api_key: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Initialize USAJobs scraper.

        Args:
            api_key: USAJobs API key (or set USAJOBS_API_KEY env var)
            user_agent: User agent email (or set USAJOBS_USER_AGENT env var)
        """
        super().__init__()

        import os
        self.api_key = api_key or os.getenv("USAJOBS_API_KEY", "")
        self.user_agent = user_agent or os.getenv("USAJOBS_USER_AGENT", "turbocode@example.com")

    def _get_source_name(self) -> str:
        return "usajobs"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search USAJobs for jobs matching criteria.

        Args:
            keywords: Search keywords
            locations: Locations to search (US locations/states)
            remote_only: Only remote/telework jobs
            limit: Max results (max 500 per request)

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # Build search query
        keyword_query = " ".join(keywords) if keywords else "technology"

        if remote_only:
            keyword_query += " telework"

        # USAJobs parameters
        params = {
            "Keyword": keyword_query,
            "ResultsPerPage": min(limit, 500),  # Max 500
            "Page": 1,
        }

        # Location (USAJobs uses location codes or city/state)
        if locations and locations[0].lower() != "remote":
            params["LocationName"] = locations[0]

        # Remote/telework filter
        if remote_only:
            params["RemoteIndicator"] = "true"

        # Required headers
        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": self.user_agent,  # Must be valid email
            "Authorization-Key": self.api_key,
        }

        url = f"{self.BASE_URL}/Search"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"USAJobs API error ({response.status}): {error_text}")
                        return jobs

                    data = await response.json()

                    # Parse results
                    search_result = data.get("SearchResult", {})
                    results = search_result.get("SearchResultItems", [])

                    print(f"USAJobs returned {len(results)} jobs for query: {keyword_query}")

                    for item in results[:limit]:
                        job = self._parse_job_result(item)
                        if job:
                            jobs.append(job)

        except Exception as e:
            print(f"Error calling USAJobs API: {e}")

        return jobs

    def _parse_job_result(self, item: dict) -> Optional[ScrapedJob]:
        """Parse a single USAJobs search result item."""
        try:
            # USAJobs wraps data in "MatchedObjectDescriptor"
            data = item.get("MatchedObjectDescriptor", {})

            # External ID (PositionID is unique)
            position_id = data.get("PositionID")
            if not position_id:
                return None

            # URLs
            apply_uri = data.get("ApplyURI", [])
            job_url = apply_uri[0] if apply_uri else f"https://www.usajobs.gov/job/{position_id}"

            # Job details
            job_title = data.get("PositionTitle", "Unknown Title")

            # Organization (agency)
            organization_name = data.get("OrganizationName", "Federal Government")

            # Department
            department_name = data.get("DepartmentName", "")
            company_name = department_name if department_name else organization_name

            # Description
            user_area = data.get("UserArea", {})
            details = user_area.get("Details", {})
            job_summary = details.get("JobSummary", "")
            major_duties = details.get("MajorDuties", [])

            job_description = job_summary
            if major_duties:
                job_description += "\n\nMajor Duties:\n" + "\n".join(major_duties)

            # Location
            position_location = data.get("PositionLocation", [])
            locations = []
            for loc in position_location:
                city = loc.get("CityName", "")
                state = loc.get("StateOrTerritory", "")
                country = loc.get("CountryCode", "")

                loc_str = ", ".join([p for p in [city, state, country] if p])
                if loc_str:
                    locations.append(loc_str)

            location = "; ".join(locations) if locations else "United States"

            # Remote/telework eligibility
            telework_eligible = data.get("TeleworkEligible", False)
            remote_policy = "remote" if telework_eligible else "onsite"

            # Salary
            position_remuneration = data.get("PositionRemuneration", [])
            salary_min, salary_max = None, None

            if position_remuneration:
                salary_info = position_remuneration[0]
                minimum_range = salary_info.get("MinimumRange")
                maximum_range = salary_info.get("MaximumRange")

                if minimum_range:
                    salary_min = int(float(minimum_range))
                if maximum_range:
                    salary_max = int(float(maximum_range))

            # Dates
            publication_start = data.get("PublicationStartDate")
            posted_date = None
            if publication_start:
                try:
                    # Format: "2025-10-20T00:00:00.0000"
                    posted_date = datetime.fromisoformat(publication_start.split(".")[0])
                except Exception:
                    pass

            # Application close date
            application_close = data.get("ApplicationCloseDate")
            expires_date = None
            if application_close:
                try:
                    expires_date = datetime.fromisoformat(application_close.split(".")[0])
                except Exception:
                    pass

            # Position schedule (Full-time, Part-time)
            position_schedule = data.get("PositionSchedule", [])
            schedule_names = [s.get("Name", "") for s in position_schedule]

            # Job category
            job_category = data.get("JobCategory", [])
            category_names = [c.get("Name", "") for c in job_category]

            # Qualifications summary
            qualifications_summary = details.get("QualificationSummary", "")

            return ScrapedJob(
                source=self.source_name,
                source_url=job_url,
                external_id=position_id,
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location,
                remote_policy=remote_policy,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                required_skills=category_names if category_names else None,
                posted_date=posted_date,
                raw_data={
                    "telework_eligible": telework_eligible,
                    "organization": organization_name,
                    "department": department_name,
                    "position_schedule": schedule_names,
                    "qualifications": qualifications_summary,
                    "application_close_date": expires_date.isoformat() if expires_date else None,
                    "security_clearance": details.get("SecurityClearance", ""),
                },
            )

        except Exception as e:
            print(f"Error parsing USAJobs job result: {e}")
            return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        USAJobs search results contain full details.
        No separate detail endpoint needed.
        """
        return None
