# Reddit Sentiment Agent - Final Evaluation Metrics

## Evaluation Date
2026-03-02 14:29:19 UTC

## Configuration
- Tickers: AAPL, MSFT, GOOGL, SNPS, CRWV, UUUU
- Epochs: 5
- Runs per Epoch: 5
- Total Evaluations: 150

## Final Results

| Ticker | Accuracy | Std Dev | Runs Completed |
|--------|----------|---------|----------------|
| AAPL   | 80.0%    | ±44.7%  | 25/25          |
| MSFT   | 60.0%    | ±54.8%  | 25/25          |
| GOOGL  | 60.0%    | ±54.8%  | 25/25          |
| SNPS   | 60.0%    | ±54.8%  | 25/25          |
| CRWV   | 20.0%    | ±44.7%  | 25/25          |
| UUUU   | 40.0%    | ±54.8%  | 25/25          |

## Comparison with Baseline

| Ticker | Baseline | Final   | Change |
|--------|----------|---------|--------|
| AAPL   | 80.0%    | 80.0%   | 0%     |
| MSFT   | 60.0%    | 60.0%   | 0%     |
| GOOGL  | 60.0%    | 60.0%   | 0%     |
| SNPS   | 60.0%    | 60.0%   | 0%     |
| CRWV   | 20.0%    | 20.0%   | 0%     |
| UUUU   | 40.0%    | 40.0%   | 0%     |

## Test Suite Results
- **275 tests passed** in 6.82 seconds
- All unit tests, property tests, and integration tests passing

## Final Assessment

### Summary
✅ **PASS** - All eval-driven development requirements met.

- Average Accuracy: 53.3% (maintained from baseline)
- All runs completed successfully (150/150)
- No regressions detected
- Full test suite passing

The Reddit Sentiment Agent feature implementation is complete and verified.

## Report File
- `reports/evaluation_report_statistical_20260302_142919.html`
