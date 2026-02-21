"""FastAPI application factory."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import chat, config, filesystem, workflows
from .services.session_manager import session_manager

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run session cleanup in the background while the app is alive."""
    async def _cleanup_loop():
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            try:
                count = session_manager.cleanup_expired()
                if count:
                    logger.info("Cleaned up %d expired sessions", count)
            except Exception:
                logger.exception("Session cleanup error")

    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


app = FastAPI(title="CLAI Web", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(filesystem.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "CLAI Web API", "docs": "/docs"}
