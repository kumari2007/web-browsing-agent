"""
Extensible LLM provider abstraction for NEXUS.
Supports local Ollama, OpenAI-compatible REST endpoints (OpenAI, Groq, OpenRouter, Gemini),
and deterministic fallback when offline or without API keys.
"""

import logging
import requests
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger("agent.rag.llm")


class BaseLLMProvider:
    """Base interface for all LLM providers."""

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        raise NotImplementedError

    def is_available(self) -> bool:
        return True


class OllamaProvider(BaseLLMProvider):
    """Local Ollama LLM provider."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout_seconds

    def is_available(self) -> bool:
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            return res.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 1024
            }
        }
        try:
            logger.info(f"Invoking Ollama ({self.model}) at {self.base_url}...")
            res = requests.post(url, json=payload, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                text = data.get("response", "").strip()
                if text:
                    return text
            logger.warning(f"Ollama returned HTTP status {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"Ollama generation failed or timed out: {e}")
        return None


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI-compatible LLM provider (OpenAI, Groq, OpenRouter, Gemini, LocalAI)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.api_key = api_key or settings.openai_api_key or ""
        self.base_url = (base_url or settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
        self.model = model or settings.openai_model or "gpt-4o-mini"
        self.timeout = timeout or 60

    def is_available(self) -> bool:
        return bool(self.api_key.strip())

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        if not self.api_key:
            logger.warning("OpenAI-compatible provider invoked without API key.")
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024
        }
        try:
            logger.info(f"Invoking OpenAI-compatible model ({self.model}) at {self.base_url}...")
            res = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
            logger.warning(f"OpenAI provider returned HTTP status {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"OpenAI provider generation failed: {e}")
        return None


class DeterministicFallbackProvider(BaseLLMProvider):
    """Fallback provider that signals caller to use deterministic rule-based grounded synthesis."""

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        return None


def get_llm_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None
) -> BaseLLMProvider:
    """Factory creating configured LLM provider instance."""
    name = (provider_name or settings.llm_provider).lower().strip()

    if name in {"openai", "groq", "openrouter", "gemini"}:
        # Set default base URL for groq / openrouter if not specified
        custom_base = base_url or settings.openai_base_url
        if not custom_base:
            if name == "groq":
                custom_base = "https://api.groq.com/openai/v1"
            elif name == "openrouter":
                custom_base = "https://openrouter.ai/api/v1"
        return OpenAICompatibleProvider(
            api_key=api_key or settings.openai_api_key,
            base_url=custom_base,
            model=model or settings.openai_model
        )
    elif name == "ollama":
        return OllamaProvider(
            base_url=base_url or settings.ollama_base_url,
            model=model or settings.ollama_model
        )
    else:
        return DeterministicFallbackProvider()
