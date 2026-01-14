"""Indeed job board scraper."""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.com job postings."""

    BASE_URL = "https://www.indeed.com"

    def _get_source_name(self) -> str:
        return "indeed"

    async def search_jobs(
        self,
        keywords: Optional[list[str]] = None,
        locations: Optional[list[str]] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> list[ScrapedJob]:
        """
        Search Indeed for jobs matching criteria.

        Args:
            keywords: Search keywords
            locations: Locations to search
            remote_only: Only remote jobs
            limit: Max results

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        # Build search query
        query = " ".join(keywords) if keywords else "software engineer"
        location = locations[0] if locations else "Remote"

        if remote_only:
            query += " remote"

        # Indeed search URL
        search_url = f"{self.BASE_URL}/jobs?q={quote_plus(query)}&l={quote_plus(location)}&sort=date"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    search_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    },
                ) as response:
                    if response.status != 200:
                        return jobs

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Find job cards (Indeed uses mosaic-provider-jobcards as container)
                    job_cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon"))

                    for card in job_cards[:limit]:
                        job = self._parse_job_card(card)
                        if job:
                            jobs.append(job)

                        # Rate limit
                        await asyncio.sleep(self.rate_limit_delay)

        except Exception as e:
            print(f"Error scraping Indeed: {e}")

        return jobs

    def _parse_job_card(self, card) -> Optional[ScrapedJob]:
        """Parse a single Indeed job card."""
        try:
            # Extract job ID
            job_id = card.get("data-jk")
            if not job_id:
                # Try finding link
                link = card.find("a", class_=re.compile(r"jcs-JobTitle"))
                if link and link.get("data-jk"):
                    job_id = link["data-jk"]
                else:
                    return None

            # Job URL
            job_url = f"{self.BASE_URL}/viewjob?jk={job_id}"

            # Job title
            title_elem = card.find("h2", class_=re.compile(r"jobTitle"))
            if not title_elem:
                title_elem = card.find("a", class_=re.compile(r"jcs-JobTitle"))
            job_title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

            # Company name
            company_elem = card.find("span", class_=re.compile(r"companyName"))
            company_name = (
                company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            )

            # Location
            location_elem = card.find("div", class_=re.compile(r"companyLocation"))
            location = location_elem.get_text(strip=True) if location_elem else None

            # Remote policy
            remote_policy = "unknown"
            if location and "remote" in location.lower():
                remote_policy = "remote"
            elif location:
                remote_policy = "onsite"

            # Salary
            salary_elem = card.find("div", class_=re.compile(r"salary-snippet"))
            salary_min, salary_max = None, None
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                salary_min, salary_max = self.extract_salary(salary_text)

            # Job snippet (short description)
            snippet_elem = card.find("div", class_=re.compile(r"job-snippet"))
            job_description = snippet_elem.get_text(strip=True) if snippet_elem else None

            # Posted date (Indeed shows "Posted X days ago")
            date_elem = card.find("span", class_=re.compile(r"date"))
            posted_date = self._parse_posted_date(
                date_elem.get_text(strip=True) if date_elem else None
            )

            return ScrapedJob(
                source=self.source_name,
                source_url=job_url,
                external_id=job_id,
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location,
                remote_policy=remote_policy,
                salary_min=salary_min,
                salary_max=salary_max,
                posted_date=posted_date,
                raw_data={
                    "search_result": True,
                    "snippet_only": True,
                },
            )

        except Exception as e:
            print(f"Error parsing Indeed job card: {e}")
            return None

    def _parse_posted_date(self, date_text: Optional[str]) -> Optional[datetime]:
        """Parse Indeed's relative date format (e.g., 'Posted 2 days ago')."""
        if not date_text:
            return None

        try:
            # Extract number of days
            match = re.search(r"(\d+)\s*(day|hour)", date_text.lower())
            if match:
                num = int(match.group(1))
                unit = match.group(2)

                if unit == "day":
                    return datetime.now() - timedelta(days=num)
                elif unit == "hour":
                    return datetime.now() - timedelta(hours=num)

            # "Just posted" or "Today"
            if "just posted" in date_text.lower() or "today" in date_text.lower():
                return datetime.now()

        except Exception:
            pass

        return None

    async def get_job_details(self, job_url: str) -> Optional[ScrapedJob]:
        """
        Get full job details from Indeed job page.

        Args:
            job_url: Full Indeed job URL

        Returns:
            ScrapedJob with full description
        """
        try:
            # Extract job ID from URL
            match = re.search(r"jk=([a-zA-Z0-9]+)", job_url)
            if not match:
                return None

            job_id = match.group(1)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    job_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    },
                ) as response:
                    if response.status != 200:
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract full description
                    desc_elem = soup.find("div", id="jobDescriptionText")
                    job_description = desc_elem.get_text(separator="\n", strip=True) if desc_elem else None

                    # Company name
                    company_elem = soup.find("div", {"data-company-name": True})
                    if not company_elem:
                        company_elem = soup.find("span", class_=re.compile(r"companyName"))
                    company_name = (
                        company_elem.get_text(strip=True) if company_elem else "Unknown Company"
                    )

                    # Job title
                    title_elem = soup.find("h1", class_=re.compile(r"jobsearch-JobInfoHeader"))
                    if not title_elem:
                        title_elem = soup.find("h1")
                    job_title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

                    # Location
                    location_elem = soup.find("div", class_=re.compile(r"jobsearch-JobInfoHeader-subtitle"))
                    location = None
                    if location_elem:
                        location_text = location_elem.get_text()
                        # Location usually after company name
                        parts = location_text.split("•")
                        if len(parts) > 1:
                            location = parts[1].strip()

                    # Remote policy
                    remote_policy = self.normalize_remote_policy(location)

                    # Salary
                    salary_elem = soup.find("div", id=re.compile(r"salaryInfoAndJobType"))
                    salary_min, salary_max = None, None
                    if salary_elem:
                        salary_text = salary_elem.get_text(strip=True)
                        salary_min, salary_max = self.extract_salary(salary_text)

                    return ScrapedJob(
                        source=self.source_name,
                        source_url=job_url,
                        external_id=job_id,
                        company_name=company_name,
                        job_title=job_title,
                        job_description=job_description,
                        location=location,
                        remote_policy=remote_policy,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        raw_data={"full_details": True},
                    )

        except Exception as e:
            print(f"Error fetching Indeed job details: {e}")
            return None
