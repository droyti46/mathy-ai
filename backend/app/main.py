"""FastAPI application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running the module directly via ``python backend/app/main.py`` by
# ensuring that the project root (``backend``) is on ``sys.path`` before any
# package imports occur. Without this, Python cannot resolve the ``app``
# package, leading to ``ModuleNotFoundError: No module named 'app'`` when the
# script is executed outside of ``python -m`` context.
if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import submit, auth, assistant, solve, tasks, themes
from app.bootstrap import build_container, init_db
from app.core.errors import register_handlers
from app.core.logging import setup_logging

app = FastAPI(title="Math Trainer API", version="0.3.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def _startup():
    setup_logging()
    register_handlers(app)
    container = build_container()
    app.state.container = container
    await init_db(container["engine"])  # auto-create tables

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(themes.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(submit.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")
app.include_router(solve.router, prefix="/api")

@app.get("/", tags=["system"])
async def health():
    return {"title": "Мати AI API", "docs": "/docs", "status": "ok"}

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "0.3.3"}