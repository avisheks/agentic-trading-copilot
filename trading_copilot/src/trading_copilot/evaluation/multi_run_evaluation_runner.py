"""Multi-run evaluation runner for statistical analysis."""

import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Dict, List

from trading_copilot.evaluation.config_models import EvaluationConfig
from trading_copilot.evaluation.epoch_runner import EpochRunner
from trading_copilot.evaluation.evaluation_runner import EvaluationRunner
from trading_copilot.evaluation.metrics_calculator import MetricsCalculator
from trading_copilot.evaluation.models import EpochPeriod, EpochResult, EvaluationConfig as SingleEvalConfig
from trading_copilot.evaluation.report_generator import EvaluationReportGenerator
from trading_copilot.evaluation.statistical_aggregator import StatisticalAggregator
from trading_copilot.evaluation.statistical_models import AggregatedEvaluationReport

logger = logging.getLogger(__name__)


class MultiRunEvaluationRunner:
    """Orchestrates multiple evaluation runs for statistical analysis.
    
    This component executes the same (ticker, epoch) combination multiple times
    to collect statistical data on prediction variance and reliability.
    
    Workflow:
    1. For each ticker:
       2. For each epoch:
          3. Run N evaluations (runs_per_epoch)
          4. Aggregate results (mean, std-dev)
    5. Generate consolidated statistical report
    """
    
    def __init__(
        self,
        epoch_runner: EpochRunner,
        metrics_calculator: MetricsCalculator,
        report_generator: EvaluationReportGenerator,
        config: EvaluationConfig,
    ) -> None:
        """Initialize multi-run evaluation runner.
        
        Args:
            epoch_runner: Runner for executing individual epochs
            metrics_calculator: Calculator for computing evaluation metrics
            report_generator: Generator for HTML reports
            config: Complete evaluation configuration
        """
        self._epoch_runner = epoch_runner
        self._metrics_calculator = metrics_calculator
        self._report_generator = report_generator
        self._config = config
        
        # Create single-run evaluation runner
        self._single_eval_runner = EvaluationRunner(
            epoch_runner=epoch_runner,
            metrics_calculator=metrics_calculator,
            report_generator=report_generator,
            max_parallelism=config.evaluation.max_parallelism,
        )
        
        # Create statistical aggregator
        self._aggregator = StatisticalAggregator(
            runs_per_epoch=config.evaluation.runs_per_epoch,
        )
    
    async def run_multi_ticker_evaluation(
        self,
        tickers: List[str],
    ) -> AggregatedEvaluationReport:
        """Run evaluation for multiple tickers with multiple runs per epoch.
        
        Args:
            tickers: List of stock ticker symbols to evaluate
            
        Returns:
            AggregatedEvaluationReport with statistical summaries
        """
        logger.info(f"Starting multi-run evaluation for {len(tickers)} tickers")
        logger.info(f"Configuration: {self._config.evaluation.num_epochs} epochs, "
                   f"{self._config.evaluation.runs_per_epoch} runs per epoch")
        
        # Store all runs: ticker -> epoch_num -> list of EpochResult
        all_ticker_runs: Dict[str, Dict[int, List[EpochResult]]] = {}
        
        for ticker in tickers:
            logger.info(f"\n{'='*60}")
            logger.info(f"Evaluating {ticker}...")
            logger.info(f"{'='*60}")
            
            ticker_runs = await self._run_ticker_evaluation(ticker)
            all_ticker_runs[ticker] = ticker_runs
            
            # Log progress
            total_runs = sum(len(runs) for runs in ticker_runs.values())
            completed_runs = sum(
                1 for runs in ticker_runs.values()
                for run in runs if run.is_correct is not None
            )
            logger.info(f"\n{ticker}: Completed {completed_runs}/{total_runs} runs")
        
        # Create aggregated report
        config_summary = {
            "num_epochs": self._config.evaluation.num_epochs,
            "runs_per_epoch": self._config.evaluation.runs_per_epoch,
            "max_parallelism": self._config.evaluation.max_parallelism,
            "lookback_days": self._config.evaluation.lookback_days,
            "prediction_days": self._config.evaluation.prediction_days,
        }
        
        report = self._aggregator.create_aggregated_report(
            ticker_runs=all_ticker_runs,
            num_epochs=self._config.evaluation.num_epochs,
            config_summary=config_summary,
        )
        
        logger.info(f"\n{'='*60}")
        logger.info("EVALUATION COMPLETE")
        logger.info(f"{'='*60}")
        
        return report
    
    async def _run_ticker_evaluation(
        self,
        ticker: str,
    ) -> Dict[int, List[EpochResult]]:
        """Run all evaluations for a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict mapping epoch_number -> list of EpochResult runs
        """
        # Generate epoch periods
        end_date = date.today()
        periods = self._single_eval_runner._generate_epoch_periods(
            self._config.evaluation.num_epochs,
            end_date,
        )
        
        # Collect results: epoch_num -> list of runs
        epoch_runs: Dict[int, List[EpochResult]] = {
            period.epoch_number: [] for period in periods
        }
        
        # Run each epoch multiple times
        for run_num in range(1, self._config.evaluation.runs_per_epoch + 1):
            if self._config.logging.log_individual_runs:
                logger.info(f"  Run {run_num}/{self._config.evaluation.runs_per_epoch}")
            
            # Execute all epochs for this run
            results = await self._single_eval_runner._execute_epochs_parallel(
                periods, ticker
            )
            
            # Store results by epoch number
            for result in results:
                epoch_runs[result.epoch_number].append(result)
        
        return epoch_runs