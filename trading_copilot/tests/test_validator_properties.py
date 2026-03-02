"""Property-based tests for ticker validation.

# Feature: trading-copilot, Property 1: Ticker Normalization
# Feature: trading-copilot, Property 2: Invalid Ticker Error Handling
"""

from hypothesis import given, strategies as st, settings

from trading_copilot.validator import TickerValidator, VALID_TICKERS


class TestTickerValidatorProperties:
    """Property-based tests for TickerValidator."""

    def setup_method(self):
        self.validator = TickerValidator()

    # Feature: trading-copilot, Property 1: Ticker Normalization
    # **Validates: Requirements 1.4**
    @given(ticker=st.text(min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_normalize_always_returns_uppercase(self, ticker):
        """For any ticker string input, the normalized output SHALL be uppercase."""
        result = self.validator.normalize(ticker)
        assert result == ticker.upper().strip()

    # Feature: trading-copilot, Property 1: Ticker Normalization (idempotence)
    # **Validates: Requirements 1.4**
    @given(ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    @settings(max_examples=100)
    def test_normalize_is_idempotent(self, ticker):
        """Normalizing twice produces the same result as normalizing once."""
        once = self.validator.normalize(ticker)
        twice = self.validator.normalize(once)
        assert once == twice

    # Feature: trading-copilot, Property 2: Invalid Ticker Error Handling
    # **Validates: Requirements 1.2**
    @given(ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    @settings(max_examples=100)
    def test_invalid_ticker_returns_error(self, ticker):
        """For any string not in valid tickers, validation returns is_valid=False with error_message."""
        normalized = ticker.upper().strip()
        if normalized not in VALID_TICKERS:
            result = self.validator.validate(ticker)
            assert result.is_valid is False
            assert result.error_message is not None
            assert len(result.error_message) > 0

    # Feature: trading-copilot, Property 2: Invalid Ticker Error Handling (numeric)
    # **Validates: Requirements 1.2**
    @given(ticker=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Nd',))))
    @settings(max_examples=100)
    def test_numeric_ticker_always_invalid(self, ticker):
        """Any purely numeric string SHALL return is_valid=False."""
        result = self.validator.validate(ticker)
        assert result.is_valid is False
        assert result.error_message is not None

    # Feature: trading-copilot, Property 1 & 2: Valid ticker case insensitivity
    # **Validates: Requirements 1.2, 1.4**
    @given(ticker=st.sampled_from(list(VALID_TICKERS)))
    @settings(max_examples=100)
    def test_valid_ticker_case_insensitive(self, ticker):
        """Valid tickers SHALL be accepted regardless of case."""
        # Test lowercase
        result_lower = self.validator.validate(ticker.lower())
        assert result_lower.is_valid is True
        assert result_lower.normalized_ticker == ticker.upper()

        # Test uppercase
        result_upper = self.validator.validate(ticker.upper())
        assert result_upper.is_valid is True
        assert result_upper.normalized_ticker == ticker.upper()

    # Feature: trading-copilot, Property 2: Empty/whitespace handling
    # **Validates: Requirements 1.2**
    @given(ticker=st.text(alphabet=' \t\n\r', min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_whitespace_only_always_invalid(self, ticker):
        """Empty or whitespace-only strings SHALL return is_valid=False."""
        result = self.validator.validate(ticker)
        assert result.is_valid is False
        assert result.error_message is not None
