"""
Applications API Routes - Auto-Application Orchestration & Field Trace
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, Optional
from app.api.dependencies import get_current_user_id
from app.repositories.application_repository import ApplicationRepository
from app.agents.application_orchestrator import ApplicationOrchestrator
from app.workers.task_manager import task_manager
from app.models.application import ApplicationSession, ApplicationStatus
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/applications", tags=["Applications"])

app_repo = ApplicationRepository()
orchestrator = ApplicationOrchestrator()


@router.get("", response_model=Dict[str, Any])
def get_user_applications(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
):
    """Retrieves all application sessions for the candidate."""
    apps = app_repo.get_user_applications(user_id=user_id, limit=limit, offset=offset)
    return {
        "success": True,
        "total": len(apps),
        "applications": [a.model_dump() for a in apps],
    }


@router.get("/{application_id}", response_model=Dict[str, Any])
def get_application(
    application_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Retrieves specific application session status and active task progress."""
    app_session = app_repo.get_application(application_id)
    if not app_session:
        raise HTTPException(status_code=404, detail="Application not found")

    live_task = task_manager.get_application_task(application_id)

    return {
        "application": app_session.model_dump(),
        "live_task": live_task,
    }


@router.get("/{application_id}/fields", response_model=Dict[str, Any])
def get_application_fields(
    application_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Retrieves full field trace audit for an application session."""
    fields = app_repo.get_application_fields(application_id)
    return {
        "success": True,
        "application_id": application_id,
        "fields": [f.model_dump() for f in fields],
    }


@router.post("", response_model=Dict[str, Any])
@router.post("/apply", response_model=Dict[str, Any])
def apply_to_job(
    payload: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """
    Initiates an asynchronous autonomous job application task via Playwright.
    """
    job_id = payload.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="Missing required field: job_id")

    # Create application session record
    session = ApplicationSession(
        user_id=user_id,
        job_id=job_id,
        status=ApplicationStatus.QUEUED,
    )
    app_repo.create_application(session)

    # Submit to async task manager
    task_manager.submit_application(
        user_id=user_id,
        application_id=session.id,
        apply_fn=lambda u, a_id, cb: orchestrator.run_application(u, a_id, cb),
    )

    return {
        "success": True,
        "application_id": session.id,
        "status": "QUEUED",
        "message": "Autonomous application task queued in background.",
    }


@router.post("/submit-confirm", response_model=Dict[str, Any])
def confirm_submission(
    payload: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """
    Marks an application as SUBMITTED after human review.
    """
    application_id = payload.get("application_id")
    if not application_id:
        raise HTTPException(status_code=400, detail="Missing application_id")

    app_repo.update_application_status(application_id, ApplicationStatus.SUBMITTED)
    return {"success": True, "message": "Application confirmed as submitted."}
