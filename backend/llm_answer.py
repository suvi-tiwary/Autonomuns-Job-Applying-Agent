import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b").strip()


def generate_answer(
    question,
    profile,
    resume_text,
    job_context
):
    """
    Generate a personalized job-application answer
    using the candidate's resume, profile and job context.
    """

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set."
        )

    prompt = f"""
You are an AI job application assistant.

Write a strong, natural and truthful answer to the
job application question below.

IMPORTANT:
- Use ONLY information supported by the candidate profile
  and resume.
- Do not invent experience, companies, achievements,
  technologies or education.
- Do not mention that an AI wrote the answer.
- Do not use generic corporate language.
- Make the answer sound like a real candidate.
- Keep it concise: normally 80-150 words.
- Directly answer the question.
- If the question asks about interest in the company,
  connect the answer to the job/company context and
  the candidate's actual skills/projects.
- Do not start with "As an AI".
- Do not use bullet points unless the question asks for them.

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

RESUME:
{resume_text[:12000]}

JOB PAGE CONTEXT:
{job_context[:12000]}

APPLICATION QUESTION:
{question}

Write ONLY the final answer that should be placed
inside the application form.
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert job application "
                    "assistant who writes truthful, "
                    "personalized application answers."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,
        "max_tokens": 300
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AIJobAgent/1.0"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        answer = (
            result["choices"][0]["message"]["content"]
            .strip()
        )

        return answer

    except Exception as error:

        print(
            "LLM generation failed:",
            error
        )

        return ""
