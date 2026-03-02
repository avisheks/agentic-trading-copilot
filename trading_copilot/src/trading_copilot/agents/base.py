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
        Perform web search using multiple RSS feeds.

        Fetches from Google News, CNBC, WSJ, and Bloomberg RSS feeds.

        Args:
            ticker: Stock ticker symbol
            query: Search query string

        Returns:
            List of search result dictionaries with title, link, published_at, snippet
        """
        import httpx
        from bs4 import BeautifulSoup
        from datetime import datetime, timezone
        
        all_results = []
        
        # Define RSS feed sources
        rss_feeds = [
            {
                "url": f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en",
                "source_name": "Google News",
                "limit": 30
            },
            {
                "url": f"https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
                "source_name": "CNBC",
                "limit": 20
            },
            {
                "url": f"https://feeds.content.dowjones.io/public/rss/mw_topstories",
                "source_name": "MarketWatch",
                "limit": 20
            },
            {
                "url": f"https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
                "source_name": "WSJ Markets",
                "limit": 20
            }
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for feed in rss_feeds:
                try:
                    response = await client.get(feed["url"])
                    response.raise_for_status()
                    
                    # Parse RSS feed
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')
                    
                    for item in items[:feed["limit"]]:
                        try:
                            title = item.find('title').text if item.find('title') else ""
                            
                            # Skip if ticker not mentioned in title
                            if ticker.upper() not in title.upper():
                                continue
                            
                            link = item.find('link').text if item.find('link') else ""
                            pub_date = item.find('pubDate').text if item.find('pubDate') else ""
                            description = item.find('description').text if item.find('description') else ""
                            
                            # Parse publication date
                            published_at = None
                            if pub_date:
                                try:
                                    from email.utils import parsedate_to_datetime
                                    published_at = parsedate_to_datetime(pub_date).isoformat()
                                except:
                                    published_at = datetime.now(timezone.utc).isoformat()
                            else:
                                published_at = datetime.now(timezone.utc).isoformat()
                            
                            # Extract source from title (Google News format: "Title - Source")
                            source = feed["source_name"]
                            if " - " in title:
                                # Source is typically at the end after the last " - "
                                potential_source = title.split(" - ")[-1].strip()
                                if len(potential_source) < 50:  # Reasonable source name length
                                    source = potential_source
                            
                            all_results.append({
                                "title": title,
                                "url": link,
                                "published_at": published_at,
                                "snippet": description if description else title,
                                "source": source,
                            })
                        except Exception:
                            continue
                            
                except Exception:
                    # If one feed fails, continue with others
                    continue
        
        if not all_results:
            raise WebSearchError(f"No results from any RSS feeds for {ticker}")
        
        return all_results

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
