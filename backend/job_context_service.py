import json
from typing import Dict, Any, Optional
import db


def extract_job_context(
    job_data: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
    job_url: Optional[str] = None,
    page_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Consolidates and normalizes structured job context for the current application.
    Prioritizes explicit job record, falling back to database or page text.
    """
    context: Dict[str, Any] = {
        "id": "",
        "title": "Role",
        "company": "Company",
        "location": "Remote",
        "remote_type": "Remote",
        "employment_type": "Full-time",
        "description": "",
        "requirements": [],
        "responsibilities": [],
        "skills": [],
        "apply_url": "",
        "source": "ATS"
    }

    # 1. From provided job_data
    if job_data and isinstance(job_data, dict):
        for k in ["id", "title", "company", "location", "remote_type", "employment_type", "description", "apply_url", "source"]:
            if job_data.get(k):
                context[k] = job_data[k]

        if isinstance(job_data.get("requirements"), list):
            context["requirements"] = job_data["requirements"]
        if isinstance(job_data.get("responsibilities"), list):
            context["responsibilities"] = job_data["responsibilities"]
        if isinstance(job_data.get("skills"), list):
            context["skills"] = job_data["skills"]

    # 2. Enrich from DB if id or url provided
    if not context.get("description") and (job_id or job_url):
        saved_jobs = db.get_jobs(limit=100)
        for j in saved_jobs:
            if (job_id and j.get("id") == job_id) or (job_url and (j.get("job_url") == job_url or j.get("apply_url") == job_url)):
                for k in ["id", "title", "company", "location", "remote_type", "employment_type", "description", "apply_url", "source"]:
                    if not context.get(k) and j.get(k):
                        context[k] = j[k]
                if not context.get("requirements") and j.get("requirements"):
                    context["requirements"] = j["requirements"]
                if not context.get("responsibilities") and j.get("responsibilities"):
                    context["responsibilities"] = j["responsibilities"]
                if not context.get("skills") and j.get("skills"):
                    context["skills"] = j["skills"]
                break

    # 3. Supplemental page excerpt if description is short
    if page_text and len(context.get("description", "")) < 100:
        clean_page = " ".join((page_text or "").split())
        context["page_excerpt"] = clean_page[:4000]

    return context


def format_job_summary_for_prompt(job_context: Dict[str, Any]) -> str:
    """
    Creates a concise textual representation of the job for the LLM prompt.
    """
    lines = [
        f"JOB TITLE: {job_context.get('title', 'Role')}",
        f"COMPANY: {job_context.get('company', 'Company')}",
        f"LOCATION: {job_context.get('location', 'Remote')} ({job_context.get('remote_type', 'Remote')})",
        f"EMPLOYMENT TYPE: {job_context.get('employment_type', 'Full-time')}"
    ]

    if job_context.get("skills"):
        skills_str = ", ".join(job_context["skills"][:10]) if isinstance(job_context["skills"], list) else str(job_context["skills"])
        lines.append(f"DESIRED SKILLS: {skills_str}")

    if job_context.get("requirements"):
        reqs = job_context["requirements"][:5]
        lines.append("KEY REQUIREMENTS:\n" + "\n".join(f"- {r}" for r in reqs))

    if job_context.get("description"):
        desc = str(job_context["description"])
        lines.append(f"JOB DESCRIPTION EXCERPT:\n{desc[:2500]}")

    return "\n".join(lines)
