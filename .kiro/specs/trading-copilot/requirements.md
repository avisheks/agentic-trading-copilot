# Requirements Document

## Introduction

The Trading Copilot is an intelligent research assistant that helps investors make informed decisions about stock investments. Given a stock ticker, the system orchestrates multiple specialized agents to gather market news, earnings call data, macro-economic trends, and social media sentiment, then synthesizes this information into actionable sentiment analysis with a short-term outlook (1-2 weeks). The system maintains a historical database of recommendations to improve future analysis and delivers reports via email.

## Glossary

- **Trading_Copilot**: The main system that orchestrates research agents and produces sentiment analysis
- **Stock_Ticker**: A unique symbol identifying a publicly traded company (e.g., AAPL, GOOGL, MSFT)
- **Research_Agent**: A specialized component that gathers specific types of information about a stock
- **News_Agent**: A Research_Agent that collects and analyzes market news for a given ticker from multiple sources
- **Earnings_Agent**: A Research_Agent that retrieves and summarizes company earnings call information
- **Macro_Agent**: A Research_Agent that analyzes macro-economic trends including geo-political factors
- **Reddit_Agent**: A Research_Agent that collates sentiment and discussions from Reddit channels for a ticker
- **Sentiment**: A classification of market outlook as either bullish (positive) or bearish (negative)
- **Sentiment_Rationale**: A justification for the sentiment classification that cites specific information from sources
- **Research_Output**: The structured data produced by a Research_Agent containing findings and analysis
- **Aggregated_Report**: The combined output from all Research_Agents before final analysis
- **Data_Source_Config**: A configuration file containing API endpoints and credentials for data sources with timestamps
- **Recommendation_Database**: A persistent store of historical recommendations, rationales, and feedback
- **Web_Report**: An HTML-formatted report suitable for email delivery with executive summary table and detailed sections
- **Historical_Reference**: A cross-reference to past recommendations for the same or related tickers
- **Source_Citation**: A reference to the original source URL from which information was collected
- **News_Source**: A financial news provider (Google News, CNBC, Wall Street Journal, Bloomberg)

## Requirements

### Requirement 1: Stock Ticker Input

**User Story:** As an investor, I want to provide a stock ticker symbol, so that I can receive research and sentiment analysis for that specific company.

#### Acceptance Criteria

1. WHEN a user provides a valid stock ticker, THE Trading_Copilot SHALL accept the input and initiate the research process
2. WHEN a user provides an invalid or unrecognized ticker, THE Trading_Copilot SHALL return a descriptive error message indicating the ticker is not valid
3. THE Trading_Copilot SHALL support major US stock exchange tickers (NYSE, NASDAQ)
4. WHEN a ticker is provided with inconsistent casing, THE Trading_Copilot SHALL normalize it to uppercase before processing

### Requirement 2: Market News Research

**User Story:** As an investor, I want to see recent market news about a stock from multiple reputable sources, so that I can understand current events affecting the company.

#### Acceptance Criteria

1. WHEN a valid ticker is provided, THE News_Agent SHALL retrieve relevant market news articles from the past 14 days
2. WHEN news articles are retrieved, THE News_Agent SHALL extract key information including headline, source, publication date, summary, and source URL
3. WHEN no recent news is available for a ticker, THE News_Agent SHALL return an empty result set with an appropriate status message
4. THE News_Agent SHALL filter out duplicate or substantially similar news articles
5. WHEN news is retrieved, THE News_Agent SHALL categorize articles by sentiment (positive, negative, neutral)
6. THE News_Agent SHALL retrieve news from multiple sources including Google News, CNBC, Wall Street Journal, and Bloomberg
7. WHEN news is retrieved from multiple sources, THE News_Agent SHALL combine results and present a unified list of articles
8. FOR ALL news articles retrieved, THE News_Agent SHALL include a valid source URL that links to the original article online

### Requirement 3: Earnings Call Analysis

**User Story:** As an investor, I want to see analysis of recent earnings calls, so that I can understand the company's financial performance and management outlook.

#### Acceptance Criteria

1. WHEN a valid ticker is provided, THE Earnings_Agent SHALL retrieve the most recent earnings call data (within the last quarter)
2. WHEN earnings data is retrieved, THE Earnings_Agent SHALL extract key metrics including revenue, EPS, guidance, and notable management commentary
3. WHEN earnings data is retrieved, THE Earnings_Agent SHALL compare actual results against analyst expectations (beat/miss/meet)
4. WHEN no recent earnings data is available, THE Earnings_Agent SHALL return the most recent available data with a timestamp indicating its age
5. IF earnings data retrieval fails, THEN THE Earnings_Agent SHALL return an error status without blocking other agents
6. FOR ALL earnings data retrieved, THE Earnings_Agent SHALL include a valid source URL that links to the original earnings report or transcript online

### Requirement 4: Reddit Sentiment Analysis

**User Story:** As an investor, I want to see sentiment and discussions from Reddit communities about a stock, so that I can understand retail investor sentiment and trending topics.

#### Acceptance Criteria

1. WHEN a valid ticker is provided, THE Reddit_Agent SHALL retrieve relevant discussions from stock-related subreddits (e.g., r/wallstreetbets, r/stocks, r/investing)
2. WHEN Reddit discussions are retrieved, THE Reddit_Agent SHALL extract key information including post title, subreddit, post date, upvote count, and summary of discussion
3. WHEN Reddit discussions are retrieved, THE Reddit_Agent SHALL categorize overall sentiment as positive, negative, or neutral
4. WHEN no recent Reddit discussions are available for a ticker, THE Reddit_Agent SHALL return an empty result set with an appropriate status message
5. IF Reddit data retrieval fails, THEN THE Reddit_Agent SHALL return an error status without blocking other agents
6. FOR ALL Reddit discussions retrieved, THE Reddit_Agent SHALL include a valid URL that links to the original Reddit post

### Requirement 5: Macro Trend Analysis

**User Story:** As an investor, I want to understand macro-economic factors affecting a stock, so that I can consider broader market conditions in my investment decision.

#### Acceptance Criteria

1. WHEN a valid ticker is provided, THE Macro_Agent SHALL identify relevant macro-economic factors for the company's sector
2. THE Macro_Agent SHALL analyze geo-political tensions that may impact the stock or its sector
3. THE Macro_Agent SHALL consider interest rate trends and their potential impact on the company
4. THE Macro_Agent SHALL evaluate supply chain or trade-related factors relevant to the company
5. WHEN macro analysis is complete, THE Macro_Agent SHALL provide a summary of key risks and opportunities
6. FOR ALL macro analysis findings, THE Macro_Agent SHALL include valid source URLs that link to the original data sources online

### Requirement 6: Research Aggregation

**User Story:** As an investor, I want all research to be combined into a coherent report, so that I can see a complete picture of the stock.

#### Acceptance Criteria

1. WHEN all Research_Agents complete their tasks, THE Trading_Copilot SHALL aggregate their outputs into an Aggregated_Report
2. THE Trading_Copilot SHALL execute Research_Agents concurrently to minimize total processing time
3. IF one Research_Agent fails, THEN THE Trading_Copilot SHALL continue processing with available data and note the missing component
4. WHEN aggregating results, THE Trading_Copilot SHALL preserve the source attribution and source URLs for each piece of information
5. THE Aggregated_Report SHALL include timestamps indicating when each data source was last updated

### Requirement 7: Sentiment Analysis and Summary

**User Story:** As an investor, I want a clear sentiment recommendation with supporting analysis and citations, so that I can make an informed investment decision.

#### Acceptance Criteria

1. WHEN the Aggregated_Report is complete, THE Trading_Copilot SHALL analyze all data to determine overall sentiment
2. THE Trading_Copilot SHALL classify sentiment as either "Bullish" or "Bearish" for the 1-2 week outlook
3. THE Trading_Copilot SHALL provide a confidence level (High, Medium, Low) for the sentiment classification
4. THE Trading_Copilot SHALL generate a Sentiment_Rationale explaining the key factors supporting the sentiment
5. THE Sentiment_Rationale SHALL explicitly cite specific information from the news sources, earnings data, Reddit discussions, and macro analysis that support the sentiment
6. THE Trading_Copilot SHALL highlight any conflicting signals or risks that could change the outlook
7. WHEN presenting results, THE Trading_Copilot SHALL clearly state that this is not financial advice and is for informational purposes only

### Requirement 8: Output Format and Email Delivery

**User Story:** As an investor, I want the analysis delivered as a professional web report to my email, so that I can review findings conveniently.

#### Acceptance Criteria

1. THE Trading_Copilot SHALL generate a Web_Report in HTML format with distinct sections
2. THE Web_Report SHALL include an executive summary table at the top with one row per ticker containing sentiment, confidence, and a hyperlink to the detailed section
3. WHEN generating the report, THE Trading_Copilot SHALL organize information hierarchically from summary table to detailed findings
4. THE Trading_Copilot SHALL send the Web_Report to a specified email address
5. WHEN errors occur during research, THE Trading_Copilot SHALL clearly indicate which sections have incomplete data in the report
6. THE Web_Report SHALL be mobile-responsive and readable on various devices
7. THE Web_Report SHALL use compact styling with reduced font size and increased text density for a professional appearance
8. FOR ALL news headlines in the detailed analysis, THE Web_Report SHALL display them as hyperlinks to the original source URLs
9. FOR ALL "Read more" or reference links in the report, THE Web_Report SHALL link to valid, real URLs from actual financial domains (not placeholder URLs like example.com)
10. AT THE BOTTOM of each ticker's detailed section, THE Web_Report SHALL include a navigation link back to the executive summary table
11. FOR ALL findings (news headlines, earnings data, macro analysis, Reddit discussions), THE Web_Report SHALL display the reference source URL from which the information was collected
12. WHEN earnings data is available, THE Web_Report SHALL display it correctly (not show "missing earnings" when data exists)

### Requirement 9: Data Source Configuration

**User Story:** As a system administrator, I want to configure data sources through a config file, so that I can easily add or remove data providers.

#### Acceptance Criteria

1. THE Trading_Copilot SHALL read data source configurations from a Data_Source_Config file
2. THE Data_Source_Config SHALL include API endpoints, credentials, and a timestamp for each data source
3. WHEN a data source is added to the config, THE Trading_Copilot SHALL use it in subsequent research requests
4. WHEN a data source is removed from the config, THE Trading_Copilot SHALL exclude it from research without code changes
5. THE Trading_Copilot SHALL validate the Data_Source_Config format on startup and report configuration errors
6. THE Data_Source_Config SHALL support multiple data sources per agent type for redundancy

### Requirement 10: Web Search Fallback

**User Story:** As a user, I want the system to work with real data even when API keys are not configured, so that I can run end-to-end analysis without mock data.

#### Acceptance Criteria

1. WHEN API keys are not present for a data source, THE Trading_Copilot SHALL fall back to web search to collect content
2. WHEN API calls fail, THE Trading_Copilot SHALL fall back to web search to collect content
3. THE web search fallback SHALL retrieve real, current information from actual financial websites and news outlets
4. WHEN using web search fallback, THE Trading_Copilot SHALL use the retrieved information for downstream sentiment analysis
5. THE Trading_Copilot SHALL be able to run end-to-end and generate reports with real data (not mock data) when API keys are unavailable

### Requirement 11: Recommendation Logging and History

**User Story:** As an investor, I want the system to remember past recommendations, so that I can track accuracy and receive historically-informed analysis.

#### Acceptance Criteria

1. WHEN a recommendation is generated, THE Trading_Copilot SHALL log the input ticker, recommendation, rationale, and timestamp to the Recommendation_Database
2. THE Trading_Copilot SHALL store the complete Aggregated_Report with each recommendation for audit purposes
3. WHEN a user provides feedback on a recommendation, THE Trading_Copilot SHALL associate the feedback with the corresponding recommendation record
4. THE Recommendation_Database SHALL support querying historical recommendations by ticker and date range
5. IF a database write fails, THEN THE Trading_Copilot SHALL log the error and continue with report delivery

### Requirement 12: Historical Cross-Reference

**User Story:** As an investor, I want to see how past recommendations for a ticker performed, so that I can contextualize the current recommendation.

#### Acceptance Criteria

1. WHEN generating a new recommendation, THE Trading_Copilot SHALL query the Recommendation_Database for previous recommendations on the same ticker
2. WHEN historical recommendations exist, THE Trading_Copilot SHALL include a Historical_Reference section in the report
3. THE Historical_Reference SHALL display past sentiment, date, and any recorded feedback for each historical recommendation
4. WHEN historical recommendations have feedback indicating accuracy, THE Trading_Copilot SHALL factor this into confidence level assessment
5. WHEN no historical recommendations exist for a ticker, THE Trading_Copilot SHALL note this is the first analysis for the ticker
