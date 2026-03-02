"""Evaluation module for backtesting Trading Copilot sentiment predictions."""

from trading_copilot.evaluation.errors import (
    ConfigurationError,
    EvaluationError,
    HistoricalDataError,
    InsufficientDataError,
    OutcomeFetchError,
)
from trading_copilot.evaluation.historical_data_fetcher import HistoricalDataFetcher
from trading_copilot.evaluation.models import (
    ActualOutcome,
    ConfusionMatrix,
    DateRange,
    EpochPeriod,
    EpochResult,
    EpochStatus,
    EvaluationConfig,
    EvaluationMetrics,
    EvaluationReport,
)
from trading_copilot.evaluation.outcome_fetcher import OutcomeFetcher
from trading_copilot.evaluation.report_generator import EvaluationReportGenerator

__all__ = [
    # Errors
    "ConfigurationError",
    "EvaluationError",
    "HistoricalDataError",
    "InsufficientDataError",
    "OutcomeFetchError",
    # Components
    "EvaluationReportGenerator",
    "HistoricalDataFetcher",
    "OutcomeFetcher",
    # Models
    "ActualOutcome",
    "ConfusionMatrix",
    "DateRange",
    "EpochPeriod",
    "EpochResult",
    "EpochStatus",
    "EvaluationConfig",
    "EvaluationMetrics",
    "EvaluationReport",
]
