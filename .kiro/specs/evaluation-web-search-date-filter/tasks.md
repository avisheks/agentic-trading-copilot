# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Fault Condition** - Historical Date Range Web Search Returns No Data
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: historical date ranges (end_date < today - 14 days) with web search fallback
  - Test that `NewsAgent._research_via_web_search()` with historical date parameters returns articles within the specified range (from Fault Condition in design)
  - The test assertions should match the Expected Behavior Properties from design: articles returned should be within date range OR status is 'no_data' with empty articles
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists because the method doesn't accept date parameters)
  - Document counterexamples found: `_research_via_web_search()` ignores date parameters and uses hardcoded 14-day lookback from today
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Default Behavior Without Date Parameters
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: `NewsAgent.research(ticker)` without date params uses 14-day lookback filter on unfixed code
  - Observe: `NewsAgent._research_via_api()` continues to work unchanged on unfixed code
  - Observe: Article deduplication and sentiment categorization work as before on unfixed code
  - Write property-based test: for all calls without date parameters, the default 14-day lookback filter is applied (from Preservation Requirements in design)
  - Verify test passes on UNFIXED code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3. Fix for historical date range web search returning no data

  - [x] 3.1 Add optional start_date and end_date parameters to NewsAgent.research()
    - Add `start_date: date | None = None` parameter
    - Add `end_date: date | None = None` parameter
    - Pass parameters through to `_research_via_web_search()` when web search fallback is used
    - _Bug_Condition: isBugCondition(input) where input.use_web_search = true AND input.end_date < today() - 14 days_
    - _Expected_Behavior: Date parameters are accepted and propagated to web search method_
    - _Preservation: Calls without date parameters continue to work as before_
    - _Requirements: 2.3_

  - [x] 3.2 Add optional start_date and end_date parameters to NewsAgent._research_via_web_search()
    - Add `start_date: date | None = None` parameter
    - Add `end_date: date | None = None` parameter
    - _Bug_Condition: isBugCondition(input) where web search uses hardcoded 14-day lookback_
    - _Expected_Behavior: Method accepts date range parameters for filtering_
    - _Preservation: Method signature change is backward compatible with None defaults_
    - _Requirements: 2.2_

  - [x] 3.3 Modify the date filtering logic in _research_via_web_search() to use caller-specified range
    - If `start_date` and `end_date` are provided, filter articles to that range (inclusive)
    - If not provided, use the existing 14-day lookback from today (preserve default behavior)
    - Update or add filter method to support date range filtering (start_date to end_date)
    - _Bug_Condition: isBugCondition(input) where cutoff_date = datetime.now() - 14 days ignores caller's date range_
    - _Expected_Behavior: Articles filtered against caller-specified date range when provided_
    - _Preservation: Default 14-day lookback preserved when no date parameters passed_
    - _Requirements: 2.1, 2.2, 2.4_

  - [x] 3.4 Update HistoricalDataFetcher.fetch() to pass date range to NewsAgent
    - Pass `start_date` and `end_date` parameters to `self._news_agent.research()`
    - Ensure date range is propagated correctly to web search fallback
    - _Bug_Condition: isBugCondition(input) where HistoricalDataFetcher cannot communicate date range to NewsAgent_
    - _Expected_Behavior: Date range passed from HistoricalDataFetcher to NewsAgent.research()_
    - _Preservation: Existing timestamp normalization and filtering in HistoricalDataFetcher unchanged_
    - _Requirements: 2.1_

  - [x] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Historical Date Range Web Search Returns Articles Within Specified Range
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Default Behavior Without Date Parameters
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
