"""Preservation property tests for web search date filter bugfix.

This test file contains property-based tests that verify the EXISTING behavior
is preserved after the bugfix is implemented. These tests MUST PASS on both
unfixed and fixed code.

**Property 2: Preservation** - Default Behavior Without Date Parameters

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5

Preservation Requirements:
- When NewsAgent.research() is called without date parameters, the default
  14-day lookback filter must continue to work
- When NewsAgent._research_via_api() is called, the existing API fetching
  and date filtering logic must remain unchanged
- Article deduplication and sentiment categorization must remain unchanged
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, settings, strategies as st

from trading_copilot.agents.news import NewsAgent
from trading_copilot.models import ArticleSentiment, NewsArticle, SourceConfig


# =============================================================================
# Test Fixtures
# =============================================================================

def create_news_agent_with_web_search_fallback() -> NewsAgent:
    """Create a NewsAgent configured to use web search fallback (no API keys)."""
    sources = [
        SourceConfig(
            name="Test News",
            api_endpoint="https://test.com/news",
            api_key_env="NONEXISTENT_API_KEY",  # Ensures web search fallback
            added_at=datetime.now(timezone.utc),
            enabled=True,
        )
    ]
    return NewsAgent(sources=sources)



def create_news_agent_with_api() -> NewsAgent:
    """Create a NewsAgent configured to use API sources."""
    sources = [
        SourceConfig(
            name="Alpha Vantage",
            api_endpoint="https://www.alphavantage.co/query",
            api_key_env="ALPHA_VANTAGE_API_KEY",
            added_at=datetime.now(timezone.utc),
            enabled=True,
        )
    ]
    return NewsAgent(sources=sources)


def create_mock_web_search_results(
    include_recent: bool = True,
    include_old: bool = True,
) -> list[dict]:
    """Create mock web search results with various dates."""
    now = datetime.now(timezone.utc)
    results = []
    
    if include_recent:
        # Articles within 14-day window
        for i in range(3):
            article_date = now - timedelta(days=i + 1)
            results.append({
                "title": f"Recent Article {i}",
                "source": "Test Source",
                "published_at": article_date.isoformat(),
                "snippet": f"Recent article {i} content",
                "url": f"https://test.com/recent/{i}",
            })
    
    if include_old:
        # Articles outside 14-day window
        for i in range(3):
            article_date = now - timedelta(days=20 + i)
            results.append({
                "title": f"Old Article {i}",
                "source": "Test Source",
                "published_at": article_date.isoformat(),
                "snippet": f"Old article {i} content",
                "url": f"https://test.com/old/{i}",
            })
    
    return results


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def ticker_strategy(draw):
    """Generate valid stock ticker symbols."""
    return draw(st.sampled_from(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA"]))


@st.composite
def article_date_strategy(draw):
    """Generate article dates spanning both within and outside 14-day window."""
    now = datetime.now(timezone.utc)
    days_ago = draw(st.integers(min_value=0, max_value=30))
    return now - timedelta(days=days_ago)


@st.composite
def mock_article_strategy(draw):
    """Generate mock web search result dictionaries."""
    article_date = draw(article_date_strategy())
    idx = draw(st.integers(min_value=0, max_value=1000))
    
    return {
        "title": f"Test Article {idx}",
        "source": "Test Source",
        "published_at": article_date.isoformat(),
        "snippet": f"Test article {idx} content about stocks",
        "url": f"https://test.com/article/{idx}",
    }



# =============================================================================
# Preservation Property Tests
# =============================================================================

class TestPreservationDefaultBehavior:
    """
    Property 2: Preservation - Default Behavior Without Date Parameters
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    
    These tests verify that the existing behavior is preserved when no date
    parameters are passed to NewsAgent.research().
    
    Preservation Requirements:
    - Default 14-day lookback filter continues to work (3.1)
    - API fetching and date filtering logic unchanged (3.2)
    - Timestamp normalization unchanged (3.3)
    - RSS feed parsing unchanged (3.4)
    - Deduplication and sentiment categorization unchanged (3.5)
    
    **IMPORTANT**: These tests MUST PASS on UNFIXED code.
    They establish the baseline behavior that must be preserved.
    """

    @pytest.mark.asyncio
    @given(ticker=ticker_strategy())
    @settings(max_examples=10, deadline=None)
    async def test_research_without_date_params_uses_14_day_lookback(
        self,
        ticker: str,
    ):
        """
        **Validates: Requirements 3.1**
        
        When research() is called without date parameters, the default
        14-day lookback filter must continue to work.
        
        This test verifies that:
        1. research(ticker) without date params still works
        2. Articles older than 14 days are filtered out
        3. Articles within 14 days are included
        """
        agent = create_news_agent_with_web_search_fallback()
        
        # Create mock results with both recent and old articles
        mock_results = create_mock_web_search_results(
            include_recent=True,
            include_old=True,
        )
        
        with patch.object(agent, '_web_search_fallback', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = mock_results
            
            # Call research WITHOUT date parameters (preservation case)
            result = await agent.research(ticker)
            
            # Verify the call succeeded
            assert result is not None
            assert result.ticker == ticker
            
            # Verify 14-day lookback filter is applied
            cutoff = datetime.now(timezone.utc) - timedelta(days=14)
            for article in result.articles:
                assert article.published_at >= cutoff, (
                    f"Article from {article.published_at} should have been filtered out. "
                    f"Cutoff is {cutoff}. Default 14-day lookback not preserved."
                )
        
        await agent.close()


    @pytest.mark.asyncio
    @given(
        ticker=ticker_strategy(),
        mock_articles=st.lists(mock_article_strategy(), min_size=1, max_size=10),
    )
    @settings(max_examples=15, deadline=None)
    async def test_web_search_filters_articles_by_14_day_cutoff(
        self,
        ticker: str,
        mock_articles: list[dict],
    ):
        """
        **Validates: Requirements 3.1, 3.4**
        
        Property: For all calls to _research_via_web_search() without date
        parameters, articles are filtered using the 14-day lookback from today.
        
        This verifies the default filtering behavior is preserved.
        """
        agent = create_news_agent_with_web_search_fallback()
        
        with patch.object(agent, '_web_search_fallback', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = mock_articles
            
            # Call _research_via_web_search WITHOUT date parameters
            result = await agent._research_via_web_search(ticker)
            
            # Verify result structure
            assert result is not None
            assert result.ticker == ticker
            assert result.data_source == "web_search"
            
            # Verify 14-day cutoff is applied
            cutoff = datetime.now(timezone.utc) - timedelta(days=14)
            for article in result.articles:
                assert article.published_at >= cutoff, (
                    f"Article dated {article.published_at} should be filtered. "
                    f"14-day cutoff: {cutoff}"
                )
        
        await agent.close()

    @pytest.mark.asyncio
    async def test_concrete_14_day_lookback_preservation(self):
        """
        **Validates: Requirements 3.1**
        
        Concrete test demonstrating the 14-day lookback behavior is preserved.
        """
        agent = create_news_agent_with_web_search_fallback()
        now = datetime.now(timezone.utc)
        
        # Create articles at specific dates with distinct headlines to avoid deduplication
        mock_results = [
            # Within 14 days - should be included
            {
                "title": "Breaking: Tech stocks surge on earnings report",
                "source": "Test",
                "published_at": (now - timedelta(days=1)).isoformat(),
                "snippet": "Recent news",
                "url": "https://test.com/1",
            },
            {
                "title": "Market analysis shows positive trends for Q1",
                "source": "Test",
                "published_at": (now - timedelta(days=7)).isoformat(),
                "snippet": "Still recent",
                "url": "https://test.com/7",
            },
            # Outside 14 days - should be filtered out
            {
                "title": "Federal Reserve announces interest rate decision",
                "source": "Test",
                "published_at": (now - timedelta(days=15)).isoformat(),
                "snippet": "Old news",
                "url": "https://test.com/15",
            },
            {
                "title": "Annual report reveals company growth metrics",
                "source": "Test",
                "published_at": (now - timedelta(days=30)).isoformat(),
                "snippet": "Very old",
                "url": "https://test.com/30",
            },
        ]
        
        with patch.object(agent, '_web_search_fallback', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = mock_results
            
            result = await agent.research("AAPL")
            
            # Should have exactly 2 articles (within 14 days)
            assert len(result.articles) == 2, (
                f"Expected 2 articles within 14-day window, got {len(result.articles)}. "
                f"14-day lookback filter not preserved."
            )
            
            # Verify the correct articles are included (recent ones)
            headlines = {a.headline for a in result.articles}
            assert "Breaking: Tech stocks surge on earnings report" in headlines
            assert "Market analysis shows positive trends for Q1" in headlines
            # Old articles should be filtered out
            assert "Federal Reserve announces interest rate decision" not in headlines
            assert "Annual report reveals company growth metrics" not in headlines
        
        await agent.close()



class TestPreservationDeduplication:
    """
    **Validates: Requirements 3.5**
    
    Tests that article deduplication continues to work as before.
    """

    @pytest.mark.asyncio
    @given(ticker=ticker_strategy())
    @settings(max_examples=10, deadline=None)
    async def test_deduplication_preserved_in_web_search(
        self,
        ticker: str,
    ):
        """
        **Validates: Requirements 3.5**
        
        Deduplication must continue to work when research() is called
        without date parameters.
        """
        agent = create_news_agent_with_web_search_fallback()
        now = datetime.now(timezone.utc)
        
        # Create duplicate articles
        mock_results = [
            {
                "title": "Breaking: Stock surges on earnings",
                "source": "Source A",
                "published_at": (now - timedelta(days=1)).isoformat(),
                "snippet": "Stock surges",
                "url": "https://test.com/1",
            },
            {
                "title": "Breaking: Stock surges on earnings",  # Duplicate headline
                "source": "Source B",
                "published_at": (now - timedelta(days=1)).isoformat(),
                "snippet": "Stock surges copy",
                "url": "https://test.com/2",
            },
            {
                "title": "Different article about market",
                "source": "Source C",
                "published_at": (now - timedelta(days=2)).isoformat(),
                "snippet": "Market news",
                "url": "https://test.com/3",
            },
        ]
        
        with patch.object(agent, '_web_search_fallback', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = mock_results
            
            result = await agent.research(ticker)
            
            # Should have 2 unique articles (duplicate removed)
            assert len(result.articles) == 2, (
                f"Expected 2 articles after deduplication, got {len(result.articles)}. "
                f"Deduplication not preserved."
            )
            
            # Verify no duplicate headlines
            headlines = [a.headline for a in result.articles]
            assert len(headlines) == len(set(headlines)), (
                "Duplicate headlines found. Deduplication not working."
            )
        
        await agent.close()

    @given(articles=st.lists(
        st.builds(
            NewsArticle,
            headline=st.text(min_size=5, max_size=100),
            source=st.text(min_size=1, max_size=50),
            published_at=st.just(datetime.now(timezone.utc)),
            summary=st.text(min_size=1, max_size=200),
            url=st.text(min_size=10, max_size=100),
            sentiment=st.just(ArticleSentiment.NEUTRAL),
        ),
        min_size=0,
        max_size=15,
    ))
    @settings(max_examples=20, deadline=None)
    def test_deduplicate_output_length_lte_input_preserved(
        self,
        articles: list[NewsArticle],
    ):
        """
        **Validates: Requirements 3.5**
        
        Deduplication output length is always <= input length.
        This property must be preserved.
        """
        agent = create_news_agent_with_web_search_fallback()
        result = agent.deduplicate(articles)
        assert len(result) <= len(articles)



class TestPreservationSentimentCategorization:
    """
    **Validates: Requirements 3.5**
    
    Tests that sentiment categorization continues to work as before.
    """

    @pytest.mark.asyncio
    @given(ticker=ticker_strategy())
    @settings(max_examples=10, deadline=None)
    async def test_sentiment_categorization_preserved(
        self,
        ticker: str,
    ):
        """
        **Validates: Requirements 3.5**
        
        Sentiment categorization must continue to work when research()
        is called without date parameters.
        """
        agent = create_news_agent_with_web_search_fallback()
        now = datetime.now(timezone.utc)
        
        mock_results = [
            {
                "title": "Stock surges on strong earnings beat",
                "source": "Test",
                "published_at": (now - timedelta(days=1)).isoformat(),
                "snippet": "Company shows strong growth and profit",
                "url": "https://test.com/positive",
            },
            {
                "title": "Stock plunges on weak guidance",
                "source": "Test",
                "published_at": (now - timedelta(days=2)).isoformat(),
                "snippet": "Company reports loss and decline",
                "url": "https://test.com/negative",
            },
        ]
        
        with patch.object(agent, '_web_search_fallback', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = mock_results
            
            result = await agent.research(ticker)
            
            # Verify sentiment was categorized
            assert len(result.articles) == 2
            
            sentiments = {a.headline: a.sentiment for a in result.articles}
            
            # Positive article should be categorized as positive
            positive_article = next(
                (a for a in result.articles if "surges" in a.headline.lower()),
                None,
            )
            if positive_article:
                assert positive_article.sentiment == ArticleSentiment.POSITIVE, (
                    f"Expected POSITIVE sentiment for '{positive_article.headline}', "
                    f"got {positive_article.sentiment}. Sentiment categorization not preserved."
                )
            
            # Negative article should be categorized as negative
            negative_article = next(
                (a for a in result.articles if "plunges" in a.headline.lower()),
                None,
            )
            if negative_article:
                assert negative_article.sentiment == ArticleSentiment.NEGATIVE, (
                    f"Expected NEGATIVE sentiment for '{negative_article.headline}', "
                    f"got {negative_article.sentiment}. Sentiment categorization not preserved."
                )
        
        await agent.close()

    def test_categorize_sentiment_returns_valid_enum(self):
        """
        **Validates: Requirements 3.5**
        
        categorize_sentiment() must return valid ArticleSentiment values.
        """
        agent = create_news_agent_with_web_search_fallback()
        
        article = NewsArticle(
            headline="Test headline",
            source="Test",
            published_at=datetime.now(timezone.utc),
            summary="Test summary",
            url="https://test.com",
            sentiment=ArticleSentiment.NEUTRAL,
        )
        
        result = agent.categorize_sentiment(article)
        assert result in [
            ArticleSentiment.POSITIVE,
            ArticleSentiment.NEGATIVE,
            ArticleSentiment.NEUTRAL,
        ]



class TestPreservationAPIBehavior:
    """
    **Validates: Requirements 3.2**
    
    Tests that API-based fetching continues to work unchanged.
    """

    @pytest.mark.asyncio
    async def test_research_via_api_unchanged(self):
        """
        **Validates: Requirements 3.2**
        
        _research_via_api() must continue to work unchanged.
        The method should still fetch from API sources and apply
        the existing date filtering logic.
        """
        agent = create_news_agent_with_api()
        now = datetime.now(timezone.utc)
        
        # Mock API response
        mock_api_response = {
            "feed": [
                {
                    "title": "API Article 1",
                    "source": "Alpha Vantage",
                    "time_published": (now - timedelta(days=1)).strftime("%Y%m%dT%H%M%S"),
                    "summary": "API article summary",
                    "url": "https://api.com/1",
                    "overall_sentiment_label": "Bullish",
                },
                {
                    "title": "API Article 2 (old)",
                    "source": "Alpha Vantage",
                    "time_published": (now - timedelta(days=20)).strftime("%Y%m%dT%H%M%S"),
                    "summary": "Old API article",
                    "url": "https://api.com/2",
                    "overall_sentiment_label": "Neutral",
                },
            ]
        }
        
        import os
        with patch.dict(os.environ, {'ALPHA_VANTAGE_API_KEY': 'test_key'}):
            with patch.object(agent._http_client, 'get', new_callable=AsyncMock) as mock_get:
                # Create a proper mock response
                mock_response = AsyncMock()
                mock_response.json = lambda: mock_api_response
                mock_response.raise_for_status = lambda: None
                mock_get.return_value = mock_response
                
                result = await agent._research_via_api("AAPL")
                
                # Verify API was called
                mock_get.assert_called_once()
                
                # Verify result structure
                assert result is not None
                assert result.ticker == "AAPL"
                assert result.data_source == "api"
                
                # Verify 14-day filter was applied (old article filtered out)
                assert len(result.articles) == 1
                assert result.articles[0].headline == "API Article 1"
        
        await agent.close()


class TestPreservationWebSearchParsing:
    """
    **Validates: Requirements 3.4**
    
    Tests that web search RSS feed parsing continues to work as before.
    """

    def test_parse_web_results_unchanged(self):
        """
        **Validates: Requirements 3.4**
        
        _parse_web_results() must continue to parse RSS feed results correctly.
        """
        agent = create_news_agent_with_web_search_fallback()
        now = datetime.now(timezone.utc)
        
        mock_results = [
            {
                "title": "Test Article",
                "source": "Google News",
                "published_at": now.isoformat(),
                "snippet": "Article snippet content",
                "url": "https://news.google.com/article",
            },
            {
                "title": "CNBC Article",
                "source": "CNBC",
                "published_at": (now - timedelta(hours=5)).isoformat(),
                "summary": "CNBC summary",
                "url": "https://cnbc.com/article",
            },
        ]
        
        articles = agent._parse_web_results(mock_results)
        
        # Verify parsing worked
        assert len(articles) == 2
        
        # Verify article structure
        for article in articles:
            assert article.headline is not None
            assert article.source is not None
            assert article.published_at is not None
            assert article.url is not None
            assert article.sentiment == ArticleSentiment.NEUTRAL  # Default before categorization

    @given(
        title=st.text(min_size=1, max_size=100),
        source=st.text(min_size=1, max_size=50),
        snippet=st.text(min_size=1, max_size=200),
    )
    @settings(max_examples=20)
    def test_parse_web_results_handles_various_inputs(
        self,
        title: str,
        source: str,
        snippet: str,
    ):
        """
        **Validates: Requirements 3.4**
        
        _parse_web_results() must handle various input formats correctly.
        """
        agent = create_news_agent_with_web_search_fallback()
        
        mock_results = [
            {
                "title": title,
                "source": source,
                "published_at": datetime.now(timezone.utc).isoformat(),
                "snippet": snippet,
                "url": "https://test.com/article",
            }
        ]
        
        articles = agent._parse_web_results(mock_results)
        
        # Should parse without error
        assert len(articles) == 1
        assert articles[0].headline == title

