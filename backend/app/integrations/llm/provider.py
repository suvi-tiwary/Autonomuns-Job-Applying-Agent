# backend/app/integrations/llm/provider.py
import json
import os
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class LLMProvider(ABC):
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
    FALLBACK_MODELS = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "mixtral-8x7b-32768"
    ]

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = (api_key or settings.GROQ_API_KEY).strip()
        self.primary_model = model or settings.GROQ_MODEL or "openai/gpt-oss-120b"

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
                    "User-Agent": "JobMateAI/2.0"
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
                logger.warning(f"Groq API HTTP Error {e.code} on model {model_name}: {error_body[:200]}")
                last_error = f"HTTP {e.code}: {error_body}"
                if e.code in [429, 404, 400, 500, 503]:
                    time.sleep(0.4)
                    continue
                else:
                    break
            except Exception as e:
                logger.warning(f"Groq connection error on model {model_name}: {e}")
                last_error = str(e)
                time.sleep(0.4)
                continue

        raise RuntimeError(f"All Groq models failed. Last error: {last_error}")


class FallbackFactProvider(LLMProvider):
    def is_configured(self) -> bool:
        return True

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 500,
        response_format: Optional[str] = None
    ) -> str:
        return ""


_llm_instance: Optional[LLMProvider] = None

def get_llm_provider(preferred_model: Optional[str] = None) -> LLMProvider:
    global _llm_instance
    if _llm_instance is None:
        if settings.GROQ_API_KEY:
            _llm_instance = GroqProvider(model=preferred_model)
        else:
            _llm_instance = FallbackFactProvider()
    return _llm_instance
