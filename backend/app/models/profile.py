# backend/app/models/profile.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


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
    user_id: str = "user_default"
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
