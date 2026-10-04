"""Factory for creating LLM Provider instances based on configuration."""

from typing import Optional

from app.ai.providers.base import LLMProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.core.config import Settings
from app.core.config import settings as global_settings


def get_llm_provider(settings: Optional[Settings] = None) -> LLMProvider:
    """
    Return the configured LLMProvider instance.
    If provider is 'gemini' and API key is provided, returns GeminiProvider.
    If provider is 'mock' or API key is absent, returns MockLLMProvider safely.
    """
    cfg = settings or global_settings
    provider_name = (cfg.llm_provider or "mock").lower()

    if provider_name == "gemini":
        if cfg.llm_api_key:
            return GeminiProvider(
                api_key=cfg.llm_api_key,
                model=cfg.llm_model,
                timeout_seconds=cfg.llm_timeout_seconds,
            )
        # Fallback to Mock if Gemini key not set in dev/test environment
        return MockLLMProvider()

    if provider_name == "mock":
        return MockLLMProvider()

    # Default fallback
    return MockLLMProvider()
