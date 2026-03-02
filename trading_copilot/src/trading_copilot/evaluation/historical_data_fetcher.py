"""Historical data fetcher for backtesting Trading Copilot predictions."""

from datetime import date, datetime, timezone

from trading_copilot.agents.news import NewsAgent
from trading_copilot.models import (
    AggregatedReport,
    AgentType,
    NewsArticle,
    NewsOutput,
)


class HistoricalDataFetcher:
    """Fetches historical news data for backtesting.
    
    This component retrieves past news articles for a specified date range
    using the existing NewsAgent, enabling evaluation of sentiment predictions
    against historical data.
    """

    def __init__(self, news_agent: NewsAgent) -> None:
        """Initialize with news agent.
        
        Args:
            news_agent: The NewsAgent instance to use for fetching news data.
        """
        self._news_agent = news_agent

    async def fetch(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> AggregatedReport:
        """Fetch news articles published within the date range.
        
        Retrieves historical news data for the specified ticker and date range,
        filtering to only include articles published within the look-back period.
        All timestamps are normalized to UTC timezone.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start of look-back period (inclusive)
            end_date: End of look-back period (inclusive)
            
        Returns:
            AggregatedReport with news data for the period. Returns empty result
            with status "no_data" when no articles are found.
        """
        # Fetch news using the existing NewsAgent
        # Pass date range to NewsAgent so it can filter at retrieval time
        news_output = await self._news_agent.research(
            ticker,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Filter articles to the specified date range
        filtered_articles = self._filter_articles_by_date_range(
            news_output.articles,
            start_date,
            end_date,
        )
        
        # Normalize all timestamps to UTC
        normalized_articles = self._normalize_timestamps_to_utc(filtered_articles)
        
        # Determine status based on filtered results
        if not normalized_articles:
            status = "no_data"
        else:
            status = news_output.status
        
        # Create filtered NewsOutput
        filtered_news_output = NewsOutput(
            ticker=ticker,
            articles=normalized_articles,
            retrieved_at=self._ensure_utc(datetime.now(timezone.utc)),
            status=status,
            data_source=news_output.data_source,
            error_message=news_output.error_message if not normalized_articles else None,
        )
        
        # Build AggregatedReport with only news data
        missing_components = [AgentType.EARNINGS, AgentType.MACRO, AgentType.REDDIT]
        
        return AggregatedReport(
            ticker=ticker,
            news=filtered_news_output,
            earnings=None,
            macro=None,
            reddit=None,
            aggregated_at=self._ensure_utc(datetime.now(timezone.utc)),
            missing_components=missing_components,
        )

    def _filter_articles_by_date_range(
        self,
        articles: list[NewsArticle],
        start_date: date,
        end_date: date,
    ) -> list[NewsArticle]:
        """Filter articles to only include those within the date range.
        
        Articles are included if their published_at date falls within
        the start_date and end_date (inclusive), regardless of whether
        the range spans week boundaries.
        
        Args:
            articles: List of news articles to filter
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of articles published within the date range
        """
        filtered = []
        for article in articles:
            # Ensure the timestamp is UTC for comparison
            article_dt = self._ensure_utc(article.published_at)
            article_date = article_dt.date()
            
            # Include articles within the date range (inclusive)
            if start_date <= article_date <= end_date:
                filtered.append(article)
        
        return filtered

    def _normalize_timestamps_to_utc(
        self,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:
        """Normalize all article timestamps to UTC timezone.
        
        Args:
            articles: List of news articles
            
        Returns:
            List of articles with UTC-normalized timestamps
        """
        normalized = []
        for article in articles:
            normalized_article = NewsArticle(
                headline=article.headline,
                source=article.source,
                published_at=self._ensure_utc(article.published_at),
                summary=article.summary,
                url=article.url,
                sentiment=article.sentiment,
            )
            normalized.append(normalized_article)
        
        return normalized

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensure a datetime is in UTC timezone.
        
        Args:
            dt: Datetime to normalize
            
        Returns:
            Datetime in UTC timezone
        """
        if dt.tzinfo is None:
            # Naive datetime - assume UTC
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            return dt.astimezone(timezone.utc)
