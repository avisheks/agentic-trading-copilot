# Implementation Plan: Reddit Sentiment Agent

## Overview

This plan implements the Reddit Sentiment Agent feature, extending the existing `RedditAgent` class to support historical date filtering, signal generation, and full integration with the Orchestrator, Analyzer, and HTML report. The implementation follows the established NewsAgent pattern and supports eval-driven development through historical data retrieval.

## Tasks

- [x] 0. Use eval-driven development hook provided before making any change
  - [x] 0.1 Run pre-implementation eval results for the current setup without any making changes
    - Save them into a folder called "{feature-name}/baseline" that can be used to compare results post-implementation changes

  - [x] 0.2 Do a git-commit of the pre-implementation setup and baseline results


- [x] 1. Extend RedditAgent data models and interface
  - [x] 1.1 Add Signal field to RedditOutput class
    - Add `signal: Signal | None = None` field to RedditOutput
    - _Requirements: 3.1_
  
  - [x] 1.2 Update research method signature for date filtering
    - Add `start_date: date | None = None` and `end_date: date | None = None` parameters
    - Match the NewsAgent interface for consistency
    - _Requirements: 5.1, 5.4_

- [x] 2. Implement signal generation logic
  - [x] 2.1 Implement _generate_signal method
    - Calculate engagement-weighted sentiment (score + num_comments)
    - Determine direction based on weighted majority (BULLISH/BEARISH)
    - Calculate strength as ratio of dominant sentiment weight
    - Return None when posts list is empty
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 2.2 Write property test for signal generation
    - **Property 4: Signal Generation**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [x] 3. Implement date range filtering
  - [x] 3.1 Update _search_reddit to accept date parameters
    - Add date parameters to web search query when provided
    - Use Google search date filters (tbs=cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY)
    - _Requirements: 5.1, 5.2_
  
  - [x] 3.2 Implement date filtering in research method
    - Filter to past 7 days when no date parameters provided
    - Filter to inclusive date range when start_date/end_date provided
    - Return status="no_data" when historical data unavailable
    - _Requirements: 1.6, 5.1, 5.3_
  
  - [ ]* 3.3 Write property test for date range filtering
    - **Property 5: Date Range Filtering**
    - **Validates: Requirements 1.6, 5.1**

- [x] 4. Checkpoint - Verify RedditAgent core functionality
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Add configuration support for Reddit sources
  - [x] 5.1 Add reddit_sources section to sources.yaml
    - Add subreddits list (wallstreetbets, stocks, investing, StockMarket)
    - Include web search fallback configuration
    - _Requirements: 7.1, 7.2_
  
  - [x] 5.2 Update ConfigManager to parse reddit_sources
    - Add reddit_sources to DataSourceConfig model
    - Parse subreddits list from configuration
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 5.3 Update RedditAgent to read subreddits from config
    - Read subreddit list from SourceConfig instead of hardcoding
    - Fall back to default subreddits if not configured
    - _Requirements: 7.1, 7.2_

- [x] 6. Enhance error handling
  - [x] 6.1 Implement exponential backoff retry logic
    - Add retry with delays: 1s, 2s, 4s
    - Return error status after 3 failed retries
    - _Requirements: 8.3_
  
  - [x] 6.2 Ensure graceful error handling
    - Catch all exceptions and return RedditOutput with status="error"
    - Include descriptive error_message
    - Never raise exceptions that block other agents
    - _Requirements: 1.4, 8.1_
  
  - [ ]* 6.3 Write property test for error handling
    - **Property 6: Error Handling**
    - **Validates: Requirements 1.4, 8.1**

- [x] 7. Checkpoint - Verify RedditAgent with configuration and error handling
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Integrate RedditAgent with Orchestrator
  - [x] 8.1 Update AggregatedReport model to include reddit field
    - Add `reddit: RedditOutput | None` field to AggregatedReport
    - _Requirements: 4.1_
  
  - [x] 8.2 Update Orchestrator to instantiate and call RedditAgent
    - Create RedditAgent with configured sources
    - Call research() concurrently with other agents
    - Include RedditOutput in AggregatedReport
    - _Requirements: 4.1_
  
  - [x] 8.3 Update missing_components tracking
    - Add AgentType.REDDIT to missing_components when reddit is None or status is error/no_data
    - _Requirements: 4.2_
  
  - [ ]* 8.4 Write property test for missing components tracking
    - **Property 7: Missing Components Tracking**
    - **Validates: Requirements 4.2**

- [x] 9. Integrate Reddit signal with Analyzer
  - [x] 9.1 Update _extract_signals to include Reddit signal
    - Extract signal from RedditOutput when available
    - Include Reddit signal in signal weighting
    - _Requirements: 4.1_
  
  - [x] 9.2 Update _generate_summary to cite Reddit discussions
    - Include Reddit sentiment in summary when data available
    - Reference subreddit names and post counts
    - _Requirements: 4.4_
  
  - [ ]* 9.3 Write property test for rationale citations
    - **Property 8: Rationale Citations**
    - **Validates: Requirements 4.4**

- [x] 10. Checkpoint - Verify Orchestrator and Analyzer integration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Add Reddit section to HTML report
  - [x] 11.1 Create Reddit sentiment section template
    - Display section header "Reddit Sentiment"
    - Show subreddit, score, and sentiment for each post
    - _Requirements: 4.3_
  
  - [x] 11.2 Render post titles as hyperlinks
    - Each post title as anchor tag with href to Reddit URL
    - _Requirements: 4.3_
  
  - [x] 11.3 Include Reddit in executive summary
    - Add Reddit sentiment summary when data available
    - Handle missing Reddit data gracefully
    - _Requirements: 4.1, 4.2_
  
  - [ ]* 11.4 Write property test for HTML rendering
    - **Property 9: HTML Rendering**
    - **Validates: Requirements 4.3**

- [ ] 12. Add comprehensive property tests for data validation
  - [ ]* 12.1 Write property test for post completeness
    - **Property 1: Post Completeness**
    - **Validates: Requirements 1.2, 1.5**
  
  - [ ]* 12.2 Write property test for sentiment classification validity
    - **Property 2: Sentiment Classification Validity**
    - **Validates: Requirements 2.1, 2.4**
  
  - [ ]* 12.3 Write property test for sentiment classification logic
    - **Property 3: Sentiment Classification Logic**
    - **Validates: Requirements 2.2, 2.3**

- [ ] 13. Final checkpoint - Run full test suite and evaluation
  - Ensure all tests pass, ask the user if questions arise.
  - Run evaluation suite: `trading_copilot/.venv/bin/python trading_copilot/scripts/run_statistical_evaluation.py`
  - Verify metrics are maintained or improved per eval-driven development requirements

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The existing RedditAgent implementation provides a foundation; tasks extend it with signal generation, date filtering, and integrations
- Follow eval-driven development: run evaluation before and after implementation to verify metrics
