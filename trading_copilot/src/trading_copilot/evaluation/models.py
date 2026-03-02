"""Data models for the Evaluation Module."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from trading_copilot.evaluation.errors import ConfigurationError
from trading_copilot.models import ConfidenceLevel, Sentiment

# Re-export ConfigurationError for backward compatibility
__all__ = ["ConfigurationError"]


@dataclass
class DateRange:
    """A date range with start and end dates."""

    start: date  # Inclusive
    end: date  # Inclusive

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("start must be <= end")


@dataclass
class EpochPeriod:
    """Defines the time periods for a single evaluation epoch."""

    epoch_number: int
    look_back: DateRange  # 2-week period for gathering sentiment data
    prediction: DateRange  # 1-week period for prediction validation


class EpochStatus(Enum):
    """Status of an epoch evaluation."""

    COMPLETE = "complete"
    NO_DATA = "no_data"  # No historical data available
    INCOMPLETE = "incomplete"  # Missing price data for outcome
    FAILED = "failed"  # Execution error


@dataclass
class ActualOutcome:
    """Actual stock price movement during prediction period."""

    direction: Sentiment  # BULLISH or BEARISH
    open_price: float  # Opening price on first day
    close_price: float  # Closing price on last day
    price_change_pct: float  # Percentage change


@dataclass
class EpochResult:
    """Result of a single epoch evaluation."""

    epoch_number: int
    period: EpochPeriod
    status: EpochStatus
    predicted_sentiment: Sentiment | None
    predicted_confidence: ConfidenceLevel | None
    actual_outcome: ActualOutcome | None
    is_correct: bool | None  # True if prediction matches actual
    execution_duration_ms: int
    error_message: str | None = None


@dataclass
class ConfusionMatrix:
    """2x2 confusion matrix for binary classification."""

    true_positive: int  # Predicted bullish, actual bullish
    false_positive: int  # Predicted bullish, actual bearish
    true_negative: int  # Predicted bearish, actual bearish
    false_negative: int  # Predicted bearish, actual bullish


@dataclass
class EvaluationMetrics:
    """Computed metrics from evaluation results."""

    precision: float  # TP / (TP + FP)
    recall: float  # TP / (TP + FN)
    f1_score: float  # 2 * (precision * recall) / (precision + recall)
    accuracy: float  # (TP + TN) / total
    confusion_matrix: ConfusionMatrix
    total_epochs: int
    completed_epochs: int
    warning: str | None = None  # e.g., "insufficient_data"


@dataclass
class EvaluationConfig:
    """Configuration for running an evaluation."""

    ticker: str  # Stock ticker to evaluate
    num_epochs: int = 10  # Number of epochs (1-52)
    max_parallelism: int = 4  # Max concurrent epoch executions

    def __post_init__(self) -> None:
        if not 1 <= self.num_epochs <= 52:
            raise ConfigurationError("num_epochs must be between 1 and 52")
        if self.max_parallelism < 1:
            raise ConfigurationError("max_parallelism must be at least 1")


@dataclass
class EvaluationReport:
    """Complete evaluation report."""

    ticker: str
    config: EvaluationConfig
    metrics: EvaluationMetrics
    epoch_results: list[EpochResult]
    generated_at: datetime
    html_content: str
