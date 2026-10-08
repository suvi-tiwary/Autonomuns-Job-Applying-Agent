"""
Resume API Routes - Resume Upload, Extraction, and Profile Sync
"""

import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import Dict, Any
from app.api.dependencies import get_current_user_id
from app.services.resume_service import ResumeService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/resume", tags=["Resume"])
resume_service = ResumeService()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """
    Uploads a candidate resume (PDF), extracts structured data using LLM,
    and updates the candidate profile automatically.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resume files are currently supported.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{user_id}_{file.filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted_data, updated_profile = resume_service.parse_and_save_resume(
            user_id=user_id, file_path=file_path
        )

        return {
            "success": True,
            "message": "Resume successfully uploaded and parsed.",
            "extracted": extracted_data,
            "profile": updated_profile.model_dump(),
        }

    except Exception as e:
        logger.error(f"Error processing resume upload for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")
