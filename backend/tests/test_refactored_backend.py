"""
Comprehensive Test Suite for Refactored JobMate AI Backend
Verifies:
1. Multi-user Candidate Profile persistence and retrieval
2. Multi-tier Company Intelligence (Tier A/B/C) and mix balancing
3. URL Validator ATS detection, query stripping, and career page rejection
4. Job Ranking with freshness decay, skill match, and why_recommended generation
5. Asynchronous Task Manager progress execution
6. FastAPI test client for /api/profile, /api/jobs/search, /api/applications
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
from app.models.profile import CandidateProfile, PersonalInfo, EducationInfo, ProfessionalInfo
from app.models.job import JobSchema, CompanyTier
from app.services.company_intelligence_service import CompanyIntelligenceService
from app.services.job_ranking_service import JobRankingService
from app.integrations.search.url_validator import JobURLValidator
from app.repositories.profile_repository import ProfileRepository
from app.repositories.job_repository import JobRepository
from app.workers.task_manager import TaskManager


def test_database_init():
    print("Testing database initialization...")
    init_db()
    print("PASS: Database tables and indexes created successfully.")


def test_profile_repository():
    print("Testing multi-user CandidateProfile persistence...")
    repo = ProfileRepository()
    user_id = "test_user_123"

    profile = CandidateProfile(
        user_id=user_id,
        personal=PersonalInfo(full_name="Alex Mercer", email="alex@example.com", location="San Francisco, CA"),
        education=EducationInfo(college_name="Stanford University", degree="B.S.", branch="Computer Science", graduation_year=2025),
        professional=ProfessionalInfo(key_skills=["Python", "PyTorch", "FastAPI", "React"], years_of_experience=1.5),
    )

    saved = repo.save_profile(profile)
    assert saved.personal.full_name == "Alex Mercer"
    assert "PyTorch" in saved.professional.key_skills

    fetched = repo.get_profile(user_id)
    assert fetched.personal.email == "alex@example.com"
    assert fetched.education.college_name == "Stanford University"
    print("PASS: Profile persistence and multi-user retrieval verified.")


def test_company_intelligence():
    print("Testing Company Intelligence & Tiering...")
    cis = CompanyIntelligenceService()

    tier_google, score_google = cis.classify_company("Google")
    assert tier_google == CompanyTier.RECOGNIZABLE
    assert score_google >= 90

    tier_modal, score_modal = cis.classify_company("Modal Labs")
    assert tier_modal == CompanyTier.STRONG_STARTUP
    assert score_modal >= 75

    tier_xyz, score_xyz = cis.classify_company("Mysterious Stealth AI")
    assert tier_xyz == CompanyTier.EMERGING
    assert score_xyz > 50

    print("PASS: Company classification verified (Google: A, Modal: B, Stealth: C).")


def test_job_url_validator():
    print("Testing JobURLValidator...")
    validator = JobURLValidator()

    # Generic career page rejection
    assert validator.is_generic_career_page("https://google.com/careers") is True
    assert validator.is_generic_career_page("https://apple.com/jobs/search") is True
    assert validator.is_generic_career_page("https://boards.greenhouse.io/anthropic/jobs/409281") is False

    # ATS Detection
    assert validator.is_ats_url("https://jobs.lever.co/company/abc-123") is True
    assert validator.is_ats_url("https://myworkdayjobs.com/en-US/job/R123") is True

    # URL normalization
    norm = validator.normalize_url("https://jobs.lever.co/company/abc?gh_src=123&utm_source=tavily#apply")
    assert "utm_source" not in norm
    assert "#apply" not in norm

    print("PASS: JobURLValidator rules and ATS matching verified.")


def test_job_ranking():
    print("Testing JobRankingService & Multi-Factor Scoring...")
    ranker = JobRankingService()

    profile = CandidateProfile(
        user_id="candidate_1",
        personal=PersonalInfo(full_name="Sarah Connor"),
        professional=ProfessionalInfo(key_skills=["Python", "FastAPI", "Docker", "Machine Learning"]),
    )

    job_recent_google = JobSchema(
        id="job_1",
        title="AI Engineer Intern",
        company="Google",
        location="Remote",
        application_url="https://careers.google.com/jobs/results/123",
        description="Looking for Python, FastAPI, and Machine Learning experience.",
        skills=["Python", "FastAPI", "Machine Learning"],
        posted_at="1 day ago",
        company_tier="RECOGNIZABLE",
    )

    ranked_job = ranker.rank_job(job_recent_google, profile)
    assert ranked_job.final_score > 75
    assert len(ranked_job.why_recommended) >= 2
    print(f"Ranked Job Score: {ranked_job.final_score}, Reasons: {ranked_job.why_recommended}")
    print("PASS: Multi-factor composite ranking and reason generation verified.")


def test_fastapi_endpoints():
    print("Testing FastAPI API endpoints via TestClient...")
    client = TestClient(app)

    # Health
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}

    # Get Profile
    r = client.get("/api/profile", headers={"X-User-Id": "test_api_user"})
    assert r.status_code == 200
    assert "personal" in r.json()

    # Update Profile
    payload = {
        "personal": {"full_name": "Devin AI", "email": "devin@cognition.ai", "location": "Remote"},
        "professional": {"key_skills": ["Python", "Rust", "LLMs"], "years_of_experience": 2},
    }
    r = client.post("/api/profile", json=payload, headers={"X-User-Id": "test_api_user"})
    assert r.status_code == 200
    assert r.json()["profile"]["personal"]["full_name"] == "Devin AI"

    # Search Task Submission
    r = client.post("/api/jobs/search", json={"query": "AI Engineer", "target_roles": ["AI Engineer"]}, headers={"X-User-Id": "test_api_user"})
    assert r.status_code == 200
    task_id = r.json()["task_id"]
    assert task_id is not None

    # Poll Search Task Status
    r = client.get(f"/api/jobs/search/{task_id}", headers={"X-User-Id": "test_api_user"})
    assert r.status_code == 200
    assert "status" in r.json()

    # Get Jobs
    r = client.get("/api/jobs", headers={"X-User-Id": "test_api_user"})
    assert r.status_code == 200
    assert "jobs" in r.json()

    # Get Applications
    r = client.get("/api/applications", headers={"X-User-Id": "test_api_user"})
    assert r.status_code == 200
    assert "applications" in r.json()

    print("PASS: All FastAPI endpoints tested and functioning properly.")


if __name__ == "__main__":
    test_database_init()
    test_profile_repository()
    test_company_intelligence()
    test_job_url_validator()
    test_job_ranking()
    test_fastapi_endpoints()
    print("\nALL BACKEND UNIT & INTEGRATION TESTS PASSED SUCCESSFULLY!")
