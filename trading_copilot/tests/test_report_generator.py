"""Unit tests for EvaluationReportGenerator."""

from datetime import date

import pytest

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
from trading_copilot.evaluation.report_generator import EvaluationReportGenerator
from trading_copilot.models import ConfidenceLevel, Sentiment


@pytest.fixture
def report_generator() -> EvaluationReportGenerator:
    """Create a report generator instance."""
    return EvaluationReportGenerator()


@pytest.fixture
def sample_config() -> EvaluationConfig:
    """Create a sample evaluation config."""
    return EvaluationConfig(ticker="AAPL", num_epochs=5, max_parallelism=2)


@pytest.fixture
def sample_metrics() -> EvaluationMetrics:
    """Create sample evaluation metrics."""
    return EvaluationMetrics(
        precision=0.75,
        recall=0.80,
        f1_score=0.77,
        accuracy=0.70,
        confusion_matrix=ConfusionMatrix(
            true_positive=3,
            false_positive=1,
            true_negative=2,
            false_negative=1,
        ),
        total_epochs=5,
        completed_epochs=5,
        warning=None,
    )


@pytest.fixture
def sample_results() -> list[EpochResult]:
    """Create sample epoch results."""
    results = []
    
    # Epoch 1: Correct bullish prediction
    results.append(
        EpochResult(
            epoch_number=1,
            period=EpochPeriod(
                epoch_number=1,
                look_back=DateRange(date(2024, 1, 7), date(2024, 1, 20)),
                prediction=DateRange(date(2024, 1, 21), date(2024, 1, 27)),
            ),
            status=EpochStatus.COMPLETE,
            predicted_sentiment=Sentiment.BULLISH,
            predicted_confidence=ConfidenceLevel.HIGH,
            actual_outcome=ActualOutcome(
                direction=Sentiment.BULLISH,
                open_price=100.0,
                close_price=105.0,
                price_change_pct=5.0,
            ),
            is_correct=True,
            execution_duration_ms=1500,
        )
    )
    
    # Epoch 2: Incorrect bearish prediction
    results.append(
        EpochResult(
            epoch_number=2,
            period=EpochPeriod(
                epoch_number=2,
                look_back=DateRange(date(2023, 12, 17), date(2023, 12, 30)),
                prediction=DateRange(date(2023, 12, 31), date(2024, 1, 6)),
            ),
            status=EpochStatus.COMPLETE,
            predicted_sentiment=Sentiment.BEARISH,
            predicted_confidence=ConfidenceLevel.MEDIUM,
            actual_outcome=ActualOutcome(
                direction=Sentiment.BULLISH,
                open_price=98.0,
                close_price=102.0,
                price_change_pct=4.08,
            ),
            is_correct=False,
            execution_duration_ms=1200,
        )
    )
    
    # Epoch 3: No data available
    results.append(
        EpochResult(
            epoch_number=3,
            period=EpochPeriod(
                epoch_number=3,
                look_back=DateRange(date(2023, 11, 26), date(2023, 12, 9)),
                prediction=DateRange(date(2023, 12, 10), date(2023, 12, 16)),
            ),
            status=EpochStatus.NO_DATA,
            predicted_sentiment=None,
            predicted_confidence=None,
            actual_outcome=None,
            is_correct=None,
            execution_duration_ms=500,
        )
    )
    
    return results


class TestEvaluationReportGenerator:
    """Tests for EvaluationReportGenerator."""

    def test_generate_returns_html_string(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that generate returns a valid HTML string."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        assert isinstance(html, str)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_report_contains_ticker(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains the ticker symbol."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        assert "AAPL" in html

    def test_report_contains_metrics(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains all computed metrics."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Check accuracy (70%)
        assert "70.0%" in html
        # Check precision (75%)
        assert "75.0%" in html
        # Check recall (80%)
        assert "80.0%" in html
        # Check F1 (77%)
        assert "77.0%" in html

    def test_report_contains_confusion_matrix(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains confusion matrix values."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Check confusion matrix values
        assert "3 (TP)" in html  # True positive
        assert "1 (FP)" in html  # False positive
        assert "2 (TN)" in html  # True negative
        assert "1 (FN)" in html  # False negative

    def test_report_contains_per_epoch_details(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains per-epoch details."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Check date ranges are present
        assert "2024-01-07" in html  # Look-back start
        assert "2024-01-20" in html  # Look-back end
        assert "2024-01-21" in html  # Prediction start
        assert "2024-01-27" in html  # Prediction end

    def test_report_contains_correctness_indicators(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains correctness indicators."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Check for checkmark (correct) and X (incorrect)
        assert "✓" in html
        assert "✗" in html

    def test_report_contains_confidence_breakdown(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains confidence breakdown."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Check confidence labels
        assert "HIGH Confidence" in html
        assert "MEDIUM Confidence" in html
        assert "LOW Confidence" in html

    def test_report_contains_epoch_status(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains epoch status badges."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Check status values
        assert "complete" in html.lower()
        assert "no data" in html.lower()

    def test_report_with_warning(
        self,
        report_generator: EvaluationReportGenerator,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report displays warning when present."""
        metrics_with_warning = EvaluationMetrics(
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            accuracy=0.0,
            confusion_matrix=ConfusionMatrix(0, 0, 0, 0),
            total_epochs=1,
            completed_epochs=1,
            warning="insufficient_data",
        )
        
        html = report_generator.generate(
            metrics_with_warning, sample_results, sample_config
        )
        
        assert "insufficient_data" in html
        assert "Warning" in html

    def test_report_contains_price_change(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains price change percentages."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Check price change is displayed
        assert "+5.00%" in html  # Epoch 1 price change
        assert "+4.08%" in html  # Epoch 2 price change

    def test_report_contains_sentiment_badges(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that report contains sentiment badges."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Check sentiment values are displayed
        assert "BULLISH" in html
        assert "BEARISH" in html

    def test_report_is_valid_html(
        self,
        report_generator: EvaluationReportGenerator,
        sample_metrics: EvaluationMetrics,
        sample_results: list[EpochResult],
        sample_config: EvaluationConfig,
    ) -> None:
        """Test that generated report is well-formed HTML."""
        html = report_generator.generate(sample_metrics, sample_results, sample_config)
        
        # Basic HTML structure checks
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html
        assert "<title>" in html
        assert "</title>" in html
