"""Unit tests for EvaluationRunner."""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

from trading_copilot.evaluation.evaluation_runner import (
    EvaluationRunner,
    EvaluationReportGenerator,
)
from trading_copilot.evaluation.models import (
    ActualOutcome,
    ConfusionMatrix,
    DateRange,
    EpochPeriod,
    EpochResult,
    EpochStatus,
    EvaluationConfig,
    EvaluationMetrics,
)
from trading_copilot.models import ConfidenceLevel, Sentiment


class TestGenerateEpochPeriods:
    """Tests for _generate_epoch_periods method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_epoch_runner = MagicMock()
        self.mock_metrics_calculator = MagicMock()
        self.mock_report_generator = MagicMock()
        
        self.runner = EvaluationRunner(
            epoch_runner=self.mock_epoch_runner,
            metrics_calculator=self.mock_metrics_calculator,
            report_generator=self.mock_report_generator,
        )

    def test_generates_correct_number_of_epochs(self) -> None:
        """Should generate exactly N epochs."""
        end_date = date(2024, 12, 14)  # A Saturday
        
        for n in [1, 5, 10, 52]:
            periods = self.runner._generate_epoch_periods(n, end_date)
            assert len(periods) == n

    def test_epoch_numbers_are_sequential(self) -> None:
        """Epoch numbers should be 1, 2, 3, ..., N."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        for i, period in enumerate(periods, start=1):
            assert period.epoch_number == i

    def test_look_back_period_is_14_days(self) -> None:
        """Each look-back period should be exactly 14 days (2 weeks)."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        for period in periods:
            duration = (period.look_back.end - period.look_back.start).days + 1
            assert duration == 14, f"Look-back period should be 14 days, got {duration}"

    def test_prediction_period_is_7_days(self) -> None:
        """Each prediction period should be exactly 7 days (1 week)."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        for period in periods:
            duration = (period.prediction.end - period.prediction.start).days + 1
            assert duration == 7, f"Prediction period should be 7 days, got {duration}"

    def test_look_back_starts_on_sunday(self) -> None:
        """Look-back periods should start on Sunday."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        for period in periods:
            # weekday(): Monday=0, ..., Sunday=6
            assert period.look_back.start.weekday() == 6, "Look-back should start on Sunday"

    def test_look_back_ends_on_saturday(self) -> None:
        """Look-back periods should end on Saturday."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        for period in periods:
            # weekday(): Monday=0, ..., Saturday=5
            assert period.look_back.end.weekday() == 5, "Look-back should end on Saturday"

    def test_prediction_starts_on_sunday(self) -> None:
        """Prediction periods should start on Sunday."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        for period in periods:
            # weekday(): Monday=0, ..., Sunday=6
            assert period.prediction.start.weekday() == 6, "Prediction should start on Sunday"

    def test_prediction_ends_on_saturday(self) -> None:
        """Prediction periods should end on Saturday."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        for period in periods:
            # weekday(): Monday=0, ..., Saturday=5
            assert period.prediction.end.weekday() == 5, "Prediction should end on Saturday"

    def test_no_look_back_periods_overlap(self) -> None:
        """No two look-back periods should overlap."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(10, end_date)
        
        for i, period1 in enumerate(periods):
            for j, period2 in enumerate(periods):
                if i != j:
                    # Check that ranges don't overlap
                    assert not self._ranges_overlap(
                        period1.look_back, period2.look_back
                    ), f"Look-back periods {i+1} and {j+1} overlap"

    def test_no_prediction_overlaps_with_look_back(self) -> None:
        """No prediction period should overlap with any look-back period."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(10, end_date)
        
        for i, period1 in enumerate(periods):
            for j, period2 in enumerate(periods):
                # Check prediction of period1 doesn't overlap with look-back of period2
                assert not self._ranges_overlap(
                    period1.prediction, period2.look_back
                ), f"Prediction {i+1} overlaps with look-back {j+1}"

    def test_prediction_immediately_follows_look_back(self) -> None:
        """Prediction period should start the day after look-back ends."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        for period in periods:
            expected_prediction_start = period.look_back.end + timedelta(days=1)
            assert period.prediction.start == expected_prediction_start

    def test_epochs_work_backwards_from_end_date(self) -> None:
        """Epochs should be ordered from most recent to oldest."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(5, end_date)
        
        # First epoch should have the most recent dates
        for i in range(len(periods) - 1):
            assert periods[i].prediction.end > periods[i + 1].prediction.end

    def test_handles_non_saturday_end_date(self) -> None:
        """Should find previous Saturday when end_date is not Saturday."""
        # Test with a Wednesday
        end_date = date(2024, 12, 11)  # Wednesday
        periods = self.runner._generate_epoch_periods(1, end_date)
        
        # First prediction should end on the previous Saturday (Dec 7)
        assert periods[0].prediction.end == date(2024, 12, 7)
        assert periods[0].prediction.end.weekday() == 5  # Saturday

    def test_single_epoch(self) -> None:
        """Should correctly generate a single epoch."""
        end_date = date(2024, 12, 14)  # A Saturday
        periods = self.runner._generate_epoch_periods(1, end_date)
        
        assert len(periods) == 1
        period = periods[0]
        
        # Prediction: Dec 8 (Sun) - Dec 14 (Sat)
        assert period.prediction.start == date(2024, 12, 8)
        assert period.prediction.end == date(2024, 12, 14)
        
        # Look-back: Nov 24 (Sun) - Dec 7 (Sat)
        assert period.look_back.start == date(2024, 11, 24)
        assert period.look_back.end == date(2024, 12, 7)

    def _ranges_overlap(self, range1: DateRange, range2: DateRange) -> bool:
        """Check if two date ranges overlap."""
        return range1.start <= range2.end and range2.start <= range1.end


class TestFindPreviousSaturday:
    """Tests for _find_previous_saturday helper method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = EvaluationRunner(
            epoch_runner=MagicMock(),
            metrics_calculator=MagicMock(),
            report_generator=MagicMock(),
        )

    def test_saturday_returns_same_date(self) -> None:
        """Saturday should return the same date."""
        saturday = date(2024, 12, 14)  # Saturday
        result = self.runner._find_previous_saturday(saturday)
        assert result == saturday

    def test_sunday_returns_previous_saturday(self) -> None:
        """Sunday should return the previous Saturday."""
        sunday = date(2024, 12, 15)  # Sunday
        result = self.runner._find_previous_saturday(sunday)
        assert result == date(2024, 12, 14)  # Previous Saturday

    def test_friday_returns_previous_saturday(self) -> None:
        """Friday should return the previous Saturday."""
        friday = date(2024, 12, 13)  # Friday
        result = self.runner._find_previous_saturday(friday)
        assert result == date(2024, 12, 7)  # Previous Saturday

    def test_monday_returns_previous_saturday(self) -> None:
        """Monday should return the previous Saturday."""
        monday = date(2024, 12, 9)  # Monday
        result = self.runner._find_previous_saturday(monday)
        assert result == date(2024, 12, 7)  # Previous Saturday


class TestEvaluationRunnerRun:
    """Tests for the run() method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_epoch_runner = MagicMock()
        self.mock_metrics_calculator = MagicMock()
        self.mock_report_generator = MagicMock()
        
        self.runner = EvaluationRunner(
            epoch_runner=self.mock_epoch_runner,
            metrics_calculator=self.mock_metrics_calculator,
            report_generator=self.mock_report_generator,
        )

    @pytest.mark.asyncio
    async def test_run_executes_all_epochs(self) -> None:
        """Should execute all epochs and return results."""
        config = EvaluationConfig(ticker="AAPL", num_epochs=3)
        
        # Mock epoch runner to return results
        mock_result = EpochResult(
            epoch_number=1,
            period=EpochPeriod(
                epoch_number=1,
                look_back=DateRange(date(2024, 11, 24), date(2024, 12, 7)),
                prediction=DateRange(date(2024, 12, 8), date(2024, 12, 14)),
            ),
            status=EpochStatus.COMPLETE,
            predicted_sentiment=Sentiment.BULLISH,
            predicted_confidence=ConfidenceLevel.HIGH,
            actual_outcome=ActualOutcome(
                direction=Sentiment.BULLISH,
                open_price=100.0,
                close_price=110.0,
                price_change_pct=10.0,
            ),
            is_correct=True,
            execution_duration_ms=100,
        )
        self.mock_epoch_runner.execute = AsyncMock(return_value=mock_result)
        
        # Mock metrics calculator
        mock_metrics = EvaluationMetrics(
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            accuracy=1.0,
            confusion_matrix=ConfusionMatrix(
                true_positive=3, false_positive=0, true_negative=0, false_negative=0
            ),
            total_epochs=3,
            completed_epochs=3,
        )
        self.mock_metrics_calculator.calculate.return_value = mock_metrics
        
        # Mock report generator
        self.mock_report_generator.generate.return_value = "<html>Report</html>"
        
        # Run evaluation
        report = await self.runner.run(config)
        
        # Verify epoch runner was called 3 times
        assert self.mock_epoch_runner.execute.call_count == 3
        
        # Verify metrics calculator was called with results
        self.mock_metrics_calculator.calculate.assert_called_once()
        
        # Verify report generator was called
        self.mock_report_generator.generate.assert_called_once()
        
        # Verify report structure
        assert report.ticker == "AAPL"
        assert report.config == config
        assert report.metrics == mock_metrics
        assert len(report.epoch_results) == 3
        assert report.html_content == "<html>Report</html>"

    @pytest.mark.asyncio
    async def test_run_passes_correct_ticker_to_epoch_runner(self) -> None:
        """Should pass the configured ticker to each epoch execution."""
        config = EvaluationConfig(ticker="MSFT", num_epochs=2)
        
        mock_result = EpochResult(
            epoch_number=1,
            period=EpochPeriod(
                epoch_number=1,
                look_back=DateRange(date(2024, 11, 24), date(2024, 12, 7)),
                prediction=DateRange(date(2024, 12, 8), date(2024, 12, 14)),
            ),
            status=EpochStatus.COMPLETE,
            predicted_sentiment=Sentiment.BULLISH,
            predicted_confidence=ConfidenceLevel.HIGH,
            actual_outcome=None,
            is_correct=None,
            execution_duration_ms=100,
        )
        self.mock_epoch_runner.execute = AsyncMock(return_value=mock_result)
        self.mock_metrics_calculator.calculate.return_value = EvaluationMetrics(
            precision=0.0, recall=0.0, f1_score=0.0, accuracy=0.0,
            confusion_matrix=ConfusionMatrix(0, 0, 0, 0),
            total_epochs=2, completed_epochs=0, warning="insufficient_data"
        )
        self.mock_report_generator.generate.return_value = ""
        
        await self.runner.run(config)
        
        # Verify ticker was passed correctly
        for call in self.mock_epoch_runner.execute.call_args_list:
            _, kwargs = call
            assert kwargs.get("ticker") == "MSFT" or call[0][1] == "MSFT"


class TestParallelEpochExecution:
    """Tests for parallel epoch execution functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_epoch_runner = MagicMock()
        self.mock_metrics_calculator = MagicMock()
        self.mock_report_generator = MagicMock()

    def _create_mock_result(self, epoch_number: int) -> EpochResult:
        """Create a mock epoch result."""
        return EpochResult(
            epoch_number=epoch_number,
            period=EpochPeriod(
                epoch_number=epoch_number,
                look_back=DateRange(date(2024, 11, 24), date(2024, 12, 7)),
                prediction=DateRange(date(2024, 12, 8), date(2024, 12, 14)),
            ),
            status=EpochStatus.COMPLETE,
            predicted_sentiment=Sentiment.BULLISH,
            predicted_confidence=ConfidenceLevel.HIGH,
            actual_outcome=ActualOutcome(
                direction=Sentiment.BULLISH,
                open_price=100.0,
                close_price=110.0,
                price_change_pct=10.0,
            ),
            is_correct=True,
            execution_duration_ms=100,
        )

    @pytest.mark.asyncio
    async def test_parallel_execution_respects_max_parallelism(self) -> None:
        """Should limit concurrent executions to max_parallelism."""
        import asyncio
        
        max_parallelism = 2
        num_epochs = 5
        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()
        
        async def mock_execute(period: EpochPeriod, ticker: str) -> EpochResult:
            nonlocal concurrent_count, max_concurrent
            async with lock:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
            
            # Simulate some work
            await asyncio.sleep(0.05)
            
            async with lock:
                concurrent_count -= 1
            
            return self._create_mock_result(period.epoch_number)
        
        self.mock_epoch_runner.execute = mock_execute
        self.mock_metrics_calculator.calculate.return_value = EvaluationMetrics(
            precision=1.0, recall=1.0, f1_score=1.0, accuracy=1.0,
            confusion_matrix=ConfusionMatrix(5, 0, 0, 0),
            total_epochs=5, completed_epochs=5,
        )
        self.mock_report_generator.generate.return_value = ""
        
        runner = EvaluationRunner(
            epoch_runner=self.mock_epoch_runner,
            metrics_calculator=self.mock_metrics_calculator,
            report_generator=self.mock_report_generator,
            max_parallelism=max_parallelism,
        )
        
        config = EvaluationConfig(ticker="AAPL", num_epochs=num_epochs)
        await runner.run(config)
        
        # Verify max concurrent executions didn't exceed max_parallelism
        assert max_concurrent <= max_parallelism, (
            f"Max concurrent executions ({max_concurrent}) exceeded "
            f"max_parallelism ({max_parallelism})"
        )

    @pytest.mark.asyncio
    async def test_continues_processing_when_epoch_fails(self) -> None:
        """Should continue processing remaining epochs if individual epoch fails."""
        call_count = 0
        
        async def mock_execute(period: EpochPeriod, ticker: str) -> EpochResult:
            nonlocal call_count
            call_count += 1
            
            # Make the second epoch fail
            if period.epoch_number == 2:
                raise RuntimeError("Simulated epoch failure")
            
            return self._create_mock_result(period.epoch_number)
        
        self.mock_epoch_runner.execute = mock_execute
        self.mock_metrics_calculator.calculate.return_value = EvaluationMetrics(
            precision=1.0, recall=1.0, f1_score=1.0, accuracy=1.0,
            confusion_matrix=ConfusionMatrix(2, 0, 0, 0),
            total_epochs=3, completed_epochs=2,
        )
        self.mock_report_generator.generate.return_value = ""
        
        runner = EvaluationRunner(
            epoch_runner=self.mock_epoch_runner,
            metrics_calculator=self.mock_metrics_calculator,
            report_generator=self.mock_report_generator,
        )
        
        config = EvaluationConfig(ticker="AAPL", num_epochs=3)
        report = await runner.run(config)
        
        # All epochs should have been attempted
        assert call_count == 3
        
        # Should have 3 results (including the failed one)
        assert len(report.epoch_results) == 3
        
        # The failed epoch should have FAILED status
        failed_result = next(r for r in report.epoch_results if r.epoch_number == 2)
        assert failed_result.status == EpochStatus.FAILED
        assert failed_result.error_message == "Simulated epoch failure"

    @pytest.mark.asyncio
    async def test_aggregates_results_from_all_epochs(self) -> None:
        """Should aggregate results from all epochs regardless of success/failure."""
        async def mock_execute(period: EpochPeriod, ticker: str) -> EpochResult:
            # Alternate between success and failure
            if period.epoch_number % 2 == 0:
                raise RuntimeError(f"Epoch {period.epoch_number} failed")
            return self._create_mock_result(period.epoch_number)
        
        self.mock_epoch_runner.execute = mock_execute
        self.mock_metrics_calculator.calculate.return_value = EvaluationMetrics(
            precision=1.0, recall=1.0, f1_score=1.0, accuracy=1.0,
            confusion_matrix=ConfusionMatrix(3, 0, 0, 0),
            total_epochs=5, completed_epochs=3,
        )
        self.mock_report_generator.generate.return_value = ""
        
        runner = EvaluationRunner(
            epoch_runner=self.mock_epoch_runner,
            metrics_calculator=self.mock_metrics_calculator,
            report_generator=self.mock_report_generator,
        )
        
        config = EvaluationConfig(ticker="AAPL", num_epochs=5)
        report = await runner.run(config)
        
        # Should have exactly 5 results
        assert len(report.epoch_results) == 5
        
        # Verify correct status for each epoch
        for result in report.epoch_results:
            if result.epoch_number % 2 == 0:
                assert result.status == EpochStatus.FAILED
            else:
                assert result.status == EpochStatus.COMPLETE

    @pytest.mark.asyncio
    async def test_preserves_result_order(self) -> None:
        """Results should be in the same order as input periods."""
        import asyncio
        import random
        
        async def mock_execute(period: EpochPeriod, ticker: str) -> EpochResult:
            # Add random delay to simulate varying execution times
            await asyncio.sleep(random.uniform(0.01, 0.05))
            return self._create_mock_result(period.epoch_number)
        
        self.mock_epoch_runner.execute = mock_execute
        self.mock_metrics_calculator.calculate.return_value = EvaluationMetrics(
            precision=1.0, recall=1.0, f1_score=1.0, accuracy=1.0,
            confusion_matrix=ConfusionMatrix(5, 0, 0, 0),
            total_epochs=5, completed_epochs=5,
        )
        self.mock_report_generator.generate.return_value = ""
        
        runner = EvaluationRunner(
            epoch_runner=self.mock_epoch_runner,
            metrics_calculator=self.mock_metrics_calculator,
            report_generator=self.mock_report_generator,
            max_parallelism=5,  # Allow all to run concurrently
        )
        
        config = EvaluationConfig(ticker="AAPL", num_epochs=5)
        report = await runner.run(config)
        
        # Results should be in order 1, 2, 3, 4, 5
        for i, result in enumerate(report.epoch_results, start=1):
            assert result.epoch_number == i

    @pytest.mark.asyncio
    async def test_all_epochs_fail_still_returns_report(self) -> None:
        """Should return a report even if all epochs fail."""
        async def mock_execute(period: EpochPeriod, ticker: str) -> EpochResult:
            raise RuntimeError(f"Epoch {period.epoch_number} failed")
        
        self.mock_epoch_runner.execute = mock_execute
        self.mock_metrics_calculator.calculate.return_value = EvaluationMetrics(
            precision=0.0, recall=0.0, f1_score=0.0, accuracy=0.0,
            confusion_matrix=ConfusionMatrix(0, 0, 0, 0),
            total_epochs=3, completed_epochs=0,
            warning="insufficient_data",
        )
        self.mock_report_generator.generate.return_value = "<html>Error Report</html>"
        
        runner = EvaluationRunner(
            epoch_runner=self.mock_epoch_runner,
            metrics_calculator=self.mock_metrics_calculator,
            report_generator=self.mock_report_generator,
        )
        
        config = EvaluationConfig(ticker="AAPL", num_epochs=3)
        report = await runner.run(config)
        
        # Should have 3 failed results
        assert len(report.epoch_results) == 3
        assert all(r.status == EpochStatus.FAILED for r in report.epoch_results)
        
        # Report should still be generated
        assert report.html_content == "<html>Error Report</html>"
