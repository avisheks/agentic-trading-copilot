# Bugfix Requirements Document

## Introduction

The evaluation module's epochs consistently show 'no_data' status when using web search fallback for historical news data. This occurs because the web search (RSS feeds) returns only recent articles, but the `HistoricalDataFetcher` filters these articles against past look-back periods (e.g., 2 weeks ago). Since web search results are typically from the last few days, they never fall within historical date ranges, resulting in empty data for all evaluation epochs.

The fix requires passing the date range parameters to the web search logic so that articles can be validated against the specified evaluation period at retrieval time, rather than relying solely on post-fetch filtering.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `HistoricalDataFetcher.fetch()` is called with a historical date range (e.g., start_date=2024-01-01, end_date=2024-01-14) AND the NewsAgent uses web search fallback THEN the system returns 'no_data' status because web search returns only recent articles that don't match the historical date range

1.2 WHEN `NewsAgent._research_via_web_search()` is called THEN the system does not accept or use start_date and end_date parameters to filter results at the source level

1.3 WHEN evaluation epochs are run for past time periods THEN all epochs show 'no_data' because the web search fallback cannot retrieve articles matching historical date ranges

### Expected Behavior (Correct)

2.1 WHEN `HistoricalDataFetcher.fetch()` is called with a date range AND the NewsAgent uses web search fallback THEN the system SHALL pass the start_date and end_date to the web search method and filter retrieved articles to only include those within the specified date range

2.2 WHEN `NewsAgent._research_via_web_search()` is called with optional start_date and end_date parameters THEN the system SHALL filter the parsed articles to only include those with published_at dates within the specified range (inclusive)

2.3 WHEN `NewsAgent.research()` is called with optional start_date and end_date parameters THEN the system SHALL pass these parameters through to the appropriate research method (_research_via_api or _research_via_web_search)

2.4 WHEN web search returns articles and a date range is specified THEN the system SHALL return 'no_data' status only if no articles fall within the specified date range, otherwise return 'success' with the filtered articles

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `NewsAgent.research()` is called without date parameters (current behavior) THEN the system SHALL CONTINUE TO use the default 14-day lookback filter

3.2 WHEN `NewsAgent._research_via_api()` is called THEN the system SHALL CONTINUE TO fetch from configured API sources and apply the existing date filtering logic

3.3 WHEN `HistoricalDataFetcher.fetch()` receives articles from NewsAgent THEN the system SHALL CONTINUE TO normalize timestamps to UTC and apply the existing date range filtering

3.4 WHEN web search RSS feeds are queried THEN the system SHALL CONTINUE TO parse articles from Google News, CNBC, MarketWatch, and WSJ feeds

3.5 WHEN articles are retrieved THEN the system SHALL CONTINUE TO deduplicate and categorize sentiment as before

## Bug Condition Analysis

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type FetchRequest { ticker: str, start_date: date, end_date: date, use_web_search: bool }
  OUTPUT: boolean
  
  // Bug occurs when fetching historical data via web search
  // Web search returns recent articles that don't match historical dates
  RETURN X.use_web_search = true AND X.end_date < today() - 7 days
END FUNCTION
```

### Property Specification

```pascal
// Property: Fix Checking - Date-filtered web search
FOR ALL X WHERE isBugCondition(X) DO
  result ← HistoricalDataFetcher.fetch'(X.ticker, X.start_date, X.end_date)
  
  // After fix: articles returned should be within date range OR status is 'no_data'
  ASSERT (result.news.status = "no_data" AND result.news.articles = []) 
         OR (FOR ALL article IN result.news.articles: 
             X.start_date <= article.published_at.date() <= X.end_date)
END FOR
```

### Preservation Goal

```pascal
// Property: Preservation Checking - Existing behavior unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  // Non-historical fetches (recent dates or API-based) should work as before
  ASSERT F(X) = F'(X)
END FOR
```

### Counterexample

```python
# Demonstrates the bug
fetcher = HistoricalDataFetcher(news_agent_with_web_search_fallback)

# Request historical data from 2 weeks ago
result = await fetcher.fetch(
    ticker="AAPL",
    start_date=date(2024, 12, 1),  # Historical date
    end_date=date(2024, 12, 14),   # Historical date
)

# BUG: Always returns 'no_data' because web search returns recent articles
# that don't fall within the Dec 1-14 range
assert result.news.status == "no_data"  # This is the bug - should have data if available
```
