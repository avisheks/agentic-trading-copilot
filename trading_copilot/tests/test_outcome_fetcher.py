"""Unit tests for OutcomeFetcher."""

from datetime import date

import pytest

from trading_copilot.evaluation.errors import OutcomeFetchError
from trading_copilot.evaluation.models import ActualOutcome
from trading_copilot.evaluation.outcome_fetcher import (
    OutcomeFetcher,
    StockPriceProvider,
)
from trading_copilot.models import Sentiment


class MockPriceProvider:
    """Mock price provider for testing."""

    def __init__(
        self,
        open_price: float,
        close_price: float,
        should_fail: bool = False,
        error_message: str = "Mock error",
    ) -> None:
        self.open_price = open_price
        self.close_price = close_price
        self.should_fail = should_fail
        self.error_message = error_message
        self.calls: list[tuple[str, date, date]] = []

    def get_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, float]:
        self.calls.append((ticker, start_date, end_date))
        
        if self.should_fail:
            raise OutcomeFetchError(self.error_message)
        
        return {
            "open_price": self.open_price,
            "close_price": self.close_price,
        }


class TestOutcomeFetcher:
    """Tests for OutcomeFetcher class."""

    @pytest.mark.asyncio
    async def test_fetch_bullish_when_close_greater_than_open(self) -> None:
        """Test that BULLISH is returned when close > open."""
        provider = MockPriceProvider(open_price=100.0, close_price=110.0)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 7),  # Sunday
            end_date=date(2024, 1, 13),   # Saturday
        )
        
        assert result.direction == Sentiment.BULLISH
        assert result.open_price == 100.0
        assert result.close_price == 110.0
        assert result.price_change_pct == pytest.approx(10.0)

    @pytest.mark.asyncio
    async def test_fetch_bearish_when_close_less_than_open(self) -> None:
        """Test that BEARISH is returned when close < open."""
        provider = MockPriceProvider(open_price=100.0, close_price=90.0)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 7),
            end_date=date(2024, 1, 13),
        )
        
        assert result.direction == Sentiment.BEARISH
        assert result.open_price == 100.0
        assert result.close_price == 90.0
        assert result.price_change_pct == pytest.approx(-10.0)

    @pytest.mark.asyncio
    async def test_fetch_bearish_when_close_equals_open(self) -> None:
        """Test that BEARISH is returned when close == open (no change)."""
        provider = MockPriceProvider(open_price=100.0, close_price=100.0)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        result = await fetcher.fetch(
            ticker="AAPL",
            start_date=date(2024, 1, 7),
            end_date=date(2024, 1, 13),
        )
        
        assert result.direction == Sentiment.BEARISH
        assert result.price_change_pct == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_fetch_raises_error_when_provider_fails(self) -> None:
        """Test that OutcomeFetchError is raised when provider fails."""
        provider = MockPriceProvider(
            open_price=0,
            close_price=0,
            should_fail=True,
            error_message="No data available",
        )
        fetcher = OutcomeFetcher(price_provider=provider)
        
        with pytest.raises(OutcomeFetchError, match="No data available"):
            await fetcher.fetch(
                ticker="INVALID",
                start_date=date(2024, 1, 7),
                end_date=date(2024, 1, 13),
            )

    @pytest.mark.asyncio
    async def test_fetch_passes_correct_parameters_to_provider(self) -> None:
        """Test that correct parameters are passed to the price provider."""
        provider = MockPriceProvider(open_price=100.0, close_price=105.0)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        start = date(2024, 2, 4)
        end = date(2024, 2, 10)
        
        await fetcher.fetch(ticker="MSFT", start_date=start, end_date=end)
        
        assert len(provider.calls) == 1
        assert provider.calls[0] == ("MSFT", start, end)

    @pytest.mark.asyncio
    async def test_fetch_returns_actual_outcome_dataclass(self) -> None:
        """Test that fetch returns an ActualOutcome instance."""
        provider = MockPriceProvider(open_price=50.0, close_price=55.0)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        result = await fetcher.fetch(
            ticker="GOOG",
            start_date=date(2024, 1, 7),
            end_date=date(2024, 1, 13),
        )
        
        assert isinstance(result, ActualOutcome)

    @pytest.mark.asyncio
    async def test_fetch_calculates_percentage_change_correctly(self) -> None:
        """Test percentage change calculation for various price movements."""
        # Test 25% increase
        provider = MockPriceProvider(open_price=80.0, close_price=100.0)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        result = await fetcher.fetch(
            ticker="TEST",
            start_date=date(2024, 1, 7),
            end_date=date(2024, 1, 13),
        )
        
        assert result.price_change_pct == pytest.approx(25.0)

    @pytest.mark.asyncio
    async def test_fetch_handles_zero_open_price(self) -> None:
        """Test that zero open price doesn't cause division error."""
        provider = MockPriceProvider(open_price=0.0, close_price=10.0)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        result = await fetcher.fetch(
            ticker="TEST",
            start_date=date(2024, 1, 7),
            end_date=date(2024, 1, 13),
        )
        
        # When open is 0, percentage change should be 0 to avoid division by zero
        assert result.price_change_pct == 0.0
        # Direction should still be determined (close > open means bullish)
        assert result.direction == Sentiment.BULLISH

    @pytest.mark.asyncio
    async def test_fetch_small_price_difference_bullish(self) -> None:
        """Test that even tiny positive difference is classified as BULLISH."""
        provider = MockPriceProvider(open_price=100.0, close_price=100.01)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        result = await fetcher.fetch(
            ticker="TEST",
            start_date=date(2024, 1, 7),
            end_date=date(2024, 1, 13),
        )
        
        assert result.direction == Sentiment.BULLISH
        assert result.price_change_pct == pytest.approx(0.01)

    @pytest.mark.asyncio
    async def test_fetch_small_price_difference_bearish(self) -> None:
        """Test that even tiny negative difference is classified as BEARISH."""
        provider = MockPriceProvider(open_price=100.0, close_price=99.99)
        fetcher = OutcomeFetcher(price_provider=provider)
        
        result = await fetcher.fetch(
            ticker="TEST",
            start_date=date(2024, 1, 7),
            end_date=date(2024, 1, 13),
        )
        
        assert result.direction == Sentiment.BEARISH
        assert result.price_change_pct == pytest.approx(-0.01)
