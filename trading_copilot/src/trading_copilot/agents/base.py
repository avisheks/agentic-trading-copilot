"""Base class for research agents."""

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
