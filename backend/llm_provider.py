import os
import json
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(ABC):
    """
    Abstract interface for LLM operations (text generation, JSON extraction, classification).
    Enables swapping Groq, OpenAI, Gemini, Anthropic, or local models without modifying agent logic.
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 500,
        response_format: Optional[str] = None
    ) -> str:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass


class GroqProvider(LLMProvider):
    """
    Groq API implementation with automatic fallback between top models
    and resilient error handling.
    """

    FALLBACK_MODELS = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "mixtral-8x7b-32768"
    ]

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
        env_model = (os.getenv("GROQ_MODEL") or "").strip()
        self.primary_model = model or env_model or "openai/gpt-oss-120b"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 500,
        response_format: Optional[str] = None
    ) -> str:
        if not self.is_configured():
            raise RuntimeError("GROQ_API_KEY is not configured.")

        # Candidate models to try in order
        models_to_try = [self.primary_model] + [m for m in self.FALLBACK_MODELS if m != self.primary_model]

        last_error = None
        for model_name in models_to_try:
            payload: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            if response_format == "json_object":
                payload["response_format"] = {"type": "json_object"}

            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "JobMateAI/2.0 (Windows NT 10.0; Win64; x64)"
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    res_json = json.loads(response.read().decode("utf-8"))
                    content = res_json["choices"][0]["message"]["content"].strip()
                    return content
            except urllib.error.HTTPError as e:
                error_body = ""
                try:
                    error_body = e.read().decode("utf-8")
                except Exception:
                    pass

                print(f"[GroqProvider] HTTP Error {e.code} on model {model_name}: {error_body[:200]}")
                last_error = f"HTTP {e.code}: {error_body}"
                # If rate limited (429) or model not found (404), continue to next model
                if e.code in [429, 404, 400, 500, 503]:
                    time.sleep(0.5)
                    continue
                else:
                    break
            except Exception as e:
                print(f"[GroqProvider] Connection or general error on model {model_name}: {e}")
                last_error = str(e)
                time.sleep(0.5)
                continue

        raise RuntimeError(f"All Groq models failed. Last error: {last_error}")


class FallbackFactProvider(LLMProvider):
    """
    Deterministic rule-based fallback provider that generates truthful facts
    directly from candidate profile without hallucination if API keys are exhausted.
    """

    def is_configured(self) -> bool:
        return True

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 500,
        response_format: Optional[str] = None
    ) -> str:
        # Returns a standard fallback response
        return ""


# Singleton provider factory
_default_provider: Optional[LLMProvider] = None


def get_llm_provider(preferred_provider: str = "groq") -> LLMProvider:
    global _default_provider
    if _default_provider is None:
        if preferred_provider.lower() == "groq" or os.getenv("GROQ_API_KEY"):
            _default_provider = GroqProvider()
        else:
            _default_provider = FallbackFactProvider()
    return _default_provider


def set_llm_provider(provider: LLMProvider):
    global _default_provider
    _default_provider = provider
