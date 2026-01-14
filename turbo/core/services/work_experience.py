"""Work experience service for business logic operations."""

from typing import List, Optional
from uuid import UUID

from turbo.core.repositories.work_experience import WorkExperienceRepository, AchievementFactRepository
from turbo.core.repositories.company import CompanyRepository
from turbo.core.schemas.work_experience import (
    WorkExperienceCreate,
    WorkExperienceUpdate,
    WorkExperiencePublic,
    WorkExperienceWithCompany,
    AchievementFactCreate,
    AchievementFactUpdate,
    AchievementFactPublic,
    WorkExperienceQuery,
    AchievementFactQuery,
)
from turbo.core.utils import strip_emojis
from turbo.utils.exceptions import TurboBaseException


class WorkExperienceService:
    """Service for work experience business logic."""

    def __init__(
        self,
        work_experience_repository: WorkExperienceRepository,
        achievement_repository: AchievementFactRepository,
        company_repository: CompanyRepository,
    ) -> None:
        self._work_experience_repository = work_experience_repository
        self._achievement_repository = achievement_repository
        self._company_repository = company_repository

    async def create_work_experience(self, data: WorkExperienceCreate) -> WorkExperiencePublic:
        """Create a new work experience."""
        # Strip emojis from text fields
        if data.role_title:
            data.role_title = strip_emojis(data.role_title)
        if data.location:
            data.location = strip_emojis(data.location)
        if data.department:
            data.department = strip_emojis(data.department)

        # Verify company exists if provided
        if data.company_id:
            company = await self._company_repository.get_by_id(data.company_id)
            if not company:
                raise TurboBaseException(f"Company with ID {data.company_id} not found", "COMPANY_NOT_FOUND")

        # Create work experience
        experience = await self._work_experience_repository.create(data)

        # Reload with achievements
        experience = await self._work_experience_repository.get_by_id_with_achievements(experience.id)

        # Return public schema
        return WorkExperiencePublic.model_validate(experience)

    async def get_work_experience(self, experience_id: UUID) -> WorkExperiencePublic:
        """Get work experience by ID with achievements."""
        experience = await self._work_experience_repository.get_by_id_with_achievements(experience_id)
        if not experience:
            raise TurboBaseException(f"Work experience with ID {experience_id} not found", "WORK_EXPERIENCE_NOT_FOUND")

        return WorkExperiencePublic.model_validate(experience)

    async def get_work_experience_with_company(self, experience_id: UUID) -> WorkExperienceWithCompany:
        """Get work experience with company details."""
        experience = await self._work_experience_repository.get_by_id_with_achievements(experience_id)
        if not experience:
            raise TurboBaseException(f"Work experience with ID {experience_id} not found", "WORK_EXPERIENCE_NOT_FOUND")

        # Get company name if exists
        company_name = None
        if experience.company_id:
            company = await self._company_repository.get_by_id(experience.company_id)
            if company:
                company_name = company.name

        # Build response
        response_dict = WorkExperiencePublic.model_validate(experience).model_dump()
        response_dict["company_name"] = company_name

        return WorkExperienceWithCompany(**response_dict)

    async def list_work_experiences(self, query: WorkExperienceQuery) -> List[WorkExperiencePublic]:
        """List work experiences with optional filters."""
        if query.company_id:
            experiences = await self._work_experience_repository.get_by_company(
                query.company_id,
                limit=query.limit,
                offset=query.offset
            )
        elif query.is_current is not None:
            if query.is_current:
                experiences = await self._work_experience_repository.get_current_experiences(
                    limit=query.limit,
                    offset=query.offset
                )
            else:
                # Get all non-current (would need a new repo method, for now get all and filter)
                all_experiences = await self._work_experience_repository.get_all_with_achievements(
                    limit=query.limit,
                    offset=query.offset
                )
                experiences = [e for e in all_experiences if not e.is_current]
        elif query.employment_type:
            experiences = await self._work_experience_repository.get_by_employment_type(
                query.employment_type,
                limit=query.limit,
                offset=query.offset
            )
        else:
            experiences = await self._work_experience_repository.get_all_with_achievements(
                limit=query.limit,
                offset=query.offset
            )

        return [WorkExperiencePublic.model_validate(exp) for exp in experiences]

    async def update_work_experience(self, experience_id: UUID, data: WorkExperienceUpdate) -> WorkExperiencePublic:
        """Update a work experience."""
        # Strip emojis from text fields
        if data.role_title:
            data.role_title = strip_emojis(data.role_title)
        if data.location:
            data.location = strip_emojis(data.location)
        if data.department:
            data.department = strip_emojis(data.department)

        # Verify company exists if provided
        if data.company_id:
            company = await self._company_repository.get_by_id(data.company_id)
            if not company:
                raise TurboBaseException(f"Company with ID {data.company_id} not found", "COMPANY_NOT_FOUND")

        # Update work experience
        experience = await self._work_experience_repository.update(experience_id, data)
        if not experience:
            raise TurboBaseException(f"Work experience with ID {experience_id} not found", "WORK_EXPERIENCE_NOT_FOUND")

        # Refresh with achievements
        experience = await self._work_experience_repository.get_by_id_with_achievements(experience_id)

        return WorkExperiencePublic.model_validate(experience)

    async def delete_work_experience(self, experience_id: UUID) -> bool:
        """Delete a work experience."""
        deleted = await self._work_experience_repository.delete(experience_id)
        if not deleted:
            raise TurboBaseException(f"Work experience with ID {experience_id} not found", "WORK_EXPERIENCE_NOT_FOUND")
        return deleted


class AchievementFactService:
    """Service for achievement fact business logic."""

    def __init__(
        self,
        achievement_repository: AchievementFactRepository,
        work_experience_repository: WorkExperienceRepository,
    ) -> None:
        self._achievement_repository = achievement_repository
        self._work_experience_repository = work_experience_repository

    async def create_achievement(self, data: AchievementFactCreate) -> AchievementFactPublic:
        """Create a new achievement fact."""
        # Strip emojis from text fields
        if data.fact_text:
            data.fact_text = strip_emojis(data.fact_text)
        if data.context:
            data.context = strip_emojis(data.context)
        if data.impact:
            data.impact = strip_emojis(data.impact)

        # Verify work experience exists
        experience = await self._work_experience_repository.get_by_id(data.experience_id)
        if not experience:
            raise TurboBaseException(f"Work experience with ID {data.experience_id} not found", "WORK_EXPERIENCE_NOT_FOUND")

        # Create achievement
        achievement = await self._achievement_repository.create(data)

        return AchievementFactPublic.model_validate(achievement)

    async def get_achievement(self, achievement_id: UUID) -> AchievementFactPublic:
        """Get achievement fact by ID."""
        achievement = await self._achievement_repository.get_by_id(achievement_id)
        if not achievement:
            raise TurboBaseException(f"Achievement with ID {achievement_id} not found", "ACHIEVEMENT_NOT_FOUND")

        return AchievementFactPublic.model_validate(achievement)

    async def list_achievements(self, query: AchievementFactQuery) -> List[AchievementFactPublic]:
        """List achievement facts with optional filters."""
        if query.experience_id:
            achievements = await self._achievement_repository.get_by_experience(
                query.experience_id,
                limit=query.limit,
                offset=query.offset
            )
        elif query.metric_type:
            achievements = await self._achievement_repository.get_by_metric_type(
                query.metric_type,
                limit=query.limit,
                offset=query.offset
            )
        elif query.dimensions:
            achievements = await self._achievement_repository.get_by_dimensions(
                query.dimensions,
                limit=query.limit,
                offset=query.offset
            )
        elif query.leadership_principles:
            achievements = await self._achievement_repository.get_by_leadership_principles(
                query.leadership_principles,
                limit=query.limit,
                offset=query.offset
            )
        elif query.skills_used:
            achievements = await self._achievement_repository.get_by_skills(
                query.skills_used,
                limit=query.limit,
                offset=query.offset
            )
        else:
            achievements = await self._achievement_repository.get_all(
                limit=query.limit,
                offset=query.offset
            )

        return [AchievementFactPublic.model_validate(ach) for ach in achievements]

    async def update_achievement(self, achievement_id: UUID, data: AchievementFactUpdate) -> AchievementFactPublic:
        """Update an achievement fact."""
        # Strip emojis from text fields
        if data.fact_text:
            data.fact_text = strip_emojis(data.fact_text)
        if data.context:
            data.context = strip_emojis(data.context)
        if data.impact:
            data.impact = strip_emojis(data.impact)

        # Update achievement
        achievement = await self._achievement_repository.update(achievement_id, data)
        if not achievement:
            raise TurboBaseException(f"Achievement with ID {achievement_id} not found", "ACHIEVEMENT_NOT_FOUND")

        return AchievementFactPublic.model_validate(achievement)

    async def delete_achievement(self, achievement_id: UUID) -> bool:
        """Delete an achievement fact."""
        deleted = await self._achievement_repository.delete(achievement_id)
        if not deleted:
            raise TurboBaseException(f"Achievement with ID {achievement_id} not found", "ACHIEVEMENT_NOT_FOUND")
        return deleted

    async def search_achievements(self, query_text: str, limit: int = 100) -> List[AchievementFactPublic]:
        """Search achievements by text."""
        achievements = await self._achievement_repository.search_by_text(
            query_text,
            limit=limit
        )

        return [AchievementFactPublic.model_validate(ach) for ach in achievements]
