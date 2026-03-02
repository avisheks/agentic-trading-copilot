# Web Search Date Filter Bugfix Design

## Overview

The evaluation module's `HistoricalDataFetcher` consistently returns 'no_data' when using web search fallback for historical news data. The root cause is that `NewsAgent._research_via_web_search()` applies a fixed 14-day lookback filter from the current date, but the `HistoricalDataFetcher` requests articles from past date ranges (e.g., 2 weeks ago). Since web search results are filtered against "today - 14 days" rather than the requested historical period, all articles are discarded.

The fix adds optional `start_date` and `end_date` parameters to `NewsAgent.research()` and `_research_via_web_search()`, allowing the caller to specify the date range for filtering at retrieval time.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when historical date ranges are requested via web search but the date filter uses current date instead of the requested range
- **Property (P)**: The desired behavior - articles should be filtered against the caller-specified date range, not a fixed 14-day lookback from today
- **Preservation**: Existing behavior when no date parameters are passed - the default 14-day lookback filter should continue to work
- **HistoricalDataFetcher**: The component in `evaluation/historical_data_fetcher.py` that fetches historical news for backtesting
- **NewsAgent**: The agent in `agents/news.py` that retrieves news articles from APIs or web search
- **_research_via_web_search**: The method that fetches news using RSS feeds when API keys are unavailable

## Bug Details

### Fault Condition

The bug manifests when `HistoricalDataFetcher.fetch()` is called with a historical date range and the `NewsAgent` uses web search fallback. The `_research_via_web_search()` method applies a hardcoded 14-day lookback filter from the current date, discarding all articles that don't match this window - even though the caller requested a different historical period.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type FetchRequest { ticker: str, start_date: date, end_date: date, use_web_search: bool }
  OUTPUT: boolean
  
  // Bug occurs when:
  // 1. Web search fallback is used (no API keys configured)
  // 2. The requested date range is historical (not within the last 14 days)
  today := current_date()
  default_cutoff := today - 14 days
  
  RETURN input.use_web_search = true 
         AND input.end_date < default_cutoff
END FUNCTION
```

### Examples

- **Bug Case 1**: Request articles for Jan 1-14, 2024 via web search → Returns 'no_data' because web search filters against "today - 14 days" (e.g., Dec 15-28, 2024)
- **Bug Case 2**: Request articles for 3 weeks ago via web search → Returns 'no_data' because all retrieved articles are outside the hardcoded 14-day window
- **Non-Bug Case**: Request articles for the last 7 days via web search → Works correctly because the requested range overlaps with the default 14-day lookback
- **Non-Bug Case**: Request articles via API (with API keys) → Works correctly because API sources accept date range parameters

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When `NewsAgent.research()` is called without date parameters, the default 14-day lookback filter must continue to work
- When `NewsAgent._research_via_api()` is called, the existing API fetching and date filtering logic must remain unchanged
- `HistoricalDataFetcher` must continue to normalize timestamps to UTC and apply its own date range filtering
- Web search RSS feed parsing (Google News, CNBC, MarketWatch, WSJ) must continue to work as before
- Article deduplication and sentiment categorization must remain unchanged

**Scope:**
All inputs that do NOT involve passing date parameters to `NewsAgent.research()` should be completely unaffected by this fix. This includes:
- Direct calls to `NewsAgent.research(ticker)` without date parameters
- API-based news fetching with configured API keys
- All existing test cases that don't use date parameters

## Hypothesized Root Cause

Based on the bug description, the root cause is:

1. **Hardcoded Date Filter**: In `_research_via_web_search()`, line 117-118:
   ```python
   cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
   filtered_articles = self._filter_by_date(articles, cutoff_date)
   ```
   This always filters against the current date, ignoring any historical date range the caller might need.

2. **Missing Parameter Propagation**: The `research()` method signature doesn't accept date parameters, so `HistoricalDataFetcher` cannot communicate the desired date range to the web search logic.

3. **Post-Fetch Filtering Only**: `HistoricalDataFetcher` applies its own date filtering after receiving articles from `NewsAgent`, but by then the articles have already been filtered against the wrong date range.

## Correctness Properties

Property 1: Fault Condition - Date-Filtered Web Search Returns Articles Within Specified Range

_For any_ input where the bug condition holds (historical date range requested via web search), the fixed `_research_via_web_search()` function SHALL filter articles against the caller-specified date range (start_date to end_date) instead of the hardcoded 14-day lookback from today.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Default Behavior Without Date Parameters

_For any_ input where no date parameters are passed to `NewsAgent.research()`, the fixed function SHALL produce the same result as the original function, preserving the default 14-day lookback filter behavior.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `trading_copilot/src/trading_copilot/agents/news.py`

**Function**: `research()` and `_research_via_web_search()`

**Specific Changes**:

1. **Add Optional Date Parameters to `research()`**:
   ```python
   async def research(
       self, 
       ticker: str,
       start_date: date | None = None,
       end_date: date | None = None,
   ) -> NewsOutput:
   ```

2. **Pass Date Parameters to `_research_via_web_search()`**:
   ```python
   async def _research_via_web_search(
       self, 
       ticker: str,
       start_date: date | None = None,
       end_date: date | None = None,
   ) -> NewsOutput:
   ```

3. **Modify Date Filtering Logic in `_research_via_web_search()`**:
   - If `start_date` and `end_date` are provided, filter articles to that range
   - If not provided, use the existing 14-day lookback from today

4. **Update `_filter_by_date()` or Add New Filter Method**:
   - Support filtering by date range (start_date to end_date) in addition to cutoff date

**File**: `trading_copilot/src/trading_copilot/evaluation/historical_data_fetcher.py`

**Function**: `fetch()`

**Specific Changes**:

5. **Pass Date Range to NewsAgent**:
   ```python
   news_output = await self._news_agent.research(
       ticker,
       start_date=start_date,
       end_date=end_date,
   )
   ```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis.

**Test Plan**: Write tests that call `HistoricalDataFetcher.fetch()` with historical date ranges when web search fallback is used. Run these tests on the UNFIXED code to observe failures.

**Test Cases**:
1. **Historical Date Range Test**: Call `fetch()` with dates from 3 weeks ago via web search (will fail on unfixed code - returns 'no_data')
2. **Date Parameter Propagation Test**: Verify `NewsAgent.research()` receives and uses date parameters (will fail on unfixed code - no parameters accepted)
3. **Web Search Date Filter Test**: Verify `_research_via_web_search()` filters against specified range (will fail on unfixed code - uses hardcoded 14-day lookback)

**Expected Counterexamples**:
- `HistoricalDataFetcher.fetch()` returns 'no_data' for all historical date ranges
- Root cause: `_research_via_web_search()` uses `datetime.now() - 14 days` instead of caller-specified range

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := NewsAgent.research'(input.ticker, input.start_date, input.end_date)
  
  // After fix: articles returned should be within specified date range
  ASSERT (result.status = "no_data" AND result.articles = []) 
         OR (FOR ALL article IN result.articles: 
             input.start_date <= article.published_at.date() <= input.end_date)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  // Calls without date parameters should work exactly as before
  ASSERT NewsAgent.research(input.ticker) = NewsAgent.research'(input.ticker)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for calls without date parameters, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Default Behavior Preservation**: Verify `research(ticker)` without date params continues to use 14-day lookback
2. **API Fallback Preservation**: Verify API-based fetching continues to work unchanged
3. **Deduplication Preservation**: Verify article deduplication continues to work
4. **Sentiment Categorization Preservation**: Verify sentiment analysis continues to work

### Unit Tests

- Test `research()` with date parameters filters correctly
- Test `research()` without date parameters uses default 14-day lookback
- Test `_research_via_web_search()` with date parameters
- Test `HistoricalDataFetcher.fetch()` passes date range to NewsAgent
- Test edge cases: start_date equals end_date, date range spans week boundaries

### Property-Based Tests

- Generate random date ranges and verify articles are filtered correctly
- Generate random tickers and verify default behavior is preserved when no dates passed
- Test that all articles returned are within the specified date range

### Integration Tests

- Test full evaluation flow with historical date ranges
- Test that epochs with historical dates return data when articles exist
- Test that web search fallback works correctly with date parameters
