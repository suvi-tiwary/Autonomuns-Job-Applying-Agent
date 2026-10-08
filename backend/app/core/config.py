# backend/app/core/config.py
import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load root .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    PROJECT_NAME: str = "JobMate Autonomous AI Agent"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    
    # Environment & Database
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "jobmate.db"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    
    # LLM Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    
    # Search Configuration
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "").strip()
    
    # Worker & Execution Settings
    MAX_CONCURRENT_SEARCHES: int = int(os.getenv("MAX_CONCURRENT_SEARCHES", "5"))
    MAX_CONCURRENT_APPLICATIONS: int = int(os.getenv("MAX_CONCURRENT_APPLICATIONS", "3"))
    DEFAULT_MAX_ANSWER_WORDS: int = 150
    DEFAULT_USER_ID: str = "user_default"


settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
