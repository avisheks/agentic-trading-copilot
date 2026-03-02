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
    - _Requirements: 8.1, 8.2, 8.5, 8.6_
  
  - [ ]* 1.3 Write property tests for config validation
    - **Property 15: Config Validation**
    - **Validates: Requirements 8.1, 8.2, 8.5**

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
    - _Requirements: 2.1, 3.5, 5.3_
  
  - [x] 4.2 Implement NewsAgent class
    - Implement research() to call Alpha Vantage News API
    - Parse API response into NewsArticle dataclasses
    - Filter articles to past 14 days
    - _Requirements: 2.1, 2.2_
  
  - [x] 4.3 Implement news deduplication
    - Create deduplicate() method using headline similarity
    - Remove articles with >90% headline similarity
    - _Requirements: 2.4_
  
  - [x] 4.4 Implement news sentiment categorization
    - Use Claude via Bedrock to classify article sentiment
    - Categorize as POSITIVE, NEGATIVE, or NEUTRAL
    - _Requirements: 2.5_
  
  - [ ]* 4.5 Write property tests for News Agent
    - **Property 3: News Article Completeness**
    - **Property 4: News Deduplication**
    - **Property 5: News Sentiment Classification**
    - **Property 6: News Date Range**
    - **Validates: Requirements 2.1, 2.2, 2.4, 2.5**

- [x] 5. Implement basic sentiment analysis
  - [x] 5.1 Create SentimentAnalyzer class
    - Initialize with Bedrock client for Claude
    - Implement analyze() method for single-agent input
    - Generate BULLISH/BEARISH classification with rationale
    - Include disclaimer text in all outputs
    - _Requirements: 6.1, 6.2, 6.4, 6.6_
  
  - [ ]* 5.2 Write property tests for sentiment analysis
    - **Property 12: Sentiment Result Completeness**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

- [x] 6. Create basic console output
  - [x] 6.1 Implement simple text report generator
    - Create formatted text output with sections
    - Include executive summary, news findings, sentiment
    - Add disclaimer at the end
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 7. Checkpoint - MVP with single agent working
  - Ensure all tests pass, ask the user if questions arise.
  - Test with real ticker (e.g., AAPL) and verify news retrieval

### Phase 3: Additional Agents (P1)

- [ ] 8. Implement Earnings Agent
  - [ ] 8.1 Create EarningsAgent class
    - Implement research() to call Financial Modeling Prep API
    - Parse earnings data into EarningsData dataclass
    - Extract revenue, EPS, guidance, management commentary
    - _Requirements: 3.1, 3.2_
  
  - [ ] 8.2 Implement earnings comparison
    - Fetch analyst expectations from API
    - Compare actual vs expected for beat/miss/meet
    - _Requirements: 3.3_
  
  - [ ] 8.3 Handle missing earnings data
    - Return most recent available data with age timestamp
    - Set appropriate status message
    - _Requirements: 3.4_
  
  - [ ]* 8.4 Write property tests for Earnings Agent
    - **Property 7: Earnings Data Completeness**
    - **Property 8: Earnings Comparison Validity**
    - **Validates: Requirements 3.2, 3.3**

- [ ] 9. Implement Macro Agent
  - [ ] 9.1 Create MacroAgent class
    - Implement research() to analyze macro factors
    - Use FRED API for economic indicators
    - Use Claude to identify sector-relevant factors
    - _Requirements: 4.1_
  
  - [ ] 9.2 Implement sector identification
    - Map tickers to sectors using static mapping or API
    - Use sector to filter relevant macro factors
    - _Requirements: 4.1_
  
  - [ ] 9.3 Implement macro factor analysis
    - Analyze geo-political, interest rate, supply chain factors
    - Generate risks and opportunities lists
    - _Requirements: 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 9.4 Write property tests for Macro Agent
    - **Property 10: Macro Analysis Completeness**
    - **Validates: Requirements 4.1, 4.5**

- [ ] 10. Checkpoint - All agents implemented
  - Ensure all tests pass, ask the user if questions arise.

### Phase 4: Agent Orchestration (P1)

- [ ] 11. Implement orchestrator with concurrent execution
  - [ ] 11.1 Create TradingCopilot orchestrator class
    - Initialize with ConfigManager and all agents
    - Implement analyze() method as main entry point
    - _Requirements: 1.1, 5.1_
  
  - [ ] 11.2 Implement concurrent agent execution
    - Use asyncio.gather() to run agents in parallel
    - Set timeout of 30 seconds per agent
    - _Requirements: 5.2_
  
  - [ ] 11.3 Implement fault-tolerant aggregation
    - Continue if individual agents fail
    - Track failed agents in missing_components
    - Preserve source attribution and timestamps
    - _Requirements: 5.3, 5.4, 5.5_
  
  - [ ]* 11.4 Write property tests for orchestration
    - **Property 9: Agent Failure Isolation**
    - **Property 11: Aggregation Completeness**
    - **Validates: Requirements 3.5, 5.1, 5.3, 5.4, 5.5**

- [ ] 12. Enhance sentiment analysis for multi-agent input
  - [ ] 12.1 Update SentimentAnalyzer for aggregated reports
    - Process news, earnings, and macro data together
    - Generate signals from each data source
    - _Requirements: 6.1_
  
  - [ ] 12.2 Implement confidence calculation
    - Calculate confidence based on signal alignment
    - HIGH if all signals agree, LOW if conflicting
    - _Requirements: 6.3_
  
  - [ ] 12.3 Implement risk highlighting
    - Identify conflicting signals
    - List risks that could change outlook
    - _Requirements: 6.5_

- [ ] 13. Checkpoint - Full pipeline working
  - Ensure all tests pass, ask the user if questions arise.

### Phase 5: Report Generation and Email (P1)

- [ ] 14. Implement HTML report generation
  - [ ] 14.1 Create ReportGenerator class
    - Use Jinja2 templates for HTML generation
    - Create mobile-responsive CSS styles
    - _Requirements: 7.1, 7.6_
  
  - [ ] 14.2 Implement report sections
    - Executive summary section
    - News findings section
    - Earnings analysis section
    - Macro trends section
    - Sentiment recommendation section
    - _Requirements: 7.2, 7.3_
  
  - [ ] 14.3 Implement error indication in reports
    - Show clear indicators for missing/failed sections
    - Explain what data is unavailable
    - _Requirements: 7.5_
  
  - [ ]* 14.4 Write property tests for report generation
    - **Property 13: Report Structure**
    - **Property 14: Report Error Indication**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.5**

- [ ] 15. Implement email delivery
  - [ ] 15.1 Create EmailService class
    - Implement SMTP connection handling
    - Support TLS encryption
    - _Requirements: 7.4_
  
  - [ ] 15.2 Implement send() method
    - Send HTML email with report
    - Handle delivery errors with retries
    - Return DeliveryResult with status
    - _Requirements: 7.4_
  
  - [ ]* 15.3 Write unit tests for email service
    - Test with mock SMTP server
    - Test error handling and retries
    - _Requirements: 7.4_

- [ ] 16. Checkpoint - Email delivery working
  - Ensure all tests pass, ask the user if questions arise.
  - Test end-to-end with real email delivery

### Phase 6: Persistence and History (P2)

- [ ] 17. Implement recommendation database
  - [ ] 17.1 Create database schema
    - Define recommendations table with all fields
    - Define feedback table with foreign key
    - Use SQLite with SQLAlchemy ORM
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [ ] 17.2 Create HistoryManager class
    - Implement save_recommendation() method
    - Store complete aggregated report as JSON
    - _Requirements: 9.1, 9.2_
  
  - [ ] 17.3 Implement history queries
    - Query by ticker
    - Query by date range
    - _Requirements: 9.4_
  
  - [ ] 17.4 Implement feedback association
    - Add add_feedback() method
    - Link feedback to recommendation by ID
    - _Requirements: 9.3_
  
  - [ ] 17.5 Implement database error resilience
    - Catch database errors
    - Log errors and continue with report delivery
    - _Requirements: 9.5_
  
  - [ ]* 17.6 Write property tests for database operations
    - **Property 17: Recommendation Storage Completeness**
    - **Property 18: Feedback Association**
    - **Property 19: History Query Correctness**
    - **Property 20: Database Failure Resilience**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

- [ ] 18. Implement historical cross-reference
  - [ ] 18.1 Add history lookup to orchestrator
    - Query history before generating new recommendation
    - Pass history to sentiment analyzer
    - _Requirements: 10.1_
  
  - [ ] 18.2 Add historical reference to reports
    - Create HistoricalReference section in HTML template
    - Display past sentiment, date, feedback
    - _Requirements: 10.2, 10.3_
  
  - [ ] 18.3 Implement accuracy-based confidence adjustment
    - Calculate historical accuracy from feedback
    - Factor accuracy into confidence level
    - _Requirements: 10.4_
  
  - [ ] 18.4 Handle first-time analysis
    - Set is_first_analysis flag when no history
    - Display appropriate message in report
    - _Requirements: 10.5_
  
  - [ ]* 18.5 Write property tests for historical features
    - **Property 21: Historical Reference Inclusion**
    - **Property 22: History Affects Confidence**
    - **Property 23: First Analysis Indicator**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

- [ ] 19. Checkpoint - History features complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 7: Config Round-Trip and Polish (P2)

- [ ] 20. Implement dynamic config updates
  - [ ] 20.1 Add config reload capability
    - Detect config file changes
    - Reload sources without restart
    - _Requirements: 8.3, 8.4_
  
  - [ ]* 20.2 Write property tests for config round-trip
    - **Property 16: Config Source Round-Trip**
    - **Validates: Requirements 8.3, 8.4**

- [ ] 21. Final integration and documentation
  - [ ] 21.1 Create main entry point script
    - Parse command line arguments (ticker, email)
    - Initialize all components
    - Run analysis and deliver report
    - _Requirements: 1.1_
  
  - [ ] 21.2 Create sample configuration files
    - Document all config options
    - Provide example with multiple data sources
    - _Requirements: 8.1, 8.2, 8.6_
  
  - [ ] 21.3 Add feedback submission endpoint
    - Create CLI command for feedback submission
    - Validate recommendation ID exists
    - _Requirements: 9.3_

- [ ] 22. Final checkpoint - All features complete
  - Ensure all tests pass, ask the user if questions arise.
  - Run full end-to-end test with all features

## Notes

- Tasks marked with `*` are optional property/unit tests and can be skipped for faster MVP
- Phase 1-2 (P0) delivers a working MVP with news analysis only
- Phase 3-5 (P1) completes the full multi-agent system with email delivery
- Phase 6-7 (P2) adds historical analysis and production polish
- Each checkpoint validates incremental progress before moving forward
- Property tests use Hypothesis library with minimum 100 iterations
