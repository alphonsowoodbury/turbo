#!/usr/bin/env python3
"""
Fix markdown descriptions by reconstructing newlines based on markdown patterns.

This script attempts to restore readability to descriptions that had newlines stripped
by intelligently adding them back based on common markdown patterns.
"""

import asyncio
import re
from uuid import UUID

from turbo.core.database.connection import get_db_session
from turbo.core.repositories import (
    IssueRepository,
    ProjectRepository,
    MilestoneRepository,
    InitiativeRepository,
)
from turbo.core.repositories.literature import LiteratureRepository


def reconstruct_markdown_newlines(text: str) -> str:
    """
    Reconstruct newlines in markdown text based on common patterns.

    This is heuristic-based and won't be perfect, but should restore
    most of the readability.
    """
    if not text or '\n' in text:
        # Already has newlines or is empty
        return text

    # Add newlines before headers
    text = re.sub(r'(#{1,6}\s)', r'\n\n\1', text)

    # Add newlines after headers (look for end of header line)
    text = re.sub(r'(#{1,6}[^#\n]+?)(\s+)(#{1,6}|\*\*|__|`|[-*]|\d+\.|\w)', r'\1\n\n\3', text)

    # Add newlines before list items (-, *, 1., 2., etc)
    text = re.sub(r'([.!?])\s+([-*]|\d+\.)\s+', r'\1\n\n\2 ', text)

    # Add newlines before bold sections if they follow a sentence
    text = re.sub(r'([.!?])\s+(\*\*)', r'\1\n\n\2', text)

    # Add newlines around code blocks
    text = re.sub(r'```', r'\n```\n', text)

    # Add newlines around horizontal rules
    text = re.sub(r'(---+|\*\*\*+|___+)', r'\n\1\n', text)

    # Clean up excessive newlines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Clean up leading/trailing whitespace
    text = text.strip()

    return text


async def fix_entity_descriptions(
    entity_name: str,
    repository_class,
    session
) -> tuple[int, int]:
    """
    Fix descriptions for a specific entity type.

    Returns:
        Tuple of (total_count, fixed_count)
    """
    repo = repository_class(session)
    entities = await repo.get_all()

    total_count = 0
    fixed_count = 0

    for entity in entities:
        if not hasattr(entity, 'description'):
            continue

        total_count += 1
        description = entity.description

        # Check if description needs fixing (has no newlines but looks like markdown)
        if description and '\n' not in description and (
            '##' in description or
            '**' in description or
            re.search(r'[-*]\s+\w', description) or
            re.search(r'\d+\.\s+\w', description)
        ):
            # Reconstruct newlines
            fixed_description = reconstruct_markdown_newlines(description)

            if fixed_description != description:
                entity.description = fixed_description
                fixed_count += 1
                print(f"  ✓ Fixed {entity_name}: {getattr(entity, 'title', getattr(entity, 'name', entity.id))}")

    if fixed_count > 0:
        await session.commit()

    return total_count, fixed_count


async def main():
    """Fix all markdown descriptions across all entities."""
    print("🔧 Fixing markdown descriptions across all entities...\n")

    entities_to_fix = [
        ("Issues", IssueRepository),
        ("Projects", ProjectRepository),
        ("Milestones", MilestoneRepository),
        ("Initiatives", InitiativeRepository),
        ("Literature", LiteratureRepository),
    ]

    total_entities = 0
    total_fixed = 0

    async for session in get_db_session():
        for entity_name, repo_class in entities_to_fix:
            print(f"Processing {entity_name}...")
            count, fixed = await fix_entity_descriptions(entity_name, repo_class, session)
            total_entities += count
            total_fixed += fixed
            print(f"  {entity_name}: {fixed}/{count} fixed\n")

    print("=" * 60)
    print(f"✓ Complete!")
    print(f"  Total entities processed: {total_entities}")
    print(f"  Total descriptions fixed: {total_fixed}")
    print("=" * 60)

    if total_fixed > 0:
        print("\n⚠️  Note: The fixes are heuristic-based and may not be perfect.")
        print("   Please review critical descriptions manually.")


if __name__ == "__main__":
    asyncio.run(main())
