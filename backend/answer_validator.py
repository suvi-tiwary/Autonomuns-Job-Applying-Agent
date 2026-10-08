import re
from typing import Optional, Dict, Any


def clean_llm_output(text: str) -> str:
    """
    Cleans raw LLM response by stripping backticks, quotes, introductory filler,
    and trailing artifacts.
    """
    if not text:
        return ""

    cleaned = text.strip()

    # Remove markdown code blocks
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```markdown"):
        cleaned = cleaned[11:]
    elif cleaned.startswith("```text"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    # Remove surrounding double quotes if whole string is quoted
    if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) > 2:
        cleaned = cleaned[1:-1].strip()

    # Remove standard introductory phrases
    filler_patterns = [
        r"^(?:Here is (?:my|an|the|a) (?:answer|response|statement|cover letter)[:\-]?\s*)",
        r"^(?:Answer[:\-]?\s*)",
        r"^(?:Response[:\-]?\s*)",
        r"^(?:As an AI[^,\.\n]+[,\.\n]\s*)"
    ]
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

    return cleaned


def shorten_to_word_limit(text: str, max_words: int) -> str:
    """
    Shortens text to fit within max_words while preserving sentence boundaries where possible.
    """
    words = text.split()
    if len(words) <= max_words:
        return text

    # Truncate words
    truncated_words = words[:max_words]
    truncated_text = " ".join(truncated_words)

    # Try to end cleanly on a period, exclamation, or question mark
    last_punct = max(truncated_text.rfind("."), truncated_text.rfind("!"), truncated_text.rfind("?"))
    if last_punct > len(truncated_text) * 0.6:
        return truncated_text[:last_punct + 1].strip()

    return truncated_text.rstrip(",;:-") + "."


def shorten_to_char_limit(text: str, max_chars: int) -> str:
    """
    Shortens text to fit within max_chars while maintaining readability.
    """
    if len(text) <= max_chars:
        return text

    # Take slice allowing for clean cutoff
    slice_text = text[:max_chars - 3].strip()
    last_space = slice_text.rfind(" ")
    if last_space > len(slice_text) * 0.7:
        slice_text = slice_text[:last_space]

    # Clean punctuation
    slice_text = slice_text.rstrip(",;:-")
    if not slice_text.endswith("."):
        slice_text += "."

    return slice_text


def validate_and_refine_answer(
    answer: str,
    field_context: Optional[Dict[str, Any]] = None,
    default_max_words: int = 150
) -> str:
    """
    Main validation and refinement pipeline:
    1. Cleans introductory fillers and fences.
    2. Validates against detected word limit or default max words.
    3. Validates against detected maxlength / character limit.
    4. Ensures final text is ready to be directly typed into Playwright DOM.
    """
    if not answer:
        return ""

    cleaned = clean_llm_output(answer)
    if not cleaned:
        return ""

    max_chars = field_context.get("max_chars") if field_context else None
    max_words = field_context.get("max_words") if field_context else None

    # Apply word limit
    target_words = max_words or default_max_words
    if target_words:
        cleaned = shorten_to_word_limit(cleaned, target_words)

    # Apply char limit
    if max_chars and len(cleaned) > max_chars:
        cleaned = shorten_to_char_limit(cleaned, max_chars)

    return cleaned.strip()
