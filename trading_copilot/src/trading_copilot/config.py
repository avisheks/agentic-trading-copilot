"""Configuration management for Trading Copilot."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from trading_copilot.models import DataSourceConfig, SourceConfig


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
