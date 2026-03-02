"""News research agent for Trading Copilot."""

import os
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

import httpx

from trading_copilot.agents.base import (
    APIAuthenticationError,
    APIConnectionError,
    AgentExecutionError,
    ResearchAgent,
    WebSearchError,
)
from trading_copilot.models import AgentType, ArticleSentiment, NewsArticle, NewsOutput, SourceConfig


class NewsAgent(ResearchAgent):
    """Gathers and analyzes market news."""

    SIMILARITY_THRESHOLD = 0.9  # 90% similarity for deduplication

    def __init__(self, sources: list[SourceConfig], bedrock_client=None):
        """
        Initialize NewsAgent.

        Args:
            sources: List of news data source configurations
            bedrock_client: Optional Bedrock client for sentiment analysis
        """
        super().__init__(sources)
        self._bedrock_client = bedrock_client
        self._http_client = httpx.AsyncClient(timeout=30.0)

    def get_agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.NEWS

    async def research(self, ticker: str) -> NewsOutput:
        """
        Retrieve news articles from past 14 days.

        Uses API sources if available, falls back to web search otherwise.

        Args:
            ticker: Validated stock ticker symbol

        Returns:
            NewsOutput with articles and metadata
        """
        if self._has_api_keys():
            return await self._research_via_api(ticker)
        else:
            return await self._research_via_web_search(ticker)

    async def _research_via_api(self, ticker: str) -> NewsOutput:
        """
        Fetch news using configured API sources.

        Args:
            ticker: Validated stock ticker symbol

        Returns:
            NewsOutput with articles from API sources
        """
        all_articles: list[NewsArticle] = []
        errors: list[str] = []

        for source in self._sources:
            if not source.enabled:
                continue

            try:
                articles = await self._fetch_from_source(ticker, source)
                all_articles.extend(articles)
            except (APIConnectionError, APIAuthenticationError) as e:
                errors.append(f"{source.name}: {str(e)}")
            except Exception as e:
                errors.append(f"{source.name}: Unexpected error - {str(e)}")

        # If all API calls failed, fall back to web search
        if not all_articles and errors:
            return await self._research_via_web_search(ticker)

        # Filter to past 14 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
        filtered_articles = self._filter_by_date(all_articles, cutoff_date)

        # Deduplicate
        deduplicated = self.deduplicate(filtered_articles)

        # Categorize sentiment for each article
        for article in deduplicated:
            if article.sentiment == ArticleSentiment.NEUTRAL:
                article.sentiment = self.categorize_sentiment(article)

        # Determine status
        if not deduplicated and not errors:
            status = "no_data"
        elif deduplicated and not errors:
            status = "success"
        elif deduplicated and errors:
            status = "partial"
        else:
            status = "no_data"

        return NewsOutput(
            ticker=ticker,
            articles=deduplicated,
            retrieved_at=datetime.now(timezone.utc),
            status=status,
            data_source="api",
            error_message="; ".join(errors) if errors else None,
        )

    async def _research_via_web_search(self, ticker: str) -> NewsOutput:
        """
        Fetch news using web search fallback.

        Args:
            ticker: Validated stock ticker symbol

        Returns:
            NewsOutput with articles from web search
        """
        try:
            query = f"{ticker} stock news"
            results = await self._web_search_fallback(ticker, query)

            if not results:
                return NewsOutput(
                    ticker=ticker,
                    articles=[],
                    retrieved_at=datetime.now(timezone.utc),
                    status="no_data",
                    data_source="web_search",
                    error_message="No results from web search",
                )

            articles = self._parse_web_results(results)

            # Filter to past 14 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
            filtered_articles = self._filter_by_date(articles, cutoff_date)

            # Deduplicate
            deduplicated = self.deduplicate(filtered_articles)

            # Categorize sentiment
            for article in deduplicated:
                if article.sentiment == ArticleSentiment.NEUTRAL:
                    article.sentiment = self.categorize_sentiment(article)

            status = "success" if deduplicated else "no_data"

            return NewsOutput(
                ticker=ticker,
                articles=deduplicated,
                retrieved_at=datetime.now(timezone.utc),
                status=status,
                data_source="web_search",
                error_message=None,
            )
        except WebSearchError as e:
            return NewsOutput(
                ticker=ticker,
                articles=[],
                retrieved_at=datetime.now(timezone.utc),
                status="no_data",
                data_source="web_search",
                error_message=str(e),
            )

    def _parse_web_results(self, results: list[dict]) -> list[NewsArticle]:
        """
        Parse web search results into NewsArticle objects.

        Args:
            results: List of search result dictionaries from multiple RSS feeds

        Returns:
            List of NewsArticle objects
        """
        articles = []
        for result in results:
            try:
                # Parse published date
                published_str = result.get("published_at", "")
                if published_str:
                    try:
                        # Handle ISO format from RSS parser
                        published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                    except ValueError:
                        published_at = datetime.now(timezone.utc)
                else:
                    published_at = datetime.now(timezone.utc)

                # Clean up the snippet (remove HTML if present)
                # Priority: snippet > summary > title
                snippet = result.get("snippet") or result.get("summary") or result.get("title", "")
                if "<" in snippet:
                    # Remove HTML tags if present
                    from bs4 import BeautifulSoup
                    snippet = BeautifulSoup(snippet, 'html.parser').get_text()

                # Extract actual source from description
                source = result.get("source", "Unknown")
                if snippet and " - " in snippet:
                    # Format is usually "Source - Article snippet"
                    potential_source = snippet.split(" - ")[0].strip()
                    # If it looks like a source name (not too long, has recognizable patterns)
                    if len(potential_source) < 50 and not potential_source.lower().startswith(('the ', 'a ', 'an ')):
                        source = potential_source
                        # Remove source from snippet
                        snippet = " - ".join(snippet.split(" - ")[1:])

                articles.append(
                    NewsArticle(
                        headline=result.get("title", ""),
                        source=source,
                        published_at=published_at,
                        summary=snippet.strip(),
                        url=result.get("url", ""),
                        sentiment=ArticleSentiment.NEUTRAL,
                    )
                )
            except (ValueError, KeyError) as e:
                continue

        return articles

    async def _fetch_from_source(
        self, ticker: str, source: SourceConfig
    ) -> list[NewsArticle]:
        """Fetch news from a specific source."""
        api_key = os.environ.get(source.api_key_env)
        if not api_key:
            raise APIAuthenticationError(f"API key not found in {source.api_key_env}")

        if "alphavantage" in source.api_endpoint.lower():
            return await self._fetch_alpha_vantage(ticker, source.api_endpoint, api_key)
        elif "finnhub" in source.api_endpoint.lower():
            return await self._fetch_finnhub(ticker, source.api_endpoint, api_key)
        else:
            raise AgentExecutionError(f"Unknown news source: {source.name}")

    async def _fetch_alpha_vantage(
        self, ticker: str, endpoint: str, api_key: str
    ) -> list[NewsArticle]:
        """Fetch news from Alpha Vantage API."""
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": api_key,
            "limit": 50,
        }

        try:
            response = await self._http_client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Failed to connect to Alpha Vantage: {e}")
        except httpx.HTTPStatusError as e:
            raise APIConnectionError(f"Alpha Vantage API error: {e}")

        articles = []
        for item in data.get("feed", []):
            try:
                published_at = datetime.strptime(
                    item.get("time_published", "")[:15], "%Y%m%dT%H%M%S"
                ).replace(tzinfo=timezone.utc)

                # Map Alpha Vantage sentiment to our enum
                av_sentiment = item.get("overall_sentiment_label", "Neutral")
                sentiment = self._map_sentiment(av_sentiment)

                articles.append(
                    NewsArticle(
                        headline=item.get("title", ""),
                        source=item.get("source", "Unknown"),
                        published_at=published_at,
                        summary=item.get("summary", ""),
                        url=item.get("url", ""),
                        sentiment=sentiment,
                    )
                )
            except (ValueError, KeyError):
                continue

        return articles

    async def _fetch_finnhub(
        self, ticker: str, endpoint: str, api_key: str
    ) -> list[NewsArticle]:
        """Fetch news from Finnhub API."""
        today = datetime.now(timezone.utc)
        from_date = (today - timedelta(days=14)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")

        params = {
            "symbol": ticker,
            "from": from_date,
            "to": to_date,
            "token": api_key,
        }

        try:
            response = await self._http_client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Failed to connect to Finnhub: {e}")
        except httpx.HTTPStatusError as e:
            raise APIConnectionError(f"Finnhub API error: {e}")

        articles = []
        for item in data if isinstance(data, list) else []:
            try:
                published_at = datetime.fromtimestamp(
                    item.get("datetime", 0), tz=timezone.utc
                )

                articles.append(
                    NewsArticle(
                        headline=item.get("headline", ""),
                        source=item.get("source", "Unknown"),
                        published_at=published_at,
                        summary=item.get("summary", ""),
                        url=item.get("url", ""),
                        sentiment=ArticleSentiment.NEUTRAL,  # Finnhub doesn't provide sentiment
                    )
                )
            except (ValueError, KeyError):
                continue

        return articles

    def _map_sentiment(self, sentiment_label: str) -> ArticleSentiment:
        """Map external sentiment labels to ArticleSentiment enum."""
        label = sentiment_label.lower()
        if "bullish" in label or "positive" in label:
            return ArticleSentiment.POSITIVE
        elif "bearish" in label or "negative" in label:
            return ArticleSentiment.NEGATIVE
        return ArticleSentiment.NEUTRAL

    def _filter_by_date(
        self, articles: list[NewsArticle], cutoff: datetime
    ) -> list[NewsArticle]:
        """Filter articles to only include those after cutoff date."""
        return [a for a in articles if a.published_at >= cutoff]

    def deduplicate(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """
        Remove duplicate or substantially similar news articles.

        Uses headline similarity to detect duplicates.
        """
        if not articles:
            return []

        unique: list[NewsArticle] = []
        seen_headlines: list[str] = []

        for article in articles:
            is_duplicate = False
            for seen in seen_headlines:
                similarity = SequenceMatcher(
                    None, article.headline.lower(), seen.lower()
                ).ratio()
                if similarity >= self.SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(article)
                seen_headlines.append(article.headline)

        return unique

    def categorize_sentiment(self, article: NewsArticle) -> ArticleSentiment:
        """
        Classify article as positive, negative, or neutral.

        Uses simple keyword-based classification for MVP.
        Can be enhanced with Claude via Bedrock later.
        """
        text = f"{article.headline} {article.summary}".lower()

        positive_keywords = [
            "surge", "soar", "jump", "gain", "rise", "beat", "exceed",
            "strong", "growth", "profit", "bullish", "upgrade", "buy",
            "outperform", "record", "breakthrough", "success", "positive",
        ]
        negative_keywords = [
            "fall", "drop", "plunge", "decline", "loss", "miss", "weak",
            "bearish", "downgrade", "sell", "underperform", "warning",
            "concern", "risk", "lawsuit", "investigation", "negative",
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        if positive_count > negative_count:
            return ArticleSentiment.POSITIVE
        elif negative_count > positive_count:
            return ArticleSentiment.NEGATIVE
        return ArticleSentiment.NEUTRAL

    async def close(self):
        """Close the HTTP client."""
        await self._http_client.aclose()
