import json
import os
from typing import Dict, Any
from pypdf import PdfReader
from dotenv import load_dotenv
from llm_provider import get_llm_provider

load_dotenv()


def extract_pdf_text(pdf_path: str) -> str:
    """Extracts raw plain text from a PDF resume."""
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
        print(f"[ResumeParser] PDF text extraction error: {e}")
        return ""


def structure_resume(resume_text: str) -> Dict[str, Any]:
    """
    Extracts structured candidate information from resume text
    matching the expanded dynamic CandidateProfile schema.
    """
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
    "city": "",
    "state": "",
    "country": "",
    "postal_code": "",
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "twitter": "",
    "college_name": "",
    "degree": "",
    "branch_specialization": "",
    "graduation_year": "",
    "current_semester": "",
    "gpa_percentage": "",
    "education": [
        {{
            "institution": "",
            "degree": "",
            "branch": "",
            "graduation_year": "",
            "current_semester": "",
            "gpa": ""
        }}
    ],
    "skills": [],
    "years_of_experience": 0,
    "summary": "",
    "projects": [
        {{
            "name": "",
            "description": "",
            "technologies": [],
            "role": "",
            "url": ""
        }}
    ],
    "experience": [
        {{
            "company": "",
            "role": "",
            "duration": "",
            "start_date": "",
            "end_date": "",
            "location": "",
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
- Do NOT invent or fabricate any information.
- If information is absent, use empty string or [].
- Extract projects with distinct technologies and concise descriptions.
- Extract skills accurately into a list of strings.
- Extract education with college name, degree, and specialization.

RESUME TEXT:
{resume_text[:14000]}
"""

    llm = get_llm_provider()
    
    try:
        content = llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured information from candidate resumes. Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            max_tokens=1500,
            response_format="json_object"
        )
    except Exception as e:
        print(f"[ResumeParser] LLM extraction error: {e}")
        # Fallback simple regex extraction
        return _fallback_regex_extraction(resume_text)

    # Clean code fences
    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        return json.loads(cleaned.strip())
    except Exception as parse_err:
        print(f"[ResumeParser] JSON parse error: {parse_err}")
        return _fallback_regex_extraction(resume_text)


def _fallback_regex_extraction(text: str) -> Dict[str, Any]:
    """Basic fallback parser when LLM is unavailable."""
    import re
    result: Dict[str, Any] = {
        "name": "",
        "email": "",
        "phone": "",
        "skills": [],
        "projects": [],
        "experience": []
    }

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        result["email"] = email_match.group(0)

    phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    if phone_match:
        result["phone"] = phone_match.group(0)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        result["name"] = lines[0][:50]

    return result