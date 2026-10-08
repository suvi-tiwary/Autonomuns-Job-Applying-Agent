"""
Jobs API Routes - Asynchronous Job Search, Task Status Polling, and Job Listings
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List, Optional
from app.api.dependencies import get_current_user_id
from app.services.job_search_service import JobSearchService
from app.repositories.job_repository import JobRepository
from app.repositories.profile_repository import ProfileRepository
from app.workers.task_manager import task_manager
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs"])

job_repo = JobRepository()
profile_repo = ProfileRepository()
job_search_service = JobSearchService()


@router.post("/search", response_model=Dict[str, Any])
def search_jobs(
    payload: Dict[str, Any] = Body(default={}),
    user_id: str = Depends(get_current_user_id),
):
    """
    Initiates an asynchronous, multi-source job search and ranking task.
    Returns immediately with a task_id for polling.
    """
    query = payload.get("query", "")
    target_roles = payload.get("target_roles", [])
    max_results = payload.get("max_results", 12)

    task_id = task_manager.submit_job_search(
        user_id=user_id,
        query=query,
        target_roles=target_roles,
        search_fn=lambda u, q, r, cb: job_search_service.execute_search_and_rank(
            user_id=u, query=q, target_roles=r, max_results=max_results, progress_callback=cb
        ),
    )

    return {
        "success": True,
        "task_id": task_id,
        "message": "Job discovery task queued in background.",
    }


@router.get("/search/{task_id}", response_model=Dict[str, Any])
def get_search_task_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Polls the progress, stage, and completion status of a background job search task.
    """
    task = task_manager.get_search_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Search task not found")

    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": task.progress,
        "stage": task.stage,
        "message": task.message,
        "total_found": task.total_found,
        "error": task.error,
    }


@router.get("", response_model=Dict[str, Any])
def get_user_jobs(
    limit: int = 50,
    offset: int = 0,
    tier: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    Retrieves the matched and scored jobs for the current candidate.
    """
    jobs = job_repo.get_user_jobs(user_id=user_id, limit=limit, offset=offset)
    if tier:
        jobs = [j for j in jobs if j.company_tier == tier.upper()]

    return {
        "success": True,
        "total": len(jobs),
        "jobs": [j.model_dump() for j in jobs],
    }


@router.delete("", response_model=Dict[str, Any])
def clear_user_jobs(user_id: str = Depends(get_current_user_id)):
    """Clears matched jobs for the current user."""
    job_repo.clear_user_jobs(user_id)
    return {"success": True, "message": "User job recommendations cleared"}
