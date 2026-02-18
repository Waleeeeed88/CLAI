"""In-memory session store: session_id → EventBus."""
import uuid
from typing import Dict, Optional
from .event_bus import EventBus


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, EventBus] = {}

    def create_session(self) -> tuple[str, EventBus]:
        session_id = str(uuid.uuid4())
        bus = EventBus()
        self._sessions[session_id] = bus
        return session_id, bus

    def get_bus(self, session_id: str) -> Optional[EventBus]:
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        bus = self._sessions.pop(session_id, None)
        if bus:
            bus.close()


# Module-level singleton
session_manager = SessionManager()
