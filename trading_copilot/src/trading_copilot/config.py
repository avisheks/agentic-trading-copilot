"""Configuration management for Trading Copilot."""

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from trading_copilot.models import DataSourceConfig, SourceConfig


# App configuration dataclasses
@dataclass
class TickerConfig:
    """Configuration for stock ticker symbols."""

    symbols: list[str]  # Normalized to uppercase


@dataclass
class EmailConfig:
    """Configuration for email delivery."""

    enabled: bool
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password_env: str | None = None  # Environment variable name
    from_email: str | None = None
    to_emails: list[str] | None = None
    use_tls: bool = True


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    format: str = "html"  # "html" or "text"
    include_news: bool = True
    include_earnings: bool = True
    include_macro: bool = True
    save_to_file: bool = False
    output_directory: str | None = None


@dataclass
class AppConfig:
    """Top-level application configuration."""

    tickers: TickerConfig
    email: EmailConfig
    report: ReportConfig


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


@dataclass
class ConfigManager:
    """Manages data source configuration."""

    config_path: Path
    _config: DataSourceConfig | None = None

    def load(self) -> DataSourceConfig:
        """Load and validate configuration from file."""
        if not self.config_path.exists():
            raise ConfigurationError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path) as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")

        errors = self.validate(raw_config)
        if errors:
            raise ConfigurationError(f"Config validation failed: {'; '.join(errors)}")

        self._config = self._parse_config(raw_config)
        return self._config

    def validate(self, config: dict[str, Any]) -> list[str]:
        """Return list of validation errors (empty if valid)."""
        errors: list[str] = []

        if not isinstance(config, dict):
            return ["Config must be a dictionary"]

        for agent_type in ["news_sources", "earnings_sources", "macro_sources"]:
            if agent_type not in config:
                errors.append(f"Missing required field: {agent_type}")
                continue

            sources = config[agent_type]
            if not isinstance(sources, list):
                errors.append(f"{agent_type} must be a list")
                continue

            for i, source in enumerate(sources):
                source_errors = self._validate_source(source, f"{agent_type}[{i}]")
                errors.extend(source_errors)

        return errors

    def _validate_source(self, source: dict[str, Any], prefix: str) -> list[str]:
        """Validate a single source configuration."""
        errors: list[str] = []

        required_fields = ["name", "api_endpoint", "api_key_env", "added_at"]
        for field in required_fields:
            if field not in source:
                errors.append(f"{prefix}: missing required field '{field}'")
            elif field != "added_at" and not source[field]:
                errors.append(f"{prefix}: '{field}' cannot be empty")

        if "added_at" in source:
            try:
                datetime.fromisoformat(str(source["added_at"]))
            except ValueError:
                errors.append(f"{prefix}: 'added_at' must be a valid ISO datetime")

        return errors

    def _parse_config(self, raw: dict[str, Any]) -> DataSourceConfig:
        """Parse raw config dict into DataSourceConfig."""
        return DataSourceConfig(
            news_sources=self._parse_sources(raw.get("news_sources", [])),
            earnings_sources=self._parse_sources(raw.get("earnings_sources", [])),
            macro_sources=self._parse_sources(raw.get("macro_sources", [])),
            last_updated=datetime.now(),
        )

    def _parse_sources(self, sources: list[dict[str, Any]]) -> list[SourceConfig]:
        """Parse list of source configs."""
        return [
            SourceConfig(
                name=s["name"],
                api_endpoint=s["api_endpoint"],
                api_key_env=s["api_key_env"],
                added_at=datetime.fromisoformat(str(s["added_at"])),
                enabled=s.get("enabled", True),
            )
            for s in sources
        ]

    def get_sources_for_agent(self, agent_type: str) -> list[SourceConfig]:
        """Get configured data sources for an agent type."""
        if self._config is None:
            self.load()

        assert self._config is not None
        source_map = {
            "news": self._config.news_sources,
            "earnings": self._config.earnings_sources,
            "macro": self._config.macro_sources,
        }
        return [s for s in source_map.get(agent_type, []) if s.enabled]


logger = logging.getLogger(__name__)


@dataclass
class AppConfigManager:
    """Manages application configuration from app_config.yaml."""

    config_path: Path
    _config: AppConfig | None = None

    # Email validation pattern
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def load(self) -> AppConfig:
        """Load and validate app configuration from YAML file."""
        if not self.config_path.exists():
            raise ConfigurationError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path) as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")

        errors = self.validate(raw_config)
        if errors:
            raise ConfigurationError(f"Config validation failed: {'; '.join(errors)}")

        self._config = self._parse_config(raw_config)
        return self._config

    def validate(self, config: dict[str, Any]) -> list[str]:
        """Return list of validation errors (empty if valid)."""
        errors: list[str] = []

        if not isinstance(config, dict):
            return ["Config must be a dictionary"]

        # Validate tickers
        errors.extend(self._validate_tickers(config))

        # Validate email
        errors.extend(self._validate_email(config))

        # Validate report
        errors.extend(self._validate_report(config))

        return errors

    def _validate_tickers(self, config: dict[str, Any]) -> list[str]:
        """Validate ticker configuration."""
        errors: list[str] = []

        if "tickers" not in config:
            errors.append("Missing required field: tickers")
            return errors

        tickers = config["tickers"]
        if not isinstance(tickers, list):
            errors.append("tickers must be a list")
            return errors

        if len(tickers) == 0:
            errors.append("tickers list cannot be empty - at least one ticker is required")
            return errors

        for ticker in tickers:
            if not isinstance(ticker, str):
                errors.append(f"Invalid ticker symbol: {ticker} (must be a string)")
                continue

            ticker_stripped = ticker.strip()
            if not ticker_stripped:
                errors.append("Invalid ticker symbol: empty string")
                continue

            # Validate alphanumeric only, max 5 chars
            if not ticker_stripped.isalnum():
                errors.append(f"Invalid ticker symbol: {ticker} (must be alphanumeric)")
            elif len(ticker_stripped) > 5:
                errors.append(f"Invalid ticker symbol: {ticker} (max 5 characters)")

        return errors

    def _validate_email(self, config: dict[str, Any]) -> list[str]:
        """Validate email configuration."""
        errors: list[str] = []

        email_config = config.get("email", {})
        if not isinstance(email_config, dict):
            errors.append("email must be a dictionary")
            return errors

        # enabled is required
        if "enabled" not in email_config:
            errors.append("Missing required field: email.enabled")
            return errors

        enabled = email_config.get("enabled", False)

        # Skip validation if email is disabled
        if not enabled:
            return errors

        # Validate required SMTP fields when enabled
        required_smtp_fields = [
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "from_email",
            "to_emails",
        ]
        missing_fields = []
        for field in required_smtp_fields:
            if field not in email_config or email_config[field] is None:
                missing_fields.append(f"email.{field}")

        if missing_fields:
            errors.append(f"Missing required fields when email is enabled: {', '.join(missing_fields)}")

        # Validate email addresses in to_emails
        to_emails = email_config.get("to_emails", [])
        if isinstance(to_emails, list):
            for email in to_emails:
                if not self._is_valid_email(email):
                    errors.append(f"Invalid email address: {email}")

        # Validate from_email format
        from_email = email_config.get("from_email")
        if from_email and not self._is_valid_email(from_email):
            errors.append(f"Invalid email address: {from_email}")

        # Check environment variable for password
        password_env = email_config.get("smtp_password_env")
        if password_env and not os.environ.get(password_env):
            logger.warning(f"Environment variable not set: {password_env}")

        return errors

    def _is_valid_email(self, email: str) -> bool:
        """Check if email address has valid format."""
        if not isinstance(email, str):
            return False
        return bool(self.EMAIL_PATTERN.match(email))

    def _validate_report(self, config: dict[str, Any]) -> list[str]:
        """Validate report configuration."""
        errors: list[str] = []

        report_config = config.get("report", {})
        if not isinstance(report_config, dict):
            errors.append("report must be a dictionary")
            return errors

        # Validate format
        report_format = report_config.get("format", "html")
        if report_format not in ("html", "text"):
            errors.append(f"Invalid report format: {report_format}. Must be 'html' or 'text'")

        # Validate output_directory when save_to_file is true
        save_to_file = report_config.get("save_to_file", False)
        if save_to_file:
            output_dir = report_config.get("output_directory")
            if not output_dir:
                errors.append("Missing required field: report.output_directory (required when save_to_file is true)")

        return errors

    def _parse_config(self, raw: dict[str, Any]) -> AppConfig:
        """Parse raw config dict into AppConfig."""
        # Parse tickers (normalize to uppercase)
        raw_tickers = raw.get("tickers", [])
        normalized_tickers = [t.strip().upper() for t in raw_tickers if isinstance(t, str)]
        ticker_config = TickerConfig(symbols=normalized_tickers)

        # Parse email config
        raw_email = raw.get("email", {})
        email_config = EmailConfig(
            enabled=raw_email.get("enabled", False),
            smtp_host=raw_email.get("smtp_host"),
            smtp_port=raw_email.get("smtp_port"),
            smtp_username=raw_email.get("smtp_username"),
            smtp_password_env=raw_email.get("smtp_password_env"),
            from_email=raw_email.get("from_email"),
            to_emails=raw_email.get("to_emails", []),
            use_tls=raw_email.get("use_tls", True),
        )

        # Parse report config with defaults
        raw_report = raw.get("report", {})
        report_config = ReportConfig(
            format=raw_report.get("format", "html"),
            include_news=raw_report.get("include_news", True),
            include_earnings=raw_report.get("include_earnings", True),
            include_macro=raw_report.get("include_macro", True),
            save_to_file=raw_report.get("save_to_file", False),
            output_directory=raw_report.get("output_directory"),
        )

        return AppConfig(
            tickers=ticker_config,
            email=email_config,
            report=report_config,
        )
