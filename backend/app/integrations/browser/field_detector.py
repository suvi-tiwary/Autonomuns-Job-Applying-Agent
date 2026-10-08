# backend/app/integrations/browser/field_detector.py
import re
from typing import Dict, Any, Optional, Tuple


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


def extract_character_and_word_limits(field: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    max_chars: Optional[int] = None
    max_words: Optional[int] = None

    raw_maxlength = field.get("maxlength")
    if raw_maxlength:
        try:
            val = int(raw_maxlength)
            if val > 0:
                max_chars = val
        except (ValueError, TypeError):
            pass

    text_context = " ".join([
        field.get("label", ""),
        field.get("placeholder", ""),
        field.get("aria_label", ""),
        field.get("surrounding_text", ""),
        field.get("parent_text", "")
    ]).lower()

    word_patterns = [
        r"(?:maximum|max|up to|limit|under|within|no more than)\s*[:\-]?\s*(\d+)\s*words?",
        r"(\d+)\s*words?\s*(?:maximum|max|limit|or less)",
        r"limit\s*[:\-]?\s*(\d+)\s*w\b"
    ]
    for pattern in word_patterns:
        match = re.search(pattern, text_context)
        if match:
            try:
                w_val = int(match.group(1))
                if 10 <= w_val <= 2000:
                    max_words = w_val
                    break
            except (ValueError, TypeError):
                pass

    char_patterns = [
        r"(?:maximum|max|up to|limit|under|within|no more than)\s*[:\-]?\s*(\d+)\s*char(?:acter)?s?",
        r"(\d+)\s*char(?:acter)?s?\s*(?:maximum|max|limit|or less)"
    ]
    for pattern in char_patterns:
        match = re.search(pattern, text_context)
        if match:
            try:
                c_val = int(match.group(1))
                if 20 <= c_val <= 10000:
                    if max_chars is None or c_val < max_chars:
                        max_chars = c_val
                    break
            except (ValueError, TypeError):
                pass

    return max_chars, max_words


def inspect_field_context(field: Dict[str, Any]) -> Dict[str, Any]:
    max_chars, max_words = extract_character_and_word_limits(field)
    label = field.get("label") or ""
    placeholder = field.get("placeholder") or ""
    aria_label = field.get("aria_label") or ""
    name = field.get("name") or ""
    field_id = field.get("id") or ""
    
    question = label or placeholder or aria_label or name or field_id or "Question"
    cleaned_question = re.sub(r"[\*:\s]+$", "", question).strip()

    return {
        **field,
        "question": cleaned_question,
        "raw_question": question,
        "max_chars": max_chars,
        "max_words": max_words,
        "is_textarea": field.get("tag", "").lower() == "textarea",
        "is_select": field.get("tag", "").lower() == "select",
        "is_checkbox": field.get("type", "").lower() in ["checkbox", "radio"]
    }


class FieldDetector:
    """Classifies extracted form elements and attaches question categories and constraints."""

    def detect_fields_with_context(self, raw_fields: list) -> list:
        from app.models.application import QuestionCategory
        results = []
        for f in raw_fields:
            ctx = inspect_field_context(f)
            q_lower = ctx["question"].lower()

            # Determine category
            if any(k in q_lower for k in ["email", "phone", "first name", "last name", "full name", "address", "city", "state", "zip", "location"]):
                ctx["category"] = QuestionCategory.CONTACT
            elif any(k in q_lower for k in ["degree", "college", "university", "gpa", "major", "graduation", "education", "school"]):
                ctx["category"] = QuestionCategory.EDUCATION
            elif any(k in q_lower for k in ["linkedin", "github", "portfolio", "website", "url"]):
                ctx["category"] = QuestionCategory.LINKS
            elif any(k in q_lower for k in ["experience", "years of experience", "work history", "employer"]):
                ctx["category"] = QuestionCategory.EXPERIENCE
            elif any(k in q_lower for k in ["project", "describe a project", "portfolio piece"]):
                ctx["category"] = QuestionCategory.PROJECTS
            elif any(k in q_lower for k in ["skill", "technologies", "languages", "tools"]):
                ctx["category"] = QuestionCategory.SKILLS
            elif any(k in q_lower for k in ["sponsor", "visa", "authorized", "authorization", "legally eligible"]):
                ctx["category"] = QuestionCategory.WORK_AUTHORIZATION
            elif any(k in q_lower for k in ["salary", "compensation", "stipend", "pay"]):
                ctx["category"] = QuestionCategory.SALARY
            elif any(k in q_lower for k in ["available", "start date", "notice period", "when can you start"]):
                ctx["category"] = QuestionCategory.AVAILABILITY
            elif any(k in q_lower for k in ["why do you want", "why this company", "why are you interested", "cover letter"]):
                ctx["category"] = QuestionCategory.WHY_COMPANY
            else:
                ctx["category"] = QuestionCategory.CUSTOM

            results.append(ctx)
        return results
