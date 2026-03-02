"""Unit tests for EpochRunner."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from trading_copilot.analyzer import SentimentAnalyzer
from trading_copilot.evaluation.epoch_runner import EpochRunner
from trading_copilot.evaluation.errors import (
    HistoricalDataError,
    OutcomeFetchError,
)
from trading_copilot.evaluation.historical_data_fetcher import HistoricalDataFetcher
from trading_copilot.evaluation.models import (
    ActualOutcome,
    DateRange,
    EpochPeriod,
    EpochStatus,
)
from trading_copilot.evaluation.outcome_fetcher import OutcomeFetcher
from trading_copilot.models import (
    AggregatedReport,
    ArticleSentiment,
    ConfidenceLevel,
    NewsArticle,
    NewsOutput,
    Sentiment,
    SentimentResult,
    Signal,
)


@pytest.fixture
def sample_epoch_period():
    """Create a sample epoch period for testing."""
    return EpochPeriod(
        epoch_number=1,
        look_back=DateRange(
            start=date(2024, 1, 1),
            end=date(2024, 1, 14),
        ),
        prediction=DateRange(
            start=date(2024, 1, 15),
            end=date(2024, 1, 21),
        ),
    )


@pytest.fixture
def sample_news_output():
    """Create sample news output with articles."""
    return NewsOutput(
        ticker="AAPL",
        articles=[
            NewsArticle(
                headline="Apple reports strong earnings",
                source="Reuters",
                published_at=datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc),
                summary="Apple exceeded expectations",
                url="https://example.com/1",
                sentiment=ArticleSentiment.POSITIVE,
            ),
            NewsArticle(
                headline="Apple launches new product",
                source="Bloomberg",
                published_at=datetime(2024, 1, 12, 14, 0, 0, tzinfo=timezone.utc),
                summary="New iPhone announced",
                url="https://example.com/2",
                sentiment=ArticleSentiment.POSITIVE,
            ),
        ],
        retrieved_at=datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
        status="success",
        data_source="test",
    )


@pytest.fixture
def sample_aggregated_report(sample_news_output):
    """Create sample aggregated report."""
    return AggregatedReport(
        ticker="AAPL",
        news=sample_news_output,
        earnings=None,
        macro=None,
        reddit=None,
        aggregated_at=datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
        missing_components=[],
    )


@pytest.fixture
def sample_sentiment_result():
    """Create sample sentiment result."""
    return SentimentResult(
        ticker="AAPL",
        sentiment=Sentiment.BULLISH,
        confidence=ConfidenceLevel.HIGH,
        signals=[],
        summary="Bullish outlook",
        key_factors=["Positive news"],
        risks=["Market volatility"],
        disclaimer="Test disclaimer",
        analyzed_at=datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
        aggregated_report=None,
    )


@pytest.fixture
def sample_actual_outcome():
    """Create sample actual outcome."""
    return ActualOutcome(
        direction=Sentiment.BULLISH,
        open_price=150.0,
        close_price=160.0,
        price_change_pct=6.67,
    )


@pytest.fixture
def mock_historical_fetcher(sample_aggregated_report):
    """Create mock historical data fetcher."""
    fetcher = MagicMock(spec=HistoricalDataFetcher)
    fetcher.fetch = AsyncMock(return_value=sample_aggregated_report)
    return fetcher


@pytest.fixture
def mock_outcome_fetcher(sample_actual_outcome):
    """Create mock outcome fetcher."""
    fetcher = MagicMock(spec=OutcomeFetcher)
    fetcher.fetch = AsyncMock(return_value=sample_actual_outcome)
    return fetcher


@pytest.fixture
def mock_sentiment_analyzer(sample_sentiment_result):
    """Create mock sentiment analyzer."""
    analyzer = MagicMock(spec=SentimentAnalyzer)
    analyzer.analyze = MagicMock(return_value=sample_sentiment_result)
    return analyzer


class TestEpochRunnerExecute:
    """Tests for EpochRunner.execute method."""

    @pytest.mark.asyncio
    async def test_successful_epoch_execution(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test successful epoch execution with matching prediction."""
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        assert result.status == EpochStatus.COMPLETE
        assert result.epoch_number == 1
        assert result.predicted_sentiment == Sentiment.BULLISH
        assert result.predicted_confidence == ConfidenceLevel.HIGH
        assert result.actual_outcome is not None
        assert result.actual_outcome.direction == Sentiment.BULLISH
        assert result.is_correct is True
        assert result.execution_duration_ms >= 0
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_incorrect_prediction(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
        sample_sentiment_result,
    ):
        """Test epoch execution with incorrect prediction."""
        # Set prediction to bullish but actual to bearish
        sample_sentiment_result.sentiment = Sentiment.BULLISH
        mock_sentiment_analyzer.analyze.return_value = sample_sentiment_result
        
        bearish_outcome = ActualOutcome(
            direction=Sentiment.BEARISH,
            open_price=160.0,
            close_price=150.0,
            price_change_pct=-6.25,
        )
        mock_outcome_fetcher.fetch = AsyncMock(return_value=bearish_outcome)
        
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        assert result.status == EpochStatus.COMPLETE
        assert result.is_correct is False
        assert result.predicted_sentiment == Sentiment.BULLISH
        assert result.actual_outcome.direction == Sentiment.BEARISH

    @pytest.mark.asyncio
    async def test_no_historical_data(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test epoch execution when no historical data is available."""
        # Return empty news data
        empty_report = AggregatedReport(
            ticker="AAPL",
            news=NewsOutput(
                ticker="AAPL",
                articles=[],
                retrieved_at=datetime.now(timezone.utc),
                status="no_data",
                data_source="test",
            ),
            earnings=None,
            macro=None,
            reddit=None,
            aggregated_at=datetime.now(timezone.utc),
            missing_components=[],
        )
        mock_historical_fetcher.fetch = AsyncMock(return_value=empty_report)
        
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        assert result.status == EpochStatus.NO_DATA
        assert result.predicted_sentiment is None
        assert result.predicted_confidence is None
        assert result.actual_outcome is None
        assert result.is_correct is None
        assert "No historical data" in result.error_message

    @pytest.mark.asyncio
    async def test_missing_price_data(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test epoch execution when stock price data is unavailable."""
        mock_outcome_fetcher.fetch = AsyncMock(
            side_effect=OutcomeFetchError("No price data available")
        )
        
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        assert result.status == EpochStatus.INCOMPLETE
        assert result.predicted_sentiment is not None  # Prediction was made
        assert result.actual_outcome is None
        assert result.is_correct is None
        assert "No price data" in result.error_message

    @pytest.mark.asyncio
    async def test_historical_data_error(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test epoch execution when historical data fetch fails."""
        mock_historical_fetcher.fetch = AsyncMock(
            side_effect=HistoricalDataError("API error")
        )
        
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        assert result.status == EpochStatus.FAILED
        assert result.predicted_sentiment is None
        assert result.actual_outcome is None
        assert result.is_correct is None
        assert "API error" in result.error_message

    @pytest.mark.asyncio
    async def test_unexpected_error(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test epoch execution when an unexpected error occurs."""
        mock_historical_fetcher.fetch = AsyncMock(
            side_effect=RuntimeError("Unexpected failure")
        )
        
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        assert result.status == EpochStatus.FAILED
        assert "Unexpected error" in result.error_message
        assert "Unexpected failure" in result.error_message

    @pytest.mark.asyncio
    async def test_execution_duration_recorded(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test that execution duration is recorded in milliseconds."""
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        # Duration should be a non-negative integer
        assert isinstance(result.execution_duration_ms, int)
        assert result.execution_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_period_preserved_in_result(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test that the epoch period is preserved in the result."""
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        assert result.period == sample_epoch_period
        assert result.period.look_back.start == date(2024, 1, 1)
        assert result.period.look_back.end == date(2024, 1, 14)
        assert result.period.prediction.start == date(2024, 1, 15)
        assert result.period.prediction.end == date(2024, 1, 21)

    @pytest.mark.asyncio
    async def test_fetcher_called_with_correct_dates(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test that fetchers are called with correct date ranges."""
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        await runner.execute(sample_epoch_period, "AAPL")
        
        # Verify historical fetcher called with look-back dates
        mock_historical_fetcher.fetch.assert_called_once_with(
            ticker="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 14),
        )
        
        # Verify outcome fetcher called with prediction dates
        mock_outcome_fetcher.fetch.assert_called_once_with(
            ticker="AAPL",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 21),
        )

    @pytest.mark.asyncio
    async def test_null_news_in_report(
        self,
        mock_historical_fetcher,
        mock_outcome_fetcher,
        mock_sentiment_analyzer,
        sample_epoch_period,
    ):
        """Test epoch execution when news is None in aggregated report."""
        null_news_report = AggregatedReport(
            ticker="AAPL",
            news=None,
            earnings=None,
            macro=None,
            reddit=None,
            aggregated_at=datetime.now(timezone.utc),
            missing_components=[],
        )
        mock_historical_fetcher.fetch = AsyncMock(return_value=null_news_report)
        
        runner = EpochRunner(
            historical_fetcher=mock_historical_fetcher,
            outcome_fetcher=mock_outcome_fetcher,
            sentiment_analyzer=mock_sentiment_analyzer,
        )
        
        result = await runner.execute(sample_epoch_period, "AAPL")
        
        assert result.status == EpochStatus.NO_DATA
