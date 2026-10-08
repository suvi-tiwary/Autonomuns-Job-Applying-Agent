# backend/app/services/resume_service.py
import os
import json
import re
from typing import Dict, Any
from pypdf import PdfReader
from app.integrations.llm.provider import get_llm_provider
from app.core.logging import logger


class ResumeService:
    @staticmethod
    def extract_pdf_text(pdf_path: str) -> str:
        if not pdf_path or not os.path.isfile(pdf_path):
            return ""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.warning(f"PDF extraction error: {e}")
            return ""

    @staticmethod
    def structure_resume_text(resume_text: str) -> Dict[str, Any]:
        if not resume_text or len(resume_text.strip()) < 20:
            return {}

        prompt = f"""
Extract comprehensive candidate profile information from this resume into valid JSON.

Schema:
{{
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "college_name": "",
    "degree": "",
    "branch_specialization": "",
    "graduation_year": "",
    "skills": [],
    "years_of_experience": 0,
    "summary": "",
    "projects": [
        {{
            "name": "",
            "description": "",
            "technologies": []
        }}
    ],
    "experience": [
        {{
            "company": "",
            "role": "",
            "duration": "",
            "description": ""
        }}
    ],
    "achievements": [],
    "certifications": [],
    "target_role": "",
    "target_location": "",
    "work_authorization": "Authorized to work without sponsorship"
}}

Rules:
- Do NOT invent or fabricate information.
- Extract projects with distinct technologies and concise descriptions.
- Extract skills accurately into a list.

RESUME TEXT:
{resume_text[:14000]}
"""
        llm = get_llm_provider()
        try:
            content = llm.generate(
                messages=[
                    {"role": "system", "content": "You extract structured information from candidate resumes. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=1500,
                response_format="json_object"
            )
            cleaned = content.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:]
            elif cleaned.startswith("```"): cleaned = cleaned[3:]
            if cleaned.endswith("```"): cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            logger.warning(f"LLM resume parsing error: {e}")
            return ResumeService._fallback_regex_extraction(resume_text)

    @staticmethod
    def _fallback_regex_extraction(text: str) -> Dict[str, Any]:
        result = {
            "name": "", "email": "", "phone": "",
            "skills": [], "projects": [], "experience": []
        }
        em = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        if em: result["email"] = em.group(0)
        ph = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        if ph: result["phone"] = ph.group(0)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines: result["name"] = lines[0][:50]
        return result


resume_service = ResumeService()
