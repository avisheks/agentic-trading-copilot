"""Bug condition exploration tests for web search date filter issue.

This test file contains property-based tests that demonstrate the bug where
historical date range web searches return 'no_data' because the date filter
uses a hardcoded 14-day lookback from today instead of the caller-specified range.

**CRITICAL**: These tests are EXPECTED TO FAIL on unfixed code.
Failure confirms the bug exists.

Bug Condition Function:
    FUNCTION isBugCondition(X)
      INPUT: X of type FetchRequest { ticker: str, start_date: date, end_date: date, use_web_search: bool }
      OUTPUT: boolean
      RETURN X.use_web_search = true AND X.end_date < today() - 14 days
    END FUNCTION
"""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, settings, strategies as st, assume

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


def create_mock_articles_in_date_range(
    start_date: date,
    end_date: date,
    count: int = 5,
) -> list[dict]:
    """Create mock web search results with articles in the specified date range."""
    articles = []
    date_range_days = (end_date - start_date).days + 1
    
    for i in range(count):
        # Distribute articles across the date range
        day_offset = i % date_range_days
        article_date = start_date + timedelta(days=day_offset)
        article_datetime = datetime.combine(
            article_date,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        
        articles.append({
            "title": f"Test Article {i} for historical period",
            "source": "Test Source",
            "published_at": article_datetime.isoformat(),
            "snippet": f"This is test article {i} content",
            "url": f"https://test.com/article/{i}",
        })
    
    return articles


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def historical_date_range_strategy(draw):
    """Generate historical date ranges that trigger the bug condition.
    
    Bug condition: end_date < today() - 14 days
    This means the entire date range is in the past, outside the default 14-day window.
    """
    today = date.today()
    
    # Generate end_date that is at least 15 days ago (to satisfy bug condition)
    days_ago_end = draw(st.integers(min_value=15, max_value=90))
    end_date = today - timedelta(days=days_ago_end)
    
    # Generate start_date that is before or equal to end_date
    # Range can be 1-14 days (typical evaluation epoch)
    range_days = draw(st.integers(min_value=1, max_value=14))
    start_date = end_date - timedelta(days=range_days - 1)
    
    return start_date, end_date


@st.composite
def ticker_strategy(draw):
    """Generate valid stock ticker symbols."""
    return draw(st.sampled_from(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA"]))


# =============================================================================
# Bug Condition Exploration Tests
# =============================================================================

class TestBugConditionExploration:
    """
    Property 1: Fault Condition - Historical Date Range Web Search Returns No Data
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    This test demonstrates the bug where historical date range web searches
    return 'no_data' because _research_via_web_search() uses a hardcoded
    14-day lookback from today instead of accepting caller-specified date ranges.
    
    **CRITICAL**: This test is EXPECTED TO FAIL on unfixed code.
    Failure confirms the bug exists.
    
    Bug Condition:
        isBugCondition(X) = X.use_web_search = true AND X.end_date < today() - 14 days
    
    Expected Behavior (after fix):
        FOR ALL X WHERE isBugCondition(X) DO
          result := NewsAgent._research_via_web_search(X.ticker, X.start_date, X.end_date)
          ASSERT (result.status = "no_data" AND result.articles = []) 
                 OR (FOR ALL article IN result.articles: 
                     X.start_date <= article.published_at.date() <= X.end_date)
        END FOR
    """

    @pytest.mark.asyncio
    @given(
        date_range=historical_date_range_strategy(),
        ticker=ticker_strategy(),
    )
    @settings(max_examples=20, deadline=None)
    async def test_web_search_with_historical_date_range_returns_filtered_articles(
        self,
        date_range: tuple[date, date],
        ticker: str,
    ):
        """
        **Validates: Requirements 1.1, 1.2, 1.3**
        
        Test that _research_via_web_search() with historical date parameters
        returns articles within the specified range.
        
        This test MUST FAIL on unfixed code because:
        1. _research_via_web_search() doesn't accept start_date/end_date parameters
        2. The method uses hardcoded 14-day lookback from today
        3. Historical articles are filtered out even when they exist
        
        Expected counterexample: _research_via_web_search() ignores date parameters
        and uses hardcoded 14-day lookback from today.
        """
        start_date, end_date = date_range
        
        # Verify bug condition is satisfied
        today = date.today()
        assert end_date < today - timedelta(days=14), "Bug condition not satisfied"
        
        agent = create_news_agent_with_web_search_fallback()
        
        # Create mock articles that ARE within the historical date range
        mock_articles = create_mock_articles_in_date_range(start_date, end_date, count=5)
        
        # Mock the web search to return articles in the historical date range
        with patch.object(agent, '_web_search_fallback', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = mock_articles
            
            # Call _research_via_web_search with date parameters
            # NOTE: On unfixed code, this will fail because the method
            # doesn't accept start_date/end_date parameters
            try:
                result = await agent._research_via_web_search(
                    ticker,
                    start_date=start_date,
                    end_date=end_date,
                )
            except TypeError as e:
                # This is the expected failure on unfixed code!
                # The method doesn't accept start_date/end_date parameters
                pytest.fail(
                    f"BUG CONFIRMED: _research_via_web_search() does not accept date parameters. "
                    f"Error: {e}. "
                    f"Counterexample: ticker={ticker}, start_date={start_date}, end_date={end_date}"
                )
            
            # If we get here, the method accepted the parameters
            # Now verify the expected behavior
            
            # Expected behavior after fix:
            # (result.status = "no_data" AND result.articles = []) 
            # OR (FOR ALL article IN result.articles: start_date <= article.published_at.date() <= end_date)
            
            if result.status == "no_data":
                assert result.articles == [], (
                    f"When status is 'no_data', articles should be empty. "
                    f"Got {len(result.articles)} articles."
                )
            else:
                # All returned articles should be within the specified date range
                for article in result.articles:
                    article_date = article.published_at.date()
                    assert start_date <= article_date <= end_date, (
                        f"Article date {article_date} is outside the specified range "
                        f"[{start_date}, {end_date}]. "
                        f"BUG: Articles are being filtered against wrong date range."
                    )
        
        await agent.close()

    @pytest.mark.asyncio
    async def test_concrete_historical_date_range_bug_demonstration(self):
        """
        **Validates: Requirements 1.1, 1.2, 1.3**
        
        Concrete test case demonstrating the bug with specific dates.
        
        This test uses a fixed historical date range (3 weeks ago) to clearly
        demonstrate the bug behavior.
        
        Expected to FAIL on unfixed code.
        """
        today = date.today()
        # Historical date range: 3 weeks ago (satisfies bug condition)
        end_date = today - timedelta(days=21)
        start_date = end_date - timedelta(days=6)  # 7-day range
        
        ticker = "AAPL"
        
        agent = create_news_agent_with_web_search_fallback()
        
        # Create mock articles within the historical date range
        mock_articles = create_mock_articles_in_date_range(start_date, end_date, count=3)
        
        with patch.object(agent, '_web_search_fallback', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = mock_articles
            
            # Attempt to call with date parameters
            try:
                result = await agent._research_via_web_search(
                    ticker,
                    start_date=start_date,
                    end_date=end_date,
                )
            except TypeError as e:
                pytest.fail(
                    f"BUG CONFIRMED: _research_via_web_search() does not accept date parameters.\n"
                    f"Error: {e}\n"
                    f"Counterexample:\n"
                    f"  ticker: {ticker}\n"
                    f"  start_date: {start_date}\n"
                    f"  end_date: {end_date}\n"
                    f"  today: {today}\n"
                    f"  days_ago: {(today - end_date).days}\n"
                    f"Root cause: _research_via_web_search() uses hardcoded 14-day lookback "
                    f"from today instead of accepting caller-specified date range."
                )
            
            # Verify expected behavior
            if result.articles:
                for article in result.articles:
                    article_date = article.published_at.date()
                    assert start_date <= article_date <= end_date, (
                        f"Article date {article_date} outside range [{start_date}, {end_date}]"
                    )
        
        await agent.close()

    @pytest.mark.asyncio
    async def test_research_method_signature_accepts_date_parameters(self):
        """
        **Validates: Requirements 1.2**
        
        Test that NewsAgent.research() accepts optional start_date and end_date parameters.
        
        This test verifies the method signature change required for the fix.
        Expected to FAIL on unfixed code because research() doesn't accept date params.
        """
        agent = create_news_agent_with_web_search_fallback()
        
        today = date.today()
        start_date = today - timedelta(days=30)
        end_date = today - timedelta(days=16)
        
        # Mock web search to avoid actual network calls
        with patch.object(agent, '_web_search_fallback', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = []
            
            try:
                # Attempt to call research() with date parameters
                result = await agent.research(
                    "AAPL",
                    start_date=start_date,
                    end_date=end_date,
                )
            except TypeError as e:
                pytest.fail(
                    f"BUG CONFIRMED: NewsAgent.research() does not accept date parameters.\n"
                    f"Error: {e}\n"
                    f"Expected: research(ticker, start_date=None, end_date=None)\n"
                    f"Root cause: Method signature doesn't include optional date parameters."
                )
        
        await agent.close()

