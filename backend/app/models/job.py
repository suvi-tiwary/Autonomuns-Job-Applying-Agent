from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class CompanyTier(str, Enum):
    RECOGNIZABLE = "recognizable"  # Tier A: Top recognizable brands & tech leaders
    STRONG_STARTUP = "strong_startup"  # Tier B: High-signal funded startups & scaleups
    EMERGING = "emerging"  # Tier C: Promising niche & early stage companies


class JobSchema(BaseModel):
    id: str = Field(..., description="Unique job identifier")
    external_id: Optional[str] = Field(default=None, description="ATS specific job ID")
    title: str = Field(..., description="Exact job title")
    company: str = Field(..., description="Company name")
    company_domain: Optional[str] = Field(default=None, description="Company website domain")
    company_tier: CompanyTier = Field(default=CompanyTier.EMERGING, description="Company categorization tier")

    @field_validator("company_tier", mode="before")
    @classmethod
    def parse_tier(cls, v):
        if isinstance(v, str):
            v_low = v.lower()
            if v_low in ["tier_a", "recognizable", "brand", "tier a"]:
                return CompanyTier.RECOGNIZABLE
            if v_low in ["tier_b", "strong_startup", "startup", "scaleup", "tier b"]:
                return CompanyTier.STRONG_STARTUP
            return CompanyTier.EMERGING
        return v
    location: str = Field(default="Remote", description="Job location or Remote")
    remote_type: Optional[str] = Field(default="Remote", description="Remote, Hybrid, or On-site")
    employment_type: Optional[str] = Field(default="Full-time", description="Full-time, Internship, Contract, etc.")
    description: str = Field(default="", description="Full or excerpted job description")
    requirements: List[str] = Field(default_factory=list, description="Extracted requirements or qualifications")
    responsibilities: List[str] = Field(default_factory=list, description="Key job responsibilities")
    skills: List[str] = Field(default_factory=list, description="Relevant skills mentioned in posting")
    salary: Optional[str] = Field(default=None, description="Salary or compensation if listed")
    posted_at: Optional[str] = Field(default=None, description="Date/time job was posted")
    discovered_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    verified_at: Optional[str] = Field(default=None, description="Timestamp when page was verified live")
    is_verified: bool = Field(default=True, description="True if page was scraped and validated HTTP 200")
    job_url: str = Field(default="", description="Canonical single job posting URL")
    apply_url: str = Field(default="", description="Direct application page or form URL")
    application_url: str = Field(default="", description="Alias for apply_url / job_url")
    ats: str = Field(default="custom", description="greenhouse, lever, ashby, workable, or custom")
    source: str = Field(default="Tavily Discovery", description="ATS or search source")
    source_type: str = Field(default="direct_ats", description="direct_ats, company_board, discovery")
    
    # Scoring & Recommendations
    freshness_score: float = Field(default=80.0, description="Recency score 0-100")
    company_score: float = Field(default=70.0, description="Company brand/signal score 0-100")
    match_score: float = Field(default=85.0, description="Resume skill & role relevance 0-100")
    final_score: float = Field(default=80.0, description="Weighted composite score 0-100")
    why_recommended: List[str] = Field(default_factory=list, description="Bullet points explaining recommendation")
    url_validated: bool = Field(default=True, description="Validated true single-job URL")

    def model_post_init(self, __context: Any) -> None:
        if self.application_url:
            if not self.job_url:
                self.job_url = self.application_url
            if not self.apply_url:
                self.apply_url = self.application_url
        elif self.apply_url and not self.application_url:
            self.application_url = self.apply_url
        elif self.job_url and not self.application_url:
            self.application_url = self.job_url
        
        if not self.job_url and self.apply_url:
            self.job_url = self.apply_url
        if not self.apply_url and self.job_url:
            self.apply_url = self.job_url
