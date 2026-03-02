"""Tests for ticker validation."""

import pytest
from trading_copilot.validator import TickerValidator, VALID_TICKERS


class TestTickerValidator:
    """Unit tests for TickerValidator."""

    def setup_method(self):
        self.validator = TickerValidator()

    def test_normalize_uppercase(self):
        """Ticker normalization converts to uppercase."""
        assert self.validator.normalize("aapl") == "AAPL"
        assert self.validator.normalize("Msft") == "MSFT"
        assert self.validator.normalize("GOOGL") == "GOOGL"

    def test_normalize_strips_whitespace(self):
        """Ticker normalization strips whitespace."""
        assert self.validator.normalize("  aapl  ") == "AAPL"
        assert self.validator.normalize("\tmsft\n") == "MSFT"

    def test_valid_ticker_accepted(self):
        """Valid tickers return successful validation."""
        result = self.validator.validate("AAPL")
        assert result.is_valid is True
        assert result.normalized_ticker == "AAPL"
        assert result.error_message is None

    def test_valid_ticker_lowercase(self):
        """Valid tickers with lowercase are normalized and accepted."""
        result = self.validator.validate("aapl")
        assert result.is_valid is True
        assert result.normalized_ticker == "AAPL"

    def test_valid_ticker_mixed_case(self):
        """Valid tickers with mixed case are normalized and accepted."""
        result = self.validator.validate("AaPl")
        assert result.is_valid is True
        assert result.normalized_ticker == "AAPL"

    def test_invalid_ticker_rejected(self):
        """Invalid tickers return error with message."""
        result = self.validator.validate("XXXXX")
        assert result.is_valid is False
        assert result.normalized_ticker is None
        assert result.error_message is not None
        assert "Unrecognized ticker" in result.error_message

    def test_empty_ticker_rejected(self):
        """Empty ticker returns error."""
        result = self.validator.validate("")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "empty" in result.error_message.lower()

    def test_whitespace_only_rejected(self):
        """Whitespace-only ticker returns error."""
        result = self.validator.validate("   ")
        assert result.is_valid is False
        assert result.error_message is not None

    def test_numeric_ticker_rejected(self):
        """Numeric ticker returns error."""
        result = self.validator.validate("12345")
        assert result.is_valid is False
        assert "letters" in result.error_message.lower()

    def test_special_chars_rejected(self):
        """Ticker with special characters returns error."""
        result = self.validator.validate("AAP$L")
        assert result.is_valid is False
        assert "letters" in result.error_message.lower()

    def test_too_long_ticker_rejected(self):
        """Ticker longer than 5 characters returns error."""
        result = self.validator.validate("TOOLONG")
        assert result.is_valid is False
        assert "1-5 characters" in result.error_message

    def test_custom_ticker_set(self):
        """Validator can use custom ticker set."""
        custom_validator = TickerValidator(valid_tickers={"TEST", "DEMO"})
        
        result = custom_validator.validate("TEST")
        assert result.is_valid is True
        
        result = custom_validator.validate("AAPL")
        assert result.is_valid is False

    def test_all_default_tickers_valid(self):
        """All default tickers in VALID_TICKERS pass validation."""
        for ticker in VALID_TICKERS:
            result = self.validator.validate(ticker)
            assert result.is_valid is True, f"Expected {ticker} to be valid"
            assert result.normalized_ticker == ticker
