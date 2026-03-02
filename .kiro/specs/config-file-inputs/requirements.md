# Requirements Document

## Introduction

This feature externalizes application configuration inputs (stock ticker symbols, email delivery settings, report preferences) into a centralized YAML configuration file. Currently, inputs like stock tickers are passed as command-line arguments and email settings require manual code changes. This feature enables users to configure the Trading Copilot application through a single config file, making it easier to manage multiple tickers, email recipients, and other runtime settings without code modifications.

## Glossary

- **Config_Manager**: The component responsible for loading, validating, and providing access to configuration data from YAML files
- **Application_Config**: The top-level configuration object containing all user-configurable inputs including tickers, email settings, and report preferences
- **Ticker_Config**: Configuration for stock ticker symbols to be analyzed by the Trading Copilot
- **Email_Config**: Configuration for email delivery including SMTP settings and recipient addresses
- **Report_Config**: Configuration for report generation preferences including format and delivery options

## Requirements

### Requirement 1: Application Configuration File Structure

**User Story:** As a user, I want to define all application inputs in a single YAML configuration file, so that I can easily manage and modify settings without changing code.

#### Acceptance Criteria

1. THE Config_Manager SHALL load application configuration from a YAML file at `trading_copilot/config/app_config.yaml`
2. WHEN the configuration file does not exist, THE Config_Manager SHALL raise a ConfigurationError with a descriptive message
3. WHEN the configuration file contains invalid YAML syntax, THE Config_Manager SHALL raise a ConfigurationError with the parsing error details
4. THE Application_Config SHALL support the following top-level sections: `tickers`, `email`, and `report`

### Requirement 2: Stock Ticker Configuration

**User Story:** As a user, I want to configure which stock tickers to analyze in the config file, so that I can easily add or remove tickers without modifying command-line arguments.

#### Acceptance Criteria

1. THE Config_Manager SHALL parse a `tickers` section containing a list of stock ticker symbols
2. WHEN the `tickers` section is missing, THE Config_Manager SHALL raise a ConfigurationError indicating the required field is missing
3. WHEN the `tickers` section is empty, THE Config_Manager SHALL raise a ConfigurationError indicating at least one ticker is required
4. WHEN a ticker symbol contains invalid characters, THE Config_Manager SHALL raise a ConfigurationError identifying the invalid ticker
5. THE Config_Manager SHALL normalize ticker symbols to uppercase format
6. FOR ALL valid ticker configurations, loading then saving then loading SHALL produce an equivalent configuration (round-trip property)

### Requirement 3: Email Delivery Configuration

**User Story:** As a user, I want to configure email delivery settings in the config file, so that I can specify recipients and SMTP settings without hardcoding them.

#### Acceptance Criteria

1. THE Config_Manager SHALL parse an `email` section containing SMTP and delivery settings
2. THE Email_Config SHALL include the following fields: `enabled`, `smtp_host`, `smtp_port`, `smtp_username`, `smtp_password_env`, `from_email`, `to_emails`, and `use_tls`
3. WHEN `email.enabled` is true and required SMTP fields are missing, THE Config_Manager SHALL raise a ConfigurationError listing the missing fields
4. WHEN `email.to_emails` contains an invalid email address format, THE Config_Manager SHALL raise a ConfigurationError identifying the invalid address
5. THE Config_Manager SHALL support multiple recipient email addresses in the `to_emails` list
6. WHEN `email.enabled` is false, THE Config_Manager SHALL skip validation of SMTP fields

### Requirement 4: Report Configuration

**User Story:** As a user, I want to configure report generation preferences in the config file, so that I can customize output format and delivery options.

#### Acceptance Criteria

1. THE Config_Manager SHALL parse a `report` section containing report generation preferences
2. THE Report_Config SHALL include the following fields: `format`, `include_news`, `include_earnings`, `include_macro`, and `save_to_file`
3. WHEN `report.format` is not one of `html` or `text`, THE Config_Manager SHALL raise a ConfigurationError with valid options
4. WHEN `report.save_to_file` is true, THE Report_Config SHALL include an `output_directory` field specifying where to save reports
5. THE Config_Manager SHALL use default values for optional report fields when not specified

### Requirement 5: Configuration Validation

**User Story:** As a user, I want the application to validate my configuration on startup, so that I receive clear error messages for any misconfigurations.

#### Acceptance Criteria

1. THE Config_Manager SHALL validate all configuration fields before returning the Application_Config
2. WHEN validation fails, THE Config_Manager SHALL return all validation errors in a single ConfigurationError
3. THE Config_Manager SHALL validate that environment variable references for sensitive fields exist in the environment
4. WHEN an environment variable is referenced but not set, THE Config_Manager SHALL include a warning in the validation result

### Requirement 6: Configuration Integration with MVP Pipeline

**User Story:** As a user, I want the MVP test script to use the config file for inputs, so that I can run end-to-end tests with my configured settings.

#### Acceptance Criteria

1. WHEN the MVP test script runs, THE script SHALL load ticker symbols from the Application_Config
2. WHEN the MVP test script runs with email enabled, THE script SHALL use Email_Config settings for report delivery
3. WHEN the `--ticker` command-line argument is provided, THE script SHALL override the config file tickers with the provided value
4. WHEN the `--config` command-line argument is provided, THE script SHALL load configuration from the specified path instead of the default
