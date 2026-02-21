"""In-memory session store: session_id -> EventBus with TTL cleanup."""
import threading
import time
import uuid
from typing import Dict, Optional
from .event_bus import EventBus

SESSION_TTL_SECONDS = 3600  # 1 hour


class SessionManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, EventBus] = {}
        self._created_at: Dict[str, float] = {}

    def create_session(self) -> tuple[str, EventBus]:
        session_id = str(uuid.uuid4())
        bus = EventBus()
        with self._lock:
            self._sessions[session_id] = bus
            self._created_at[session_id] = time.monotonic()
        return session_id, bus

    def get_bus(self, session_id: str) -> Optional[EventBus]:
        with self._lock:
            return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        with self._lock:
            bus = self._sessions.pop(session_id, None)
            self._created_at.pop(session_id, None)
        if bus:
            bus.close()

    def cleanup_expired(self) -> int:
        """Remove sessions older than TTL. Returns count of cleaned sessions."""
        now = time.monotonic()
        with self._lock:
            expired = [
                sid for sid, created in self._created_at.items()
                if now - created > SESSION_TTL_SECONDS
            ]
        for sid in expired:
            self.close_session(sid)
        return len(expired)


# Module-level singleton
session_manager = SessionManager()
