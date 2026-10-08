# backend/app/agents/answer_validator.py
import re
from typing import Optional, Dict, Any


class AnswerValidator:
    @staticmethod
    def clean_llm_output(text: str) -> str:
        if not text:
            return ""

        cleaned = text.strip()
        if cleaned.startswith("```json"): cleaned = cleaned[7:]
        elif cleaned.startswith("```markdown"): cleaned = cleaned[11:]
        elif cleaned.startswith("```text"): cleaned = cleaned[7:]
        elif cleaned.startswith("```"): cleaned = cleaned[3:]

        if cleaned.endswith("```"): cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) > 2:
            cleaned = cleaned[1:-1].strip()

        filler_patterns = [
            r"^(?:Here is (?:my|an|the|a) (?:answer|response|statement|cover letter)[:\-]?\s*)",
            r"^(?:Answer[:\-]?\s*)",
            r"^(?:Response[:\-]?\s*)",
            r"^(?:As an AI[^,\.\n]+[,\.\n]\s*)"
        ]
        for pattern in filler_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

        return cleaned

    @staticmethod
    def shorten_to_word_limit(text: str, max_words: int) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text

        truncated_words = words[:max_words]
        truncated_text = " ".join(truncated_words)

        last_punct = max(truncated_text.rfind("."), truncated_text.rfind("!"), truncated_text.rfind("?"))
        if last_punct > len(truncated_text) * 0.6:
            return truncated_text[:last_punct + 1].strip()

        return truncated_text.rstrip(",;:-") + "."

    @staticmethod
    def shorten_to_char_limit(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text

        slice_text = text[:max_chars - 3].strip()
        last_space = slice_text.rfind(" ")
        if last_space > len(slice_text) * 0.7:
            slice_text = slice_text[:last_space]

        slice_text = slice_text.rstrip(",;:-")
        if not slice_text.endswith("."):
            slice_text += "."

        return slice_text

    @classmethod
    def validate_and_refine_answer(
        cls,
        answer: str,
        field_context: Optional[Dict[str, Any]] = None,
        default_max_words: int = 150
    ) -> str:
        if not answer:
            return ""

        cleaned = cls.clean_llm_output(answer)
        if not cleaned:
            return ""

        max_chars = field_context.get("max_chars") if field_context else None
        max_words = field_context.get("max_words") if field_context else default_max_words
        target_words = max_words or default_max_words

        if target_words:
            cleaned = cls.shorten_to_word_limit(cleaned, target_words)

        if max_chars and len(cleaned) > max_chars:
            cleaned = cls.shorten_to_char_limit(cleaned, max_chars)

        return cleaned.strip()


answer_validator = AnswerValidator()
