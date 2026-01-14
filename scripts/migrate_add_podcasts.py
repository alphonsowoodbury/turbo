#!/usr/bin/env python3
"""
Migration script to add podcast_shows and podcast_episodes tables.

This script safely adds the podcast tables to an existing database.

Usage:
    python scripts/migrate_add_podcasts.py --dry-run  # Preview changes
    python scripts/migrate_add_podcasts.py            # Apply migration
    python scripts/migrate_add_podcasts.py --rollback # Rollback changes
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from turbo.core.database.connection import get_engine
from turbo.core.models.base import Base
from turbo.core.models.podcast import PodcastShow, PodcastEpisode


async def table_exists(engine: AsyncEngine, table_name: str) -> bool:
    """Check if a table exists in the database."""
    async with engine.connect() as conn:
        # Use SQLAlchemy inspector for database-agnostic check
        result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table(table_name)
        )
        return result


async def check_current_state(engine: AsyncEngine) -> dict:
    """Check current database state."""
    state = {
        "podcast_shows_exists": await table_exists(engine, "podcast_shows"),
        "podcast_episodes_exists": await table_exists(engine, "podcast_episodes"),
    }
    return state


async def create_podcast_tables(engine: AsyncEngine, dry_run: bool = False) -> None:
    """Create podcast tables."""
    state = await check_current_state(engine)

    print("\n=== Current Database State ===")
    print(f"podcast_shows table exists: {state['podcast_shows_exists']}")
    print(f"podcast_episodes table exists: {state['podcast_episodes_exists']}")

    if state['podcast_shows_exists'] and state['podcast_episodes_exists']:
        print("\n✓ Both podcast tables already exist. No migration needed.")
        return

    if dry_run:
        print("\n=== DRY RUN MODE ===")
        print("Would create the following tables:")
        if not state['podcast_shows_exists']:
            print("  - podcast_shows")
        if not state['podcast_episodes_exists']:
            print("  - podcast_episodes")
        print("\nRun without --dry-run to apply changes.")
        return

    print("\n=== Applying Migration ===")

    try:
        async with engine.begin() as conn:
            # Create only the podcast tables
            if not state['podcast_shows_exists']:
                print("Creating podcast_shows table...")
                await conn.run_sync(PodcastShow.__table__.create, checkfirst=True)
                print("✓ podcast_shows table created")

            if not state['podcast_episodes_exists']:
                print("Creating podcast_episodes table...")
                await conn.run_sync(PodcastEpisode.__table__.create, checkfirst=True)
                print("✓ podcast_episodes table created")

        print("\n✓ Migration completed successfully!")

        # Verify
        new_state = await check_current_state(engine)
        print("\n=== New Database State ===")
        print(f"podcast_shows table exists: {new_state['podcast_shows_exists']}")
        print(f"podcast_episodes table exists: {new_state['podcast_episodes_exists']}")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        raise


async def rollback_podcast_tables(engine: AsyncEngine, dry_run: bool = False) -> None:
    """Rollback podcast tables (drop them)."""
    state = await check_current_state(engine)

    print("\n=== Current Database State ===")
    print(f"podcast_shows table exists: {state['podcast_shows_exists']}")
    print(f"podcast_episodes table exists: {state['podcast_episodes_exists']}")

    if not state['podcast_shows_exists'] and not state['podcast_episodes_exists']:
        print("\n✓ No podcast tables exist. Nothing to rollback.")
        return

    if dry_run:
        print("\n=== DRY RUN MODE ===")
        print("Would drop the following tables:")
        if state['podcast_episodes_exists']:
            print("  - podcast_episodes (child table, dropped first)")
        if state['podcast_shows_exists']:
            print("  - podcast_shows")
        print("\nRun without --dry-run to apply changes.")
        return

    print("\n⚠️  WARNING: This will DELETE all podcast data!")
    response = input("Are you sure you want to rollback? Type 'yes' to confirm: ")

    if response.lower() != 'yes':
        print("Rollback cancelled.")
        return

    print("\n=== Applying Rollback ===")

    try:
        async with engine.begin() as conn:
            # Drop child table first (foreign key constraint)
            if state['podcast_episodes_exists']:
                print("Dropping podcast_episodes table...")
                await conn.run_sync(PodcastEpisode.__table__.drop, checkfirst=True)
                print("✓ podcast_episodes table dropped")

            if state['podcast_shows_exists']:
                print("Dropping podcast_shows table...")
                await conn.run_sync(PodcastShow.__table__.drop, checkfirst=True)
                print("✓ podcast_shows table dropped")

        print("\n✓ Rollback completed successfully!")

        # Verify
        new_state = await check_current_state(engine)
        print("\n=== New Database State ===")
        print(f"podcast_shows table exists: {new_state['podcast_shows_exists']}")
        print(f"podcast_episodes table exists: {new_state['podcast_episodes_exists']}")

    except Exception as e:
        print(f"\n✗ Rollback failed: {e}")
        raise


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate database to add podcast tables"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration (drop podcast tables)"
    )

    args = parser.parse_args()

    print("=== Podcast Tables Migration ===")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    engine = get_engine()

    try:
        if args.rollback:
            await rollback_podcast_tables(engine, dry_run=args.dry_run)
        else:
            await create_podcast_tables(engine, dry_run=args.dry_run)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())