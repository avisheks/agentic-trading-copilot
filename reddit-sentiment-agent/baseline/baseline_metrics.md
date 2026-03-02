# Reddit Sentiment Agent - Baseline Evaluation Metrics

## Evaluation Date
2026-03-02 13:11:17 UTC

## Configuration
- Tickers: AAPL, MSFT, GOOGL, SNPS, CRWV, UUUU
- Epochs: 5
- Runs per Epoch: 5
- Total Evaluations: 150

## Baseline Results

| Ticker | Accuracy | Std Dev | Runs Completed |
|--------|----------|---------|----------------|
| AAPL   | 80.0%    | ±44.7%  | 25/25          |
| MSFT   | 60.0%    | ±54.8%  | 25/25          |
| GOOGL  | 60.0%    | ±54.8%  | 25/25          |
| SNPS   | 60.0%    | ±54.8%  | 25/25          |
| CRWV   | 20.0%    | ±44.7%  | 25/25          |
| UUUU   | 40.0%    | ±54.8%  | 25/25          |

## Overall Statistics
- Average Accuracy: 53.3%
- All runs completed successfully (150/150)

## Notes
- This baseline was captured BEFORE implementing the Reddit Sentiment Agent feature
- Per eval-driven development practices, post-implementation metrics must maintain or improve these scores
- The HTML report with detailed statistical analysis is saved in the same folder

## Report File
- `evaluation_report_statistical_20260302_131117.html`
