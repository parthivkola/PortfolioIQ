"""FastAPI application factory with lifespan management."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import v1_router
from app.core.config import settings
from app.middleware.error_handler import register_error_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.tasks.scheduler import configure_scheduler, scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: configure scheduler, validate connections.
    Shutdown: stop scheduler, close pools.
    """
    logger.info("starting up (env=%s)", settings.app_env)

    configure_scheduler()
    scheduler.start()
    logger.info("scheduler started")

    yield

    scheduler.shutdown(wait=False)
    logger.info("scheduler stopped")

    from app.core.database import engine

    await engine.dispose()
    logger.info("database pool closed")

    from app.core.redis import redis_pool

    await redis_pool.aclose()
    logger.info("redis pool closed")


app = FastAPI(
    title="Portfolio Intelligence Platform",
    description="Investment portfolio tracking and analytics API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware (order matters: outermost runs first)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
register_error_handlers(app)

# Routers
app.include_router(v1_router)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# SPA catch-all: serve index.html for the root path
@app.get("/")
async def serve_spa():
    return FileResponse(str(STATIC_DIR / "index.html"))
