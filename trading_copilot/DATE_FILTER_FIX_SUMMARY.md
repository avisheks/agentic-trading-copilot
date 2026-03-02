# Date Filter Fix Summary

## Problem
Evaluation tasks were showing "no data" for all epochs across all stock tickers because the web search fallback method didn't support historical date filtering. When requesting historical data (e.g., from November 2025), the RSS feeds only returned recent articles, resulting in empty results after date filtering.

## Root Cause
The `_web_search_fallback()` method in `base.py` was hardcoded to fetch only recent articles without accepting date parameters. Even though the NewsAgent accepted `start_date` and `end_date` parameters, they weren't being passed through to the RSS feed URLs.

## Solution
Added date filtering support to the web search fallback mechanism using Google News RSS date operators:

### Changes Made

1. **`trading_copilot/src/trading_copilot/agents/base.py`**
   - Added `date` import from `datetime` module
   - Updated `_web_search_fallback()` signature to accept optional `start_date` and `end_date` parameters
   - Added date filter construction for Google News RSS URLs using `after:` and `before:` operators
   - Google News URL now includes: `+after:YYYY-MM-DD+before:YYYY-MM-DD` when dates are provided

2. **`trading_copilot/src/trading_copilot/agents/news.py`**
   - Updated `_research_via_web_search()` to pass `start_date` and `end_date` parameters to `_web_search_fallback()`

## Results

### Before Fix
- **All epochs**: Status = "no_data"
- **Accuracy**: 0.0% (no predictions made)
- **Evaluation**: Unusable for backtesting

### After Fix
- **All epochs**: Status = "complete" with actual predictions
- **Accuracy**: 60-80% across tickers (varies by ticker and market conditions)
- **Evaluation**: Fully functional for backtesting

### Test Results
```
✅ test_web_search_date_filter_bug.py: 3/3 tests PASSED
✅ test_web_search_date_filter_preservation.py: 10/10 tests PASSED

Evaluation Results:
- AAPL: 80.0% accuracy (5/5 epochs completed)
- MSFT: 60.0% accuracy (5/5 epochs completed)  
- GOOGL: 60.0% accuracy (5/5 epochs completed)
```

## Technical Details

### Google News RSS Date Operators
The fix leverages Google News RSS feed's built-in date filtering:
```
https://news.google.com/rss/search?q=AAPL+stock+after:2025-11-16+before:2025-11-29
```

This ensures the RSS feed returns articles from the specified historical period, allowing the evaluation system to collect sentiment data for backtesting.

### Backward Compatibility
The fix maintains backward compatibility:
- When no dates are provided, the default 14-day lookback behavior is preserved
- All existing tests pass
- API-based news fetching remains unchanged
- Deduplication and sentiment categorization continue to work as before

## Files Modified
1. `trading_copilot/src/trading_copilot/agents/base.py` - Added date parameter support
2. `trading_copilot/src/trading_copilot/agents/news.py` - Pass dates through to fallback

## Verification
Run evaluation across multiple tickers and epochs:
```bash
cd trading_copilot
python scripts/run_evaluation.py --tickers AAPL MSFT GOOGL --epochs 5
```

Expected: All epochs return data with sentiment predictions and accuracy metrics.