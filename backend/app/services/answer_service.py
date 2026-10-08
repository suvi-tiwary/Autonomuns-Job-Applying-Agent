# backend/app/services/answer_service.py
import re
from typing import Optional, Dict, Any
from app.core.database import get_db
from app.models.application import QuestionCategory


def normalize_question(text: str) -> str:
    clean = re.sub(r"[^\w\s]", "", (text or "").lower())
    return " ".join(clean.split())


class AnswerService:
    @staticmethod
    def get_cached_answer(
        question: str,
        company: str = "",
        job_title: str = "",
        question_type: str = "DESCRIPTIVE",
        user_id: str = "user_default"
    ) -> Optional[str]:
        if not question:
            return None

        norm_q = normalize_question(question)
        with get_db() as conn:
            cursor = conn.cursor()

            # 1. Exact match for same user & same company
            if company:
                cursor.execute("""
                    SELECT answer, company FROM application_answers
                    WHERE normalized_question = ? AND LOWER(company) = LOWER(?) AND (user_id = ? OR user_id = 'user_default')
                    ORDER BY updated_at DESC LIMIT 1
                """, (norm_q, company, user_id))
                row = cursor.fetchone()
                if row and row["answer"]:
                    return row["answer"]

            # 2. General question across companies
            if question_type not in [QuestionCategory.WHY_COMPANY.value, QuestionCategory.COVER_LETTER.value]:
                cursor.execute("""
                    SELECT answer, company FROM application_answers
                    WHERE normalized_question = ? AND (user_id = ? OR user_id = 'user_default')
                    ORDER BY updated_at DESC LIMIT 1
                """, (norm_q, user_id))
                row = cursor.fetchone()
                if row and row["answer"]:
                    return row["answer"]

            # 3. Company-specific question from previous session -> adapt company name
            if company and question_type in [QuestionCategory.WHY_COMPANY.value, QuestionCategory.COVER_LETTER.value]:
                cursor.execute("""
                    SELECT answer, company FROM application_answers
                    WHERE normalized_question = ? AND (user_id = ? OR user_id = 'user_default')
                    ORDER BY updated_at DESC LIMIT 1
                """, (norm_q, user_id))
                row = cursor.fetchone()
                if row and row["answer"] and row["company"]:
                    adapted = re.sub(re.escape(row["company"]), company, row["answer"], flags=re.IGNORECASE)
                    return adapted

        return None

    @staticmethod
    def cache_answer(
        question: str,
        answer: str,
        question_type: str = "DESCRIPTIVE",
        job_id: str = "",
        company: str = "",
        user_id: str = "user_default"
    ):
        if not question or not answer or len(answer.strip()) < 10:
            return

        norm_q = normalize_question(question)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO application_answers (
                    user_id, question, normalized_question, question_type, answer, job_id, company
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, question, norm_q, question_type, answer.strip(), job_id, company))
            conn.commit()


answer_service = AnswerService()
