"""Outcome fetcher for determining actual stock price movements."""

from datetime import date, timedelta
from typing import Protocol

import yfinance as yf

from trading_copilot.evaluation.errors import OutcomeFetchError
from trading_copilot.evaluation.models import ActualOutcome
from trading_copilot.models import Sentiment


class StockPriceProvider(Protocol):
    """Protocol for fetching stock price data."""

    def get_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, float]:
        """Get stock prices for a date range.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for price data
            end_date: End date for price data
            
        Returns:
            Dictionary with 'open_price' and 'close_price' keys
            
        Raises:
            OutcomeFetchError: If price data cannot be retrieved
        """
        ...


class YFinanceProvider:
    """Stock price provider using yfinance library."""

    def get_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, float]:
        """Get stock prices using yfinance.
        
        Fetches the opening price on the first trading day at or after start_date
        and the closing price on the last trading day at or before end_date.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for price data (Sunday)
            end_date: End date for price data (Saturday)
            
        Returns:
            Dictionary with 'open_price' and 'close_price' keys
            
        Raises:
            OutcomeFetchError: If price data cannot be retrieved
        """
        try:
            # Extend the date range slightly to ensure we capture trading days
            # since start_date (Sunday) and end_date (Saturday) are typically non-trading days
            fetch_start = start_date - timedelta(days=1)
            fetch_end = end_date + timedelta(days=2)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(
                start=fetch_start.isoformat(),
                end=fetch_end.isoformat(),
            )
            
            if hist.empty:
                raise OutcomeFetchError(
                    f"No stock price data available for {ticker} "
                    f"between {start_date} and {end_date}"
                )
            
            # Filter to only include dates within our target range
            hist = hist[
                (hist.index.date >= start_date) & 
                (hist.index.date <= end_date)
            ]
            
            if hist.empty:
                raise OutcomeFetchError(
                    f"No trading days found for {ticker} "
                    f"between {start_date} and {end_date}"
                )
            
            # Get opening price from first trading day and closing price from last
            open_price = float(hist.iloc[0]["Open"])
            close_price = float(hist.iloc[-1]["Close"])
            
            return {
                "open_price": open_price,
                "close_price": close_price,
            }
            
        except OutcomeFetchError:
            raise
        except Exception as e:
            raise OutcomeFetchError(
                f"Failed to fetch stock prices for {ticker}: {e}"
            ) from e


class OutcomeFetcher:
    """Fetches actual stock price outcomes for validation.
    
    This component retrieves stock price data for a prediction period
    and determines whether the stock was bullish or bearish based on
    the price movement.
    """

    def __init__(
        self,
        price_provider: StockPriceProvider | None = None,
    ) -> None:
        """Initialize with optional price provider.
        
        Args:
            price_provider: Provider for stock price data. Defaults to
                YFinanceProvider if not specified.
        """
        self._price_provider = price_provider or YFinanceProvider()

    async def fetch(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> ActualOutcome:
        """Determine if stock was bullish or bearish during the period.
        
        Retrieves stock prices for the prediction period and classifies
        the movement as:
        - BULLISH: if closing price on end_date > opening price on start_date
        - BEARISH: if closing price on end_date <= opening price on start_date
        
        Args:
            ticker: Stock ticker symbol
            start_date: First day of prediction period (Sunday)
            end_date: Last day of prediction period (Saturday)
            
        Returns:
            ActualOutcome with direction and price data
            
        Raises:
            OutcomeFetchError: If stock price data is unavailable,
                indicating the epoch should be marked as "incomplete"
        """
        # Fetch prices from the provider
        prices = self._price_provider.get_prices(ticker, start_date, end_date)
        
        open_price = prices["open_price"]
        close_price = prices["close_price"]
        
        # Classify direction based on price movement
        # Bullish: close > open
        # Bearish: close <= open
        direction = (
            Sentiment.BULLISH if close_price > open_price else Sentiment.BEARISH
        )
        
        # Calculate percentage change
        if open_price != 0:
            price_change_pct = ((close_price - open_price) / open_price) * 100
        else:
            price_change_pct = 0.0
        
        return ActualOutcome(
            direction=direction,
            open_price=open_price,
            close_price=close_price,
            price_change_pct=price_change_pct,
        )
