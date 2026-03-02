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

        Args:
            ticker: Validated stock ticker symbol

        Returns:
            NewsOutput with articles and metadata
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
            error_message="; ".join(errors) if errors else None,
        )

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
