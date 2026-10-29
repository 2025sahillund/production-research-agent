"""
Base Tool definition with built-in resilience:
- Execution timing & metrics
- Timeout & retry behavior (tenacity)
- Caching layer
- Malformed output protection
- Prompt injection detection & sanitization
"""

import time
import re
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.schema import ToolResult
from src.config import settings

logger = logging.getLogger(__name__)

# Pattern to detect common indirect prompt injection payloads in retrieved web text
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s*:\s*you\s+are\s+now",
    r"disregard\s+the\s+above",
    r"you\s+must\s+output\s+the\s+following",
    r"new\s+system\s+prompt\s*:",
    r"<\|im_start\|>",
    r"<\|system\|>",
    r"delete\s+all\s+files",
]


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool description"

    def __init__(self):
        self._cache: Dict[str, ToolResult] = {}

    @abstractmethod
    def _run(self, **kwargs) -> Any:
        """Internal execution method implemented by subclasses."""
        pass

    def execute(self, **kwargs) -> ToolResult:
        """
        Public execution wrapper providing:
        - Input logging
        - Caching
        - Retry logic with backoff
        - Error boundary (never raises an unhandled exception into the agent loop)
        - Output sanitization
        """
        cache_key = f"{self.name}:{sorted(kwargs.items())}"
        if settings.CACHE_TOOL_CALLS and cache_key in self._cache:
            cached_result = self._cache[cache_key].model_copy()
            cached_result.cached = True
            logger.info(f"[{self.name}] Returning cached result for {kwargs}")
            return cached_result

        start_time = time.perf_counter()
        query_repr = str(kwargs.get("query") or kwargs.get("url") or kwargs.get("topic") or kwargs)
        
        retries = 0
        last_error = None

        while retries <= settings.TOOL_MAX_RETRIES:
            try:
                raw_data = self._run(**kwargs)
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                
                # Check and sanitize output for security
                sanitized = False
                warning = None
                if settings.PROMPT_INJECTION_PROTECTION and isinstance(raw_data, (str, list, dict)):
                    cleaned_data, detected = self._sanitize_prompt_injection(raw_data)
                    if detected:
                        sanitized = True
                        warning = "Warning: Potential prompt injection signature detected and neutralized."
                        raw_data = cleaned_data

                result = ToolResult(
                    tool_name=self.name,
                    query=query_repr,
                    success=True,
                    status_code=200,
                    data=raw_data,
                    latency_ms=latency_ms,
                    sanitized=sanitized,
                    warning=warning
                )
                
                if settings.CACHE_TOOL_CALLS:
                    self._cache[cache_key] = result
                
                return result

            except Exception as e:
                last_error = str(e)
                retries += 1
                logger.warning(f"[{self.name}] Error on attempt {retries}/{settings.TOOL_MAX_RETRIES + 1}: {e}")
                if retries <= settings.TOOL_MAX_RETRIES:
                    time.sleep(settings.RETRY_BACKOFF_FACTOR * (2 ** (retries - 1)))

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        # Graceful failure return: do not crash the agent orchestrator
        return ToolResult(
            tool_name=self.name,
            query=query_repr,
            success=False,
            status_code=500,
            data=None,
            error=f"Tool execution failed after {settings.TOOL_MAX_RETRIES + 1} attempts: {last_error}",
            latency_ms=latency_ms
        )

    def _sanitize_prompt_injection(self, data: Any) -> tuple[Any, bool]:
        """Detect and defang potential prompt injection attacks in retrieved content."""
        detected = False
        
        def clean_text(text: str) -> str:
            nonlocal detected
            cleaned = text
            for pattern in INJECTION_PATTERNS:
                if re.search(pattern, cleaned, re.IGNORECASE):
                    detected = True
                    cleaned = re.sub(pattern, "[REDACTED_UNTRUSTED_INSTRUCTION]", cleaned, flags=re.IGNORECASE)
            return cleaned

        if isinstance(data, str):
            return clean_text(data), detected
        elif isinstance(data, list):
            cleaned_list = []
            for item in data:
                if isinstance(item, dict):
                    cleaned_dict = {k: clean_text(v) if isinstance(v, str) else v for k, v in item.items()}
                    cleaned_list.append(cleaned_dict)
                elif isinstance(item, str):
                    cleaned_list.append(clean_text(item))
                else:
                    cleaned_list.append(item)
            return cleaned_list, detected
        elif isinstance(data, dict):
            cleaned_dict = {k: clean_text(v) if isinstance(v, str) else v for k, v in data.items()}
            return cleaned_dict, detected
        
        return data, False
