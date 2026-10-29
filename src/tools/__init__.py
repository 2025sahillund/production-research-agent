"""
Tool registry and discovery.
"""

from typing import Dict
from src.tools.base import BaseTool
from src.tools.search import WebSearchTool
from src.tools.scraper import ContentFetcherTool
from src.tools.tech_kb import TechKBTool
from src.tools.fact_checker import FactCheckerTool


def get_default_tools() -> Dict[str, BaseTool]:
    """Instantiate and return the standard tool suite."""
    tools = [
        WebSearchTool(),
        ContentFetcherTool(),
        TechKBTool(),
        FactCheckerTool()
    ]
    return {tool.name: tool for tool in tools}


__all__ = [
    "BaseTool",
    "WebSearchTool",
    "ContentFetcherTool",
    "TechKBTool",
    "FactCheckerTool",
    "get_default_tools"
]

