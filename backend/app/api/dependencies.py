"""
API Dependencies - Request Context & User Authentication Injection
Provides clean dependency injection for FastAPI endpoints without global state.
"""

from fastapi import Header
from app.core.config import settings


def get_current_user_id(x_user_id: str = Header(default=None)) -> str:
    """
    Extracts user_id from the X-User-Id header.
    Defaults to settings.DEFAULT_USER_ID ('user_default') if not provided.
    This guarantees full multi-user readiness while maintaining 100% backward compatibility.
    """
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()
    return settings.DEFAULT_USER_ID
