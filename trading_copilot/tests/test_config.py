"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from trading_copilot.config import ConfigManager, ConfigurationError


class TestConfigManager:
    """Unit tests for ConfigManager."""

    def test_load_valid_config(self):
        """Valid config file loads successfully."""
        config_data = {
            "news_sources": [
                {
                    "name": "Test News",
                    "api_endpoint": "https://api.test.com",
                    "api_key_env": "TEST_API_KEY",
                    "added_at": "2024-01-01T00:00:00",
                    "enabled": True,
                }
            ],
            "earnings_sources": [],
            "macro_sources": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        manager = ConfigManager(config_path=config_path)
        config = manager.load()

        assert len(config.news_sources) == 1
        assert config.news_sources[0].name == "Test News"
        assert config.news_sources[0].api_endpoint == "https://api.test.com"
        assert config.news_sources[0].enabled is True

        config_path.unlink()

    def test_missing_config_file_raises_error(self):
        """Missing config file raises ConfigurationError."""
        manager = ConfigManager(config_path=Path("/nonexistent/config.yaml"))
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.load()
        
        assert "not found" in str(exc_info.value)

    def test_invalid_yaml_raises_error(self):
        """Invalid YAML raises ConfigurationError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)

        manager = ConfigManager(config_path=config_path)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.load()
        
        assert "Invalid YAML" in str(exc_info.value)
        config_path.unlink()

    def test_missing_required_field_raises_error(self):
        """Missing required field raises ConfigurationError."""
        config_data = {
            "news_sources": [],
            # Missing earnings_sources and macro_sources
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        manager = ConfigManager(config_path=config_path)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.load()
        
        assert "Missing required field" in str(exc_info.value)
        config_path.unlink()

    def test_source_missing_api_endpoint_raises_error(self):
        """Source missing api_endpoint raises ConfigurationError."""
        config_data = {
            "news_sources": [
                {
                    "name": "Test",
                    # Missing api_endpoint
                    "api_key_env": "KEY",
                    "added_at": "2024-01-01T00:00:00",
                }
            ],
            "earnings_sources": [],
            "macro_sources": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        manager = ConfigManager(config_path=config_path)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.load()
        
        assert "api_endpoint" in str(exc_info.value)
        config_path.unlink()

    def test_get_sources_for_agent(self):
        """get_sources_for_agent returns correct sources."""
        config_data = {
            "news_sources": [
                {
                    "name": "News1",
                    "api_endpoint": "https://news1.com",
                    "api_key_env": "KEY1",
                    "added_at": "2024-01-01T00:00:00",
                    "enabled": True,
                },
                {
                    "name": "News2",
                    "api_endpoint": "https://news2.com",
                    "api_key_env": "KEY2",
                    "added_at": "2024-01-01T00:00:00",
                    "enabled": False,
                },
            ],
            "earnings_sources": [],
            "macro_sources": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        manager = ConfigManager(config_path=config_path)
        manager.load()
        
        sources = manager.get_sources_for_agent("news")
        assert len(sources) == 1  # Only enabled sources
        assert sources[0].name == "News1"

        config_path.unlink()

    def test_validate_returns_empty_for_valid_config(self):
        """validate() returns empty list for valid config."""
        config_data = {
            "news_sources": [
                {
                    "name": "Test",
                    "api_endpoint": "https://test.com",
                    "api_key_env": "KEY",
                    "added_at": "2024-01-01T00:00:00",
                }
            ],
            "earnings_sources": [],
            "macro_sources": [],
        }

        manager = ConfigManager(config_path=Path("dummy"))
        errors = manager.validate(config_data)
        assert errors == []

    def test_validate_returns_errors_for_invalid_config(self):
        """validate() returns list of errors for invalid config."""
        config_data = {
            "news_sources": [
                {
                    "name": "",  # Empty name
                    "api_endpoint": "https://test.com",
                    "api_key_env": "KEY",
                    "added_at": "invalid-date",  # Invalid date
                }
            ],
            "earnings_sources": [],
            "macro_sources": [],
        }

        manager = ConfigManager(config_path=Path("dummy"))
        errors = manager.validate(config_data)
        assert len(errors) >= 2
