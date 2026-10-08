"""
Profile API Routes - Candidate Profile Management
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
from app.api.dependencies import get_current_user_id
from app.services.profile_service import ProfileService
from app.repositories.profile_repository import ProfileRepository
from app.models.profile import CandidateProfile
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/profile", tags=["Profile"])
profile_repo = ProfileRepository()
profile_service = ProfileService(profile_repo)


@router.get("", response_model=Dict[str, Any])
def get_profile(user_id: str = Depends(get_current_user_id)):
    """Fetches the persistent candidate profile for the current user."""
    profile = profile_service.get_profile(user_id)
    return profile.model_dump()


@router.post("", response_model=Dict[str, Any])
def update_profile(
    payload: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Updates the persistent candidate profile for the current user."""
    try:
        updated_profile = profile_service.update_profile(user_id, payload)
        return {
            "success": True,
            "message": "Candidate profile updated successfully",
            "profile": updated_profile.model_dump(),
        }
    except Exception as e:
        logger.error(f"Error updating profile for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
