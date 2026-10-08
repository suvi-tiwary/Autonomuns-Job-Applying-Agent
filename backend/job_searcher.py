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

CURATED_ATS_FALLBACK = [
    "https://job-boards.greenhouse.io/gitlab/jobs/8704363002",
    "https://job-boards.greenhouse.io/moduscreate/jobs/7977989003",
    "https://job-boards.greenhouse.io/canonical/jobs/5643440",
    "https://jobs.lever.co/zimperium/5b35759a-d445-4fcb-b255-d719330af055",
    "https://job-boards.greenhouse.io/mongodb/jobs/8083366",
]


def search_jobs(profile: dict) -> List[Dict[str, Any]]:
    """
    DYNAMIC ATS SEARCH & REAL-TIME VERIFICATION PIPELINE:
    1. Reads user's target role, location, and primary skills.
    2. Queries live ATS boards via Tavily with high-intent keywords.
    3. Verifies every candidate link against live employer ATS pages.
    4. Filters out 404s, login walls, and generic portals.
    5. Returns fresh, verified JobSchema listings.
    """
    skills = profile.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]

    target_role = profile.get("target_role") or "Software Engineer"
    target_location = profile.get("target_location") or ""
    
    # Build clean search queries
    top_skill = skills[0] if skills else ""
    loc_clause = f"{target_location}" if target_location else ""

    queries = [
        f'(site:job-boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com) {target_role} {loc_clause} apply',
        f'(site:job-boards.greenhouse.io OR site:jobs.lever.co) {target_role} {top_skill} jobs',
    ]

    candidate_urls: List[str] = []

    # 1. Live Tavily Search
    if TAVILY_API_KEY:
        for q in queries:
            if len(candidate_urls) >= 12:
                break
            try:
                payload = {
                    "api_key": TAVILY_API_KEY,
                    "query": q.strip(),
                    "search_depth": "basic",
                    "max_results": 8
                }
                res = requests.post(
                    "https://api.tavily.com/search",
                    json=payload,
                    timeout=10,
                    headers={"User-Agent": "JobMate-AI/1.0"}
                )
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("results", []):
                        u = item.get("url", "").strip()
                        if u and u.startswith("http") and u not in candidate_urls:
                            candidate_urls.append(u)
            except Exception as err:
                print(f"[JobSearcher] Tavily error for query '{q}': {err}")

    # Fallback to curated list only if Tavily returned 0 URLs
    if not candidate_urls:
        print("[JobSearcher] Using curated emergency fallback pool")
        candidate_urls = list(CURATED_ATS_FALLBACK)

    # 2. Strict Real-Time Verification
    verified_jobs: List[Dict[str, Any]] = []

    for url in candidate_urls:
        if len(verified_jobs) >= 6:
            break

        try:
            job_schema: JobSchema = verify_and_extract_job(url)
            if job_schema and job_schema.is_verified:
                # Deduplicate by canonical URL and title+company
                is_duplicate = any(
                    j.get("job_url") == job_schema.job_url or
                    (j.get("title", "").lower() == job_schema.title.lower() and j.get("company", "").lower() == job_schema.company.lower())
                    for j in verified_jobs
                )
                if not is_duplicate:
                    verified_jobs.append(job_schema.model_dump())
        except Exception as ver_err:
            print(f"[JobSearcher] Error verifying {url}: {ver_err}")

    print(f"[JobSearcher] Verification complete: {len(verified_jobs)} fresh individual job postings found.")
    return verified_jobs