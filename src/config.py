"""
Global configuration and environment parameters.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    # Model configuration
    DEFAULT_LLM_PROVIDER: str = "mock"  # "openai", "gemini", "groq", or "mock"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", None)
    
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Reliability & Resilience Policies
    TOOL_TIMEOUT_SECONDS: float = 6.0
    TOOL_MAX_RETRIES: int = 2
    RETRY_BACKOFF_FACTOR: float = 0.5
    MAX_SEARCH_RESULTS: int = 5
    MAX_SCRAPED_CHARS: int = 4000
    
    # Filtering & Guardrail Thresholds
    MIN_SOURCE_RELEVANCE_SCORE: float = 0.45
    PROMPT_INJECTION_PROTECTION: bool = True
    CACHE_TOOL_CALLS: bool = True
    ENABLE_JUDGE_STEP: bool = True


settings = AgentSettings()
