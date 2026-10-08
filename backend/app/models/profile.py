from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator


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

    @field_validator("graduation_year", mode="before")
    @classmethod
    def convert_str(cls, v):
        return str(v) if v is not None else ""


class EducationInfo(BaseModel):
    college_name: str = ""
    degree: str = ""
    branch_specialization: str = ""
    branch: str = ""
    graduation_year: str = ""
    current_semester: str = ""
    gpa_percentage: str = ""
    gpa: str = ""
    history: List[EducationItem] = Field(default_factory=list)

    @field_validator("graduation_year", "gpa", "gpa_percentage", mode="before")
    @classmethod
    def convert_str(cls, v):
        return str(v) if v is not None else ""

    def model_post_init(self, __context: Any) -> None:
        if self.branch and not self.branch_specialization:
            self.branch_specialization = self.branch
        elif self.branch_specialization and not self.branch:
            self.branch = self.branch_specialization
        if self.gpa and not self.gpa_percentage:
            self.gpa_percentage = self.gpa
        elif self.gpa_percentage and not self.gpa:
            self.gpa = self.gpa_percentage


class LinksInfo(BaseModel):
    portfolio_url: str = ""
    portfolio: str = ""
    github_url: str = ""
    github: str = ""
    linkedin_url: str = ""
    linkedin: str = ""
    twitter_url: str = ""
    custom_links: Dict[str, str] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.portfolio and not self.portfolio_url:
            self.portfolio_url = self.portfolio
        elif self.portfolio_url and not self.portfolio:
            self.portfolio = self.portfolio_url
        if self.github and not self.github_url:
            self.github_url = self.github
        elif self.github_url and not self.github:
            self.github = self.github_url
        if self.linkedin and not self.linkedin_url:
            self.linkedin_url = self.linkedin
        elif self.linkedin_url and not self.linkedin:
            self.linkedin = self.linkedin_url


class ProjectItem(BaseModel):
    name: str = ""
    title: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)
    role: str = ""
    url: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.title and not self.name:
            self.name = self.title
        elif self.name and not self.title:
            self.title = self.name


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
    years_of_experience: float = 0.0
    summary: str = ""
    projects: List[ProjectItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    @field_validator("experience_years", mode="before")
    @classmethod
    def convert_exp_str(cls, v):
        return str(v) if v is not None else "0"

    @field_validator("years_of_experience", mode="before")
    @classmethod
    def convert_exp_float(cls, v):
        try:
            return float(v) if v is not None else 0.0
        except (ValueError, TypeError):
            return 0.0


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
