# Implementation Plan: Trading Copilot

## Overview

This implementation plan follows an incremental MVP approach, starting with core functionality and progressively adding sophistication. Priority levels indicate the order of implementation:

- **P0 (MVP Core)**: Minimal viable product - single agent, basic output
- **P1 (MVP Complete)**: All agents, email delivery, basic persistence
- **P2 (Enhanced)**: Historical analysis, confidence tuning, production hardening

## Tasks

### Phase 1: Project Setup and Core Infrastructure (P0)

- [x] 1. Set up project structure and dependencies
  - [x] 1.1 Create Python project with pyproject.toml
    - Initialize project with Python 3.11+ requirement
    - Add dependencies: strands-agents, boto3, httpx, pydantic, jinja2
    - Set up virtual environment and install dependencies
    - _Requirements: 8.1_
  
  - [x] 1.2 Create configuration management
    - Implement ConfigManager class to load YAML/JSON config
    - Define DataSourceConfig and SourceConfig dataclasses
    - Implement config validation with error reporting
    - Create sample config file with Alpha Vantage and Finnhub sources
    - _Requirements: 9.1, 9.2, 9.5, 9.6_
  
  - [ ]* 1.3 Write property tests for config validation
    - **Property 30: Config Validation**
    - **Validates: Requirements 9.1, 9.2, 9.5**

- [x] 2. Implement ticker validation
  - [x] 2.1 Create TickerValidator class
    - Implement validate() method checking against NYSE/NASDAQ symbols
    - Implement normalize() method for uppercase conversion
    - Use a static list of valid tickers (can be enhanced later with API)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x]* 2.2 Write property tests for ticker validation
    - **Property 1: Ticker Normalization**
    - **Property 2: Invalid Ticker Error Handling**
    - **Validates: Requirements 1.2, 1.4**

- [x] 3. Checkpoint - Ensure project builds and config loads
  - Ensure all tests pass, ask the user if questions arise.

### Phase 2: First Agent - News Research (P0)

- [x] 4. Implement News Agent
  - [x] 4.1 Create base ResearchAgent abstract class
    - Define abstract research() method
    - Define get_agent_type() method
    - Implement common error handling patterns
    - Add _has_api_keys() method for fallback detection
    - Add _web_search_fallback() method for web search
    - _Requirements: 2.1, 3.5, 5.5, 10.1, 10.2_
  
  - [x] 4.2 Implement NewsAgent class with multi-source support
    - Implement research() to call multiple news APIs
    - Support Google News, CNBC, WSJ, Bloomberg, MarketWatch RSS feeds
    - Parse API/RSS responses into NewsArticle dataclasses
    - Filter articles to past 14 days
    - Include source URL for each article
    - Track sources_used in output
    - _Requirements: 2.1, 2.2, 2.6, 2.7, 2.8_
  
  - [x] 4.3 Implement news deduplication
    - Create deduplicate() method using headline similarity
    - Remove articles with >90% headline similarity
    - _Requirements: 2.4_
  
  - [x] 4.4 Implement news sentiment categorization
    - Use Claude via Bedrock to classify article sentiment
    - Categorize as POSITIVE, NEGATIVE, or NEUTRAL
    - _Requirements: 2.5_
  
  - [x] 4.5 Implement RSS feed fallback for NewsAgent
    - Implement _research_via_rss_feeds() method
    - Fetch from Google News, CNBC, WSJ, Bloomberg, MarketWatch RSS
    - Parse RSS XML into NewsArticle objects with source URLs
    - Combine results from multiple sources
    - _Requirements: 2.6, 2.7, 10.1, 10.2, 10.3_
  
  - [ ]* 4.6 Write property tests for News Agent
    - **Property 3: News Article Completeness**
    - **Property 4: News Deduplication**
    - **Property 5: News Sentiment Classification**
    - **Property 6: News Date Range**
    - **Property 7: News Multi-Source Retrieval**
    - **Validates: Requirements 2.1, 2.2, 2.4, 2.5, 2.6, 2.7, 2.8**

- [x] 5. Implement basic sentiment analysis
  - [x] 5.1 Create SentimentAnalyzer class
    - Initialize with Bedrock client for Claude
    - Implement analyze() method for single-agent input
    - Generate BULLISH/BEARISH classification with rationale
    - Include disclaimer text in all outputs
    - _Requirements: 7.1, 7.2, 7.4, 7.7_
  
  - [ ] 5.2 Implement sentiment rationale with citations
    - Generate rationale that explicitly cites news headlines
    - Generate rationale that cites earnings data points
    - Generate rationale that cites Reddit discussions
    - Generate rationale that cites macro analysis factors
    - Create SentimentRationale dataclass with citation lists
    - _Requirements: 7.5_
  
  - [ ]* 5.3 Write property tests for sentiment analysis
    - **Property 17: Sentiment Result Completeness**
    - **Property 18: Sentiment Rationale Citations**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.7**

- [x] 6. Create basic console output
  - [x] 6.1 Implement simple text report generator
    - Create formatted text output with sections
    - Include executive summary, news findings, sentiment
    - Add disclaimer at the end
    - _Requirements: 8.1, 8.3_

- [x] 7. Checkpoint - MVP with single agent working
  - Ensure all tests pass, ask the user if questions arise.
  - Test with real ticker (e.g., AAPL) and verify news retrieval

### Phase 3: Additional Agents (P1)

- [ ] 8. Implement Earnings Agent
  - [ ] 8.1 Create EarningsAgent class
    - Implement research() to call Financial Modeling Prep API
    - Parse earnings data into EarningsData dataclass
    - Extract revenue, EPS, guidance, management commentary
    - Include source_url to earnings report/transcript
    - _Requirements: 3.1, 3.2, 3.6_
  
  - [ ] 8.2 Implement earnings comparison
    - Fetch analyst expectations from API
    - Compare actual vs expected for beat/miss/meet
    - _Requirements: 3.3_
  
  - [ ] 8.3 Handle missing earnings data
    - Return most recent available data with age timestamp
    - Set appropriate status message
    - _Requirements: 3.4_
  
  - [ ] 8.4 Implement web search fallback for EarningsAgent
    - Search for "{ticker} earnings report Q{quarter}"
    - Search for "{ticker} earnings call transcript"
    - Parse web results using Claude
    - Set data_source to "web_search" when using fallback
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ]* 8.5 Write property tests for Earnings Agent
    - **Property 8: Earnings Data Completeness**
    - **Property 9: Earnings Comparison Validity**
    - **Validates: Requirements 3.2, 3.3, 3.6**

- [ ] 9. Implement Macro Agent
  - [ ] 9.1 Create MacroAgent class
    - Implement research() to analyze macro factors
    - Use FRED API for economic indicators
    - Use Claude to identify sector-relevant factors
    - Include source_urls for all macro data
    - _Requirements: 5.1, 5.6_
  
  - [ ] 9.2 Implement sector identification
    - Map tickers to sectors using static mapping or API
    - Use sector to filter relevant macro factors
    - _Requirements: 5.1_
  
  - [ ] 9.3 Implement macro factor analysis
    - Analyze geo-political, interest rate, supply chain factors
    - Generate risks and opportunities lists
    - _Requirements: 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 9.4 Implement web search fallback for MacroAgent
    - Search for "{ticker} sector analysis"
    - Search for "{ticker} macro factors"
    - Parse web results using Claude
    - Set data_source to "web_search" when using fallback
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ]* 9.5 Write property tests for Macro Agent
    - **Property 11: Macro Analysis Completeness**
    - **Validates: Requirements 5.1, 5.5, 5.6**

- [ ] 10. Implement Reddit Agent
  - [ ] 10.1 Create RedditAgent class
    - Implement research() to retrieve Reddit discussions
    - Target subreddits: wallstreetbets, stocks, investing, StockMarket
    - Parse posts into RedditPost dataclass
    - Extract title, subreddit, score, num_comments, url, created_at, snippet
    - _Requirements: 4.1, 4.2_
  
  - [ ] 10.2 Implement Reddit sentiment categorization
    - Use Claude to classify post sentiment
    - Consider Reddit-specific keywords (moon, rocket, tendies, etc.)
    - Consider engagement metrics (upvotes, comments)
    - Categorize as POSITIVE, NEGATIVE, or NEUTRAL
    - _Requirements: 4.3_
  
  - [ ] 10.3 Handle missing Reddit data
    - Return empty posts list with status "no_data"
    - Set appropriate error_message
    - _Requirements: 4.4, 4.5_
  
  - [ ] 10.4 Implement Google Search fallback for RedditAgent
    - Search using "site:reddit.com/r/{subreddit} {ticker}"
    - Parse search results into RedditPost objects
    - Ensure all URLs contain "reddit.com"
    - Set data_source to "google_search" when using fallback
    - _Requirements: 4.6, 10.1, 10.2, 10.3_
  
  - [ ] 10.5 Implement Reddit post deduplication
    - Remove duplicate posts (same URL or substantially similar title)
    - _Requirements: 4.2_
  
  - [ ]* 10.6 Write property tests for Reddit Agent
    - **Property 12: Reddit Post Completeness**
    - **Property 13: Reddit Sentiment Classification**
    - **Property 14: Reddit No-Data Handling**
    - **Property 15: Reddit Subreddit Coverage**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6**

- [ ] 11. Checkpoint - All agents implemented
  - Ensure all tests pass, ask the user if questions arise.

### Phase 4: Agent Orchestration (P1)

- [ ] 12. Implement orchestrator with concurrent execution
  - [ ] 12.1 Create TradingCopilot orchestrator class
    - Initialize with ConfigManager and all agents (News, Earnings, Macro, Reddit)
    - Implement analyze() method as main entry point
    - _Requirements: 1.1, 6.1_
  
  - [ ] 12.2 Implement concurrent agent execution
    - Use asyncio.gather() to run all four agents in parallel
    - Set timeout of 30 seconds per agent
    - _Requirements: 6.2_
  
  - [ ] 12.3 Implement fault-tolerant aggregation
    - Continue if individual agents fail
    - Track failed agents in missing_components
    - Preserve source attribution, timestamps, and source URLs
    - _Requirements: 6.3, 6.4, 6.5_
  
  - [ ]* 12.4 Write property tests for orchestration
    - **Property 10: Agent Failure Isolation**
    - **Property 16: Aggregation Completeness**
    - **Validates: Requirements 3.5, 4.5, 6.1, 6.3, 6.4, 6.5**

- [ ] 13. Enhance sentiment analysis for multi-agent input
  - [ ] 13.1 Update SentimentAnalyzer for aggregated reports
    - Process news, earnings, macro, and Reddit data together
    - Generate signals from each data source
    - _Requirements: 7.1_
  
  - [ ] 13.2 Implement confidence calculation
    - Calculate confidence based on signal alignment
    - HIGH if all signals agree, LOW if conflicting
    - _Requirements: 7.3_
  
  - [ ] 13.3 Implement risk highlighting
    - Identify conflicting signals
    - List risks that could change outlook
    - _Requirements: 7.6_

- [ ] 14. Checkpoint - Full pipeline working
  - Ensure all tests pass, ask the user if questions arise.

### Phase 5: Report Generation and Email (P1)

- [x] 15. Implement HTML report generation
  - [x] 15.1 Create ReportGenerator class
    - Use Jinja2 templates for HTML generation
    - Create mobile-responsive CSS styles
    - Use compact styling with reduced font size for professional appearance
    - _Requirements: 8.1, 8.6, 8.7_
  
  - [x] 15.2 Implement executive summary table
    - Create summary table at top of report
    - One row per ticker with: ticker (hyperlink), sentiment badge, confidence badge, news count
    - Ticker name links to detailed section anchor
    - _Requirements: 8.2_
  
  - [x] 15.3 Implement report sections with hyperlinks
    - News section: headlines as hyperlinks to source URLs
    - Earnings section: link to earnings report source
    - Macro section: links to macro data sources
    - Reddit section: post titles as hyperlinks to Reddit threads
    - _Requirements: 8.3, 8.8, 8.11_
  
  - [x] 15.4 Implement navigation links
    - Add "Back to Summary" link at bottom of each ticker section
    - Link back to executive summary table anchor
    - _Requirements: 8.10_
  
  - [x] 15.5 Implement error indication in reports
    - Show clear indicators for missing/failed sections
    - Explain what data is unavailable
    - Fix "missing earnings" display when data exists
    - _Requirements: 8.5, 8.12_
  
  - [x] 15.6 Ensure URL validity in reports
    - Validate all URLs are real (not placeholder domains)
    - No example.com, placeholder.com, or test.com URLs
    - _Requirements: 8.9_
  
  - [ ]* 15.7 Write property tests for report generation
    - **Property 19: Report Executive Summary Table**
    - **Property 20: Report Headlines as Hyperlinks**
    - **Property 21: Report URL Validity**
    - **Property 22: Report Navigation Links**
    - **Property 23: Report Source URL Display**
    - **Property 24: Report Earnings Display Correctness**
    - **Property 25: Report Structure**
    - **Property 26: Report Error Indication**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.5, 8.8, 8.9, 8.10, 8.11, 8.12**

- [x] 16. Implement email delivery
  - [x] 16.1 Create EmailService class
    - Implement SMTP connection handling
    - Support TLS encryption
    - _Requirements: 8.4_
  
  - [x] 16.2 Implement send() method
    - Send HTML email with report
    - Handle delivery errors with retries
    - Return DeliveryResult with status
    - _Requirements: 8.4_
  
  - [x]* 16.3 Write unit tests for email service
    - Test with mock SMTP server
    - Test error handling and retries
    - _Requirements: 8.4_

- [x] 17. Checkpoint - Email delivery working
  - Ensure all tests pass, ask the user if questions arise.
  - Test end-to-end with real email delivery

### Phase 6: Web Search Fallback Integration (P1)

- [ ] 18. Implement end-to-end web search fallback
  - [ ] 18.1 Verify all agents support web search fallback
    - NewsAgent: RSS feeds fallback
    - EarningsAgent: Web search fallback
    - MacroAgent: Web search fallback
    - RedditAgent: Google Search fallback
    - _Requirements: 10.1, 10.2_
  
  - [ ] 18.2 Implement fallback data integration
    - Ensure web search data flows through aggregation
    - Preserve source URLs from web search results
    - Use fallback data for sentiment analysis
    - _Requirements: 10.4_
  
  - [ ] 18.3 Test end-to-end without API keys
    - Run full pipeline with no API keys configured
    - Verify real data (not mock) is retrieved
    - Verify valid HTML report is generated
    - _Requirements: 10.5_
  
  - [ ]* 18.4 Write property tests for web search fallback
    - **Property 27: Web Search Fallback Activation**
    - **Property 28: Web Search Data Integration**
    - **Property 29: End-to-End Without API Keys**
    - **Validates: Requirements 10.1, 10.2, 10.4, 10.5**

- [ ] 19. Checkpoint - Web search fallback complete
  - Ensure all tests pass, ask the user if questions arise.
  - Test with API keys removed to verify fallback works

### Phase 7: Persistence and History (P2)

- [ ] 20. Implement recommendation database
  - [ ] 20.1 Create database schema
    - Define recommendations table with all fields
    - Define feedback table with foreign key
    - Use SQLite with SQLAlchemy ORM
    - _Requirements: 11.1, 11.2, 11.3_
  
  - [ ] 20.2 Create HistoryManager class
    - Implement save_recommendation() method
    - Store complete aggregated report as JSON
    - _Requirements: 11.1, 11.2_
  
  - [ ] 20.3 Implement history queries
    - Query by ticker
    - Query by date range
    - _Requirements: 11.4_
  
  - [ ] 20.4 Implement feedback association
    - Add add_feedback() method
    - Link feedback to recommendation by ID
    - _Requirements: 11.3_
  
  - [ ] 20.5 Implement database error resilience
    - Catch database errors
    - Log errors and continue with report delivery
    - _Requirements: 11.5_
  
  - [ ]* 20.6 Write property tests for database operations
    - **Property 32: Recommendation Storage Completeness**
    - **Property 33: Feedback Association**
    - **Property 34: History Query Correctness**
    - **Property 35: Database Failure Resilience**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

- [ ] 21. Implement historical cross-reference
  - [ ] 21.1 Add history lookup to orchestrator
    - Query history before generating new recommendation
    - Pass history to sentiment analyzer
    - _Requirements: 12.1_
  
  - [ ] 21.2 Add historical reference to reports
    - Create HistoricalReference section in HTML template
    - Display past sentiment, date, feedback
    - _Requirements: 12.2, 12.3_
  
  - [ ] 21.3 Implement accuracy-based confidence adjustment
    - Calculate historical accuracy from feedback
    - Factor accuracy into confidence level
    - _Requirements: 12.4_
  
  - [ ] 21.4 Handle first-time analysis
    - Set is_first_analysis flag when no history
    - Display appropriate message in report
    - _Requirements: 12.5_
  
  - [ ]* 21.5 Write property tests for historical features
    - **Property 36: Historical Reference Inclusion**
    - **Property 37: History Affects Confidence**
    - **Property 38: First Analysis Indicator**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**

- [ ] 22. Checkpoint - History features complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 8: Config Round-Trip and Polish (P2)

- [ ] 23. Implement dynamic config updates
  - [ ] 23.1 Add config reload capability
    - Detect config file changes
    - Reload sources without restart
    - _Requirements: 9.3, 9.4_
  
  - [ ]* 23.2 Write property tests for config round-trip
    - **Property 31: Config Source Round-Trip**
    - **Validates: Requirements 9.3, 9.4**

- [ ] 24. Final integration and documentation
  - [ ] 24.1 Create main entry point script
    - Parse command line arguments (ticker, email)
    - Initialize all components
    - Run analysis and deliver report
    - _Requirements: 1.1_
  
  - [ ] 24.2 Create sample configuration files
    - Document all config options
    - Provide example with multiple data sources
    - _Requirements: 9.1, 9.2, 9.6_
  
  - [ ] 24.3 Add feedback submission endpoint
    - Create CLI command for feedback submission
    - Validate recommendation ID exists
    - _Requirements: 11.3_

- [ ] 25. Final checkpoint - All features complete
  - Ensure all tests pass, ask the user if questions arise.
  - Run full end-to-end test with all features

## Notes

- Tasks marked with `*` are optional property/unit tests and can be skipped for faster MVP
- Phase 1-2 (P0) delivers a working MVP with news analysis only
- Phase 3-5 (P1) completes the full multi-agent system with email delivery
- Phase 6 (P1) ensures web search fallback works end-to-end
- Phase 7-8 (P2) adds historical analysis and production polish
- Each checkpoint validates incremental progress before moving forward
- Property tests use Hypothesis library with minimum 100 iterations
- All agents must include valid source URLs in their output for traceability
- HTML reports must use real URLs (no placeholder domains like example.com)
