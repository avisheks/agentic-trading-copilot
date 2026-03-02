"""Error types for the Evaluation Module."""


class EvaluationError(Exception):
    """Base exception for evaluation module errors."""

    pass


class ConfigurationError(EvaluationError):
    """Raised when evaluation configuration is invalid."""

    pass


class HistoricalDataError(EvaluationError):
    """Raised when historical data retrieval fails."""

    pass


class OutcomeFetchError(EvaluationError):
    """Raised when stock price data cannot be retrieved."""

    pass


class InsufficientDataError(EvaluationError):
    """Raised when there's not enough data for meaningful metrics."""

    pass
