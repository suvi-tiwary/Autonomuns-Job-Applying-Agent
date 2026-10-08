"""
Settings API Routes - Agent Preferences and Automation Controls
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
from app.api.dependencies import get_current_user_id
from app.repositories.application_repository import ApplicationRepository
from app.models.application import AgentSettings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/settings", tags=["Settings"])
app_repo = ApplicationRepository()


@router.get("", response_model=Dict[str, Any])
def get_settings(user_id: str = Depends(get_current_user_id)):
    """Fetches user agent configuration settings."""
    settings_obj = app_repo.get_agent_settings(user_id)
    return settings_obj.model_dump()


@router.post("", response_model=Dict[str, Any])
def update_settings(
    payload: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Updates user agent configuration settings."""
    try:
        updated = app_repo.update_agent_settings(user_id, payload)
        return {
            "success": True,
            "message": "Agent settings updated successfully",
            "settings": updated.model_dump(),
        }
    except Exception as e:
        logger.error(f"Error updating agent settings for {user_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
