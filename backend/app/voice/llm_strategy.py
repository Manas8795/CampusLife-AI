"""
Strategy Pattern — LLM Provider Selection (Module 7 / Module 8)
================================================================
Formally implements the GoF Strategy Pattern for LLM inference.

Each concrete strategy encapsulates one provider (Ollama, OpenAI, Local Domain Engine).
The LocalStudentLLM selects the highest-priority available strategy at runtime —
adding a new provider (Gemini, Groq, etc.) simply requires adding a new subclass
without touching any existing code. (Open/Closed Principle — SOLID)

Class Hierarchy:
  LLMStrategy (ABC)
    ├── OllamaStrategy
    ├── OpenAIStrategy
    └── LocalDomainStrategy   ← guaranteed fallback, zero external dependencies

Usage:
  strategy = OllamaStrategy(url="http://127.0.0.1:11434", model="llama3.2:1b")
  result = strategy.generate(prompt, system_prompt)
"""

import re
import json
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger("campuslife.llm_strategy")


class LLMStrategy(ABC):
    """
    Abstract base class for all LLM provider strategies.
    Concrete subclasses implement generate() with provider-specific HTTP calls.
    """

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str) -> Optional[str]:
        """
        Send a prompt to the LLM provider and return the plain-text reply.
        Returns None if the provider is unavailable or the call fails.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """
        Quickly check whether this provider is reachable (health check).
        Should complete within 500ms.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for logging and API response attribution."""
        ...

    # ------------------------------------------------------------------
    # Shared helper: strip prompt echo / boilerplate from LLM output
    # ------------------------------------------------------------------
    @staticmethod
    def _clean(text: str) -> str:
        if not text:
            return ""
        clean = text.strip()
        echo_patterns = [
            r"^Current Real-World Local Time:\s*.*?\n",
            r"^Local Time:\s*.*?\n",
            r"^Student User:\s*['\"].*?['\"]\s*",
            r"^Student:\s*['\"].*?['\"]\s*",
            r"^Intent:\s*[A-Z_]+\s*",
            r"^Tool Executed:\s*[a-z_]+\s*",
            r"^Data:\s*.*?\n",
            r"^Contextual Database Signals:\s*.*?\n",
            r"^Short conversational English reply:\s*",
            r"^Respond concisely.*?\n",
        ]
        for pat in echo_patterns:
            clean = re.sub(pat, "", clean, flags=re.MULTILINE | re.IGNORECASE).strip()
        return clean


# ---------------------------------------------------------------------------
# Concrete Strategy 1: Ollama Local Server
# ---------------------------------------------------------------------------
class OllamaStrategy(LLMStrategy):
    """
    Concrete strategy: Ollama local inference server (llama3.2, phi3, mistral…).
    Uses the /api/chat endpoint with optimised parameters for low-latency CPU inference.
    """

    _availability_cache: Optional[bool] = None
    _last_check: float = 0.0
    _CACHE_TTL = 5.0  # seconds

    def __init__(self, url: str, model: str):
        self._url = url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return f"Ollama Local Engine ({self._model})"

    def is_available(self) -> bool:
        now = time.time()
        if self._availability_cache is not None and (now - self._last_check) < self._CACHE_TTL:
            return self._availability_cache
        try:
            req = urllib.request.Request(
                f"{self._url}/api/tags",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=0.25) as res:
                available = res.status == 200
        except Exception:
            available = False
        self._availability_cache = available
        self._last_check = now
        return available

    def get_active_model(self) -> str:
        """Returns the first available model name or falls back to configured model."""
        try:
            req = urllib.request.Request(
                f"{self._url}/api/tags",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=0.5) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", [])]
                    if models:
                        return models[0]
        except Exception:
            pass
        return self._model

    def generate(self, prompt: str, system_prompt: str) -> Optional[str]:
        if not self.is_available():
            return None
        model = self.get_active_model()
        english_system = (
            f"{system_prompt} "
            "Respond exclusively in fluent, articulate English with full sentences and detailed explanations. Never cut off mid-sentence."
        )
        try:
            payload = json.dumps(
                {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": english_system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "keep_alive": "60m",
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 450,
                        "num_ctx": 2048,
                        "num_thread": 8,
                    },
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{self._url}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=25.0) as res:
                if res.status == 200:
                    resp = json.loads(res.read().decode("utf-8"))
                    ans = resp.get("message", {}).get("content", "").strip()
                    if ans:
                        cleaned = self._clean(ans)
                        logger.debug("ollama_response_received", extra={"model": model, "length": len(cleaned)})
                        return cleaned
        except Exception as exc:
            logger.warning("ollama_call_failed", extra={"error": str(exc)})
        return None


# ---------------------------------------------------------------------------
# Concrete Strategy 2: OpenAI API
# ---------------------------------------------------------------------------
class OpenAIStrategy(LLMStrategy):
    """
    Concrete strategy: OpenAI gpt-4o-mini cloud inference.
    Only active when OPENAI_API_KEY is configured in environment settings.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "OpenAI gpt-4o-mini"

    def is_available(self) -> bool:
        return bool(self._api_key)

    def generate(self, prompt: str, system_prompt: str) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            payload = json.dumps(
                {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 600,
                    "temperature": 0.5,
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=5.0) as res:
                if res.status == 200:
                    resp = json.loads(res.read().decode("utf-8"))
                    ans = resp["choices"][0]["message"]["content"].strip()
                    if ans:
                        return self._clean(ans)
        except Exception as exc:
            logger.warning("openai_call_failed", extra={"error": str(exc)})
        return None


# ---------------------------------------------------------------------------
# Concrete Strategy 3: Local Domain Engine (guaranteed English fallback)
# ---------------------------------------------------------------------------
class LocalDomainStrategy(LLMStrategy):
    """
    Concrete strategy: Deterministic local student domain engine.
    Zero external dependencies — guaranteed to return English output.
    Used as the final fallback in the strategy chain.
    """

    @property
    def name(self) -> str:
        return "CampusLife Local Domain Engine (English Enforced)"

    def is_available(self) -> bool:
        return True  # Always available — no external dependencies

    def generate(self, prompt: str, system_prompt: str) -> Optional[str]:
        # Delegate to the existing _dynamic_student_intelligence method
        # This is a thin adapter — the engine is fully owned by LocalStudentLLM
        return None  # Signals caller to use its own domain engine


# ---------------------------------------------------------------------------
# Strategy Chain Factory
# ---------------------------------------------------------------------------
def build_strategy_chain(settings) -> list:
    """
    Constructs the ordered strategy chain from application settings.
    Priority: Ollama → OpenAI → Local Domain Engine.
    New providers can be inserted here without touching any other code.
    """
    chain = [
        OllamaStrategy(url=settings.LOCAL_LLM_URL, model=settings.LOCAL_LLM_MODEL),
    ]
    if settings.OPENAI_API_KEY:
        chain.append(OpenAIStrategy(api_key=settings.OPENAI_API_KEY))
    # LocalDomainStrategy is always the final fallback — handled specially in LocalStudentLLM
    return chain
