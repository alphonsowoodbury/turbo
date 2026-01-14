"""Populate Neo4j knowledge graph with resume data.

This script loads deduplicated resume data and populates the Neo4j knowledge graph
with skills, technologies, projects, and their relationships.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from turbo.core.services.knowledge_graph import KnowledgeGraphService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def populate_from_resume_data(data: dict[str, Any], kg: KnowledgeGraphService) -> dict[str, int]:
    """Populate knowledge graph from resume data.

    Args:
        data: Deduplicated resume data dictionary
        kg: KnowledgeGraphService instance

    Returns:
        Statistics about entities created
    """
    stats = {
        "skills_added": 0,
        "projects_added": 0,
        "technologies_added": 0,
        "relationships_added": 0,
    }

    # Add skills to the graph
    logger.info("Adding skills to knowledge graph...")
    skills = data.get("skills", [])
    for skill in skills:
        try:
            # Determine category based on common patterns
            skill_lower = skill.lower()
            category = "technical"

            if any(lang in skill_lower for lang in ["python", "java", "go", "javascript", "typescript"]):
                category = "language"
            elif any(fw in skill_lower for fw in ["framework", "react", "vue", "fastapi", "flask"]):
                category = "framework"
            elif any(tool in skill_lower for tool in ["docker", "kubernetes", "terraform", "git"]):
                category = "tool"
            elif any(db in skill_lower for db in ["sql", "postgres", "mongo", "dynamodb"]):
                category = "database"
            elif any(cloud in skill_lower for cloud in ["aws", "azure", "gcp", "cloud"]):
                category = "cloud"

            skill_id = await kg.add_skill(
                name=skill,
                canonical_name=skill,  # Already deduplicated
                category=category,
            )
            stats["skills_added"] += 1
            logger.debug(f"Added skill: {skill} ({category})")
        except Exception as e:
            logger.warning(f"Failed to add skill '{skill}': {e}")

    logger.info(f"Added {stats['skills_added']} skills")

    # Add projects and their technologies
    logger.info("Adding projects and technology relationships...")
    projects = data.get("projects", [])

    for project in projects:
        project_name = project.get("name", "")
        if not project_name:
            continue

        try:
            technologies = project.get("technologies", [])

            # Create project-technology relationships
            for tech in technologies:
                try:
                    await kg.add_project_technology_relationship(
                        project_name=project_name,
                        technology_name=tech,
                    )
                    stats["relationships_added"] += 1
                    logger.debug(f"Linked project '{project_name}' to technology '{tech}'")
                except Exception as e:
                    logger.warning(f"Failed to link '{project_name}' to '{tech}': {e}")

            stats["projects_added"] += 1
            stats["technologies_added"] += len(technologies)
        except Exception as e:
            logger.warning(f"Failed to process project '{project_name}': {e}")

    logger.info(f"Added {stats['projects_added']} projects with {stats['relationships_added']} relationships")

    # Add experience technologies
    logger.info("Adding experience-based technologies...")
    experiences = data.get("experience", [])

    for exp in experiences:
        company = exp.get("company", "")
        technologies = exp.get("technologies", [])

        for tech in technologies:
            try:
                # Also add as a technology node if it doesn't exist
                await kg.add_skill(
                    name=tech,
                    canonical_name=tech,
                    category="technology",
                )
            except Exception as e:
                logger.debug(f"Technology '{tech}' may already exist: {e}")

    return stats


async def main() -> None:
    """Main entry point for graph population."""
    # Load deduplicated resume data
    data_path = Path("/tmp/smart_dedup.json")

    if not data_path.exists():
        logger.error(f"Resume data not found at {data_path}")
        logger.info("Run the smart deduplication endpoint first:")
        logger.info("  curl -X GET 'http://localhost:8001/api/v1/resumes/aggregate/profile/smart?use_graph=false' > /tmp/smart_dedup.json")
        return

    logger.info(f"Loading resume data from {data_path}")
    with open(data_path) as f:
        resume_data = json.load(f)

    # Check if Neo4j configuration exists
    try:
        from turbo.utils.config import settings

        neo4j_uri = getattr(settings, "NEO4J_URI", None)
        if not neo4j_uri:
            logger.warning("NEO4J_URI not configured in settings")
            logger.info("Using default: bolt://localhost:7687")
    except Exception as e:
        logger.warning(f"Could not load settings: {e}")

    # Initialize knowledge graph service
    logger.info("Connecting to Neo4j...")
    async with KnowledgeGraphService() as kg:
        logger.info("Connected to Neo4j successfully")

        # Populate the graph
        stats = await populate_from_resume_data(resume_data, kg)

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("Knowledge Graph Population Complete")
        logger.info("="*60)
        logger.info(f"Skills added:         {stats['skills_added']}")
        logger.info(f"Projects added:       {stats['projects_added']}")
        logger.info(f"Technologies added:   {stats['technologies_added']}")
        logger.info(f"Relationships added:  {stats['relationships_added']}")
        logger.info("="*60)

        # Test graph functionality
        logger.info("\nTesting graph queries...")

        # Test skill lookup
        test_skills = ["Python", "AWS Lambda", "Docker"]
        for skill in test_skills:
            canonical = await kg.get_canonical_skill_name(skill)
            if canonical:
                logger.info(f"  ✓ Found canonical form for '{skill}': {canonical}")
            else:
                logger.info(f"  ✗ No canonical form found for '{skill}'")

        # Test semantic search
        logger.info("\nTesting semantic search for 'machine learning'...")
        results = await kg.search_entities("machine learning", limit=5)
        if results:
            logger.info(f"  Found {len(results)} related entities:")
            for result in results[:3]:
                logger.info(f"    - {result.get('name')} (score: {result.get('score', 0):.3f})")
        else:
            logger.info("  No results found (vector search may not be available)")


if __name__ == "__main__":
    asyncio.run(main())
