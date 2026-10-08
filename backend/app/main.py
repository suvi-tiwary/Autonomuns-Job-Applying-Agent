"""
JobMate AI - Autonomous Job Application Platform Backend
FastAPI Modular Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import get_logger
from app.api.routes.profile import router as profile_router
from app.api.routes.resume import router as resume_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.applications import router as applications_router
from app.api.routes.settings import router as settings_router
from app.api.routes.agent import router as agent_router

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: initialize database tables and verify configuration."""
    logger.info("Starting JobMate AI Backend...")
    init_db()
    logger.info("Database schema and indexes initialized.")
    yield
    logger.info("JobMate AI Backend shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers with /api prefix
app.include_router(profile_router, prefix="/api")
app.include_router(resume_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(agent_router, prefix="/api")

# Backward Compatibility routes directly at root
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(settings_router)
app.include_router(agent_router)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
