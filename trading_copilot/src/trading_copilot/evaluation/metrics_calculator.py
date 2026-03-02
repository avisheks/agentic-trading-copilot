"""Metrics calculator for evaluation results."""

from trading_copilot.evaluation.errors import InsufficientDataError
from trading_copilot.evaluation.models import (
    ConfusionMatrix,
    EpochResult,
    EpochStatus,
    EvaluationMetrics,
)
from trading_copilot.models import Sentiment


class MetricsCalculator:
    """Calculates classification metrics from epoch results."""

    def calculate(self, results: list[EpochResult]) -> EvaluationMetrics:
        """
        Compute precision, recall, F1, accuracy, and confusion matrix.

        Args:
            results: List of completed epoch results

        Returns:
            EvaluationMetrics with all computed metrics

        Raises:
            InsufficientDataError: If fewer than 2 completed epochs
        """
        # Filter to only completed epochs with valid predictions and outcomes
        completed_results = [
            r
            for r in results
            if r.status == EpochStatus.COMPLETE
            and r.predicted_sentiment is not None
            and r.actual_outcome is not None
        ]

        total_epochs = len(results)
        completed_epochs = len(completed_results)

        # Check for insufficient data
        if completed_epochs < 2:
            # Return metrics with warning for insufficient data
            return EvaluationMetrics(
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                accuracy=0.0,
                confusion_matrix=ConfusionMatrix(
                    true_positive=0,
                    false_positive=0,
                    true_negative=0,
                    false_negative=0,
                ),
                total_epochs=total_epochs,
                completed_epochs=completed_epochs,
                warning="insufficient_data",
            )

        # Build confusion matrix
        confusion_matrix = self._build_confusion_matrix(completed_results)

        # Calculate metrics
        precision = self._calculate_precision(confusion_matrix)
        recall = self._calculate_recall(confusion_matrix)
        f1_score = self._calculate_f1(precision, recall)
        accuracy = self._calculate_accuracy(confusion_matrix)

        return EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            accuracy=accuracy,
            confusion_matrix=confusion_matrix,
            total_epochs=total_epochs,
            completed_epochs=completed_epochs,
            warning=None,
        )

    def _build_confusion_matrix(
        self, results: list[EpochResult]
    ) -> ConfusionMatrix:
        """
        Build a 2x2 confusion matrix from epoch results.

        Confusion matrix definitions:
        - True Positive (TP): Predicted bullish, actual bullish
        - False Positive (FP): Predicted bullish, actual bearish
        - True Negative (TN): Predicted bearish, actual bearish
        - False Negative (FN): Predicted bearish, actual bullish
        """
        tp = 0  # Predicted bullish, actual bullish
        fp = 0  # Predicted bullish, actual bearish
        tn = 0  # Predicted bearish, actual bearish
        fn = 0  # Predicted bearish, actual bullish

        for result in results:
            predicted = result.predicted_sentiment
            actual = result.actual_outcome.direction

            if predicted == Sentiment.BULLISH and actual == Sentiment.BULLISH:
                tp += 1
            elif predicted == Sentiment.BULLISH and actual == Sentiment.BEARISH:
                fp += 1
            elif predicted == Sentiment.BEARISH and actual == Sentiment.BEARISH:
                tn += 1
            elif predicted == Sentiment.BEARISH and actual == Sentiment.BULLISH:
                fn += 1

        return ConfusionMatrix(
            true_positive=tp,
            false_positive=fp,
            true_negative=tn,
            false_negative=fn,
        )

    def _calculate_precision(self, matrix: ConfusionMatrix) -> float:
        """
        Calculate precision for bullish predictions.

        Precision = TP / (TP + FP)
        Returns 0.0 if there are no positive predictions.
        """
        denominator = matrix.true_positive + matrix.false_positive
        if denominator == 0:
            return 0.0
        return matrix.true_positive / denominator

    def _calculate_recall(self, matrix: ConfusionMatrix) -> float:
        """
        Calculate recall for bullish predictions.

        Recall = TP / (TP + FN)
        Returns 0.0 if there are no actual positives.
        """
        denominator = matrix.true_positive + matrix.false_negative
        if denominator == 0:
            return 0.0
        return matrix.true_positive / denominator

    def _calculate_f1(self, precision: float, recall: float) -> float:
        """
        Calculate F1-score.

        F1 = 2 * (precision * recall) / (precision + recall)
        Returns 0.0 if both precision and recall are 0.
        """
        denominator = precision + recall
        if denominator == 0:
            return 0.0
        return 2 * (precision * recall) / denominator

    def _calculate_accuracy(self, matrix: ConfusionMatrix) -> float:
        """
        Calculate overall accuracy.

        Accuracy = (TP + TN) / total
        Returns 0.0 if there are no predictions.
        """
        total = (
            matrix.true_positive
            + matrix.false_positive
            + matrix.true_negative
            + matrix.false_negative
        )
        if total == 0:
            return 0.0
        return (matrix.true_positive + matrix.true_negative) / total
