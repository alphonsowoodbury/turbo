"""Job search service orchestrating scrapers, scoring, and storage."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from turbo.core.repositories.job_posting import (
    JobPostingRepository,
    SearchCriteriaRepository,
    JobSearchHistoryRepository,
)
from turbo.core.schemas.job_posting import (
    JobPostingCreate,
    JobPostingResponse,
    JobPostingUpdate,
    SearchCriteriaCreate,
    SearchCriteriaResponse,
    SearchCriteriaUpdate,
    JobSearchHistoryCreate,
    JobSearchHistoryResponse,
)
from turbo.core.services.job_scrapers import (
    BaseScraper,
    IndeedScraper,
    AdzunaScraper,
    JSearchScraper,
    RemotiveScraper,
    TheMuseScraper,
    ArbeitnowScraper,
    ReedScraper,
    USAJobsScraper,
    WeWorkRemotelyScraper,
    ScrapedJob,
)
from turbo.core.services.job_deduplication import JobDeduplicationService
from turbo.utils.exceptions import TurboBaseException


class JobSearchService:
    """Service for job search operations."""

    def __init__(
        self,
        job_posting_repository: JobPostingRepository,
        search_criteria_repository: SearchCriteriaRepository,
        search_history_repository: JobSearchHistoryRepository,
    ):
        self._job_posting_repo = job_posting_repository
        self._criteria_repo = search_criteria_repository
        self._history_repo = search_history_repository
        self._dedup_service = JobDeduplicationService(job_posting_repository)

        # Initialize scrapers
        self._scrapers: dict[str, BaseScraper] = {
            "indeed": IndeedScraper(),
            "adzuna": AdzunaScraper(),
            "jsearch": JSearchScraper(),
            "remotive": RemotiveScraper(),
            "themuse": TheMuseScraper(),
            "arbeitnow": ArbeitnowScraper(),
            "reed": ReedScraper(),
            "usajobs": USAJobsScraper(),
            "weworkremotely": WeWorkRemotelyScraper(),
        }

    # ========================================================================
    # Job Posting Operations
    # ========================================================================

    async def create_job_posting(self, data: JobPostingCreate) -> JobPostingResponse:
        """Create a new job posting."""
        posting = await self._job_posting_repo.create(data)
        return JobPostingResponse.model_validate(posting)

    async def get_job_posting(self, posting_id: UUID) -> JobPostingResponse:
        """Get job posting by ID."""
        posting = await self._job_posting_repo.get_by_id(posting_id)
        if not posting:
            raise TurboBaseException(f"Job posting {posting_id} not found", "JOB_POSTING_NOT_FOUND")
        return JobPostingResponse.model_validate(posting)

    async def list_job_postings(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JobPostingResponse]:
        """List job postings with optional filters."""
        if status:
            postings = await self._job_posting_repo.get_by_status(status, limit, offset)
        elif source:
            postings = await self._job_posting_repo.get_by_source(source, limit, offset)
        elif min_score is not None:
            postings = await self._job_posting_repo.get_by_min_score(min_score, limit, offset)
        else:
            postings = await self._job_posting_repo.get_all(limit, offset)

        return [JobPostingResponse.model_validate(p) for p in postings]

    async def update_job_posting(
        self, posting_id: UUID, data: JobPostingUpdate
    ) -> JobPostingResponse:
        """Update a job posting."""
        posting = await self._job_posting_repo.update(posting_id, data)
        if not posting:
            raise TurboBaseException(f"Job posting {posting_id} not found", "JOB_POSTING_NOT_FOUND")
        return JobPostingResponse.model_validate(posting)

    async def delete_job_posting(self, posting_id: UUID) -> bool:
        """Delete a job posting."""
        success = await self._job_posting_repo.delete(posting_id)
        if not success:
            raise TurboBaseException(f"Job posting {posting_id} not found", "JOB_POSTING_NOT_FOUND")
        return success

    # ========================================================================
    # Search Criteria Operations
    # ========================================================================

    async def create_search_criteria(self, data: SearchCriteriaCreate) -> SearchCriteriaResponse:
        """Create new search criteria."""
        criteria = await self._criteria_repo.create(data)
        return SearchCriteriaResponse.model_validate(criteria)

    async def get_search_criteria(self, criteria_id: UUID) -> SearchCriteriaResponse:
        """Get search criteria by ID."""
        criteria = await self._criteria_repo.get_by_id(criteria_id)
        if not criteria:
            raise TurboBaseException(f"Search criteria {criteria_id} not found", "CRITERIA_NOT_FOUND")
        return SearchCriteriaResponse.model_validate(criteria)

    async def list_search_criteria(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> list[SearchCriteriaResponse]:
        """List search criteria."""
        if is_active is not None:
            if is_active:
                criteria = await self._criteria_repo.get_active_criteria()
            else:
                all_criteria = await self._criteria_repo.get_all(limit, offset)
                criteria = [c for c in all_criteria if not c.is_active]
        else:
            criteria = await self._criteria_repo.get_all(limit, offset)

        return [SearchCriteriaResponse.model_validate(c) for c in criteria]

    async def update_search_criteria(
        self, criteria_id: UUID, data: SearchCriteriaUpdate
    ) -> SearchCriteriaResponse:
        """Update search criteria."""
        criteria = await self._criteria_repo.update(criteria_id, data)
        if not criteria:
            raise TurboBaseException(f"Search criteria {criteria_id} not found", "CRITERIA_NOT_FOUND")
        return SearchCriteriaResponse.model_validate(criteria)

    async def delete_search_criteria(self, criteria_id: UUID) -> bool:
        """Delete search criteria."""
        success = await self._criteria_repo.delete(criteria_id)
        if not success:
            raise TurboBaseException(f"Search criteria {criteria_id} not found", "CRITERIA_NOT_FOUND")
        return success

    # ========================================================================
    # Job Search Execution
    # ========================================================================

    async def execute_search(
        self, criteria_id: UUID, sources: Optional[list[str]] = None
    ) -> JobSearchHistoryResponse:
        """
        Execute a job search based on search criteria.

        Args:
            criteria_id: ID of search criteria to use
            sources: List of sources to search (default: all enabled in criteria)

        Returns:
            Search history record with results
        """
        # Get criteria
        criteria = await self._criteria_repo.get_by_id(criteria_id)
        if not criteria:
            raise TurboBaseException(f"Search criteria {criteria_id} not found", "CRITERIA_NOT_FOUND")

        # Determine which sources to search
        search_sources = sources or criteria.enabled_sources or ["indeed"]

        total_found = 0
        total_matched = 0
        total_new = 0

        for source in search_sources:
            scraper = self._scrapers.get(source)
            if not scraper:
                continue

            # Create search history record
            history_data = JobSearchHistoryCreate(
                search_criteria_id=criteria_id,
                source=source,
                query_params={
                    "keywords": criteria.job_titles,
                    "locations": criteria.locations,
                    "remote_only": criteria.exclude_onsite,
                },
                status="running",
            )
            history = await self._history_repo.create(history_data)

            try:
                start_time = datetime.now()

                # Deduplication tracking
                duplicate_exact = 0
                duplicate_fuzzy = 0
                duplicate_details = []

                # Execute search
                scraped_jobs = await scraper.search_jobs(
                    keywords=criteria.job_titles,
                    locations=criteria.locations,
                    remote_only=criteria.exclude_onsite,
                    limit=100,
                )

                # Process and score jobs
                for scraped_job in scraped_jobs:
                    total_found += 1

                    # Check if job is a duplicate (exact or fuzzy match)
                    is_duplicate, existing_job, similarity = await self._dedup_service.is_duplicate(
                        scraped_job,
                        threshold=self._dedup_service.LIKELY_DUPLICATE_THRESHOLD
                    )

                    if is_duplicate:
                        # Track duplicate type
                        if similarity >= 0.95:
                            duplicate_exact += 1
                        else:
                            duplicate_fuzzy += 1

                        # Record duplicate details
                        duplicate_details.append({
                            "job_title": scraped_job.job_title,
                            "company": scraped_job.company_name,
                            "similarity": round(similarity, 2),
                            "existing_source": existing_job.source if existing_job else None,
                            "existing_id": str(existing_job.id) if existing_job else None,
                        })
                        continue

                    total_new += 1

                    # Score the job
                    score, reasons = self._score_job(scraped_job, criteria)

                    # Only save if score meets threshold (e.g., > 50)
                    if score >= 50:
                        total_matched += 1

                        # Create job posting
                        posting_data = JobPostingCreate(
                            source=scraped_job.source,
                            source_url=scraped_job.source_url,
                            external_id=scraped_job.external_id,
                            company_name=scraped_job.company_name,
                            job_title=scraped_job.job_title,
                            job_description=scraped_job.job_description,
                            location=scraped_job.location,
                            remote_policy=scraped_job.remote_policy,
                            salary_min=scraped_job.salary_min,
                            salary_max=scraped_job.salary_max,
                            salary_currency=scraped_job.salary_currency,
                            required_skills=scraped_job.required_skills,
                            preferred_skills=scraped_job.preferred_skills,
                            posted_date=scraped_job.posted_date,
                            match_score=score,
                            match_reasons=reasons,
                            raw_data=scraped_job.raw_data,
                        )
                        await self._job_posting_repo.create(posting_data)

                # Update history record with dedup stats
                duration = (datetime.now() - start_time).seconds
                history.status = "completed"
                history.jobs_found = total_found
                history.jobs_matched = total_matched
                history.jobs_new = total_new
                history.jobs_duplicate_exact = duplicate_exact
                history.jobs_duplicate_fuzzy = duplicate_fuzzy
                history.dedup_stats = {
                    "total_duplicates": duplicate_exact + duplicate_fuzzy,
                    "exact_matches": duplicate_exact,
                    "fuzzy_matches": duplicate_fuzzy,
                    "duplicate_rate": round((duplicate_exact + duplicate_fuzzy) / total_found * 100, 1) if total_found > 0 else 0,
                    "duplicate_details": duplicate_details[:10],  # Keep top 10 for reference
                }
                history.completed_at = datetime.now()
                history.duration_seconds = duration
                await self._history_repo._session.commit()

            except Exception as e:
                # Mark history as failed
                history.status = "failed"
                history.error_message = str(e)
                history.completed_at = datetime.now()
                await self._history_repo._session.commit()
                raise

        # Update criteria last_search_at and next_search_at
        update_data = SearchCriteriaUpdate(
            last_search_at=datetime.now(),
            next_search_at=datetime.now() + timedelta(hours=criteria.search_frequency_hours),
        )
        await self._criteria_repo.update(criteria_id, update_data)

        # Return the history record
        return JobSearchHistoryResponse.model_validate(history)

    def _score_job(self, job: ScrapedJob, criteria) -> tuple[float, dict]:
        """
        Score how well a job matches the criteria.

        Returns:
            Tuple of (score, reasons_dict)
            Score is 0-100
        """
        score = 0.0
        reasons = {}

        weights = criteria.scoring_weights or {
            "salary": 0.3,
            "location": 0.2,
            "keywords": 0.3,
            "title": 0.2,
        }

        # Score title match
        title_score = 0
        if criteria.job_titles:
            job_title_lower = job.job_title.lower()
            for target_title in criteria.job_titles:
                if target_title.lower() in job_title_lower:
                    title_score = 100
                    reasons["title_match"] = target_title
                    break
        score += title_score * weights.get("title", 0.2)

        # Score keywords
        keyword_score = 0
        matched_keywords = []
        if criteria.required_keywords and job.job_description:
            desc_lower = job.job_description.lower()
            for keyword in criteria.required_keywords:
                if keyword.lower() in desc_lower:
                    matched_keywords.append(keyword)
            if matched_keywords:
                keyword_score = (len(matched_keywords) / len(criteria.required_keywords)) * 100
                reasons["matched_keywords"] = matched_keywords
        score += keyword_score * weights.get("keywords", 0.3)

        # Score location/remote
        location_score = 0
        if criteria.exclude_onsite and job.remote_policy == "remote":
            location_score = 100
            reasons["remote_match"] = True
        elif criteria.locations and job.location:
            job_location_lower = job.location.lower()
            for target_location in criteria.locations:
                if target_location.lower() in job_location_lower:
                    location_score = 100
                    reasons["location_match"] = target_location
                    break
        score += location_score * weights.get("location", 0.2)

        # Score salary
        salary_score = 0
        if criteria.salary_minimum and job.salary_min:
            if job.salary_min >= criteria.salary_minimum:
                salary_score = 100
                reasons["salary_meets_minimum"] = True
            else:
                # Partial credit if close
                salary_score = (job.salary_min / criteria.salary_minimum) * 100
                reasons["salary_below_minimum"] = True
        score += salary_score * weights.get("salary", 0.3)

        # Check for excluded keywords
        if criteria.excluded_keywords and job.job_description:
            desc_lower = job.job_description.lower()
            excluded_found = []
            for keyword in criteria.excluded_keywords:
                if keyword.lower() in desc_lower:
                    excluded_found.append(keyword)
            if excluded_found:
                score = score * 0.5  # Heavily penalize
                reasons["excluded_keywords_found"] = excluded_found

        return round(score, 2), reasons

    async def get_search_history(
        self, criteria_id: Optional[UUID] = None, limit: int = 50
    ) -> list[JobSearchHistoryResponse]:
        """Get search history."""
        if criteria_id:
            history = await self._history_repo.get_by_criteria(criteria_id, limit)
        else:
            history = await self._history_repo.get_recent_searches(limit)

        return [JobSearchHistoryResponse.model_validate(h) for h in history]
