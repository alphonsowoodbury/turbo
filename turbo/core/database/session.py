"""Database session management utilities."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.database.connection import get_session_factory


class DatabaseSessionManager:
    """Manages database sessions for the application."""

    def __init__(self) -> None:
        self._session_factory = get_session_factory()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new database session."""
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_session(self) -> AsyncSession:
        """Get a new database session (caller responsible for closing)."""
        return self._session_factory()

    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            async with self.session() as session:
                # Execute a simple query to test connection
                await session.execute("SELECT 1")
                return True
        except Exception:
            return False


# Global session manager instance
_session_manager: DatabaseSessionManager | None = None


def get_session_manager() -> DatabaseSessionManager:
    """Get the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = DatabaseSessionManager()
    return _session_manager
