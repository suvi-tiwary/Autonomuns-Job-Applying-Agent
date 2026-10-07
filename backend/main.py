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
from models import ApplicationStatus
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

# In-memory sync with DB
current_profile, current_resume_path, current_resume_filename = db.get_active_profile()
current_jobs = db.get_jobs()


@app.get("/")
def root():
    return {
        "status": "JobMate AI Agent running",
        "database": "SQLite connected",
        "saved_jobs_count": len(db.get_jobs()),
        "has_profile": current_profile is not None
    }


@app.post("/api/resume/upload")
async def upload_resume(
    file: UploadFile = File(...)
):
    global current_profile
    global current_resume_path
    global current_resume_filename

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
    profile = structure_resume(resume_text)

    current_profile = profile
    current_resume_path = os.path.abspath(file_path)
    current_resume_filename = file.filename

    db.save_profile(
        profile_data=profile,
        resume_path=current_resume_path,
        resume_filename=current_resume_filename
    )

    return {
        "success": True,
        "profile": profile,
        "resume_path": current_resume_path,
        "resume_filename": current_resume_filename
    }


@app.post("/api/jobs/search")
async def find_jobs(request: Request):
    global current_profile
    global current_resume_path
    global current_resume_filename
    global current_jobs

    if not current_profile:
        current_profile, current_resume_path, current_resume_filename = db.get_active_profile()

    if not current_profile:
        raise HTTPException(
            status_code=400,
            detail="Upload a resume first"
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

    search_profile = dict(current_profile)
    if role and role.strip():
        search_profile["target_role"] = role.strip()
    if location and location.strip():
        search_profile["target_location"] = location.strip()

    # Search & strict verification pipeline
    verified_jobs = search_jobs(search_profile)
    ranked_jobs = rank_jobs(verified_jobs, search_profile)

    # Persist verified jobs to SQLite database
    db.save_jobs(ranked_jobs)
    current_jobs = db.get_jobs()

    return {
        "success": True,
        "count": len(current_jobs),
        "jobs": current_jobs
    }


@app.get("/api/jobs")
def get_jobs():
    global current_jobs
    jobs = db.get_jobs()
    current_jobs = jobs
    return {
        "success": True,
        "count": len(jobs),
        "jobs": jobs
    }


@app.delete("/api/jobs")
def clear_jobs():
    global current_jobs
    db.clear_jobs()
    current_jobs = []
    return {
        "success": True,
        "message": "Jobs cleared successfully"
    }


@app.get("/api/profile")
def get_profile():
    global current_profile
    global current_resume_path
    global current_resume_filename

    profile, resume_path, resume_filename = db.get_active_profile()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No resume uploaded"
        )
    current_profile = profile
    current_resume_path = resume_path
    current_resume_filename = resume_filename
    return {
        "success": True,
        "profile": profile,
        "resume_path": resume_path,
        "resume_filename": resume_filename
    }


@app.get("/api/applications")
def get_applications():
    apps = db.get_applications()
    return {
        "success": True,
        "count": len(apps),
        "applications": apps
    }


class ApplyRequest(BaseModel):
    job: Optional[Dict[str, Any]] = None
    url: Optional[str] = None


@app.post("/apply")
@app.post("/api/apply")
async def start_apply(
    request: ApplyRequest,
    background_tasks: BackgroundTasks
):
    global current_profile
    global current_resume_path

    if not current_profile or not current_resume_path:
        current_profile, current_resume_path, _ = db.get_active_profile()

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

    # Record application session in DB
    app_id = db.save_application(
        job_url=job_url,
        apply_url=job_url,
        job_title=job_title,
        company=company,
        job_id=job_id,
        status=ApplicationStatus.APPLY_STARTED.value,
        result=None
    )

    def run_agent_in_proactor(application_id: int, target_url: str, candidate: dict, resume: str):
        import asyncio
        import sys
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from application_agent import apply_to_job
            print(f"\n[Backend] Launching visible browser auto-apply on REAL employer page: {target_url}")
            result = loop.run_until_complete(
                apply_to_job(
                    job_url=target_url,
                    candidate_profile=candidate,
                    resume_path=resume,
                    interactive=False
                )
            )
            print(f"[Backend] Real employer auto-apply paused with result: {result}")
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

    background_tasks.add_task(run_agent_in_proactor, app_id, job_url, current_profile, current_resume_path)

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
