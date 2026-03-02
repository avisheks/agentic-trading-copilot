"""Evaluation runner for orchestrating multi-epoch evaluations."""

import asyncio
from datetime import date, datetime, timedelta, timezone

from trading_copilot.evaluation.epoch_runner import EpochRunner
from trading_copilot.evaluation.metrics_calculator import MetricsCalculator
from trading_copilot.evaluation.models import (
    DateRange,
    EpochPeriod,
    EpochResult,
    EpochStatus,
    EvaluationConfig,
    EvaluationMetrics,
    EvaluationReport,
)
from trading_copilot.evaluation.report_generator import EvaluationReportGenerator


class EvaluationRunner:
    """Orchestrates multi-epoch evaluation of sentiment predictions.
    
    This component is the main entry point for running evaluations. It:
    1. Generates N non-overlapping epoch periods working backwards from end_date
    2. Executes epochs in parallel (up to max_parallelism concurrent executions)
    3. Aggregates results and calculates metrics
    4. Generates an HTML report
    
    Fault tolerance: If individual epochs fail, processing continues for remaining
    epochs and partial results are reported.
    """

    def __init__(
        self,
        epoch_runner: EpochRunner,
        metrics_calculator: MetricsCalculator,
        report_generator: EvaluationReportGenerator,
        max_parallelism: int = 4,
    ) -> None:
        """Initialize with dependencies.
        
        Args:
            epoch_runner: Runner for executing individual epochs
            metrics_calculator: Calculator for computing evaluation metrics
            report_generator: Generator for HTML reports
            max_parallelism: Maximum concurrent epoch executions (used in Task 8.2)
        """
        self._epoch_runner = epoch_runner
        self._metrics_calculator = metrics_calculator
        self._report_generator = report_generator
        self._max_parallelism = max_parallelism

    async def run(self, config: EvaluationConfig) -> EvaluationReport:
        """Execute evaluation across N epochs.
        
        Args:
            config: Evaluation configuration with ticker, epoch count, etc.
            
        Returns:
            EvaluationReport with metrics and per-epoch results
        """
        # Generate epoch periods working backwards from today
        end_date = date.today()
        periods = self._generate_epoch_periods(config.num_epochs, end_date)
        
        # Execute epochs in parallel with limited concurrency
        results = await self._execute_epochs_parallel(periods, config.ticker)
        
        # Calculate metrics from results
        metrics = self._metrics_calculator.calculate(results)
        
        # Generate HTML report
        html_content = self._report_generator.generate(metrics, results, config)
        
        return EvaluationReport(
            ticker=config.ticker,
            config=config,
            metrics=metrics,
            epoch_results=results,
            generated_at=datetime.now(timezone.utc),
            html_content=html_content,
        )

    async def _execute_epochs_parallel(
        self,
        periods: list[EpochPeriod],
        ticker: str,
    ) -> list[EpochResult]:
        """Execute epochs in parallel with limited concurrency.
        
        Uses asyncio.Semaphore to limit concurrent executions to max_parallelism.
        Continues processing remaining epochs if individual epochs fail.
        
        Args:
            periods: List of epoch periods to execute
            ticker: Stock ticker symbol
            
        Returns:
            List of EpochResult objects, one for each period (in same order as input)
        """
        semaphore = asyncio.Semaphore(self._max_parallelism)
        
        async def execute_with_semaphore(period: EpochPeriod) -> EpochResult:
            """Execute a single epoch with semaphore-limited concurrency."""
            async with semaphore:
                try:
                    return await self._epoch_runner.execute(period, ticker)
                except Exception as e:
                    # If epoch fails, return a failed result instead of propagating
                    return EpochResult(
                        epoch_number=period.epoch_number,
                        period=period,
                        status=EpochStatus.FAILED,
                        predicted_sentiment=None,
                        predicted_confidence=None,
                        actual_outcome=None,
                        is_correct=None,
                        execution_duration_ms=0,
                        error_message=str(e),
                    )
        
        # Create tasks for all epochs
        tasks = [execute_with_semaphore(period) for period in periods]
        
        # Execute all tasks concurrently and gather results
        # return_exceptions=False since we handle exceptions in execute_with_semaphore
        results = await asyncio.gather(*tasks)
        
        return list(results)

    def _generate_epoch_periods(
        self,
        n: int,
        end_date: date,
    ) -> list[EpochPeriod]:
        """Generate N non-overlapping epoch periods working backwards from end_date.
        
        Each epoch consists of:
        - 2-week look-back period (Sunday to Saturday) - 14 days
        - 1-week prediction period (Sunday to Saturday) - 7 days
        
        Epochs are arranged so:
        1. No two look-back periods overlap
        2. No prediction period overlaps with any look-back period
        
        The layout for each epoch (working backwards):
        - Prediction period: 7 days (Sun-Sat)
        - Look-back period: 14 days (Sun-Sat, two weeks)
        
        Total span per epoch: 21 days (3 weeks)
        
        Args:
            n: Number of epochs to generate (1-52)
            end_date: The date to work backwards from
            
        Returns:
            List of EpochPeriod objects, ordered from most recent to oldest
        """
        periods: list[EpochPeriod] = []
        
        # Find the most recent Saturday on or before end_date
        # This will be the end of the first prediction period
        current_end = self._find_previous_saturday(end_date)
        
        for epoch_num in range(1, n + 1):
            # Prediction period: 1 week (Sunday to Saturday)
            # The prediction period ends on current_end (Saturday)
            prediction_end = current_end
            prediction_start = prediction_end - timedelta(days=6)  # Sunday
            
            # Look-back period: 2 weeks (Sunday to Saturday)
            # Ends the day before prediction starts (Saturday)
            look_back_end = prediction_start - timedelta(days=1)  # Saturday
            look_back_start = look_back_end - timedelta(days=13)  # Sunday (14 days total)
            
            period = EpochPeriod(
                epoch_number=epoch_num,
                look_back=DateRange(start=look_back_start, end=look_back_end),
                prediction=DateRange(start=prediction_start, end=prediction_end),
            )
            periods.append(period)
            
            # Move to the next epoch (3 weeks back = 21 days)
            # The next epoch's prediction period ends the day before this epoch's look-back starts
            current_end = look_back_start - timedelta(days=1)  # Saturday before look_back_start
        
        return periods

    def _find_previous_saturday(self, d: date) -> date:
        """Find the most recent Saturday on or before the given date.
        
        Args:
            d: The reference date
            
        Returns:
            The most recent Saturday on or before d
        """
        # weekday(): Monday=0, Tuesday=1, ..., Saturday=5, Sunday=6
        days_since_saturday = (d.weekday() + 2) % 7  # Saturday=0, Sunday=1, Monday=2, etc.
        return d - timedelta(days=days_since_saturday)
