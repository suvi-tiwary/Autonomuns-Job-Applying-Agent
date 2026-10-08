import re
from typing import Dict, Any, Optional, Tuple


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


def extract_character_and_word_limits(field: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    """
    Detects maximum character limit and maximum word limit from DOM attributes
    and surrounding instruction text.
    Returns (max_chars, max_words).
    """
    max_chars: Optional[int] = None
    max_words: Optional[int] = None

    # 1. Inspect HTML maxlength attribute
    raw_maxlength = field.get("maxlength")
    if raw_maxlength:
        try:
            val = int(raw_maxlength)
            if val > 0:
                max_chars = val
        except (ValueError, TypeError):
            pass

    # 2. Combine textual signals
    text_context = " ".join([
        field.get("label", ""),
        field.get("placeholder", ""),
        field.get("aria_label", ""),
        field.get("surrounding_text", ""),
        field.get("parent_text", "")
    ]).lower()

    # Regex patterns for word limits
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

    # Regex patterns for character limits
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
    """
    Enriches raw field dictionary with normalized contextual cues and limit detection.
    """
    max_chars, max_words = extract_character_and_word_limits(field)
    
    label = field.get("label") or ""
    placeholder = field.get("placeholder") or ""
    aria_label = field.get("aria_label") or ""
    name = field.get("name") or ""
    field_id = field.get("id") or ""
    
    # Primary visible prompt / question
    question = label or placeholder or aria_label or name or field_id or "Question"
    
    # Clean up trailing asterisks or colons from label
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
