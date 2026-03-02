"""Statistical aggregation for multi-run evaluation results."""

import statistics
from collections import Counter
from typing import Optional

from trading_copilot.evaluation.models import EpochResult, EvaluationMetrics
from trading_copilot.evaluation.statistical_models import (
    AggregatedEvaluationReport,
    EpochStatistics,
    RunStatistics,
    TickerStatistics,
)


class StatisticalAggregator:
    """Aggregates multiple evaluation runs into statistical summaries."""
    
    def __init__(self, runs_per_epoch: int) -> None:
        """Initialize aggregator.
        
        Args:
            runs_per_epoch: Expected number of runs per (ticker, epoch) combination
        """
        self._runs_per_epoch = runs_per_epoch
    
    def aggregate_epoch_runs(
        self,
        epoch_runs: list[EpochResult],
    ) -> EpochStatistics:
        """Aggregate multiple runs of the same epoch.
        
        Args:
            epoch_runs: List of EpochResult from multiple runs of same epoch
            
        Returns:
            EpochStatistics with aggregated metrics
        """
        if not epoch_runs:
            raise ValueError("Cannot aggregate empty list of epoch runs")
        
        # All runs should be for the same epoch and ticker
        epoch_number = epoch_runs[0].epoch_number
        ticker = epoch_runs[0].period.look_back.start.strftime("%Y-%m-%d")  # Placeholder
        
        # Calculate correctness across runs
        correctness_values = []
        for run in epoch_runs:
            if run.is_correct is not None:
                correctness_values.append(1.0 if run.is_correct else 0.0)
        
        if correctness_values:
            accuracy_stats = self._compute_statistics(correctness_values)
            num_correct = sum(int(v) for v in correctness_values)
            num_total = len(correctness_values)
        else:
            accuracy_stats = RunStatistics(0.0, 0.0, 0.0, 0.0, 0)
            num_correct = 0
            num_total = 0
        
        # Find consensus prediction (most common)
        predictions = [r.predicted_sentiment for r in epoch_runs if r.predicted_sentiment]
        consensus_prediction = Counter(predictions).most_common(1)[0][0] if predictions else None
        
        # Find consensus confidence (most common)
        confidences = [r.predicted_confidence for r in epoch_runs if r.predicted_confidence]
        consensus_confidence = Counter(confidences).most_common(1)[0][0] if confidences else None
        
        # Actual outcome (same across all runs)
        actual_outcome = None
        actual_price_change = None
        if epoch_runs[0].actual_outcome:
            actual_outcome = epoch_runs[0].actual_outcome.direction
            actual_price_change = epoch_runs[0].actual_outcome.price_change_pct
        
        return EpochStatistics(
            epoch_number=epoch_number,
            ticker=ticker,
            accuracy=accuracy_stats,
            num_correct=num_correct,
            num_total=num_total,
            individual_runs=epoch_runs,
            consensus_prediction=consensus_prediction,
            consensus_confidence=consensus_confidence,
            actual_outcome=actual_outcome,
            actual_price_change=actual_price_change,
        )
    
    def aggregate_ticker_runs(
        self,
        ticker: str,
        all_epoch_runs: dict[int, list[EpochResult]],
    ) -> TickerStatistics:
        """Aggregate all runs for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            all_epoch_runs: Dict mapping epoch_number -> list of EpochResult runs
            
        Returns:
            TickerStatistics with aggregated metrics
        """
        # Aggregate each epoch's runs
        epoch_statistics = []
        for epoch_num in sorted(all_epoch_runs.keys()):
            epoch_runs = all_epoch_runs[epoch_num]
            if epoch_runs:
                epoch_stats = self.aggregate_epoch_runs(epoch_runs)
                epoch_statistics.append(epoch_stats)
        
        # Collect metrics for overall statistics
        all_metrics: list[EvaluationMetrics] = []
        for epoch_runs in all_epoch_runs.values():
            for run in epoch_runs:
                # Calculate metrics for this run (if complete)
                if run.is_correct is not None:
                    metrics = self._calculate_run_metrics([run])
                    all_metrics.append(metrics)
        
        # Compute overall statistics from EPOCH-level accuracies
        if epoch_statistics:
            # Use epoch-level accuracy means for ticker-level statistics
            epoch_accuracy_means = [epoch.accuracy.mean for epoch in epoch_statistics]
            
            accuracy_stats = self._compute_statistics(epoch_accuracy_means)
            mean_accuracy = statistics.mean(epoch_accuracy_means)
            std_accuracy = statistics.stdev(epoch_accuracy_means) if len(epoch_accuracy_means) > 1 else 0.0
            
            # For precision, recall, F1 - calculate from all individual runs
            if all_metrics:
                precision_values = [m.precision for m in all_metrics]
                recall_values = [m.recall for m in all_metrics]
                f1_values = [m.f1_score for m in all_metrics]
                
                precision_stats = self._compute_statistics(precision_values)
                recall_stats = self._compute_statistics(recall_values)
                f1_stats = self._compute_statistics(f1_values)
                
                # Sum confusion matrix across all runs
                total_tp = sum(m.confusion_matrix.true_positive for m in all_metrics)
                total_fp = sum(m.confusion_matrix.false_positive for m in all_metrics)
                total_tn = sum(m.confusion_matrix.true_negative for m in all_metrics)
                total_fn = sum(m.confusion_matrix.false_negative for m in all_metrics)
            else:
                zero_stats = RunStatistics(0.0, 0.0, 0.0, 0.0, 0)
                precision_stats = recall_stats = f1_stats = zero_stats
                total_tp = total_fp = total_tn = total_fn = 0
        else:
            zero_stats = RunStatistics(0.0, 0.0, 0.0, 0.0, 0)
            accuracy_stats = precision_stats = recall_stats = f1_stats = zero_stats
            mean_accuracy = 0.0
            std_accuracy = 0.0
            total_tp = total_fp = total_tn = total_fn = 0
        
        # Count metadata
        total_epochs = len(all_epoch_runs)
        total_runs = sum(len(runs) for runs in all_epoch_runs.values())
        completed_runs = sum(
            1 for runs in all_epoch_runs.values()
            for run in runs if run.is_correct is not None
        )
        
        return TickerStatistics(
            ticker=ticker,
            mean_accuracy=mean_accuracy,
            std_accuracy=std_accuracy,
            accuracy_stats=accuracy_stats,
            precision_stats=precision_stats,
            recall_stats=recall_stats,
            f1_stats=f1_stats,
            total_true_positives=total_tp,
            total_false_positives=total_fp,
            total_true_negatives=total_tn,
            total_false_negatives=total_fn,
            epoch_statistics=epoch_statistics,
            total_epochs=total_epochs,
            total_runs=total_runs,
            completed_runs=completed_runs,
        )
    
    def create_aggregated_report(
        self,
        ticker_runs: dict[str, dict[int, list[EpochResult]]],
        num_epochs: int,
        config_summary: dict,
    ) -> AggregatedEvaluationReport:
        """Create complete aggregated evaluation report.
        
        Args:
            ticker_runs: Dict mapping ticker -> epoch_num -> list of EpochResult
            num_epochs: Total number of epochs per ticker
            config_summary: Configuration metadata
            
        Returns:
            AggregatedEvaluationReport with full statistics
        """
        ticker_statistics = {}
        for ticker, epoch_runs in ticker_runs.items():
            ticker_stats = self.aggregate_ticker_runs(ticker, epoch_runs)
            ticker_statistics[ticker] = ticker_stats
        
        return AggregatedEvaluationReport(
            ticker_statistics=ticker_statistics,
            total_tickers=len(ticker_runs),
            total_epochs_per_ticker=num_epochs,
            runs_per_epoch=self._runs_per_epoch,
            config_summary=config_summary,
        )
    
    def _compute_statistics(self, values: list[float]) -> RunStatistics:
        """Compute statistics for a list of numeric values.
        
        Args:
            values: List of numeric values
            
        Returns:
            RunStatistics with mean, std dev, min, max
        """
        if not values:
            return RunStatistics(0.0, 0.0, 0.0, 0.0, 0)
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        min_val = min(values)
        max_val = max(values)
        
        return RunStatistics(
            mean=mean,
            std_dev=std_dev,
            min_value=min_val,
            max_value=max_val,
            sample_size=len(values),
        )
    
    def _calculate_run_metrics(self, epoch_results: list[EpochResult]) -> EvaluationMetrics:
        """Calculate metrics for a single run (helper method).
        
        Args:
            epoch_results: List containing single EpochResult
            
        Returns:
            EvaluationMetrics for the run
        """
        from trading_copilot.evaluation.models import ConfusionMatrix
        
        tp = fp = tn = fn = 0
        
        for result in epoch_results:
            if result.is_correct is None:
                continue
            
            predicted = result.predicted_sentiment
            actual = result.actual_outcome.direction if result.actual_outcome else None
            
            if predicted == "bullish" and actual == "bullish":
                tp += 1
            elif predicted == "bullish" and actual == "bearish":
                fp += 1
            elif predicted == "bearish" and actual == "bearish":
                tn += 1
            elif predicted == "bearish" and actual == "bullish":
                fn += 1
        
        # Calculate metrics
        total = tp + fp + tn + fn
        accuracy = (tp + tn) / total if total > 0 else 0.0
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Create confusion matrix
        confusion_matrix = ConfusionMatrix(
            true_positive=tp,
            false_positive=fp,
            true_negative=tn,
            false_negative=fn,
        )
        
        return EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            confusion_matrix=confusion_matrix,
            total_epochs=len(epoch_results),
            completed_epochs=len([r for r in epoch_results if r.is_correct is not None]),
        )
