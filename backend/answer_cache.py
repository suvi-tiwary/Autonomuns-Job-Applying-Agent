import json
import re
from typing import Optional, Dict, Any
import db
from models import QuestionCategory


def get_cached_or_adapted_answer(
    question: str,
    company: str,
    job_title: str,
    question_type: str = "DESCRIPTIVE"
) -> Optional[str]:
    """
    Retrieves reusable cached answer from database if available.
    For company-specific questions, adapts company name if from a previous session.
    """
    cached_record = db.get_cached_answer(question, company=company, question_type=question_type)
    if not cached_record:
        return None

    raw_answer = cached_record.get("answer", "")
    old_company = cached_record.get("company", "")

    if not raw_answer:
        return None

    # If same company, return cached answer directly
    if old_company and company and old_company.lower() == company.lower():
        return raw_answer

    # If company-specific question but different company, substitute company name cleanly
    if question_type in [QuestionCategory.WHY_COMPANY.value, QuestionCategory.COVER_LETTER.value]:
        if old_company and company:
            adapted = re.sub(re.escape(old_company), company, raw_answer, flags=re.IGNORECASE)
            return adapted
        return None  # Let LLM regenerate for different company if significant differences

    # For general project or achievement or experience questions, reuse directly
    return raw_answer


def cache_application_answer(
    question: str,
    answer: str,
    question_type: str = "DESCRIPTIVE",
    job_id: str = "",
    company: str = "",
    candidate_id: int = 1
):
    """
    Saves generated and validated answer to the application_answers database table.
    """
    if not question or not answer or len(answer.strip()) < 10:
        return

    try:
        db.save_application_answer(
            question=question,
            answer=answer.strip(),
            question_type=question_type,
            job_id=job_id,
            company=company,
            candidate_id=candidate_id
        )
    except Exception as e:
        print(f"[AnswerCache] Notice: could not cache answer: {e}")
