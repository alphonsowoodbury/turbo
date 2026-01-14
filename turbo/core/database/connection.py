"""Database connection and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from turbo.core.database.base import Base
from turbo.utils.config import get_settings

# Global engine instance
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine() -> AsyncEngine:
    """Create and configure the database engine."""
    settings = get_settings()

    # Configure engine based on database type
    if settings.database.url.startswith("sqlite"):
        # SQLite specific configuration
        engine = create_async_engine(
            settings.database.url,
            echo=settings.database.echo,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
            },
        )
    else:
        # PostgreSQL or other databases
        # For Fly.io internal connections, SSL is not needed
        connect_args = {}
        if ".flycast" in settings.database.url or ".internal" in settings.database.url:
            connect_args["ssl"] = False
        engine = create_async_engine(
            settings.database.url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            connect_args=connect_args,
        )

    return engine


def get_engine() -> AsyncEngine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from turbo.core.models import (  # noqa: F401
            Agent,
            AgentSession,
            Blueprint,
            Comment,
            Document,
            Favorite,
            Form,
            FormResponse,
            FormResponseAudit,
            Initiative,
            Issue,
            Literature,
            Milestone,
            PodcastShow,
            PodcastEpisode,
            Project,
            ProjectEntityCounter,
            SavedFilter,
            ScriptRun,
            Tag,
            TerminalSession,
            WorkLog,
        )

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Close database connections."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None

    _session_factory = None


# Context manager for database operations
class DatabaseConnection:
    """Context manager for database operations."""

    def __init__(self) -> None:
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        """Enter async context."""
        session_factory = get_session_factory()
        self.session = session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self.session:
            if exc_type is not None:
                await self.session.rollback()
            await self.session.close()


# Utility function for running database operations
async def run_in_transaction(operation):
    """Run an operation within a database transaction."""
    async with DatabaseConnection() as session:
        try:
            result = await operation(session)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise
