import asyncio
import sys



from fastapi import FastAPI
import os
import shutil
import tempfile

from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )
from resume_parser import (
    extract_pdf_text,


    structure_resume
)

from job_searcher import search_jobs
from job_matcher import rank_jobs


app = FastAPI(
    title="AI Job Agent"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


current_profile = None
current_resume_path = None
current_jobs = []


@app.get("/")
def root():

    return {
        "status": "AI Job Agent running"
    }


@app.post("/api/resume/upload")
async def upload_resume(
    file: UploadFile = File(...)
):

    global current_profile
    global current_resume_path

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are supported"
        )

    upload_dir = "uploads"

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_dir,
        file.filename
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    resume_text = extract_pdf_text(
        file_path
    )

    profile = structure_resume(
        resume_text
    )

    current_profile = profile
    current_resume_path = os.path.abspath(
        file_path
    )

    return {
        "success": True,
        "profile": profile,
        "resume_path": current_resume_path
    }


@app.post("/api/jobs/search")
def find_jobs():

    global current_jobs

    if not current_profile:

        raise HTTPException(
            status_code=400,
            detail="Upload a resume first"
        )

    jobs = search_jobs(
        current_profile
    )

    ranked_jobs = rank_jobs(
        jobs,
        current_profile
    )

    current_jobs = ranked_jobs

    return {
        "success": True,
        "count": len(ranked_jobs),
        "jobs": ranked_jobs
    }


@app.get("/api/jobs")
def get_jobs():

    return {
        "jobs": current_jobs
    }


@app.get("/api/profile")
def get_profile():
    if not current_profile:
        raise HTTPException(
            status_code=404,
            detail="No resume uploaded"
        )
    return {
        "profile": current_profile
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

    job_data = request.job or {}
    job_url = request.url or job_data.get("url") or job_data.get("link") or job_data.get("job_url")

    if not job_url:
        raise HTTPException(
            status_code=400,
            detail="Job URL is required to start application"
        )

    async def run_agent_task():
        try:
            from application_agent import apply_to_job
            await apply_to_job(
                job_url=job_url,
                candidate_profile=current_profile,
                resume_path=current_resume_path,
                interactive=False
            )
        except Exception as err:
            print("Auto-apply agent background error:", err)

    background_tasks.add_task(run_agent_task)

    return {
        "success": True,
        "message": f"Application agent started for {job_url}",
        "job_url": job_url
    }
