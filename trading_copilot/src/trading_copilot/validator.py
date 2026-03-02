"""Ticker validation for Trading Copilot."""

from trading_copilot.models import ValidationResult

# Common NYSE/NASDAQ tickers - this is a subset for MVP
# Can be enhanced later with API-based validation
VALID_TICKERS = {
    # Tech
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC",
    "CRM", "ORCL", "ADBE", "CSCO", "IBM", "QCOM", "TXN", "AVGO", "NOW", "SNOW",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "V", "MA", "PYPL",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT", "DHR", "BMY",
    # Consumer
    "WMT", "HD", "PG", "KO", "PEP", "COST", "NKE", "MCD", "SBUX", "TGT",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "OXY", "PSX", "VLO", "MPC", "HAL",
    # Industrial
    "CAT", "BA", "HON", "UPS", "GE", "MMM", "LMT", "RTX", "DE", "UNP",
    # Telecom
    "T", "VZ", "TMUS", "CMCSA", "CHTR",
    # Other popular
    "DIS", "NFLX", "UBER", "LYFT", "ABNB", "SQ", "SHOP", "ZM", "DOCU", "CRWD",
}


class TickerValidator:
    """Validates and normalizes stock ticker symbols."""

    def __init__(self, valid_tickers: set[str] | None = None):
        """Initialize with optional custom ticker set."""
        self._valid_tickers = valid_tickers or VALID_TICKERS

    def normalize(self, ticker: str) -> str:
        """Convert ticker to uppercase standard format."""
        return ticker.upper().strip()

    def validate(self, ticker: str) -> ValidationResult:
        """
        Validate ticker against NYSE/NASDAQ listings.

        Args:
            ticker: Raw ticker input

        Returns:
            ValidationResult with normalized ticker or error details
        """
        if not ticker or not ticker.strip():
            return ValidationResult(
                is_valid=False,
                normalized_ticker=None,
                error_message="Ticker cannot be empty",
            )

        normalized = self.normalize(ticker)

        # Check for invalid characters
        if not normalized.isalpha():
            return ValidationResult(
                is_valid=False,
                normalized_ticker=None,
                error_message=f"Invalid ticker format: '{ticker}'. Tickers must contain only letters.",
            )

        # Check length (typical tickers are 1-5 characters)
        if len(normalized) > 5:
            return ValidationResult(
                is_valid=False,
                normalized_ticker=None,
                error_message=f"Invalid ticker: '{ticker}'. Ticker symbols are typically 1-5 characters.",
            )

        # Check against known valid tickers
        if normalized not in self._valid_tickers:
            return ValidationResult(
                is_valid=False,
                normalized_ticker=None,
                error_message=f"Unrecognized ticker: '{normalized}'. Not found in NYSE/NASDAQ listings.",
            )

        return ValidationResult(
            is_valid=True,
            normalized_ticker=normalized,
            error_message=None,
        )
