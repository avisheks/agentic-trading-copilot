# Implementation Plan: Evaluation Module

## Overview

Implement a backtesting module for the Trading Copilot that evaluates sentiment prediction accuracy on historical data. The module retrieves past news data, generates predictions using the existing `SentimentAnalyzer`, and validates against actual stock price movements across multiple non-overlapping epochs.

## Tasks

- [x] 1. Create data models and error types
  - [x] 1.1 Add evaluation data models to a new `evaluation/models.py` file
    - Create `DateRange`, `EpochPeriod`, `EpochStatus`, `ActualOutcome`, `EpochResult` dataclasses
    - Create `ConfusionMatrix`, `EvaluationMetrics`, `EvaluationReport` dataclasses
    - Create `EvaluationConfig` with validation in `__post_init__`
    - _Requirements: 5.5, 8.1, 8.2, 8.3_
  
  - [x] 1.2 Add evaluation error types to `evaluation/errors.py`
    - Create `EvaluationError`, `ConfigurationError`, `HistoricalDataError`
    - Create `OutcomeFetchError`, `InsufficientDataError`
    - _Requirements: 8.4_
  
  - [ ]* 1.3 Write property test for epoch count validation
    - **Property 9: Epoch Count Validation**
    - **Validates: Requirements 5.5**
  
  - [ ]* 1.4 Write property test for configuration validation
    - **Property 12: Configuration Validation**
    - **Validates: Requirements 8.4**

- [x] 2. Implement HistoricalDataFetcher
  - [x] 2.1 Create `evaluation/historical_data_fetcher.py`
    - Implement `fetch(ticker, start_date, end_date)` method
    - Use existing `NewsAgent` to retrieve news for date range
    - Normalize all timestamps to UTC
    - Return empty result with status "no_data" when no articles found
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 2.2 Write property test for date range filtering
    - **Property 1: Date Range Filtering**
    - **Validates: Requirements 1.1, 1.5**
  
  - [ ]* 2.3 Write property test for UTC timestamp normalization
    - **Property 2: UTC Timestamp Normalization**
    - **Validates: Requirements 1.4**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement OutcomeFetcher
  - [x] 4.1 Create `evaluation/outcome_fetcher.py`
    - Implement `fetch(ticker, start_date, end_date)` method
    - Retrieve stock prices for the prediction period
    - Classify as BULLISH if close_price > open_price, BEARISH otherwise
    - Return `ActualOutcome` with direction, prices, and percentage change
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 4.2 Write property test for bullish/bearish classification
    - **Property 4: Bullish/Bearish Classification Correctness**
    - **Validates: Requirements 3.2, 3.3**

- [x] 5. Implement MetricsCalculator
  - [x] 5.1 Create `evaluation/metrics_calculator.py`
    - Implement `calculate(results)` method
    - Build confusion matrix from epoch results
    - Compute precision, recall, F1-score, and accuracy
    - Return `insufficient_data` warning if fewer than 2 completed epochs
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ]* 5.2 Write property test for metrics calculation correctness
    - **Property 10: Metrics Calculation Correctness**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [x] 6. Implement EpochRunner
  - [x] 6.1 Create `evaluation/epoch_runner.py`
    - Implement `execute(period, ticker)` async method
    - Fetch historical data for look-back period using `HistoricalDataFetcher`
    - Generate sentiment prediction using existing `SentimentAnalyzer`
    - Fetch actual outcome using `OutcomeFetcher`
    - Return `EpochResult` with prediction, actual, match status, and duration
    - Handle missing data by marking epoch as NO_DATA or INCOMPLETE
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 6.2 Write property test for prediction output completeness
    - **Property 3: Prediction Output Completeness**
    - **Validates: Requirements 2.1, 2.3, 2.4**
  
  - [ ]* 6.3 Write property test for epoch result completeness
    - **Property 5: Epoch Result Completeness**
    - **Validates: Requirements 4.4, 4.5**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement EvaluationRunner
  - [x] 8.1 Create `evaluation/evaluation_runner.py`
    - Implement `run(config)` async method as main entry point
    - Implement `_generate_epoch_periods(n, end_date)` for non-overlapping periods
    - Each epoch: 2-week look-back (Sun-Sat) + 1-week prediction (Sun-Sat)
    - Work backwards from end_date ensuring no overlap
    - _Requirements: 5.1_
  
  - [x] 8.2 Implement parallel epoch execution
    - Execute up to `max_parallelism` EpochRunners concurrently
    - Aggregate results from all epochs
    - Continue processing if individual epochs fail
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [ ]* 8.3 Write property test for non-overlapping epoch periods
    - **Property 6: Non-Overlapping Epoch Periods**
    - **Validates: Requirements 5.1**
  
  - [ ]* 8.4 Write property test for result aggregation count
    - **Property 7: Result Aggregation Count**
    - **Validates: Requirements 5.3**
  
  - [ ]* 8.5 Write property test for fault tolerance
    - **Property 8: Fault Tolerance**
    - **Validates: Requirements 5.4**

- [x] 9. Implement EvaluationReportGenerator
  - [x] 9.1 Create `evaluation/report_generator.py`
    - Implement `generate(metrics, results, config)` method
    - Generate HTML report with metrics summary section
    - Include per-epoch details: prediction, actual outcome, correctness
    - Include date ranges for each epoch
    - Include confidence breakdown in summary
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 9.2 Write property test for report content completeness
    - **Property 11: Report Content Completeness**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

- [ ] 12. Update report format to match trading-copilot styling
  - [ ] 12.1 Update HTML template with trading-copilot gradient header
    - Use `linear-gradient(135deg, #1a365d 0%, #2c5282 100%)` for header
    - Match header structure: title, ticker, timestamp
    - _Requirements: 7.4_
  
  - [ ] 12.2 Add summary table with metrics badges
    - Display Accuracy, Precision, Recall, F1 Score in table format
    - Add color-coded badges (green ≥70%, yellow 50-69%, red <50%)
    - Include epochs completed count
    - _Requirements: 7.1, 7.5_
  
  - [ ] 12.3 Add section divider matching trading-copilot format
    - Use gradient background matching header
    - Display "Detailed Analysis by Epoch" text
    - _Requirements: 7.4_
  
  - [ ] 12.4 Update per-epoch details with anchor IDs and back-to-top navigation
    - Add anchor ID `#epoch-{number}` to each epoch section
    - Add `<a href="#top">↑ Back to Summary</a>` link after each epoch
    - Style epoch cards to match trading-copilot individual ticker reports
    - _Requirements: 7.2, 7.3_
  
  - [ ] 12.5 Add mobile-responsive @media queries
    - Add breakpoint at 768px for mobile devices
    - Reduce padding and font sizes on mobile
    - Stack metrics grid vertically on mobile
    - _Requirements: 7.4_
  
  - [ ] 12.6 Update unit tests for new report format
    - Test gradient header presence
    - Test summary table structure
    - Test section divider presence
    - Test back-to-top navigation links
    - Test @media queries presence
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 10. Wire components and create module entry point
  - [x] 10.1 Create `evaluation/__init__.py` with public exports
    - Export `EvaluationRunner`, `EvaluationConfig`, `EvaluationReport`
    - Export error types for external handling
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [x] 10.2 Add evaluation configuration to `app_config.yaml`
    - Add `evaluation` section with `num_epochs`, `max_parallelism` defaults
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ]* 10.3 Write unit tests for component integration
    - Test EvaluationRunner orchestration
    - Test error handling and graceful degradation
    - _Requirements: 5.4, 8.4_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests use `hypothesis` library with minimum 100 iterations per property
- All new files go in `trading_copilot/src/trading_copilot/evaluation/` directory
- Test files go in `trading_copilot/tests/` directory
- Reuses existing `SentimentAnalyzer`, `NewsAgent`, and HTML report patterns
- Epochs work backwards from current date to ensure most recent data is evaluated
