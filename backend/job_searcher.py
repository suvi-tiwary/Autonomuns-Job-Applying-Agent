import os
import re
import json
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from models import JobSchema
from job_verifier import verify_and_extract_job

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# High-quality direct ATS job pools for guaranteed live fallback discovery
CURATED_ATS_CANDIDATES = [
    "https://job-boards.greenhouse.io/gitlab/jobs/8704363002",
    "https://job-boards.greenhouse.io/moduscreate/jobs/7977989003",
    "https://job-boards.greenhouse.io/canonical/jobs/5643440",
    "https://jobs.lever.co/zimperium/5b35759a-d445-4fcb-b255-d719330af055",
    "https://job-boards.greenhouse.io/mongodb/jobs/8083366",
    "https://jobs.lever.co/mashgin/19a14c15-5e89-4fb2-be7a-5c1be01ba952",
    "https://job-boards.greenhouse.io/automattic/jobs/1234567",
]


def search_jobs(profile: dict) -> List[Dict[str, Any]]:
    """
    STRICT JOB SEARCH & VERIFICATION PIPELINE:
    1. Extract candidate skills and target role.
    2. Query Tavily with targeted ATS constraints.
    3. Extract candidate URLs.
    4. Verify each URL through JobVerifier (HTTP 200, title, company, description, apply_url).
    5. Discard 404s, generic careers pages, login walls, and unverified links.
    6. Return verified JobSchema dictionaries.
    """
    skills = profile.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]

    target_role = profile.get("target_role") or "AI Engineer"
    skills_str = " ".join(skills[:3]) if skills else "Python Machine Learning"

    # Targeted query specifically for single job posts on top ATS boards
    query = f"(site:job-boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com) \"{target_role}\" {skills_str} apply"

    candidate_urls = []

    # 1. Discover via Tavily
    if TAVILY_API_KEY:
        try:
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 8
            }
            res = requests.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=12,
                headers={"User-Agent": "JobMate-AI/1.0"}
            )
            if res.status_code == 200:
                data = res.json()
                for item in data.get("results", []):
                    u = item.get("url", "").strip()
                    if u and u.startswith("http") and u not in candidate_urls:
                        candidate_urls.append(u)
        except Exception as err:
            print(f"[JobSearcher] Tavily discovery error: {err}")

    # Add curated pool as candidates
    for u in CURATED_ATS_CANDIDATES:
        if u not in candidate_urls:
            candidate_urls.append(u)

    # 2. Strict Verification Pipeline
    verified_jobs: List[Dict[str, Any]] = []

    for url in candidate_urls:
        if len(verified_jobs) >= 5:
            break

        job_schema: JobSchema = verify_and_extract_job(url)
        if job_schema and job_schema.is_verified:
            # Check for duplicates by canonical job_url or title+company
            is_duplicate = any(
                j["job_url"] == job_schema.job_url or
                (j["title"].lower() == job_schema.title.lower() and j["company"].lower() == job_schema.company.lower())
                for j in verified_jobs
            )
            if not is_duplicate:
                verified_jobs.append(job_schema.model_dump())

    print(f"[JobSearcher] Verification complete: {len(verified_jobs)} verified individual job postings ready.")
    return verified_jobs