"""Smart deduplication service using fuzzy matching and semantic similarity."""

import logging
from typing import Any, Optional

from rapidfuzz import fuzz, process

# Optional knowledge graph import
try:
    from turbo.core.services.knowledge_graph import KnowledgeGraphService
except ImportError:
    KnowledgeGraphService = None  # type: ignore

logger = logging.getLogger(__name__)


class ResumeDeduplicatorService:
    """Smart deduplication using fuzzy matching and semantic similarity."""

    def __init__(self, kg_service: Optional[Any] = None):
        """Initialize deduplication service.

        Args:
            kg_service: Optional knowledge graph service for graph-based deduplication
        """
        self.embedder = None
        self.kg_service = kg_service
        self._load_embedder()

    def _load_embedder(self) -> None:
        """Load sentence transformer model for semantic similarity."""
        try:
            from sentence_transformers import SentenceTransformer

            # Load lightweight 22MB model
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence transformer model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"Failed to load embedder: {e}. Falling back to fuzzy matching only.")
            self.embedder = None

    async def deduplicate_skills_with_graph(
        self, skills: list[str], threshold: int = 90, use_graph: bool = True
    ) -> list[str]:
        """Deduplicate skills using fuzzy matching and optional graph relationships.

        Args:
            skills: List of skill strings
            threshold: Similarity threshold (0-100)
            use_graph: Whether to use knowledge graph for semantic matching

        Returns:
            Deduplicated list of skills
        """
        if not skills:
            return []

        # Normalize AWS service names
        normalized_skills = []
        for skill in skills:
            normalized = self._normalize_aws_skill(skill)
            normalized_skills.append((skill, normalized))

        # If graph available, check for existing skill nodes
        skill_canonical_map = {}
        if use_graph and self.kg_service:
            for original, normalized in normalized_skills:
                # Query graph for similar skills using vector similarity
                try:
                    related = await self.kg_service.find_related_entities(
                        entity_id=normalized,
                        entity_type="skill",
                        limit=1,
                    )
                    if related:
                        # Use canonical form from graph
                        skill_canonical_map[normalized.lower()] = related[0].get(
                            "name", normalized
                        )
                except Exception as e:
                    logger.debug(f"Graph lookup failed for {normalized}: {e}")

        # Group similar skills
        unique_skills = []
        seen_normalized = set()

        for original, normalized in normalized_skills:
            # Check canonical mapping from graph
            canonical = skill_canonical_map.get(normalized.lower(), normalized)

            # Check if we've seen this canonical form
            if canonical.lower() in seen_normalized:
                continue

            # Check fuzzy match against existing unique skills
            matches = process.extract(
                canonical,
                [s for _, s in unique_skills],
                scorer=fuzz.token_sort_ratio,
                limit=1,
            )

            if matches and matches[0][1] >= threshold:
                # Similar to existing skill, skip
                continue

            unique_skills.append((original, canonical))
            seen_normalized.add(canonical.lower())

        return [original for original, _ in unique_skills]

    def deduplicate_skills(
        self, skills: list[str], threshold: int = 90
    ) -> list[str]:
        """Deduplicate skills using fuzzy matching (sync version).

        Args:
            skills: List of skill strings
            threshold: Similarity threshold (0-100)

        Returns:
            Deduplicated list of skills
        """
        if not skills:
            return []

        # Normalize AWS service names
        normalized_skills = []
        for skill in skills:
            normalized = self._normalize_aws_skill(skill)
            normalized_skills.append((skill, normalized))

        # Group similar skills
        unique_skills = []
        seen_normalized = set()

        for original, normalized in normalized_skills:
            # Check if we've seen this normalized form
            if normalized.lower() in seen_normalized:
                continue

            # Check fuzzy match against existing unique skills
            matches = process.extract(
                normalized,
                [s for _, s in unique_skills],
                scorer=fuzz.token_sort_ratio,
                limit=1,
            )

            if matches and matches[0][1] >= threshold:
                # Similar to existing skill, skip
                continue

            unique_skills.append((original, normalized))
            seen_normalized.add(normalized.lower())

        return [original for original, _ in unique_skills]

    def _normalize_aws_skill(self, skill: str) -> str:
        """Normalize AWS service names.

        Args:
            skill: Skill name

        Returns:
            Normalized skill name
        """
        skill_lower = skill.lower().strip()

        # AWS service mappings
        aws_services = {
            "lambda": "AWS Lambda",
            "s3": "AWS S3",
            "ec2": "AWS EC2",
            "ecs": "AWS ECS",
            "eks": "AWS EKS",
            "dynamodb": "AWS DynamoDB",
            "step functions": "AWS Step Functions",
            "api gateway": "AWS API Gateway",
            "cloudwatch": "AWS CloudWatch",
            "glue": "AWS Glue",
            "sqs": "AWS SQS",
            "sns": "AWS SNS",
            "eventbridge": "AWS EventBridge",
            "cloudformation": "AWS CloudFormation",
        }

        # Check if it's an AWS service without prefix
        for service_key, full_name in aws_services.items():
            if skill_lower == service_key or skill_lower == f"aws {service_key}":
                return full_name

        # Normalize "Infrastructure as Code" variations
        if "infrastructure" in skill_lower and "code" in skill_lower:
            return "Infrastructure as Code (IaC)"

        # Normalize CI/CD variations
        if "ci/cd" in skill_lower or "cicd" in skill_lower:
            return "CI/CD"

        return skill

    def deduplicate_certifications(
        self, certifications: list[str], threshold: int = 85
    ) -> list[str]:
        """Deduplicate certifications using fuzzy matching.

        Args:
            certifications: List of certification strings
            threshold: Similarity threshold (0-100)

        Returns:
            Deduplicated list of certifications
        """
        if not certifications:
            return []

        unique_certs = []

        for cert in certifications:
            # Normalize certification names
            normalized = cert.strip()

            # AWS certification normalization
            if "aws" in normalized.lower():
                if "solutions architect" in normalized.lower() and "associate" in normalized.lower():
                    normalized = "AWS Certified Solutions Architect - Associate"
                elif "developer" in normalized.lower() and "associate" in normalized.lower():
                    normalized = "AWS Certified Developer - Associate"

            # Check fuzzy match
            if unique_certs:
                matches = process.extract(
                    normalized,
                    unique_certs,
                    scorer=fuzz.token_sort_ratio,
                    limit=1,
                )
                if matches and matches[0][1] >= threshold:
                    continue

            unique_certs.append(normalized)

        return unique_certs

    def deduplicate_experiences(
        self, experiences: list[dict[str, Any]], threshold: float = 0.8
    ) -> list[dict[str, Any]]:
        """Deduplicate experiences using title/company matching and description similarity.

        Args:
            experiences: List of experience dicts
            threshold: Similarity threshold for descriptions (0-1)

        Returns:
            Deduplicated list of experiences
        """
        if not experiences:
            return []

        unique_experiences = []

        for exp in experiences:
            company = exp.get("company", "").lower().strip()
            title = exp.get("title", "").lower().strip()
            start_date = exp.get("start_date", "").strip()
            description = exp.get("description", "")

            # Check for exact company+title+date match
            is_duplicate = False
            for unique_exp in unique_experiences:
                unique_company = unique_exp.get("company", "").lower().strip()
                unique_title = unique_exp.get("title", "").lower().strip()
                unique_start = unique_exp.get("start_date", "").strip()

                # Same company and similar title
                if company == unique_company and fuzz.ratio(title, unique_title) >= 85:
                    # Check if dates match or overlap
                    if start_date == unique_start:
                        # Merge descriptions (keep longer one)
                        if len(description) > len(unique_exp.get("description", "")):
                            unique_exp["description"] = description
                            # Merge technologies
                            unique_tech = set(unique_exp.get("technologies", []))
                            new_tech = set(exp.get("technologies", []))
                            unique_exp["technologies"] = list(unique_tech | new_tech)
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_experiences.append(exp)

        return unique_experiences

    async def deduplicate_projects_with_graph(
        self,
        projects: list[dict[str, Any]],
        threshold: int = 80,
        use_semantic: bool = True,
    ) -> list[dict[str, Any]]:
        """Deduplicate projects using fuzzy matching, tech overlap, and semantic similarity.

        Args:
            projects: List of project dicts
            threshold: Fuzzy matching threshold (0-100)
            use_semantic: Whether to use semantic similarity from embeddings

        Returns:
            Deduplicated list of projects
        """
        if not projects:
            return []

        # Generate embeddings for descriptions if semantic matching enabled
        embeddings_map = {}
        if use_semantic and self.embedder:
            for i, project in enumerate(projects):
                desc = project.get("description", "")
                if desc:
                    try:
                        embeddings_map[i] = self.embedder.encode(desc)
                    except Exception as e:
                        logger.debug(f"Failed to embed project {i}: {e}")

        unique_projects = []

        for i, project in enumerate(projects):
            name = project.get("name", "").strip()
            technologies = set(project.get("technologies", []))
            current_embedding = embeddings_map.get(i)

            # Check fuzzy match on name
            is_duplicate = False
            for j, unique_proj in enumerate(unique_projects):
                unique_name = unique_proj.get("name", "").strip()
                unique_tech = set(unique_proj.get("technologies", []))

                # Check name similarity
                name_similarity = fuzz.token_sort_ratio(name, unique_name)

                # Check technology overlap (Jaccard similarity)
                if technologies and unique_tech:
                    tech_overlap = len(technologies & unique_tech) / len(
                        technologies | unique_tech
                    )
                else:
                    tech_overlap = 0

                # Check semantic similarity of descriptions
                semantic_similarity = 0.0
                if current_embedding is not None:
                    unique_embedding = embeddings_map.get(
                        projects.index(unique_proj)
                        if unique_proj in projects
                        else None
                    )
                    if unique_embedding is not None:
                        # Cosine similarity
                        import numpy as np

                        semantic_similarity = float(
                            np.dot(current_embedding, unique_embedding)
                            / (
                                np.linalg.norm(current_embedding)
                                * np.linalg.norm(unique_embedding)
                            )
                        )

                # Duplicate if:
                # 1. High name similarity (>= threshold)
                # 2. Moderate name similarity (>= 60) + high tech overlap (>= 0.7)
                # 3. High semantic similarity (>= 0.85) + some name/tech overlap
                if (
                    name_similarity >= threshold
                    or (name_similarity >= 60 and tech_overlap >= 0.7)
                    or (
                        semantic_similarity >= 0.85
                        and (name_similarity >= 50 or tech_overlap >= 0.5)
                    )
                ):
                    # Merge descriptions (keep longer one)
                    current_desc = project.get("description", "")
                    unique_desc = unique_proj.get("description", "")
                    if len(current_desc) > len(unique_desc):
                        unique_proj["description"] = current_desc

                    # Merge technologies
                    unique_proj["technologies"] = list(unique_tech | technologies)

                    # Prefer non-null dates
                    if project.get("date") and not unique_proj.get("date"):
                        unique_proj["date"] = project["date"]
                    if project.get("url") and not unique_proj.get("url"):
                        unique_proj["url"] = project["url"]

                    logger.debug(
                        f"Merged project '{name}' into '{unique_name}' "
                        f"(name: {name_similarity}%, tech: {tech_overlap:.2f}, "
                        f"semantic: {semantic_similarity:.2f})"
                    )

                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_projects.append(project)

        return unique_projects

    def deduplicate_projects(
        self, projects: list[dict[str, Any]], threshold: int = 80
    ) -> list[dict[str, Any]]:
        """Deduplicate projects using fuzzy name matching and technology overlap.

        Args:
            projects: List of project dicts
            threshold: Fuzzy matching threshold (0-100)

        Returns:
            Deduplicated list of projects
        """
        if not projects:
            return []

        unique_projects = []

        for project in projects:
            name = project.get("name", "").strip()
            technologies = set(project.get("technologies", []))

            # Check fuzzy match on name
            is_duplicate = False
            for unique_proj in unique_projects:
                unique_name = unique_proj.get("name", "").strip()
                unique_tech = set(unique_proj.get("technologies", []))

                # Check name similarity
                name_similarity = fuzz.token_sort_ratio(name, unique_name)

                # Check technology overlap
                if technologies and unique_tech:
                    tech_overlap = len(technologies & unique_tech) / len(
                        technologies | unique_tech
                    )
                else:
                    tech_overlap = 0

                # Duplicate if high name similarity OR high tech overlap
                if name_similarity >= threshold or (
                    name_similarity >= 60 and tech_overlap >= 0.7
                ):
                    # Merge descriptions (keep longer one)
                    current_desc = project.get("description", "")
                    unique_desc = unique_proj.get("description", "")
                    if len(current_desc) > len(unique_desc):
                        unique_proj["description"] = current_desc

                    # Merge technologies
                    unique_proj["technologies"] = list(unique_tech | technologies)

                    # Prefer non-null dates
                    if project.get("date") and not unique_proj.get("date"):
                        unique_proj["date"] = project["date"]
                    if project.get("url") and not unique_proj.get("url"):
                        unique_proj["url"] = project["url"]

                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_projects.append(project)

        return unique_projects

    async def smart_deduplicate_async(
        self, aggregated_data: dict[str, Any], use_graph: bool = True
    ) -> dict[str, Any]:
        """Apply smart deduplication with graph support to all aggregated resume data.

        Args:
            aggregated_data: Aggregated resume data
            use_graph: Whether to use knowledge graph for enhanced deduplication

        Returns:
            Smart-deduplicated data
        """
        logger.info(
            f"Starting smart deduplication... (graph_enabled={use_graph and self.kg_service is not None})"
        )

        # Deduplicate skills
        if aggregated_data.get("skills"):
            original_count = len(aggregated_data["skills"])
            if use_graph and self.kg_service:
                aggregated_data["skills"] = await self.deduplicate_skills_with_graph(
                    aggregated_data["skills"]
                )
            else:
                aggregated_data["skills"] = self.deduplicate_skills(
                    aggregated_data["skills"]
                )
            deduped_count = len(aggregated_data["skills"])
            logger.info(
                f"Skills: {original_count} → {deduped_count} "
                f"({original_count - deduped_count} removed)"
            )

        # Deduplicate certifications
        if aggregated_data.get("certifications"):
            original_count = len(aggregated_data["certifications"])
            aggregated_data["certifications"] = self.deduplicate_certifications(
                aggregated_data["certifications"]
            )
            deduped_count = len(aggregated_data["certifications"])
            logger.info(
                f"Certifications: {original_count} → {deduped_count} "
                f"({original_count - deduped_count} removed)"
            )

        # Deduplicate experiences
        if aggregated_data.get("experience"):
            original_count = len(aggregated_data["experience"])
            aggregated_data["experience"] = self.deduplicate_experiences(
                aggregated_data["experience"]
            )
            deduped_count = len(aggregated_data["experience"])
            logger.info(
                f"Experience: {original_count} → {deduped_count} "
                f"({original_count - deduped_count} removed)"
            )

        # Deduplicate projects (with semantic similarity if embedder available)
        if aggregated_data.get("projects"):
            original_count = len(aggregated_data["projects"])
            aggregated_data["projects"] = await self.deduplicate_projects_with_graph(
                aggregated_data["projects"], use_semantic=self.embedder is not None
            )
            deduped_count = len(aggregated_data["projects"])
            logger.info(
                f"Projects: {original_count} → {deduped_count} "
                f"({original_count - deduped_count} removed)"
            )

        # Update metadata
        if "metadata" in aggregated_data:
            aggregated_data["metadata"]["deduplication_applied"] = True
            aggregated_data["metadata"]["deduplication_method"] = (
                "graph_enhanced" if (use_graph and self.kg_service) else "fuzzy_only"
            )
            aggregated_data["metadata"]["embeddings_used"] = self.embedder is not None
            aggregated_data["metadata"]["stats"] = {
                "total_experience_count": len(aggregated_data.get("experience", [])),
                "total_education_count": len(aggregated_data.get("education", [])),
                "total_skills_count": len(aggregated_data.get("skills", [])),
                "total_projects_count": len(aggregated_data.get("projects", [])),
                "total_certifications_count": len(
                    aggregated_data.get("certifications", [])
                ),
            }

        logger.info("Smart deduplication completed")
        return aggregated_data

    def smart_deduplicate(self, aggregated_data: dict[str, Any]) -> dict[str, Any]:
        """Apply smart deduplication to all aggregated resume data (sync version).

        Args:
            aggregated_data: Aggregated resume data

        Returns:
            Smart-deduplicated data
        """
        logger.info("Starting smart deduplication...")

        # Deduplicate skills
        if aggregated_data.get("skills"):
            original_count = len(aggregated_data["skills"])
            aggregated_data["skills"] = self.deduplicate_skills(
                aggregated_data["skills"]
            )
            deduped_count = len(aggregated_data["skills"])
            logger.info(
                f"Skills: {original_count} → {deduped_count} "
                f"({original_count - deduped_count} removed)"
            )

        # Deduplicate certifications
        if aggregated_data.get("certifications"):
            original_count = len(aggregated_data["certifications"])
            aggregated_data["certifications"] = self.deduplicate_certifications(
                aggregated_data["certifications"]
            )
            deduped_count = len(aggregated_data["certifications"])
            logger.info(
                f"Certifications: {original_count} → {deduped_count} "
                f"({original_count - deduped_count} removed)"
            )

        # Deduplicate experiences
        if aggregated_data.get("experience"):
            original_count = len(aggregated_data["experience"])
            aggregated_data["experience"] = self.deduplicate_experiences(
                aggregated_data["experience"]
            )
            deduped_count = len(aggregated_data["experience"])
            logger.info(
                f"Experience: {original_count} → {deduped_count} "
                f"({original_count - deduped_count} removed)"
            )

        # Deduplicate projects
        if aggregated_data.get("projects"):
            original_count = len(aggregated_data["projects"])
            aggregated_data["projects"] = self.deduplicate_projects(
                aggregated_data["projects"]
            )
            deduped_count = len(aggregated_data["projects"])
            logger.info(
                f"Projects: {original_count} → {deduped_count} "
                f"({original_count - deduped_count} removed)"
            )

        # Update metadata
        if "metadata" in aggregated_data:
            aggregated_data["metadata"]["deduplication_applied"] = True
            aggregated_data["metadata"]["stats"] = {
                "total_experience_count": len(aggregated_data.get("experience", [])),
                "total_education_count": len(aggregated_data.get("education", [])),
                "total_skills_count": len(aggregated_data.get("skills", [])),
                "total_projects_count": len(aggregated_data.get("projects", [])),
                "total_certifications_count": len(
                    aggregated_data.get("certifications", [])
                ),
            }

        logger.info("Smart deduplication completed")
        return aggregated_data
