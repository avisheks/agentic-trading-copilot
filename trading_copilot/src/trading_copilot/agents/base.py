"""Base class for research agents."""

import os
from abc import ABC, abstractmethod
from typing import Any

from trading_copilot.models import AgentType, SourceConfig


class AgentError(Exception):
    """Base exception for agent errors."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent exceeds time limit."""

    pass


class AgentExecutionError(AgentError):
    """Raised when agent encounters an unhandled exception."""

    pass


class APIConnectionError(AgentError):
    """Raised when network connection to API fails."""

    pass


class APIRateLimitError(AgentError):
    """Raised when API rate limit is exceeded."""

    pass


class APIAuthenticationError(AgentError):
    """Raised when API authentication fails."""

    pass


class WebSearchError(AgentError):
    """Raised when web search fallback fails."""

    pass


class ResearchAgent(ABC):
    """Base class for all research agents."""

    def __init__(self, sources: list[SourceConfig]):
        """
        Initialize with data source configurations.

        Args:
            sources: List of configured data sources for this agent
        """
        self._sources = sources

    @property
    def sources(self) -> list[SourceConfig]:
        """Get configured data sources."""
        return self._sources

    @abstractmethod
    async def research(self, ticker: str) -> Any:
        """
        Execute research for the given ticker.

        Args:
            ticker: Validated stock ticker symbol

        Returns:
            Research output specific to the agent type

        Raises:
            AgentTimeoutError: If research exceeds time limit
            AgentExecutionError: If an unhandled error occurs
            APIConnectionError: If API connection fails
        """
        pass

    @abstractmethod
    def get_agent_type(self) -> AgentType:
        """Return the type of this agent."""
        pass

    def _has_api_keys(self) -> bool:
        """
        Check if required API keys are configured.

        Returns:
            True if at least one enabled source has its API key set
        """
        for source in self._sources:
            if source.enabled and os.environ.get(source.api_key_env):
                return True
        return False

    async def _web_search_fallback(self, ticker: str, query: str) -> list[dict]:
        """
        Perform web search as fallback when APIs unavailable.

        This is a placeholder that returns mock data for MVP.
        In production, this would integrate with a web search API.

        Args:
            ticker: Stock ticker symbol
            query: Search query string

        Returns:
            List of search result dictionaries
        """
        # MVP: Return empty list - subclasses can override with actual implementation
        return []

    def _parse_web_results(self, results: list[dict]) -> Any:
        """
        Parse web search results into structured output.

        Subclasses should override this to parse results into their specific output type.

        Args:
            results: List of search result dictionaries

        Returns:
            Parsed output specific to the agent type
        """
        raise NotImplementedError("Subclasses must implement _parse_web_results")
