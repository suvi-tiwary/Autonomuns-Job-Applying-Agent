import os
import asyncio
from typing import Dict, Any, Optional
from application_orchestrator import orchestrate_application
from models import ApplicationStatus, AgentSettings


async def apply_to_job(
    job_url: str,
    candidate_profile: dict = None,
    resume_path: str = None,
    interactive: bool = False,
    job_data: dict = None,
    application_id: int = None,
    settings: AgentSettings = None
) -> dict:
    """
    Automated job application entry point.
    Delegates to the modular application_orchestrator pipeline.
    """
    return await orchestrate_application(
        job_url=job_url,
        candidate_profile=candidate_profile,
        resume_path=resume_path,
        job_data=job_data,
        application_id=application_id,
        settings=settings
    )