"""Populate work experience and achievements from Alphonso's resume data."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from turbo.core.database.connection import get_db_session
from turbo.core.repositories.company import CompanyRepository
from turbo.core.repositories.work_experience import WorkExperienceRepository, AchievementFactRepository
from turbo.core.schemas.company import CompanyCreate
from turbo.core.schemas.work_experience import WorkExperienceCreate, AchievementFactCreate


async def populate_jpmc_experience():
    """Populate JPMorganChase work experience with granular achievement facts."""

    async for session in get_db_session():
        try:
            company_repo = CompanyRepository(session)
            work_exp_repo = WorkExperienceRepository(session)
            achievement_repo = AchievementFactRepository(session)

            # 1. Create JPMorganChase company
            print("Creating JPMorganChase company...")
            jpmc_company = CompanyCreate(
                name="JPMorganChase",
                industry="Financial Services",
                size="Large (500+)",
                location="Columbus, OH",
                remote_policy="Hybrid"
            )
            jpmc = await company_repo.create(jpmc_company)
            print(f"✅ Created company: {jpmc.name} (ID: {jpmc.id})")

            # 2. Create work experience
            print("\nCreating Senior Software Engineer work experience...")
            work_exp = WorkExperienceCreate(
                company_id=jpmc.id,
                role_title="Senior Software Engineer",
                start_date="2019-01-01",
                end_date="2024-12-31",
                is_current=False,
                location="Columbus, OH",
                employment_type="full_time",
                department="Cloud Engineering",
                team_context={
                    "team_size": 8,
                    "reporting_to": "Engineering Manager",
                    "cross_functional_teams": ["cybersecurity", "architecture", "governance"]
                },
                technologies=[
                    "AWS Lambda", "AWS Step Functions", "DynamoDB", "Serverless",
                    "Python", "SQL", "Terraform", "Docker", "Kubernetes", "Snowflake",
                    "Apache Solr", "TensorFlow", "Keras"
                ]
            )
            experience = await work_exp_repo.create(work_exp)
            print(f"✅ Created work experience: {experience.role_title} at {jpmc.name}")
            print(f"   Experience ID: {experience.id}")

            # 3. Create granular achievement facts
            print("\nCreating achievement facts...")

            achievements = [
                # Cost Optimization
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Delivered platform objectives using only 30% of allocated budget through cost-efficient serverless architecture",
                    metric_type="cost_savings",
                    metric_value=70,
                    metric_unit="percentage",
                    dimensions=["frugality", "technical_excellence", "innovation"],
                    leadership_principles=["frugality", "invent_and_simplify"],
                    skills_used=["AWS Lambda", "Serverless Architecture", "Cost Optimization"],
                    context="Platform migration project with allocated budget for traditional infrastructure",
                    impact="Enabled reinvestment of saved funds into additional features and team capacity",
                    display_order=1
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Operating at 70% under traditional costs through serverless and cloud-native designs",
                    metric_type="cost_savings",
                    metric_value=70,
                    metric_unit="percentage",
                    dimensions=["frugality", "technical_excellence"],
                    leadership_principles=["frugality", "think_big"],
                    skills_used=["AWS", "Serverless Architecture", "Cloud-Native Design"],
                    context="Comparison against traditional on-premises infrastructure costs",
                    impact="Sustained cost efficiency while scaling platform capabilities",
                    display_order=2
                ),

                # Speed & Efficiency
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Reduced integration time from weeks to 3 days through streamlined onboarding workflows",
                    metric_type="time_reduction",
                    metric_value=85,
                    metric_unit="percentage",
                    dimensions=["customer_obsession", "operational_excellence", "technical"],
                    leadership_principles=["customer_obsession", "bias_for_action"],
                    skills_used=["API Design", "Workflow Automation", "Developer Experience"],
                    context="New client onboarding process was taking 2-3 weeks due to manual configuration",
                    impact="Enabled faster revenue generation and improved client satisfaction scores",
                    display_order=3
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Cut integration complexity from weeks to same-day deployments via DynamoDB-driven configuration framework",
                    metric_type="time_reduction",
                    metric_value=95,
                    metric_unit="percentage",
                    dimensions=["technical_excellence", "innovation", "operational_excellence"],
                    leadership_principles=["invent_and_simplify", "bias_for_action"],
                    skills_used=["DynamoDB", "Configuration Management", "Automation"],
                    context="Complex deployment process requiring extensive manual configuration and testing",
                    impact="Enabled rapid iteration and reduced deployment risk through automation",
                    display_order=4
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Delivered monitoring dashboard 6 months ahead of schedule through proactive problem identification",
                    metric_type="time_ahead_of_schedule",
                    metric_value=6,
                    metric_unit="months",
                    dimensions=["ownership", "bias_for_action", "technical"],
                    leadership_principles=["bias_for_action", "deliver_results"],
                    skills_used=["Monitoring", "Dashboard Development", "Problem Solving"],
                    context="Dashboard was planned for Q4 but identified critical need earlier",
                    impact="Prevented production incidents and improved operational visibility",
                    display_order=5
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Optimized query response times to sub-2 seconds while handling millions of daily queries",
                    metric_type="performance_improvement",
                    metric_value=2,
                    metric_unit="seconds",
                    dimensions=["technical_excellence", "customer_obsession"],
                    leadership_principles=["customer_obsession", "deliver_results"],
                    skills_used=["Apache Solr", "Query Optimization", "Performance Tuning"],
                    context="Search queries were taking 5-10 seconds impacting user experience",
                    impact="Improved user satisfaction and enabled real-time search capabilities",
                    display_order=6
                ),

                # Platform Engineering & Scale
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Architected event-driven data platform processing 250GB+ daily workflows with exactly-once guarantees",
                    metric_type="scale",
                    metric_value=250,
                    metric_unit="gigabytes_daily",
                    dimensions=["technical_excellence", "innovation", "ownership"],
                    leadership_principles=["think_big", "deliver_results"],
                    skills_used=["Event-Driven Architecture", "AWS Step Functions", "Data Engineering"],
                    context="Enterprise-scale data platform requirements for financial services",
                    impact="Enabled 20-analyst team capacity and 300% analytical capacity increase",
                    display_order=7
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Built source-agnostic ingestion framework supporting S3, REST API, and Snowflake Marketplace integrations",
                    metric_type="technical_achievement",
                    metric_value=3,
                    metric_unit="integration_types",
                    dimensions=["technical_excellence", "innovation", "flexibility"],
                    leadership_principles=["invent_and_simplify", "think_big"],
                    skills_used=["API Design", "S3", "Snowflake", "Integration Patterns"],
                    context="Need to support multiple data source types without code duplication",
                    impact="Enabled rapid onboarding of new data sources and reduced maintenance burden",
                    display_order=8
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Enabled internal teams to bypass 2.5 years of development through self-service APIs",
                    metric_type="time_savings",
                    metric_value=2.5,
                    metric_unit="years",
                    dimensions=["customer_obsession", "innovation", "leadership"],
                    leadership_principles=["customer_obsession", "think_big"],
                    skills_used=["API Design", "Self-Service Platforms", "Developer Experience"],
                    context="Internal teams needed data access but would have required 2.5 years to build infrastructure",
                    impact="Accelerated time-to-market for multiple teams and products",
                    display_order=9
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Engineered metadata enrichment framework for catalog with 150K+ datasets",
                    metric_type="scale",
                    metric_value=150000,
                    metric_unit="datasets",
                    dimensions=["technical_excellence", "scale", "data_quality"],
                    leadership_principles=["think_big", "deliver_results"],
                    skills_used=["Metadata Management", "Data Cataloging", "Automation"],
                    context="Enterprise data catalog needed automated metadata enrichment at scale",
                    impact="Improved data discoverability and governance across organization",
                    display_order=10
                ),

                # Leadership & Capacity
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Helped 45+ engineers achieve AWS certifications focusing on serverless best practices",
                    metric_type="team_impact",
                    metric_value=45,
                    metric_unit="engineers",
                    dimensions=["leadership", "mentorship", "technical_excellence"],
                    leadership_principles=["hire_and_develop_the_best", "learn_and_be_curious"],
                    skills_used=["AWS", "Serverless", "Mentorship", "Training"],
                    context="Organization push for AWS certification and serverless adoption",
                    impact="Elevated team capabilities and enabled adoption of modern cloud patterns",
                    display_order=11
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Scaled analytical capacity by 300% through custom database architecture",
                    metric_type="capacity_increase",
                    metric_value=300,
                    metric_unit="percentage",
                    dimensions=["technical_excellence", "scale", "innovation"],
                    leadership_principles=["think_big", "deliver_results"],
                    skills_used=["Database Architecture", "SQL", "Performance Optimization"],
                    context="Analyst team constrained by database performance limitations",
                    impact="Enabled 20-analyst team capacity from original 5-6 analysts",
                    display_order=12
                ),

                # Infrastructure & Performance
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Eliminated 15% of redundant processes and reduced processing time by 25% through SQL optimization",
                    metric_type="performance_improvement",
                    metric_value=25,
                    metric_unit="percentage",
                    dimensions=["technical_excellence", "operational_excellence"],
                    leadership_principles=["bias_for_action", "deliver_results"],
                    skills_used=["SQL Optimization", "Performance Analysis", "Process Improvement"],
                    context="Data processing workflows had significant redundancy and inefficiency",
                    impact="Reduced infrastructure costs and improved data freshness",
                    display_order=13
                ),
                AchievementFactCreate(
                    experience_id=experience.id,
                    fact_text="Resolved critical operations issue blocking $1.5M software upgrade",
                    metric_type="business_impact",
                    metric_value=1500000,
                    metric_unit="dollars",
                    dimensions=["ownership", "technical", "problem_solving"],
                    leadership_principles=["ownership", "bias_for_action"],
                    skills_used=["Problem Solving", "System Architecture", "Debugging"],
                    context="Critical production issue preventing major software upgrade",
                    impact="Unblocked strategic initiative and prevented revenue loss",
                    display_order=14
                ),
            ]

            created_count = 0
            for achievement_data in achievements:
                achievement = await achievement_repo.create(achievement_data)
                created_count += 1
                print(f"   ✅ [{created_count}/{len(achievements)}] {achievement.fact_text[:80]}...")

            print(f"\n✅ Successfully created {created_count} achievement facts")
            print(f"\n🎉 Work experience data populated successfully!")
            print(f"   Company ID: {jpmc.id}")
            print(f"   Experience ID: {experience.id}")
            print(f"   Achievements: {created_count} factual statements")

            await session.commit()

        except Exception as e:
            print(f"\n❌ Error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(populate_jpmc_experience())
