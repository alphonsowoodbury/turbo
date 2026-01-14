"""Agent activity tracking service for monitoring AI agents in real-time."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import logging
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from turbo.core.models.agent_session import AgentSession as DBAgentSession, AgentSessionStatus

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent status types."""
    IDLE = "idle"
    STARTING = "starting"
    PROCESSING = "processing"
    TYPING = "typing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentSession:
    """Represents an active AI agent session."""
    session_id: str
    entity_type: str
    entity_id: str
    status: AgentStatus
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    # Metrics
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0

    # Context
    entity_title: Optional[str] = None
    comment_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary with ISO timestamps."""
        data = asdict(self)
        data["started_at"] = self.started_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data


class AgentActivityTracker:
    """Tracks all AI agent activity in real-time."""

    def __init__(self):
        self.active_sessions: Dict[str, AgentSession] = {}
        self.recent_sessions: List[AgentSession] = []
        self.max_recent = 100  # Keep last 100 completed sessions
        self._cleanup_task = None

    async def start(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_sessions())

    async def stop(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_old_sessions(self):
        """Periodically clean up old completed sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Remove sessions older than 1 hour from recent list
                cutoff = datetime.utcnow() - timedelta(hours=1)
                self.recent_sessions = [
                    s for s in self.recent_sessions
                    if s.completed_at and s.completed_at > cutoff
                ]

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup task: {e}")

    def create_session(
        self,
        entity_type: str,
        entity_id: str,
        entity_title: Optional[str] = None,
        comment_count: int = 0
    ) -> str:
        """Create a new agent session and return session ID."""
        session_id = str(uuid4())
        session = AgentSession(
            session_id=session_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=AgentStatus.STARTING,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            entity_title=entity_title,
            comment_count=comment_count
        )

        self.active_sessions[session_id] = session
        return session_id

    def update_status(
        self,
        session_id: str,
        status: AgentStatus,
        error: Optional[str] = None
    ):
        """Update session status."""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        session.status = status
        session.updated_at = datetime.utcnow()

        if error:
            session.error = error

        if status in (AgentStatus.COMPLETED, AgentStatus.ERROR):
            session.completed_at = datetime.utcnow()
            session.duration_seconds = (
                session.completed_at - session.started_at
            ).total_seconds()

    def update_metrics(
        self,
        session_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0
    ):
        """Update session metrics."""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        session.input_tokens = input_tokens
        session.output_tokens = output_tokens
        session.cost_usd = cost_usd
        session.updated_at = datetime.utcnow()

    def complete_session(
        self,
        session_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0
    ):
        """Mark session as completed and move to recent."""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        session.status = AgentStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        session.duration_seconds = (
            session.completed_at - session.started_at
        ).total_seconds()
        session.input_tokens = input_tokens
        session.output_tokens = output_tokens
        session.cost_usd = cost_usd
        session.updated_at = datetime.utcnow()

        # Move to recent sessions
        self.recent_sessions.insert(0, session)
        if len(self.recent_sessions) > self.max_recent:
            self.recent_sessions = self.recent_sessions[:self.max_recent]

        # Remove from active
        del self.active_sessions[session_id]

    async def persist_session(self, session_id: str, db: AsyncSession):
        """Persist session to database."""
        session = self.active_sessions.get(session_id)
        if not session:
            # Check recent sessions
            session = next((s for s in self.recent_sessions if s.session_id == session_id), None)

        if not session:
            logger.warning(f"Session {session_id} not found for persistence")
            return

        try:
            # Create DB model
            db_session = DBAgentSession(
                session_id=session.session_id,
                entity_type=session.entity_type,
                entity_id=session.entity_id,
                entity_title=session.entity_title,
                status=AgentSessionStatus(session.status.value),
                error=session.error,
                input_tokens=session.input_tokens,
                output_tokens=session.output_tokens,
                cost_usd=session.cost_usd,
                duration_seconds=session.duration_seconds,
                comment_count=session.comment_count,
                started_at=session.started_at,
                updated_at=session.updated_at,
                completed_at=session.completed_at,
            )

            db.add(db_session)
            await db.commit()
            logger.info(f"Persisted session {session_id} to database")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to persist session {session_id}: {e}")

    def fail_session(self, session_id: str, error: str):
        """Mark session as failed."""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        session.status = AgentStatus.ERROR
        session.error = error
        session.completed_at = datetime.utcnow()
        session.duration_seconds = (
            session.completed_at - session.started_at
        ).total_seconds()
        session.updated_at = datetime.utcnow()

        # Move to recent sessions
        self.recent_sessions.insert(0, session)
        if len(self.recent_sessions) > self.max_recent:
            self.recent_sessions = self.recent_sessions[:self.max_recent]

        # Remove from active
        del self.active_sessions[session_id]

    async def get_recent_from_db(self, db: AsyncSession, limit: int = 50) -> List[dict]:
        """Get recent sessions from database."""
        try:
            query = (
                select(DBAgentSession)
                .where(DBAgentSession.completed_at.isnot(None))
                .order_by(desc(DBAgentSession.completed_at))
                .limit(limit)
            )

            result = await db.execute(query)
            sessions = result.scalars().all()

            return [session.to_dict() for session in sessions]
        except Exception as e:
            logger.error(f"Failed to get recent sessions from DB: {e}")
            return []

    async def get_stats_from_db(self, db: AsyncSession) -> dict:
        """Get statistics from database."""
        try:
            # Get count of completed sessions in last 24 hours
            cutoff = datetime.utcnow() - timedelta(hours=24)
            query = select(DBAgentSession).where(
                DBAgentSession.completed_at >= cutoff
            )

            result = await db.execute(query)
            recent_sessions = result.scalars().all()

            total_tokens = sum(
                s.input_tokens + s.output_tokens for s in recent_sessions
            )
            total_cost = sum(s.cost_usd for s in recent_sessions)

            completed_sessions = [s for s in recent_sessions if s.duration_seconds > 0]
            avg_duration = (
                sum(s.duration_seconds for s in completed_sessions) / len(completed_sessions)
                if completed_sessions else 0
            )

            return {
                "active_count": len(self.active_sessions),
                "recent_count": len(recent_sessions),
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "avg_duration_seconds": round(avg_duration, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get stats from DB: {e}")
            # Fall back to in-memory stats
            return self.get_stats()

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get session by ID from active sessions."""
        return self.active_sessions.get(session_id)

    def get_all_active(self) -> List[AgentSession]:
        """Get all active sessions."""
        return list(self.active_sessions.values())

    def get_recent(self, limit: int = 50) -> List[AgentSession]:
        """Get recent completed sessions."""
        return self.recent_sessions[:limit]

    def get_stats(self) -> dict:
        """Get overall statistics."""
        active_count = len(self.active_sessions)
        recent_count = len(self.recent_sessions)

        # Calculate totals from recent sessions
        total_tokens = sum(
            s.input_tokens + s.output_tokens for s in self.recent_sessions
        )
        total_cost = sum(s.cost_usd for s in self.recent_sessions)

        # Average response time
        completed_sessions = [s for s in self.recent_sessions if s.duration_seconds > 0]
        avg_duration = (
            sum(s.duration_seconds for s in completed_sessions) / len(completed_sessions)
            if completed_sessions else 0
        )

        return {
            "active_count": active_count,
            "recent_count": recent_count,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_duration_seconds": round(avg_duration, 2)
        }


# Global singleton instance
tracker = AgentActivityTracker()
