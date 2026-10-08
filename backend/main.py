import asyncio
import os
import shutil
import sys
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )

import db
from models import ApplicationStatus, AgentSettings, CandidateProfile
from profile_service import (
    normalize_to_candidate_profile,
    candidate_profile_to_legacy_dict,
    populate_from_resume_extraction,
    save_candidate_profile_to_db,
    get_active_candidate_profile_from_db
)
from resume_parser import (
    extract_pdf_text,
    structure_resume
)
from job_searcher import search_jobs
from job_matcher import rank_jobs

# Initialize database schema
db.init_db()

app = FastAPI(
    title="JobMate AI Agent"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    candidate_profile, _, _ = get_active_candidate_profile_from_db()
    return {
        "status": "JobMate AI Agent running",
        "database": "SQLite connected",
        "saved_jobs_count": len(db.get_jobs()),
        "has_profile": candidate_profile is not None
    }


# =========================================================
# CANDIDATE PROFILE API (PERSISTENT & DYNAMIC)
# =========================================================

@app.post("/api/resume/upload")
async def upload_resume(
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are supported"
        )

    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    resume_text = extract_pdf_text(file_path)
    extracted_data = structure_resume(resume_text)

    # Get existing profile if any to merge
    existing_profile, _, _ = get_active_candidate_profile_from_db()
    candidate_profile = populate_from_resume_extraction(extracted_data, existing_profile)
    candidate_profile.resume_path = os.path.abspath(file_path)
    candidate_profile.resume_filename = file.filename

    # Save to SQLite DB
    saved_profile = save_candidate_profile_to_db(
        candidate_profile,
        resume_path=candidate_profile.resume_path,
        resume_filename=candidate_profile.resume_filename
    )

    return {
        "success": True,
        "profile": saved_profile.model_dump(),
        "legacy_profile": candidate_profile_to_legacy_dict(saved_profile),
        "resume_path": saved_profile.resume_path,
        "resume_filename": saved_profile.resume_filename
    }


@app.get("/api/profile")
def get_profile():
    candidate_profile, resume_path, resume_filename = get_active_candidate_profile_from_db()
    if not candidate_profile:
        raise HTTPException(
            status_code=404,
            detail="No candidate profile found"
        )

    return {
        "success": True,
        "profile": candidate_profile.model_dump(),
        "legacy_profile": candidate_profile_to_legacy_dict(candidate_profile),
        "resume_path": resume_path,
        "resume_filename": resume_filename
    }


@app.post("/api/profile")
@app.put("/api/profile")
async def update_profile(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    existing_profile, resume_path, resume_filename = get_active_candidate_profile_from_db()
    updated_profile = normalize_to_candidate_profile(body)
    
    if not updated_profile.resume_path and resume_path:
        updated_profile.resume_path = resume_path
    if not updated_profile.resume_filename and resume_filename:
        updated_profile.resume_filename = resume_filename

    saved_profile = save_candidate_profile_to_db(
        updated_profile,
        resume_path=updated_profile.resume_path or "",
        resume_filename=updated_profile.resume_filename or ""
    )

    return {
        "success": True,
        "message": "Candidate profile saved to database",
        "profile": saved_profile.model_dump(),
        "legacy_profile": candidate_profile_to_legacy_dict(saved_profile),
        "resume_path": saved_profile.resume_path,
        "resume_filename": saved_profile.resume_filename
    }


# =========================================================
# AGENT SETTINGS API
# =========================================================

@app.get("/api/settings")
def get_settings():
    settings = db.get_agent_settings()
    return {
        "success": True,
        "settings": settings.model_dump()
    }


@app.post("/api/settings")
@app.put("/api/settings")
def update_settings(settings: AgentSettings):
    saved = db.save_agent_settings(settings)
    return {
        "success": True,
        "settings": saved.model_dump()
    }


# =========================================================
# JOB SEARCH & MATCHING
# =========================================================

@app.post("/api/jobs/search")
async def find_jobs(request: Request):
    candidate_profile, resume_path, resume_filename = get_active_candidate_profile_from_db()

    if not candidate_profile:
        raise HTTPException(
            status_code=400,
            detail="Upload a resume or configure candidate profile first"
        )

    role = None
    location = None
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            role = body.get("role")
            location = body.get("location")
        elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            form = await request.form()
            role = form.get("role")
            location = form.get("location")
    except Exception:
        pass

    search_profile = candidate_profile_to_legacy_dict(candidate_profile)
    if role and role.strip():
        search_profile["target_role"] = role.strip()
    if location and location.strip():
        search_profile["target_location"] = location.strip()

    # Search & strict verification pipeline
    verified_jobs = search_jobs(search_profile)
    ranked_jobs = rank_jobs(verified_jobs, search_profile)

    # Persist newly discovered verified jobs to SQLite database
    if ranked_jobs:
        db.save_jobs(ranked_jobs)
        current_jobs = ranked_jobs
    else:
        current_jobs = db.get_jobs()

    return {
        "success": True,
        "count": len(current_jobs),
        "jobs": current_jobs
    }


@app.get("/api/jobs")
def get_jobs():
    jobs = db.get_jobs()
    return {
        "success": True,
        "count": len(jobs),
        "jobs": jobs
    }


@app.delete("/api/jobs")
def clear_jobs():
    db.clear_jobs()
    return {
        "success": True,
        "message": "Jobs cleared successfully"
    }


# =========================================================
# APPLICATIONS & HISTORY
# =========================================================

@app.get("/api/applications")
def get_applications():
    apps = db.get_applications()
    return {
        "success": True,
        "count": len(apps),
        "applications": apps
    }


@app.get("/api/applications/{app_id}/fields")
def get_application_fields_log(app_id: int):
    fields = db.get_application_fields(app_id)
    return {
        "success": True,
        "application_id": app_id,
        "fields": fields
    }


class ApplyRequest(BaseModel):
    job: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    settings: Optional[AgentSettings] = None


@app.post("/apply")
@app.post("/api/apply")
async def start_apply(
    request: ApplyRequest,
    background_tasks: BackgroundTasks
):
    candidate_profile, resume_path, _ = get_active_candidate_profile_from_db()

    job_data = request.job or {}
    job_url = request.url or job_data.get("apply_url") or job_data.get("job_url") or job_data.get("url") or job_data.get("link")
    job_title = job_data.get("title") or job_data.get("job_title") or "Application"
    company = job_data.get("company") or job_data.get("company_name") or ""
    job_id = str(job_data.get("id") or "")

    if not job_url or not job_url.startswith("http"):
        raise HTTPException(
            status_code=400,
            detail="Valid HTTP job URL is required to start application"
        )

    agent_settings = request.settings or db.get_agent_settings()

    # Record application session in DB
    app_id = db.save_application(
        job_url=job_url,
        apply_url=job_url,
        job_title=job_title,
        company=company,
        job_id=job_id,
        status=ApplicationStatus.APPLY_STARTED.value,
        settings=agent_settings.model_dump(),
        result=None
    )

    def run_agent_in_proactor(
        application_id: int,
        target_url: str,
        candidate_dict: dict,
        resume: str,
        job_dict: dict,
        settings_obj: AgentSettings
    ):
        import asyncio
        import sys
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from application_orchestrator import orchestrate_application
            print(f"\n[Backend] Launching visible browser auto-apply on REAL employer page: {target_url}")
            result = loop.run_until_complete(
                orchestrate_application(
                    job_url=target_url,
                    candidate_profile=candidate_dict,
                    resume_path=resume,
                    job_data=job_dict,
                    application_id=application_id,
                    settings=settings_obj
                )
            )
            print(f"[Backend] Auto-apply completed with status: {result.get('status')}")
            db.update_application(
                application_id,
                status=result.get("status", ApplicationStatus.READY_FOR_REVIEW.value),
                result=result
            )
        except Exception as err:
            print("[Backend] Auto-apply error:", err)
            db.update_application(
                application_id,
                status=ApplicationStatus.FAILED.value,
                result={"error": str(err)}
            )
        finally:
            loop.close()

    candidate_dict = candidate_profile.model_dump() if candidate_profile else {}
    background_tasks.add_task(
        run_agent_in_proactor,
        app_id,
        job_url,
        candidate_dict,
        resume_path,
        job_data,
        agent_settings
    )

    return {
        "success": True,
        "message": f"Real employer application agent started for {job_url}",
        "job_url": job_url,
        "application_id": app_id,
        "status": ApplicationStatus.APPLY_STARTED.value
    }


class ConfirmSubmitRequest(BaseModel):
    application_id: Optional[int] = None
    job_url: Optional[str] = None


@app.post("/api/apply/submit-confirm")
async def confirm_submit(request: ConfirmSubmitRequest):
    if request.application_id:
        db.update_application(
            request.application_id,
            status=ApplicationStatus.SUBMITTED.value,
            result={"success": True, "manually_submitted_by_applicant": True}
        )
    return {
        "success": True,
        "status": ApplicationStatus.SUBMITTED.value,
        "message": "Application confirmed and successfully recorded as submitted on employer site!"
    }
