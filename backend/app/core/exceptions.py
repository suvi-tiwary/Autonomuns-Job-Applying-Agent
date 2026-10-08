# backend/app/core/exceptions.py
from fastapi import HTTPException, status

class JobMateException(Exception):
    """Base exception for JobMate application."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ResourceNotFoundException(JobMateException):
    pass

class ValidationException(JobMateException):
    pass

class LLMProviderException(JobMateException):
    pass

class BrowserAutomationException(JobMateException):
    pass
