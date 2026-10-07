import os
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    VERIFIED = "VERIFIED"
    APPLY_STARTED = "APPLY_STARTED"
    FORM_FILLING = "FORM_FILLING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"


class JobSchema(BaseModel):
    id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Exact job title")
    company: str = Field(..., description="Company name")
    location: str = Field(default="Remote", description="Job location or Remote")
    remote_type: Optional[str] = Field(default="Remote", description="Remote, Hybrid, or On-site")
    employment_type: Optional[str] = Field(default="Full-time", description="Full-time, Internship, Contract, etc.")
    description: str = Field(default="", description="Full or excerpted job description")
    requirements: List[str] = Field(default_factory=list, description="Extracted requirements or qualifications")
    responsibilities: List[str] = Field(default_factory=list, description="Key job responsibilities")
    skills: List[str] = Field(default_factory=list, description="Relevant skills mentioned in posting")
    experience_required: Optional[str] = Field(default=None, description="Experience level or years")
    salary: Optional[str] = Field(default=None, description="Salary or compensation if listed")
    posted_at: Optional[str] = Field(default=None, description="Date/time job was posted")
    source: str = Field(default="Tavily Discovery", description="ATS or search source")
    source_url: Optional[str] = Field(default=None, description="Original discovery URL")
    job_url: str = Field(..., description="Canonical single job posting URL")
    apply_url: str = Field(..., description="Direct application page or form URL")
    ats: str = Field(default="custom", description="greenhouse, lever, ashby, workable, or custom")
    external_job_id: Optional[str] = Field(default=None, description="ATS specific job ID")
    discovered_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    verified_at: Optional[str] = Field(default=None, description="Timestamp when page was verified live")
    is_verified: bool = Field(default=True, description="True if page was scraped and validated HTTP 200")
    match_score: float = Field(default=0.0, description="Match score (0-100) vs candidate resume")


class UserProfile(BaseModel):
    full_name: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    portfolio: Optional[str] = ""
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[str] = ""
    education: Optional[str] = ""
    resume_path: Optional[str] = ""
    resume_filename: Optional[str] = ""
    target_role: Optional[str] = ""
    target_location: Optional[str] = ""


class ApplicationSession(BaseModel):
    id: Optional[int] = None
    job_id: str
    job_title: str
    company: str
    job_url: str
    apply_url: str
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    steps_log: List[str] = Field(default_factory=list)
    filled_fields: List[Dict[str, Any]] = Field(default_factory=list)
    skipped_sensitive_fields: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    error_message: Optional[str] = None
