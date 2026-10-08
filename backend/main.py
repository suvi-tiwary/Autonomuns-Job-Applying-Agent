"""
Root Entrypoint for JobMate AI Application
Imports and exposes the modular FastAPI application from app.main.
Allows running with: uvicorn main:app --reload --port 8000
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
