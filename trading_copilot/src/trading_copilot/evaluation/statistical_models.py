"""Statistical models for multi-run evaluation results."""

from dataclasses import dataclass, field
from typing import Optional

from trading_copilot.evaluation.models import EpochResult


@dataclass
class RunStatistics:
    """Statistics for multiple runs of the same epoch.
    
    Aggregates results from multiple runs of the same (ticker, epoch)
    combination to provide mean, standard deviation, min, and max.
    """
    
    mean: float
    std_dev: float
    min_value: float
    max_value: float
    sample_size: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "mean": self.mean,
            "std_dev": self.std_dev,
            "min": self.min_value,
            "max": self.max_value,
            "n": self.sample_size,
        }


@dataclass
class EpochStatistics:
    """Aggregated statistics for a single epoch across multiple runs."""
    
    epoch_number: int
    ticker: str
    
    # Correctness statistics (across all runs)
    accuracy: RunStatistics
    num_correct: int
    num_total: int
    
    # Individual run results (optional, for detailed analysis)
    individual_runs: list[EpochResult] = field(default_factory=list)
    
    # Most common prediction across runs
    consensus_prediction: Optional[str] = None
    consensus_confidence: Optional[str] = None
    
    # Actual outcome (same across all runs)
    actual_outcome: Optional[str] = None
    actual_price_change: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "epoch_number": self.epoch_number,
            "ticker": self.ticker,
            "accuracy": self.accuracy.to_dict(),
            "num_correct": self.num_correct,
            "num_total": self.num_total,
            "consensus_prediction": self.consensus_prediction,
            "consensus_confidence": self.consensus_confidence,
            "actual_outcome": self.actual_outcome,
            "actual_price_change": self.actual_price_change,
        }


@dataclass
class TickerStatistics:
    """Aggregated statistics for a ticker across all epochs and runs."""
    
    ticker: str
    
    # Overall metrics (mean across all epochs)
    mean_accuracy: float
    std_accuracy: float
    
    # Detailed statistics
    accuracy_stats: RunStatistics
    precision_stats: RunStatistics
    recall_stats: RunStatistics
    f1_stats: RunStatistics
    
    # Confusion matrix totals (summed across all runs)
    total_true_positives: int
    total_false_positives: int
    total_true_negatives: int
    total_false_negatives: int
    
    # Epoch-level statistics
    epoch_statistics: list[EpochStatistics] = field(default_factory=list)
    
    # Metadata
    total_epochs: int = 0
    total_runs: int = 0
    completed_runs: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "ticker": self.ticker,
            "mean_accuracy": self.mean_accuracy,
            "std_accuracy": self.std_accuracy,
            "accuracy_stats": self.accuracy_stats.to_dict(),
            "precision_stats": self.precision_stats.to_dict(),
            "recall_stats": self.recall_stats.to_dict(),
            "f1_stats": self.f1_stats.to_dict(),
            "confusion_matrix": {
                "tp": self.total_true_positives,
                "fp": self.total_false_positives,
                "tn": self.total_true_negatives,
                "fn": self.total_false_negatives,
            },
            "metadata": {
                "total_epochs": self.total_epochs,
                "total_runs": self.total_runs,
                "completed_runs": self.completed_runs,
            },
        }


@dataclass
class AggregatedEvaluationReport:
    """Complete evaluation report with multi-run statistics."""
    
    ticker_statistics: dict[str, TickerStatistics]
    
    # Overall summary
    total_tickers: int
    total_epochs_per_ticker: int
    runs_per_epoch: int
    
    # Configuration metadata
    config_summary: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "ticker_statistics": {
                ticker: stats.to_dict()
                for ticker, stats in self.ticker_statistics.items()
            },
            "summary": {
                "total_tickers": self.total_tickers,
                "total_epochs_per_ticker": self.total_epochs_per_ticker,
                "runs_per_epoch": self.runs_per_epoch,
            },
            "config": self.config_summary,
        }