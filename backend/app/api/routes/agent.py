"""
Agent API Routes - Health, Capabilities, and Global System Status
"""

from fastapi import APIRouter
from typing import Dict, Any
from app.core.config import settings

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.get("/status", response_model=Dict[str, Any])
def get_agent_status():
    """Returns agent platform runtime status and configured capabilities."""
    return {
        "status": "ONLINE",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_configured": bool(settings.GROQ_API_KEY),
        "tavily_configured": bool(settings.TAVILY_API_KEY),
        "database": "SQLite WAL Multi-User",
        "browser_engine": "Playwright Chromium",
    }
