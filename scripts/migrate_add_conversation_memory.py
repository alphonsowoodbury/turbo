#!/usr/bin/env python3
"""
Migration script to add conversation memory and summary tables.

This script safely adds the conversation memory system tables to an existing database.

Usage:
    python scripts/migrate_add_conversation_memory.py --dry-run  # Preview changes
    python scripts/migrate_add_conversation_memory.py            # Apply migration
    python scripts/migrate_add_conversation_memory.py --rollback # Rollback changes
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


async def table_exists(engine: AsyncEngine, table_name: str) -> bool:
    """Check if a table exists in the database."""
    async with engine.connect() as conn:
        result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table(table_name)
        )
        return result


async def check_current_state(engine: AsyncEngine) -> dict:
    """Check current database state."""
    state = {
        "conversation_memories_exists": await table_exists(engine, "conversation_memories"),
        "conversation_summaries_exists": await table_exists(engine, "conversation_summaries"),
    }
    return state


async def apply_migration(engine: AsyncEngine, dry_run: bool = False) -> None:
    """Apply conversation memory tables migration from SQL file."""
    state = await check_current_state(engine)

    print("\n=== Current Database State ===")
    print(f"conversation_memories table exists: {state['conversation_memories_exists']}")
    print(f"conversation_summaries table exists: {state['conversation_summaries_exists']}")

    if state['conversation_memories_exists'] and state['conversation_summaries_exists']:
        print("\n✓ Both conversation memory tables already exist. No migration needed.")
        return

    if dry_run:
        print("\n=== DRY RUN MODE ===")
        print("Would create the following tables:")
        if not state['conversation_memories_exists']:
            print("  - conversation_memories (long-term memory storage)")
        if not state['conversation_summaries_exists']:
            print("  - conversation_summaries (message range summaries)")
        print("\nWould also create:")
        print("  - Indexes for performance (entity lookups, importance, relevance)")
        print("  - Constraints (importance range, relevance range, message range)")
        print("  - Unique constraint on summary ranges")
        print("\nRun without --dry-run to apply changes.")
        return

    print("\n=== Applying Migration ===")

    # Read SQL migration file
    migration_file = project_root / "migrations" / "011_add_conversation_memory_tables.sql"

    if not migration_file.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    try:
        async with engine.begin() as conn:
            print("Executing migration SQL...")

            # Execute the entire SQL as one block
            # PostgreSQL can handle multiple statements in a single execution
            await conn.execute(text(migration_sql))

            print("✓ Executed migration SQL successfully")

        print("\n✓ Migration completed successfully!")

        # Verify
        new_state = await check_current_state(engine)
        print("\n=== New Database State ===")
        print(f"conversation_memories table exists: {new_state['conversation_memories_exists']}")
        print(f"conversation_summaries table exists: {new_state['conversation_summaries_exists']}")

        if new_state['conversation_memories_exists'] and new_state['conversation_summaries_exists']:
            print("\n✅ All conversation memory tables created successfully!")
            print("\n📊 Tables created:")
            print("  - conversation_memories: Long-term memory storage with semantic search")
            print("  - conversation_summaries: Message range summaries for efficient context")
            print("\n🔍 Features enabled:")
            print("  - Semantic memory search using 384-dimensional embeddings")
            print("  - Temporal decay for memory relevance")
            print("  - Automatic conversation summarization")
            print("  - Knowledge graph integration")
        else:
            print("\n⚠️  Warning: Some tables may not have been created correctly")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        raise


async def rollback_migration(engine: AsyncEngine, dry_run: bool = False) -> None:
    """Rollback conversation memory tables (drop them)."""
    state = await check_current_state(engine)

    print("\n=== Current Database State ===")
    print(f"conversation_memories table exists: {state['conversation_memories_exists']}")
    print(f"conversation_summaries table exists: {state['conversation_summaries_exists']}")

    if not state['conversation_memories_exists'] and not state['conversation_summaries_exists']:
        print("\n✓ No conversation memory tables exist. Nothing to rollback.")
        return

    if dry_run:
        print("\n=== DRY RUN MODE ===")
        print("Would drop the following tables:")
        if state['conversation_summaries_exists']:
            print("  - conversation_summaries")
        if state['conversation_memories_exists']:
            print("  - conversation_memories")
        print("\nRun without --dry-run to apply changes.")
        return

    print("\n⚠️  WARNING: This will DELETE all conversation memory and summary data!")
    response = input("Are you sure you want to rollback? Type 'yes' to confirm: ")

    if response.lower() != 'yes':
        print("Rollback cancelled.")
        return

    print("\n=== Applying Rollback ===")

    try:
        async with engine.begin() as conn:
            # Drop tables
            if state['conversation_summaries_exists']:
                print("Dropping conversation_summaries table...")
                await conn.execute(text("DROP TABLE IF EXISTS conversation_summaries CASCADE"))
                print("✓ conversation_summaries table dropped")

            if state['conversation_memories_exists']:
                print("Dropping conversation_memories table...")
                await conn.execute(text("DROP TABLE IF EXISTS conversation_memories CASCADE"))
                print("✓ conversation_memories table dropped")

        print("\n✓ Rollback completed successfully!")

        # Verify
        new_state = await check_current_state(engine)
        print("\n=== New Database State ===")
        print(f"conversation_memories table exists: {new_state['conversation_memories_exists']}")
        print(f"conversation_summaries table exists: {new_state['conversation_summaries_exists']}")

    except Exception as e:
        print(f"\n✗ Rollback failed: {e}")
        raise


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate database to add conversation memory tables"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration (drop conversation memory tables)"
    )

    args = parser.parse_args()

    print("=== Conversation Memory Tables Migration ===")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Migration file: migrations/011_add_conversation_memory_tables.sql")

    engine = get_engine()

    try:
        if args.rollback:
            await rollback_migration(engine, dry_run=args.dry_run)
        else:
            await apply_migration(engine, dry_run=args.dry_run)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
