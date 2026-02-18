"""FastAPI application factory."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import chat, filesystem, workflows

app = FastAPI(title="CLAI Web", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(filesystem.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "CLAI Web API", "docs": "/docs"}
