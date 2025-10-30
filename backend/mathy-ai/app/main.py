from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging
from app.core.errors import register_handlers
from app.bootstrap import build_container, init_db
from app.api.routers import themes, tasks, attempts, hints, solve, chat, auth

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
app.include_router(attempts.router, prefix="/api")
app.include_router(hints.router, prefix="/api")
app.include_router(solve.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "0.3.3"}
