"""Tests for News Agent."""

from datetime import datetime, timedelta, timezone

import pytest

from trading_copilot.agents.news import NewsAgent
from trading_copilot.models import ArticleSentiment, NewsArticle, SourceConfig


class TestNewsAgent:
    """Unit tests for NewsAgent."""

    def setup_method(self):
        self.sources = [
            SourceConfig(
                name="Test News",
                api_endpoint="https://test.com/news",
                api_key_env="TEST_API_KEY",
                added_at=datetime.now(timezone.utc),
                enabled=True,
            )
        ]
        self.agent = NewsAgent(sources=self.sources)

    def test_get_agent_type(self):
        """Agent returns correct type."""
        from trading_copilot.models import AgentType
        assert self.agent.get_agent_type() == AgentType.NEWS

    def test_deduplicate_removes_exact_duplicates(self):
        """Deduplication removes articles with identical headlines."""
        now = datetime.now(timezone.utc)
        articles = [
            NewsArticle(
                headline="Apple reports record earnings",
                source="Source A",
                published_at=now,
                summary="Summary 1",
                url="https://a.com/1",
                sentiment=ArticleSentiment.POSITIVE,
            ),
            NewsArticle(
                headline="Apple reports record earnings",
                source="Source B",
                published_at=now,
                summary="Summary 2",
                url="https://b.com/1",
                sentiment=ArticleSentiment.POSITIVE,
            ),
        ]

        result = self.agent.deduplicate(articles)
        assert len(result) == 1
        assert result[0].source == "Source A"

    def test_deduplicate_removes_similar_headlines(self):
        """Deduplication removes articles with >90% similar headlines."""
        now = datetime.now(timezone.utc)
        articles = [
            NewsArticle(
                headline="Apple reports record earnings for Q4",
                source="Source A",
                published_at=now,
                summary="Summary 1",
                url="https://a.com/1",
                sentiment=ArticleSentiment.POSITIVE,
            ),
            NewsArticle(
                headline="Apple reports record earnings for Q4!",
                source="Source B",
                published_at=now,
                summary="Summary 2",
                url="https://b.com/1",
                sentiment=ArticleSentiment.POSITIVE,
            ),
        ]

        result = self.agent.deduplicate(articles)
        assert len(result) == 1

    def test_deduplicate_keeps_different_headlines(self):
        """Deduplication keeps articles with different headlines."""
        now = datetime.now(timezone.utc)
        articles = [
            NewsArticle(
                headline="Apple reports record earnings",
                source="Source A",
                published_at=now,
                summary="Summary 1",
                url="https://a.com/1",
                sentiment=ArticleSentiment.POSITIVE,
            ),
            NewsArticle(
                headline="Microsoft announces new product",
                source="Source B",
                published_at=now,
                summary="Summary 2",
                url="https://b.com/1",
                sentiment=ArticleSentiment.NEUTRAL,
            ),
        ]

        result = self.agent.deduplicate(articles)
        assert len(result) == 2

    def test_deduplicate_empty_list(self):
        """Deduplication handles empty list."""
        result = self.agent.deduplicate([])
        assert result == []

    def test_deduplicate_output_length_lte_input(self):
        """Deduplication output length is always <= input length."""
        now = datetime.now(timezone.utc)
        articles = [
            NewsArticle(
                headline=f"Headline {i}",
                source="Source",
                published_at=now,
                summary="Summary",
                url=f"https://test.com/{i}",
                sentiment=ArticleSentiment.NEUTRAL,
            )
            for i in range(10)
        ]

        result = self.agent.deduplicate(articles)
        assert len(result) <= len(articles)

    def test_categorize_sentiment_positive(self):
        """Categorization detects positive sentiment."""
        article = NewsArticle(
            headline="Stock surges on strong earnings beat",
            source="Test",
            published_at=datetime.now(timezone.utc),
            summary="Company exceeded expectations with record growth",
            url="https://test.com",
            sentiment=ArticleSentiment.NEUTRAL,
        )

        result = self.agent.categorize_sentiment(article)
        assert result == ArticleSentiment.POSITIVE

    def test_categorize_sentiment_negative(self):
        """Categorization detects negative sentiment."""
        article = NewsArticle(
            headline="Stock plunges on weak guidance",
            source="Test",
            published_at=datetime.now(timezone.utc),
            summary="Company warns of declining sales and loss concerns",
            url="https://test.com",
            sentiment=ArticleSentiment.NEUTRAL,
        )

        result = self.agent.categorize_sentiment(article)
        assert result == ArticleSentiment.NEGATIVE

    def test_categorize_sentiment_neutral(self):
        """Categorization returns neutral for balanced content."""
        article = NewsArticle(
            headline="Company announces quarterly results",
            source="Test",
            published_at=datetime.now(timezone.utc),
            summary="The company reported its financial results today",
            url="https://test.com",
            sentiment=ArticleSentiment.NEUTRAL,
        )

        result = self.agent.categorize_sentiment(article)
        assert result == ArticleSentiment.NEUTRAL

    def test_filter_by_date(self):
        """Date filtering removes old articles."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=14)

        articles = [
            NewsArticle(
                headline="Recent news",
                source="Test",
                published_at=now - timedelta(days=1),
                summary="Summary",
                url="https://test.com/1",
                sentiment=ArticleSentiment.NEUTRAL,
            ),
            NewsArticle(
                headline="Old news",
                source="Test",
                published_at=now - timedelta(days=20),
                summary="Summary",
                url="https://test.com/2",
                sentiment=ArticleSentiment.NEUTRAL,
            ),
        ]

        result = self.agent._filter_by_date(articles, cutoff)
        assert len(result) == 1
        assert result[0].headline == "Recent news"

    def test_map_sentiment_positive(self):
        """Sentiment mapping handles positive labels."""
        assert self.agent._map_sentiment("Bullish") == ArticleSentiment.POSITIVE
        assert self.agent._map_sentiment("Somewhat-Bullish") == ArticleSentiment.POSITIVE
        assert self.agent._map_sentiment("positive") == ArticleSentiment.POSITIVE

    def test_map_sentiment_negative(self):
        """Sentiment mapping handles negative labels."""
        assert self.agent._map_sentiment("Bearish") == ArticleSentiment.NEGATIVE
        assert self.agent._map_sentiment("Somewhat-Bearish") == ArticleSentiment.NEGATIVE
        assert self.agent._map_sentiment("negative") == ArticleSentiment.NEGATIVE

    def test_map_sentiment_neutral(self):
        """Sentiment mapping handles neutral labels."""
        assert self.agent._map_sentiment("Neutral") == ArticleSentiment.NEUTRAL
        assert self.agent._map_sentiment("Unknown") == ArticleSentiment.NEUTRAL


class TestNewsArticleCompleteness:
    """Tests for news article completeness (Property 3)."""

    def test_article_has_required_fields(self):
        """NewsArticle contains all required non-empty fields."""
        article = NewsArticle(
            headline="Test headline",
            source="Test source",
            published_at=datetime.now(timezone.utc),
            summary="Test summary",
            url="https://test.com",
            sentiment=ArticleSentiment.NEUTRAL,
        )

        assert article.headline and len(article.headline) > 0
        assert article.source and len(article.source) > 0
        assert article.published_at is not None
        assert article.summary and len(article.summary) > 0
