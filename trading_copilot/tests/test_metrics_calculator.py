"""Unit tests for MetricsCalculator."""

from datetime import date

import pytest

from trading_copilot.evaluation.metrics_calculator import MetricsCalculator
from trading_copilot.evaluation.models import (
    ActualOutcome,
    DateRange,
    EpochPeriod,
    EpochResult,
    EpochStatus,
    EvaluationMetrics,
)
from trading_copilot.models import ConfidenceLevel, Sentiment


def create_epoch_result(
    epoch_number: int,
    predicted: Sentiment,
    actual: Sentiment,
    status: EpochStatus = EpochStatus.COMPLETE,
) -> EpochResult:
    """Helper to create an EpochResult for testing."""
    period = EpochPeriod(
        epoch_number=epoch_number,
        look_back=DateRange(start=date(2024, 1, 1), end=date(2024, 1, 14)),
        prediction=DateRange(start=date(2024, 1, 15), end=date(2024, 1, 21)),
    )
    
    actual_outcome = ActualOutcome(
        direction=actual,
        open_price=100.0,
        close_price=110.0 if actual == Sentiment.BULLISH else 90.0,
        price_change_pct=10.0 if actual == Sentiment.BULLISH else -10.0,
    )
    
    return EpochResult(
        epoch_number=epoch_number,
        period=period,
        status=status,
        predicted_sentiment=predicted if status == EpochStatus.COMPLETE else None,
        predicted_confidence=ConfidenceLevel.HIGH if status == EpochStatus.COMPLETE else None,
        actual_outcome=actual_outcome if status == EpochStatus.COMPLETE else None,
        is_correct=predicted == actual if status == EpochStatus.COMPLETE else None,
        execution_duration_ms=100,
    )


class TestMetricsCalculator:
    """Tests for MetricsCalculator class."""

    def test_calculate_returns_insufficient_data_warning_with_zero_epochs(self) -> None:
        """Test that insufficient_data warning is returned with no epochs."""
        calculator = MetricsCalculator()
        
        result = calculator.calculate([])
        
        assert result.warning == "insufficient_data"
        assert result.completed_epochs == 0
        assert result.total_epochs == 0

    def test_calculate_returns_insufficient_data_warning_with_one_epoch(self) -> None:
        """Test that insufficient_data warning is returned with only one epoch."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),
        ]
        
        result = calculator.calculate(results)
        
        assert result.warning == "insufficient_data"
        assert result.completed_epochs == 1
        assert result.total_epochs == 1

    def test_calculate_no_warning_with_two_completed_epochs(self) -> None:
        """Test that no warning is returned with exactly 2 completed epochs."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),
        ]
        
        result = calculator.calculate(results)
        
        assert result.warning is None
        assert result.completed_epochs == 2

    def test_calculate_precision_all_true_positives(self) -> None:
        """Test precision when all bullish predictions are correct."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),
            create_epoch_result(2, Sentiment.BULLISH, Sentiment.BULLISH),
        ]
        
        result = calculator.calculate(results)
        
        # Precision = TP / (TP + FP) = 2 / (2 + 0) = 1.0
        assert result.precision == pytest.approx(1.0)

    def test_calculate_precision_with_false_positives(self) -> None:
        """Test precision with some false positives."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),  # TP
            create_epoch_result(2, Sentiment.BULLISH, Sentiment.BEARISH),  # FP
        ]
        
        result = calculator.calculate(results)
        
        # Precision = TP / (TP + FP) = 1 / (1 + 1) = 0.5
        assert result.precision == pytest.approx(0.5)

    def test_calculate_precision_zero_when_no_bullish_predictions(self) -> None:
        """Test precision is 0 when there are no bullish predictions."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BEARISH, Sentiment.BULLISH),  # FN
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),  # TN
        ]
        
        result = calculator.calculate(results)
        
        # Precision = TP / (TP + FP) = 0 / (0 + 0) = 0.0
        assert result.precision == pytest.approx(0.0)

    def test_calculate_recall_all_actual_bullish_predicted(self) -> None:
        """Test recall when all actual bullish cases are predicted correctly."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),  # TP
            create_epoch_result(2, Sentiment.BULLISH, Sentiment.BULLISH),  # TP
        ]
        
        result = calculator.calculate(results)
        
        # Recall = TP / (TP + FN) = 2 / (2 + 0) = 1.0
        assert result.recall == pytest.approx(1.0)

    def test_calculate_recall_with_false_negatives(self) -> None:
        """Test recall with some false negatives."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),  # TP
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BULLISH),  # FN
        ]
        
        result = calculator.calculate(results)
        
        # Recall = TP / (TP + FN) = 1 / (1 + 1) = 0.5
        assert result.recall == pytest.approx(0.5)

    def test_calculate_recall_zero_when_no_actual_bullish(self) -> None:
        """Test recall is 0 when there are no actual bullish cases."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BEARISH),  # FP
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),  # TN
        ]
        
        result = calculator.calculate(results)
        
        # Recall = TP / (TP + FN) = 0 / (0 + 0) = 0.0
        assert result.recall == pytest.approx(0.0)

    def test_calculate_f1_score(self) -> None:
        """Test F1 score calculation."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),  # TP
            create_epoch_result(2, Sentiment.BULLISH, Sentiment.BEARISH),  # FP
            create_epoch_result(3, Sentiment.BEARISH, Sentiment.BULLISH),  # FN
            create_epoch_result(4, Sentiment.BEARISH, Sentiment.BEARISH),  # TN
        ]
        
        result = calculator.calculate(results)
        
        # Precision = 1 / (1 + 1) = 0.5
        # Recall = 1 / (1 + 1) = 0.5
        # F1 = 2 * (0.5 * 0.5) / (0.5 + 0.5) = 0.5
        assert result.f1_score == pytest.approx(0.5)

    def test_calculate_f1_zero_when_precision_and_recall_zero(self) -> None:
        """Test F1 is 0 when both precision and recall are 0."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BEARISH, Sentiment.BEARISH),  # TN
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),  # TN
        ]
        
        result = calculator.calculate(results)
        
        assert result.f1_score == pytest.approx(0.0)

    def test_calculate_accuracy(self) -> None:
        """Test accuracy calculation."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),  # TP
            create_epoch_result(2, Sentiment.BULLISH, Sentiment.BEARISH),  # FP
            create_epoch_result(3, Sentiment.BEARISH, Sentiment.BULLISH),  # FN
            create_epoch_result(4, Sentiment.BEARISH, Sentiment.BEARISH),  # TN
        ]
        
        result = calculator.calculate(results)
        
        # Accuracy = (TP + TN) / total = (1 + 1) / 4 = 0.5
        assert result.accuracy == pytest.approx(0.5)

    def test_calculate_accuracy_perfect(self) -> None:
        """Test accuracy when all predictions are correct."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),  # TP
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),  # TN
        ]
        
        result = calculator.calculate(results)
        
        # Accuracy = (TP + TN) / total = (1 + 1) / 2 = 1.0
        assert result.accuracy == pytest.approx(1.0)

    def test_calculate_confusion_matrix(self) -> None:
        """Test confusion matrix is built correctly."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),  # TP
            create_epoch_result(2, Sentiment.BULLISH, Sentiment.BEARISH),  # FP
            create_epoch_result(3, Sentiment.BEARISH, Sentiment.BULLISH),  # FN
            create_epoch_result(4, Sentiment.BEARISH, Sentiment.BEARISH),  # TN
        ]
        
        result = calculator.calculate(results)
        
        assert result.confusion_matrix.true_positive == 1
        assert result.confusion_matrix.false_positive == 1
        assert result.confusion_matrix.true_negative == 1
        assert result.confusion_matrix.false_negative == 1

    def test_calculate_excludes_incomplete_epochs(self) -> None:
        """Test that incomplete epochs are excluded from metrics."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),
            create_epoch_result(3, Sentiment.BULLISH, Sentiment.BULLISH, EpochStatus.INCOMPLETE),
        ]
        
        result = calculator.calculate(results)
        
        assert result.total_epochs == 3
        assert result.completed_epochs == 2
        # Only 2 completed epochs should be counted in confusion matrix
        total_in_matrix = (
            result.confusion_matrix.true_positive
            + result.confusion_matrix.false_positive
            + result.confusion_matrix.true_negative
            + result.confusion_matrix.false_negative
        )
        assert total_in_matrix == 2

    def test_calculate_excludes_failed_epochs(self) -> None:
        """Test that failed epochs are excluded from metrics."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),
            create_epoch_result(3, Sentiment.BULLISH, Sentiment.BULLISH, EpochStatus.FAILED),
        ]
        
        result = calculator.calculate(results)
        
        assert result.total_epochs == 3
        assert result.completed_epochs == 2

    def test_calculate_excludes_no_data_epochs(self) -> None:
        """Test that no_data epochs are excluded from metrics."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),
            create_epoch_result(3, Sentiment.BULLISH, Sentiment.BULLISH, EpochStatus.NO_DATA),
        ]
        
        result = calculator.calculate(results)
        
        assert result.total_epochs == 3
        assert result.completed_epochs == 2

    def test_calculate_returns_evaluation_metrics_instance(self) -> None:
        """Test that calculate returns an EvaluationMetrics instance."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH),
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH),
        ]
        
        result = calculator.calculate(results)
        
        assert isinstance(result, EvaluationMetrics)

    def test_calculate_insufficient_data_when_all_epochs_incomplete(self) -> None:
        """Test insufficient_data warning when all epochs are incomplete."""
        calculator = MetricsCalculator()
        results = [
            create_epoch_result(1, Sentiment.BULLISH, Sentiment.BULLISH, EpochStatus.INCOMPLETE),
            create_epoch_result(2, Sentiment.BEARISH, Sentiment.BEARISH, EpochStatus.FAILED),
            create_epoch_result(3, Sentiment.BULLISH, Sentiment.BULLISH, EpochStatus.NO_DATA),
        ]
        
        result = calculator.calculate(results)
        
        assert result.warning == "insufficient_data"
        assert result.total_epochs == 3
        assert result.completed_epochs == 0
