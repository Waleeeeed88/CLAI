"""Queue-backed SSE event bus.

Background threads call put() to emit events.
FastAPI drains the queue via the async stream() generator.
"""
import asyncio
import json
import queue
import threading
import time
from typing import Any, AsyncGenerator, Dict


class EventBus:
    _SENTINEL = object()  # signals end of stream
    _HEARTBEAT_INTERVAL = 15  # seconds between keep-alive pings

    def __init__(self):
        self._q: queue.Queue = queue.Queue()
        self._cancelled = threading.Event()

    @property
    def is_cancelled(self) -> bool:
        """Check if this run has been cancelled."""
        return self._cancelled.is_set()

    def cancel(self) -> None:
        """Signal cancellation to the background worker thread."""
        self._cancelled.set()

    def put(self, event: Dict[str, Any]) -> None:
        """Called from a background thread to emit an event."""
        self._q.put(event)

    def close(self) -> None:
        """Signal the SSE stream to end."""
        self._q.put(self._SENTINEL)

    async def stream(self) -> AsyncGenerator[str, None]:
        """Async generator consumed by FastAPI StreamingResponse."""
        loop = asyncio.get_running_loop()
        last_event = time.monotonic()

        while True:
            try:
                event = await loop.run_in_executor(
                    None, lambda: self._q.get(timeout=0.25)
                )
            except queue.Empty:
                # Send heartbeat comment to keep connection alive
                if time.monotonic() - last_event > self._HEARTBEAT_INTERVAL:
                    yield ": heartbeat\n\n"
                    last_event = time.monotonic()
                continue

            last_event = time.monotonic()

            if event is self._SENTINEL:
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break

            yield f"data: {json.dumps(event)}\n\n"
