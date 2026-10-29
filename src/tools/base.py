"""
Base Tool definition with built-in resilience:
- Execution timing & metrics
- Timeout & retry behavior (tenacity)
- Caching layer
- Malformed output protection
- Multi-vector Prompt Injection detection & sanitization
- Telemetry attributes (retrieval counts, origin, retries)
"""

import time
import re
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.schema import ToolResult
from src.config import settings

logger = logging.getLogger(__name__)

# Comprehensive pattern registry for detecting indirect prompt injections in retrieved web content
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"system\s*:\s*you\s+are\s+now",
    r"new\s+system\s+prompt\s*:",
    r"you\s+are\s+now\s+in\s+(developer|unrestricted|god|dan)\s+mode",
    r"you\s+must\s+(now\s+)?output\s+the\s+following",
    r"print\s+(your\s+)?(system\s+prompt|initial\s+instructions)",
    r"<\|im_start\|>",
    r"<\|system\|>",
    r"\[INST\]",
    r"<<SYS>>",
    r"delete\s+all\s+(files|data|records)",
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
        - Telemetry provenance recording
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
                        warning = "Security: Potential indirect prompt injection pattern detected and sanitized."
                        raw_data = cleaned_data

                # Extract telemetry signals
                retrieved_count = 1
                filtered_count = 0
                origin_type = "local"
                fallback_triggered = False

                if isinstance(raw_data, dict):
                    retrieved_count = raw_data.get("total_retrieved", 1 if raw_data.get("found") or raw_data.get("success") else 0)
                    filtered_count = raw_data.get("discarded_noise_count", 0)
                    mode_val = raw_data.get("mode")
                    if mode_val == "live_web":
                        origin_type = "live_web"
                    elif mode_val == "fallback_index":
                        origin_type = "fallback_index"
                        fallback_triggered = True
                    elif self.name == "tech_kb":
                        origin_type = "curated_kb"
                    elif self.name == "content_fetcher":
                        origin_type = "scraped_page" if not raw_data.get("simulated") else "fallback_index"
                    elif self.name == "fact_checker":
                        origin_type = "verification_rule"

                result = ToolResult(
                    tool_name=self.name,
                    query=query_repr,
                    success=True,
                    status_code=200,
                    data=raw_data,
                    latency_ms=latency_ms,
                    sanitized=sanitized,
                    warning=warning,
                    retrieved_count=retrieved_count,
                    filtered_count=filtered_count,
                    origin_type=origin_type,
                    retry_count=retries,
                    fallback_triggered=fallback_triggered
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
            latency_ms=latency_ms,
            retry_count=retries - 1,
            origin_type="error"
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
