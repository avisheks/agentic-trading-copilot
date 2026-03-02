"""Epoch runner for executing single evaluation epochs."""

import time
from datetime import datetime, timezone

from trading_copilot.analyzer import SentimentAnalyzer
from trading_copilot.evaluation.errors import (
    EvaluationError,
    HistoricalDataError,
    OutcomeFetchError,
)
from trading_copilot.evaluation.historical_data_fetcher import HistoricalDataFetcher
from trading_copilot.evaluation.models import (
    EpochPeriod,
    EpochResult,
    EpochStatus,
)
from trading_copilot.evaluation.outcome_fetcher import OutcomeFetcher


class EpochRunner:
    """Executes a single epoch evaluation.
    
    This component orchestrates the evaluation of a single epoch by:
    1. Fetching historical data for the look-back period
    2. Generating a sentiment prediction using the SentimentAnalyzer
    3. Fetching the actual outcome for the prediction period
    4. Comparing the prediction against the actual outcome
    """

    def __init__(
        self,
        historical_fetcher: HistoricalDataFetcher,
        outcome_fetcher: OutcomeFetcher,
        sentiment_analyzer: SentimentAnalyzer,
    ) -> None:
        """Initialize with dependencies.
        
        Args:
            historical_fetcher: Fetcher for historical news data
            outcome_fetcher: Fetcher for actual stock price outcomes
            sentiment_analyzer: Analyzer for generating sentiment predictions
        """
        self._historical_fetcher = historical_fetcher
        self._outcome_fetcher = outcome_fetcher
        self._sentiment_analyzer = sentiment_analyzer

    async def execute(
        self,
        period: EpochPeriod,
        ticker: str,
    ) -> EpochResult:
        """Execute single epoch evaluation.
        
        Performs the following steps:
        1. Fetch historical data for the 2-week look-back period
        2. Generate sentiment prediction for the 1-week prediction period
        3. Fetch actual outcome for the prediction period
        4. Compare prediction vs actual
        
        Args:
            period: The epoch period containing look-back and prediction date ranges
            ticker: Stock ticker symbol to evaluate
            
        Returns:
            EpochResult with prediction, actual outcome, match status, and duration
        """
        start_time = time.perf_counter()
        
        try:
            # Step 1: Fetch historical data for look-back period
            aggregated_report = await self._historical_fetcher.fetch(
                ticker=ticker,
                start_date=period.look_back.start,
                end_date=period.look_back.end,
            )
            
            # Check if we have historical data
            if (
                aggregated_report.news is None
                or aggregated_report.news.status == "no_data"
                or not aggregated_report.news.articles
            ):
                execution_duration_ms = self._calculate_duration_ms(start_time)
                return EpochResult(
                    epoch_number=period.epoch_number,
                    period=period,
                    status=EpochStatus.NO_DATA,
                    predicted_sentiment=None,
                    predicted_confidence=None,
                    actual_outcome=None,
                    is_correct=None,
                    execution_duration_ms=execution_duration_ms,
                    error_message="No historical data available for look-back period",
                )
            
            # Step 2: Generate sentiment prediction using SentimentAnalyzer
            sentiment_result = self._sentiment_analyzer.analyze(aggregated_report)
            
            # Step 3: Fetch actual outcome for prediction period
            try:
                actual_outcome = await self._outcome_fetcher.fetch(
                    ticker=ticker,
                    start_date=period.prediction.start,
                    end_date=period.prediction.end,
                )
            except OutcomeFetchError as e:
                # Missing price data - mark as INCOMPLETE
                execution_duration_ms = self._calculate_duration_ms(start_time)
                return EpochResult(
                    epoch_number=period.epoch_number,
                    period=period,
                    status=EpochStatus.INCOMPLETE,
                    predicted_sentiment=sentiment_result.sentiment,
                    predicted_confidence=sentiment_result.confidence,
                    actual_outcome=None,
                    is_correct=None,
                    execution_duration_ms=execution_duration_ms,
                    error_message=str(e),
                )
            
            # Step 4: Compare prediction vs actual
            is_correct = sentiment_result.sentiment == actual_outcome.direction
            
            execution_duration_ms = self._calculate_duration_ms(start_time)
            
            return EpochResult(
                epoch_number=period.epoch_number,
                period=period,
                status=EpochStatus.COMPLETE,
                predicted_sentiment=sentiment_result.sentiment,
                predicted_confidence=sentiment_result.confidence,
                actual_outcome=actual_outcome,
                is_correct=is_correct,
                execution_duration_ms=execution_duration_ms,
            )
            
        except (HistoricalDataError, EvaluationError) as e:
            # Known evaluation errors - mark as FAILED
            execution_duration_ms = self._calculate_duration_ms(start_time)
            return EpochResult(
                epoch_number=period.epoch_number,
                period=period,
                status=EpochStatus.FAILED,
                predicted_sentiment=None,
                predicted_confidence=None,
                actual_outcome=None,
                is_correct=None,
                execution_duration_ms=execution_duration_ms,
                error_message=str(e),
            )
        except Exception as e:
            # Unexpected errors - mark as FAILED with error message
            execution_duration_ms = self._calculate_duration_ms(start_time)
            return EpochResult(
                epoch_number=period.epoch_number,
                period=period,
                status=EpochStatus.FAILED,
                predicted_sentiment=None,
                predicted_confidence=None,
                actual_outcome=None,
                is_correct=None,
                execution_duration_ms=execution_duration_ms,
                error_message=f"Unexpected error: {e}",
            )

    def _calculate_duration_ms(self, start_time: float) -> int:
        """Calculate execution duration in milliseconds.
        
        Args:
            start_time: Start time from time.perf_counter()
            
        Returns:
            Duration in milliseconds as an integer
        """
        elapsed = time.perf_counter() - start_time
        return int(elapsed * 1000)
