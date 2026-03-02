"""Unit tests for HistoricalDataFetcher."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from trading_copilot.agents.news import NewsAgent
from trading_copilot.evaluation.historical_data_fetcher import HistoricalDataFetcher
from trading_copilot.models import (
    AgentType,
    ArticleSentiment,
    NewsArticle,
    NewsOutput,
)


@pytest.fixture
def mock_news_agent():
    """Create a mock NewsAgent."""
    agent = MagicMock(spec=NewsAgent)
    agent.research = AsyncMock()
    return agent


@pytest.fixture
def sample_articles():
    """Create sample news articles for testing."""
    return [
        NewsArticle(
            headline="Article 1",
            source="Source A",
            published_at=datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc),
            summary="Summary 1",
            url="https://example.com/1",
            sentiment=ArticleSentiment.POSITIVE,
        ),
        NewsArticle(
            headline="Article 2",
            source="Source B",
            published_at=datetime(2024, 1, 15, 8, 30, 0, tzinfo=timezone.utc),
            summary="Summary 2",
            url="https://example.com/2",
            sentiment=ArticleSentiment.NEGATIVE,
        ),
        NewsArticle(
            headline="Article 3",
            source="Source C",
            published_at=datetime(2024, 1, 20, 14, 0, 0, tzinfo=timezone.utc),
            summary="Summary 3",
            url="https://example.com/3",
            sentiment=ArticleSentiment.NEUTRAL,
        ),
    ]


class TestHistoricalDataFetcher:
    """Tests for HistoricalDataFetcher class."""

    @pytest.mark.asyncio
    async def test_fetch_filters_articles_by_date_range(
        self, mock_news_agent, sample_articles
    ):
        """Test that fetch filters articles to the specified date range.
        
        Validates: Requirements 1.1, 1.5
        """
        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=sample_articles,
            retrieved_at=datetime.now(timezone.utc),
            status="success",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 15),
        )

        # Should only include articles from Jan 10-15
        assert len(result.news.articles) == 2
        headlines = [a.headline for a in result.news.articles]
        assert "Article 1" in headlines
        assert "Article 2" in headlines
        assert "Article 3" not in headlines

    @pytest.mark.asyncio
    async def test_fetch_returns_no_data_when_no_articles_in_range(
        self, mock_news_agent, sample_articles
    ):
        """Test that fetch returns status 'no_data' when no articles match.
        
        Validates: Requirement 1.3
        """
        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=sample_articles,
            retrieved_at=datetime.now(timezone.utc),
            status="success",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 2, 1),  # No articles in February
            end_date=date(2024, 2, 14),
        )

        assert result.news.status == "no_data"
        assert len(result.news.articles) == 0

    @pytest.mark.asyncio
    async def test_fetch_returns_no_data_when_source_has_no_articles(
        self, mock_news_agent
    ):
        """Test that fetch returns status 'no_data' when source returns empty.
        
        Validates: Requirement 1.3
        """
        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=[],
            retrieved_at=datetime.now(timezone.utc),
            status="no_data",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 14),
        )

        assert result.news.status == "no_data"
        assert len(result.news.articles) == 0

    @pytest.mark.asyncio
    async def test_fetch_normalizes_timestamps_to_utc(self, mock_news_agent):
        """Test that all timestamps are normalized to UTC.
        
        Validates: Requirement 1.4
        """
        # Create article with non-UTC timezone
        from datetime import timedelta

        pst = timezone(timedelta(hours=-8))
        article_with_pst = NewsArticle(
            headline="PST Article",
            source="Source",
            published_at=datetime(2024, 1, 10, 8, 0, 0, tzinfo=pst),  # 8 AM PST
            summary="Summary",
            url="https://example.com",
            sentiment=ArticleSentiment.NEUTRAL,
        )

        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=[article_with_pst],
            retrieved_at=datetime.now(timezone.utc),
            status="success",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 10),
        )

        # Verify timestamp is in UTC
        assert len(result.news.articles) == 1
        article = result.news.articles[0]
        assert article.published_at.tzinfo == timezone.utc
        # 8 AM PST = 4 PM UTC
        assert article.published_at.hour == 16

    @pytest.mark.asyncio
    async def test_fetch_includes_articles_from_week_boundaries(
        self, mock_news_agent
    ):
        """Test that articles from both partial weeks are included.
        
        Validates: Requirement 1.5
        """
        # Create articles spanning a week boundary (Sunday Jan 7 to Saturday Jan 13)
        articles = [
            NewsArticle(
                headline="Saturday Article",
                source="Source",
                published_at=datetime(2024, 1, 6, 12, 0, 0, tzinfo=timezone.utc),  # Saturday
                summary="Summary",
                url="https://example.com/1",
                sentiment=ArticleSentiment.NEUTRAL,
            ),
            NewsArticle(
                headline="Sunday Article",
                source="Source",
                published_at=datetime(2024, 1, 7, 12, 0, 0, tzinfo=timezone.utc),  # Sunday
                summary="Summary",
                url="https://example.com/2",
                sentiment=ArticleSentiment.NEUTRAL,
            ),
            NewsArticle(
                headline="Monday Article",
                source="Source",
                published_at=datetime(2024, 1, 8, 12, 0, 0, tzinfo=timezone.utc),  # Monday
                summary="Summary",
                url="https://example.com/3",
                sentiment=ArticleSentiment.NEUTRAL,
            ),
        ]

        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=articles,
            retrieved_at=datetime.now(timezone.utc),
            status="success",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        # Date range spans week boundary
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 6),  # Saturday
            end_date=date(2024, 1, 8),    # Monday
        )

        # All three articles should be included
        assert len(result.news.articles) == 3

    @pytest.mark.asyncio
    async def test_fetch_uses_existing_news_agent(self, mock_news_agent):
        """Test that fetch uses the same data sources via NewsAgent.
        
        Validates: Requirement 1.2
        """
        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=[],
            retrieved_at=datetime.now(timezone.utc),
            status="no_data",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 14),
        )

        # Verify NewsAgent.research was called with the ticker
        mock_news_agent.research.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_fetch_returns_aggregated_report_structure(
        self, mock_news_agent, sample_articles
    ):
        """Test that fetch returns properly structured AggregatedReport."""
        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=sample_articles,
            retrieved_at=datetime.now(timezone.utc),
            status="success",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        # Verify AggregatedReport structure
        assert result.ticker == "AAPL"
        assert result.news is not None
        assert result.earnings is None
        assert result.macro is None
        assert AgentType.EARNINGS in result.missing_components
        assert AgentType.MACRO in result.missing_components
        assert result.aggregated_at.tzinfo == timezone.utc

    @pytest.mark.asyncio
    async def test_fetch_handles_naive_datetime(self, mock_news_agent):
        """Test that naive datetimes are handled correctly (assumed UTC)."""
        # Create article with naive datetime (no timezone)
        article_naive = NewsArticle(
            headline="Naive Article",
            source="Source",
            published_at=datetime(2024, 1, 10, 12, 0, 0),  # No timezone
            summary="Summary",
            url="https://example.com",
            sentiment=ArticleSentiment.NEUTRAL,
        )

        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=[article_naive],
            retrieved_at=datetime.now(timezone.utc),
            status="success",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 10),
        )

        # Verify timestamp is now UTC
        assert len(result.news.articles) == 1
        article = result.news.articles[0]
        assert article.published_at.tzinfo == timezone.utc

    @pytest.mark.asyncio
    async def test_fetch_inclusive_date_boundaries(self, mock_news_agent):
        """Test that start and end dates are inclusive."""
        articles = [
            NewsArticle(
                headline="Start Day Article",
                source="Source",
                published_at=datetime(2024, 1, 10, 0, 0, 1, tzinfo=timezone.utc),  # Just after midnight
                summary="Summary",
                url="https://example.com/1",
                sentiment=ArticleSentiment.NEUTRAL,
            ),
            NewsArticle(
                headline="End Day Article",
                source="Source",
                published_at=datetime(2024, 1, 15, 23, 59, 59, tzinfo=timezone.utc),  # Just before midnight
                summary="Summary",
                url="https://example.com/2",
                sentiment=ArticleSentiment.NEUTRAL,
            ),
        ]

        mock_news_agent.research.return_value = NewsOutput(
            ticker="AAPL",
            articles=articles,
            retrieved_at=datetime.now(timezone.utc),
            status="success",
            data_source="api",
        )

        fetcher = HistoricalDataFetcher(mock_news_agent)
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 15),
        )

        # Both articles should be included (boundaries are inclusive)
        assert len(result.news.articles) == 2
