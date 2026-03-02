# Reddit Sentiment Agent - Revised Evaluation Metrics

## Evaluation Date
2026-03-02 14:26:00 UTC

## Configuration
- Tickers: AAPL, MSFT, GOOGL, SNPS, CRWV, UUUU
- Epochs: 5
- Runs per Epoch: 5
- Total Evaluations: 150

## Revised Results (Post-Implementation)

| Ticker | Accuracy | Std Dev | Runs Completed |
|--------|----------|---------|----------------|
| AAPL   | 80.0%    | ±44.7%  | 25/25          |
| MSFT   | 60.0%    | ±54.8%  | 25/25          |
| GOOGL  | 60.0%    | ±54.8%  | 25/25          |
| SNPS   | 60.0%    | ±54.8%  | 25/25          |
| CRWV   | 20.0%    | ±44.7%  | 25/25          |
| UUUU   | 40.0%    | ±54.8%  | 25/25          |

## Comparison with Baseline

| Ticker | Baseline | Revised | Change |
|--------|----------|---------|--------|
| AAPL   | 80.0%    | 80.0%   | 0%     |
| MSFT   | 60.0%    | 60.0%   | 0%     |
| GOOGL  | 60.0%    | 60.0%   | 0%     |
| SNPS   | 60.0%    | 60.0%   | 0%     |
| CRWV   | 20.0%    | 20.0%   | 0%     |
| UUUU   | 40.0%    | 40.0%   | 0%     |

## Overall Assessment

### Metrics Improved
- None (no regressions either)

### Metrics Regressed
- None

### Summary
✅ **PASS** - The Reddit Sentiment Agent implementation maintains all baseline metrics.

- Average Accuracy: 53.3% (unchanged)
- All runs completed successfully (150/150)
- No regressions detected

The implementation meets eval-driven development requirements. The Reddit Sentiment Agent has been successfully integrated without degrading existing functionality.

## Report File
- `evaluation_report_statistical_20260302_142600.html`
