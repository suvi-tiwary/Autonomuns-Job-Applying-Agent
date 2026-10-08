# backend/app/models/application.py
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    QUEUED = "QUEUED"
    DISCOVERED = "DISCOVERED"
    VERIFIED = "VERIFIED"
    APPLY_STARTED = "APPLY_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
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


class AgentSettings(BaseModel):
    user_id: str = "user_default"
    auto_answer_descriptive: bool = True
    auto_submit: bool = False
    preferred_model: str = "openai/gpt-oss-120b"
    max_answer_words: int = 150


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


class ApplicationSession(BaseModel):
    id: Optional[Union[int, str]] = None
    user_id: str = "user_default"
    job_id: str = ""
    job_title: str = ""
    company: str = ""
    job_url: str = ""
    apply_url: str = ""
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    steps_log: List[str] = Field(default_factory=list)
    filled_fields: List[Dict[str, Any]] = Field(default_factory=list)
    skipped_sensitive_fields: List[Dict[str, Any]] = Field(default_factory=list)
    settings: Optional[AgentSettings] = Field(default_factory=AgentSettings)
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
