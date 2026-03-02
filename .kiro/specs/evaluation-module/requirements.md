# Requirements Document

## Introduction

The Evaluation Module tests the Trading Copilot's sentiment prediction performance on historical data. It retrieves data from past periods, generates sentiment predictions for upcoming weeks, and validates those predictions against actual stock price movements. The module supports running evaluations across multiple non-overlapping epochs in parallel to provide statistically meaningful performance metrics.

## Glossary

- **Evaluation_Module**: The system component that orchestrates historical backtesting of sentiment predictions
- **Epoch**: A single evaluation period consisting of a look-back window (2 weeks) followed by a prediction window (1 week)
- **Look_Back_Period**: The 2-week historical data window (Sunday to Saturday) used to gather sentiment data for prediction
- **Prediction_Period**: The 1-week forward window (Sunday to Saturday) for which sentiment is predicted
- **Actual_Outcome**: The observed stock price movement (bullish or bearish) during the prediction period
- **Epoch_Runner**: A subagent that executes a single epoch evaluation independently
- **Metrics_Calculator**: The component that computes precision, recall, F1-score, and confusion matrix from evaluation results
- **Historical_Data_Fetcher**: The component that retrieves past news and sentiment data for a specified date range

## Requirements

### Requirement 1: Historical Data Retrieval

**User Story:** As a developer, I want to retrieve historical news and sentiment data for a specified date range, so that I can evaluate the copilot's prediction accuracy on past data.

#### Acceptance Criteria

1. WHEN a look-back period is specified, THE Historical_Data_Fetcher SHALL retrieve news articles published within that 2-week window
2. WHEN retrieving historical data, THE Historical_Data_Fetcher SHALL use the same data sources configured for the live Trading Copilot
3. IF no historical data is available for the specified period, THEN THE Historical_Data_Fetcher SHALL return an empty result with status "no_data"
4. THE Historical_Data_Fetcher SHALL normalize all timestamps to UTC timezone
5. WHEN a date range spans a week boundary, THE Historical_Data_Fetcher SHALL include articles from both partial weeks

### Requirement 2: Sentiment Prediction Generation

**User Story:** As a developer, I want to generate sentiment predictions based on historical look-back data, so that I can compare predictions against actual outcomes.

#### Acceptance Criteria

1. WHEN historical data is provided for a look-back period, THE Evaluation_Module SHALL generate a sentiment prediction (bullish or bearish) for the upcoming prediction period
2. THE Evaluation_Module SHALL use the existing SentimentAnalyzer to generate predictions from historical data
3. WHEN generating a prediction, THE Evaluation_Module SHALL record the confidence level (HIGH, MEDIUM, LOW) alongside the sentiment
4. THE Evaluation_Module SHALL store the prediction timestamp and the look-back period dates used

### Requirement 3: Actual Outcome Determination

**User Story:** As a developer, I want to determine the actual stock price movement during a prediction period, so that I can validate predictions against reality.

#### Acceptance Criteria

1. WHEN a prediction period is specified, THE Evaluation_Module SHALL determine if the stock was bullish or bearish during that week
2. THE Evaluation_Module SHALL classify a week as bullish if the closing price on Saturday is higher than the opening price on Sunday
3. THE Evaluation_Module SHALL classify a week as bearish if the closing price on Saturday is lower than or equal to the opening price on Sunday
4. IF stock price data is unavailable for the prediction period, THEN THE Evaluation_Module SHALL mark the epoch as "incomplete" and exclude it from metrics calculation

### Requirement 4: Single Epoch Evaluation

**User Story:** As a developer, I want to run a single epoch evaluation, so that I can test the prediction accuracy for one specific time period.

#### Acceptance Criteria

1. WHEN an epoch is executed, THE Epoch_Runner SHALL retrieve historical data for the 2-week look-back period
2. WHEN an epoch is executed, THE Epoch_Runner SHALL generate a sentiment prediction for the 1-week prediction period
3. WHEN an epoch is executed, THE Epoch_Runner SHALL determine the actual outcome for the prediction period
4. THE Epoch_Runner SHALL return an EpochResult containing the prediction, actual outcome, and match status (correct or incorrect)
5. WHEN the epoch completes, THE Epoch_Runner SHALL record the execution duration in milliseconds

### Requirement 5: Multi-Epoch Parallel Evaluation

**User Story:** As a developer, I want to run multiple epoch evaluations in parallel, so that I can efficiently gather statistically significant performance data.

#### Acceptance Criteria

1. WHEN N epochs are requested, THE Evaluation_Module SHALL create N non-overlapping look-back periods working backwards from the current date
2. THE Evaluation_Module SHALL execute up to N Epoch_Runners in parallel as concurrent subagents
3. WHEN all epochs complete, THE Evaluation_Module SHALL aggregate results from all Epoch_Runners
4. IF an individual epoch fails, THEN THE Evaluation_Module SHALL continue processing remaining epochs and report partial results
5. THE Evaluation_Module SHALL support configuring N between 1 and 52 epochs (1 year of weekly data)

### Requirement 6: Performance Metrics Calculation

**User Story:** As a developer, I want to calculate standard classification metrics, so that I can objectively measure the copilot's prediction accuracy.

#### Acceptance Criteria

1. WHEN epoch results are aggregated, THE Metrics_Calculator SHALL compute precision for bullish predictions
2. WHEN epoch results are aggregated, THE Metrics_Calculator SHALL compute recall for bullish predictions
3. WHEN epoch results are aggregated, THE Metrics_Calculator SHALL compute the F1-score
4. WHEN epoch results are aggregated, THE Metrics_Calculator SHALL generate a 2x2 confusion matrix (predicted vs actual: bullish/bearish)
5. THE Metrics_Calculator SHALL compute overall accuracy as the ratio of correct predictions to total predictions
6. IF fewer than 2 completed epochs exist, THEN THE Metrics_Calculator SHALL return metrics with a "insufficient_data" warning

### Requirement 7: Evaluation Report Generation

**User Story:** As a developer, I want to generate a comprehensive evaluation report, so that I can review and share the backtesting results.

#### Acceptance Criteria

1. WHEN evaluation completes, THE Evaluation_Module SHALL generate a report containing all computed metrics
2. THE Evaluation_Module SHALL include per-epoch details showing prediction, actual outcome, and correctness
3. THE Evaluation_Module SHALL include the date ranges for each epoch in the report
4. THE Evaluation_Module SHALL support HTML format for the evaluation report
5. WHEN generating the report, THE Evaluation_Module SHALL include a summary section with overall accuracy and confidence breakdown

### Requirement 8: Configuration Management

**User Story:** As a developer, I want to configure evaluation parameters, so that I can customize the backtesting scope and behavior.

#### Acceptance Criteria

1. THE Evaluation_Module SHALL read the number of epochs (N) from configuration with a default value of 10
2. THE Evaluation_Module SHALL read the ticker symbol to evaluate from configuration
3. THE Evaluation_Module SHALL support configuring the parallelism level for epoch execution
4. WHEN configuration is invalid, THE Evaluation_Module SHALL raise a ConfigurationError with a descriptive message
