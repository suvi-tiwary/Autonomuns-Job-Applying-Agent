import os
from enum import Enum
from typing import Optional, List, Dict, Any, Union
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


class QuestionCategory(str, Enum):
    PERSONAL_INFO = "PERSONAL_INFO"
    CONTACT_INFO = "CONTACT_INFO"
    EDUCATION = "EDUCATION"
    LINK = "LINK"
    WORK_AUTHORIZATION = "WORK_AUTHORIZATION"
    LOCATION = "LOCATION"
    SALARY = "SALARY"
    AVAILABILITY = "AVAILABILITY"
    YES_NO = "YES_NO"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    DESCRIPTIVE = "DESCRIPTIVE"
    PROJECT_DESCRIPTION = "PROJECT_DESCRIPTION"
    WHY_COMPANY = "WHY_COMPANY"
    WHY_ROLE = "WHY_ROLE"
    ACHIEVEMENT = "ACHIEVEMENT"
    EXPERIENCE = "EXPERIENCE"
    COVER_LETTER = "COVER_LETTER"
    SENSITIVE_LEGAL = "SENSITIVE_LEGAL"
    UNKNOWN = "UNKNOWN"


# =========================================================
# DYNAMIC CANDIDATE PROFILE SCHEMA
# =========================================================

class PersonalInfo(BaseModel):
    full_name: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    postal_code: str = ""
    address: str = ""


class EducationItem(BaseModel):
    institution: str = ""
    degree: str = ""
    branch: str = ""
    graduation_year: str = ""
    current_semester: str = ""
    gpa_percentage: str = ""
    start_year: Optional[str] = ""
    end_year: Optional[str] = ""


class EducationInfo(BaseModel):
    college_name: str = ""
    degree: str = ""
    branch_specialization: str = ""
    graduation_year: str = ""
    current_semester: str = ""
    gpa_percentage: str = ""
    history: List[EducationItem] = Field(default_factory=list)


class LinksInfo(BaseModel):
    portfolio_url: str = ""
    github_url: str = ""
    linkedin_url: str = ""
    twitter_url: str = ""
    custom_links: Dict[str, str] = Field(default_factory=dict)


class ProjectItem(BaseModel):
    name: str = ""
    title: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)
    role: str = ""
    url: str = ""


class ExperienceItem(BaseModel):
    company: str = ""
    role: str = ""
    title: str = ""
    duration: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    description: str = ""


class ProfessionalInfo(BaseModel):
    key_skills: List[str] = Field(default_factory=list)
    experience_years: str = "0"
    summary: str = ""
    projects: List[ProjectItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)


class PreferencesInfo(BaseModel):
    preferred_job_roles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    remote_preference: str = "Remote"
    work_authorization: str = "Authorized to work without sponsorship"
    willing_to_relocate: str = "Yes"
    notice_period: str = "Immediate"
    expected_salary_stipend: str = ""


class CandidateProfile(BaseModel):
    personal: PersonalInfo = Field(default_factory=PersonalInfo)
    education: EducationInfo = Field(default_factory=EducationInfo)
    links: LinksInfo = Field(default_factory=LinksInfo)
    professional: ProfessionalInfo = Field(default_factory=ProfessionalInfo)
    preferences: PreferencesInfo = Field(default_factory=PreferencesInfo)
    application_answers: Dict[str, str] = Field(default_factory=dict)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    extracted_fields: List[str] = Field(default_factory=list)
    resume_path: Optional[str] = ""
    resume_filename: Optional[str] = ""
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))


# Legacy flat UserProfile model compatibility
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


# =========================================================
# JOB & APPLICATION SCHEMAS
# =========================================================

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


class ApplicationFieldRecord(BaseModel):
    id: Optional[int] = None
    application_id: int
    field_name: str
    question: str
    detected_type: str
    source: str = "PROFILE"  # PROFILE, LLM, CACHE, SENSITIVE_SKIPPED, DEFAULT
    generated_answer: Optional[str] = ""
    filled_successfully: bool = True
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))


class AgentSettings(BaseModel):
    auto_answer_descriptive: bool = True
    auto_submit: bool = False
    preferred_model: str = "openai/gpt-oss-120b"
    max_answer_words: int = 150


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
    settings: Optional[AgentSettings] = Field(default_factory=AgentSettings)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    error_message: Optional[str] = None
