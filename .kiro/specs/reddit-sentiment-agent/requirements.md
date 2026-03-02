# Requirements Document: Reddit Sentiment Agent

## Introduction

The Reddit Sentiment Agent is a specialized research agent within the Trading Copilot system that gathers and analyzes sentiment from Reddit discussions about stock tickers. It retrieves posts from popular investing subreddits (r/wallstreetbets, r/stocks, r/investing, r/StockMarket), classifies sentiment, and generates signals that contribute to the overall sentiment analysis. The agent must support historical data retrieval for evaluation purposes and follow eval-driven development practices.

## Glossary

- **Reddit_Agent**: A Research_Agent that collates sentiment and discussions from Reddit channels for a ticker
- **RedditPost**: A data structure representing a Reddit post with title, subreddit, score, comments, URL, timestamp, and sentiment
- **RedditOutput**: The structured output from the Reddit Agent containing posts and metadata
- **Subreddit**: A Reddit community focused on a specific topic (e.g., r/wallstreetbets for stock trading)
- **Sentiment_Signal**: A directional indicator (bullish/bearish) with strength derived from Reddit sentiment analysis
- **Historical_Data**: Past Reddit discussions retrieved for a specific date range for evaluation backtesting
- **Baseline_Metrics**: Evaluation scores recorded before implementing changes, per eval-driven development

## Requirements

### Requirement 1: Reddit Data Retrieval

**User Story:** As an investor, I want to see discussions from Reddit communities about a stock, so that I can understand retail investor sentiment and trending topics.

#### Acceptance Criteria

1. WHEN a valid ticker is provided, THE Reddit_Agent SHALL retrieve relevant discussions from stock-related subreddits (r/wallstreetbets, r/stocks, r/investing, r/StockMarket)
2. WHEN Reddit discussions are retrieved, THE Reddit_Agent SHALL extract key information including post title, subreddit, post date, upvote score, comment count, and snippet/summary
3. WHEN no recent Reddit discussions are available for a ticker, THE Reddit_Agent SHALL return an empty result set with status "no_data" and an appropriate message
4. IF Reddit data retrieval fails, THEN THE Reddit_Agent SHALL return an error status without blocking other agents
5. FOR ALL Reddit discussions retrieved, THE Reddit_Agent SHALL include a valid URL that links to the original Reddit post
6. WHEN retrieving discussions, THE Reddit_Agent SHALL filter to posts from the past 7 days by default

### Requirement 2: Sentiment Classification

**User Story:** As an investor, I want Reddit posts classified by sentiment, so that I can quickly understand the overall retail investor mood.

#### Acceptance Criteria

1. WHEN Reddit discussions are retrieved, THE Reddit_Agent SHALL categorize each post's sentiment as POSITIVE, NEGATIVE, or NEUTRAL
2. WHEN classifying sentiment, THE Reddit_Agent SHALL use Reddit-specific keywords (moon, rocket, tendies, calls, puts, bearish, bullish, etc.)
3. WHEN classifying sentiment, THE Reddit_Agent SHALL consider post engagement metrics (high upvote scores indicate stronger sentiment)
4. WHEN a post contains mixed signals, THE Reddit_Agent SHALL classify it as NEUTRAL

### Requirement 3: Signal Generation

**User Story:** As the Trading Copilot system, I want the Reddit Agent to produce a sentiment signal, so that it can be aggregated with other agent signals.

#### Acceptance Criteria

1. WHEN Reddit posts are analyzed, THE Reddit_Agent SHALL generate a Signal with source=REDDIT, direction (BULLISH/BEARISH), and strength (0.0-1.0)
2. WHEN calculating signal direction, THE Reddit_Agent SHALL use the majority sentiment across retrieved posts
3. WHEN calculating signal strength, THE Reddit_Agent SHALL weight posts by engagement (upvotes, comments)
4. WHEN no posts are retrieved, THE Reddit_Agent SHALL NOT generate a signal (return None)

### Requirement 4: Aggregated Report Integration

**User Story:** As an investor viewing the report, I want Reddit sentiment included in the aggregated analysis, so that I have a complete picture.

#### Acceptance Criteria

1. WHEN the Aggregated_Report is generated, THE Trading_Copilot SHALL include RedditOutput alongside NewsOutput, EarningsOutput, and MacroOutput
2. WHEN Reddit data is missing, THE Trading_Copilot SHALL note REDDIT in the missing_components list
3. WHEN generating the HTML report, THE Trading_Copilot SHALL display Reddit posts with titles as hyperlinks to original posts
4. WHEN generating the sentiment rationale, THE Trading_Copilot SHALL cite specific Reddit discussions that support the sentiment

### Requirement 5: Historical Data for Evaluation

**User Story:** As a developer running evaluations, I want to retrieve historical Reddit data for past date ranges, so that I can backtest sentiment predictions.

#### Acceptance Criteria

1. WHEN start_date and end_date parameters are provided, THE Reddit_Agent SHALL retrieve discussions from that specific date range
2. WHEN retrieving historical data, THE Reddit_Agent SHALL use web search with date filters to find archived discussions
3. WHEN historical data is unavailable for a date range, THE Reddit_Agent SHALL return status "no_data" with an appropriate message
4. THE Reddit_Agent research method SHALL accept optional start_date and end_date parameters matching the NewsAgent interface

### Requirement 6: Baseline Documentation

**User Story:** As a developer following eval-driven development, I want baseline metrics documented, so that I can verify the Reddit Agent improves or maintains accuracy.

#### Acceptance Criteria

1. BEFORE implementing Reddit Agent changes, THE developer SHALL run the evaluation suite and record baseline metrics
2. AFTER implementing Reddit Agent changes, THE developer SHALL run the evaluation suite and compare to baseline
3. WHEN evaluation metrics degrade, THE change SHALL NOT be merged unless explicitly justified
4. THE design document SHALL specify how Reddit signals affect overall sentiment accuracy

### Requirement 7: Configuration

**User Story:** As a system administrator, I want Reddit data sources configurable, so that I can adjust subreddits or add API sources.

#### Acceptance Criteria

1. THE Reddit_Agent SHALL read subreddit list from configuration (sources.yaml)
2. WHEN a reddit_sources section is added to sources.yaml, THE Reddit_Agent SHALL use those configurations
3. THE Reddit_Agent SHALL support web search fallback when no API keys are configured

### Requirement 8: Error Handling

**User Story:** As a user, I want the system to handle Reddit failures gracefully, so that I still receive analysis from other sources.

#### Acceptance Criteria

1. WHEN Reddit API or web search fails, THE Reddit_Agent SHALL return RedditOutput with status "error" and error_message
2. WHEN Reddit fails, THE Trading_Copilot SHALL continue with other agents and note the failure in the report
3. WHEN rate limiting occurs, THE Reddit_Agent SHALL implement exponential backoff before retrying
