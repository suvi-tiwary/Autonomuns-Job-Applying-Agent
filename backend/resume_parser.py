import json
import os
from pypdf import PdfReader
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b").strip()


def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text() or ""
        text += page_text + "\n"

    return text


def structure_resume(resume_text):

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")

    prompt = f"""
Extract structured candidate information from this resume.

Return ONLY valid JSON.

Schema:

{{
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "education": [],
    "experience": [],
    "projects": [],
    "skills": [],
    "certifications": [],
    "achievements": [],
    "years_of_experience": 0
}}

Rules:

- Do not invent information.
- If information does not exist, use empty string or [].
- Extract projects with their technologies and descriptions.
- Extract technical skills separately.
- Extract education accurately.
- Extract experience accurately.

RESUME:

{resume_text}
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You extract structured information from resumes."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0,
        "response_format": {
            "type": "json_object"
        }
    }

    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AIJobAgent/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")

        print("====================================")
        print("GROQ API ERROR")
        print("STATUS:", e.code)
        print("DETAIL:", error_body)
        print("====================================")

        raise RuntimeError(
            f"Groq API error {e.code}: {error_body}"
        )

    except urllib.error.URLError as e:
        print("====================================")
        print("GROQ CONNECTION ERROR")
        print("DETAIL:", e.reason)
        print("====================================")

        raise RuntimeError(
            f"Could not connect to Groq: {e.reason}"
        )

    content = result["choices"][0]["message"]["content"].strip()

    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    return json.loads(content.strip())