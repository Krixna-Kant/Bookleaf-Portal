from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class LLMProvider:
    name = "base"

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, timeout: float) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "openai/gpt-oss-120b",
                "temperature": 0.2,
                "max_tokens": 500,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=self.timeout,
        )
        if response.status_code == 429:
            raise LLMError("Groq rate-limited the request")
        if response.status_code >= 400:
            raise LLMError(f"Groq error {response.status_code}: {response.text[:240]}")
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, timeout: float) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        response = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            params={"key": self.api_key},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
            },
            timeout=self.timeout,
        )
        if response.status_code == 429:
            raise LLMError("Gemini rate-limited the request")
        if response.status_code >= 400:
            raise LLMError(f"Gemini error {response.status_code}")
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def get_provider() -> LLMProvider | None:
    settings = get_settings()
    timeout = settings.ai_timeout_seconds
    provider = settings.ai_provider.lower().strip()
    if provider == "groq" and settings.groq_api_key:
        return GroqProvider(settings.groq_api_key, timeout)
    if provider == "gemini" and settings.gemini_api_key:
        return GeminiProvider(settings.gemini_api_key, timeout)
    if provider == "groq" and settings.gemini_api_key:
        return GeminiProvider(settings.gemini_api_key, timeout)
    if provider == "gemini" and settings.groq_api_key:
        return GroqProvider(settings.groq_api_key, timeout)
    logger.info("No free LLM key configured; AI calls will be skipped")
    return None
