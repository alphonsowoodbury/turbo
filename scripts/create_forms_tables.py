#!/usr/bin/env python3
"""
Script to create the forms-related database tables.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from turbo.core.database.connection import init_database


async def create_tables():
    """Create all database tables including forms tables."""
    print("Creating database tables...")
    await init_database()
    print("\n✓ Successfully created all database tables!")
    print("  Including:")
    print("  - forms")
    print("  - form_responses")
    print("  - form_response_audit")


if __name__ == "__main__":
    asyncio.run(create_tables())
