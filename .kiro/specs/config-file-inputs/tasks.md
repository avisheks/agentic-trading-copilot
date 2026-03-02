# Implementation Plan: Config File Inputs

## Overview

Extend the existing config module with `AppConfigManager` and dataclasses for application configuration (tickers, email, report settings). Integrate with the MVP test script to load inputs from `app_config.yaml`.

## Tasks

- [x] 1. Create configuration dataclasses
  - [x] 1.1 Add `TickerConfig`, `EmailConfig`, `ReportConfig`, and `AppConfig` dataclasses to `config.py`
    - Define fields as specified in design document
    - Use `| None` for optional fields
    - _Requirements: 1.4, 2.1, 3.2, 4.2_

- [x] 2. Implement AppConfigManager
  - [x] 2.1 Create `AppConfigManager` class with `load()` and `validate()` methods
    - Handle file not found and YAML parsing errors
    - Parse raw YAML into dataclass instances
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 2.2 Implement ticker validation logic
    - Validate alphanumeric characters only, max 5 chars
    - Normalize to uppercase
    - Reject empty ticker list
    - _Requirements: 2.2, 2.3, 2.4, 2.5_
  
  - [x] 2.3 Implement email validation logic
    - Validate required SMTP fields when enabled=true
    - Validate email address format for to_emails
    - Skip validation when enabled=false
    - _Requirements: 3.3, 3.4, 3.5, 3.6_
  
  - [x] 2.4 Implement report validation logic
    - Validate format is "html" or "text"
    - Require output_directory when save_to_file=true
    - Apply default values for optional fields
    - _Requirements: 4.3, 4.4, 4.5_
  
  - [x] 2.5 Implement error aggregation
    - Collect all validation errors before raising ConfigurationError
    - Check environment variable references and log warnings
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ]* 2.6 Write property test for ticker normalization
    - **Property 1: Ticker Normalization**
    - **Validates: Requirements 2.1, 2.5**
  
  - [ ]* 2.7 Write property test for configuration round-trip
    - **Property 2: Configuration Round-Trip**
    - **Validates: Requirements 2.6**
  
  - [ ]* 2.8 Write property test for invalid ticker rejection
    - **Property 3: Invalid Ticker Rejection**
    - **Validates: Requirements 2.4**
  
  - [ ]* 2.9 Write property test for invalid email format rejection
    - **Property 4: Invalid Email Format Rejection**
    - **Validates: Requirements 3.4**
  
  - [ ]* 2.10 Write property test for conditional email validation
    - **Property 5: Conditional Email Validation**
    - **Validates: Requirements 3.6**
  
  - [ ]* 2.11 Write property test for error aggregation
    - **Property 6: Error Aggregation**
    - **Validates: Requirements 5.2**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Create default app_config.yaml
  - [x] 4.1 Create `trading_copilot/config/app_config.yaml` with example configuration
    - Include sample tickers (AAPL, MSFT, GOOGL)
    - Include email section with enabled=false
    - Include report section with sensible defaults
    - _Requirements: 1.1, 1.4_

- [x] 5. Integrate with MVP test script
  - [x] 5.1 Update `test_mvp.py` to load tickers from AppConfigManager
    - Load app_config.yaml on startup
    - Use configured tickers instead of hardcoded default
    - _Requirements: 6.1_
  
  - [x] 5.2 Add `--config` command-line argument support
    - Allow specifying custom config file path
    - Default to `config/app_config.yaml`
    - _Requirements: 6.4_
  
  - [x] 5.3 Preserve `--ticker` argument as override
    - When provided, override config file tickers
    - _Requirements: 6.3_
  
  - [ ]* 5.4 Write unit tests for MVP script config integration
    - Test loading from config file
    - Test --ticker override behavior
    - Test --config path override
    - _Requirements: 6.1, 6.3, 6.4_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests use `hypothesis` library with minimum 100 iterations
- Existing `ConfigManager` for sources.yaml remains unchanged
- `AppConfigManager` follows same patterns as existing `ConfigManager`
