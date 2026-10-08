# backend/app/models/search_task.py
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.job import JobSchema


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SearchTask(BaseModel):
    task_id: str
    user_id: str = "user_default"
    query: str = ""
    target_role: Optional[str] = ""
    target_location: Optional[str] = ""
    status: TaskStatus = TaskStatus.QUEUED
    progress: int = 0
    stage: str = "QUEUED"
    message: str = ""
    total_found: int = 0
    jobs: List[JobSchema] = Field(default_factory=list)
    error: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
