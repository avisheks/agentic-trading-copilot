"""HTML report generator for evaluation results."""

from datetime import datetime, timezone

from jinja2 import Environment, BaseLoader

from trading_copilot.evaluation.models import (
    EpochResult,
    EpochStatus,
    EvaluationConfig,
    EvaluationMetrics,
)
from trading_copilot.models import ConfidenceLevel, Sentiment


# HTML template for evaluation report - follows styling from html_report.py
EVALUATION_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evaluation Report - {{ ticker }}</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.4;
            color: #333;
            background-color: #f5f5f5;
            padding: 15px;
            font-size: 14px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 1.3rem;
            margin-bottom: 8px;
        }
        .header .ticker {
            font-size: 2rem;
            font-weight: bold;
            letter-spacing: 1.5px;
        }
        .header .timestamp {
            font-size: 0.8rem;
            opacity: 0.85;
            margin-top: 8px;
        }
        .section {
            padding: 18px;
            border-bottom: 1px solid #e2e8f0;
        }
        .section:last-child {
            border-bottom: none;
        }
        .section-title {
            font-size: 1rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .metric-box {
            padding: 15px;
            background: #f7fafc;
            border-radius: 6px;
            text-align: center;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: bold;
            color: #2d3748;
        }
        .metric-label {
            font-size: 0.75rem;
            color: #718096;
            margin-top: 4px;
            text-transform: uppercase;
        }
        .metric-good .metric-value { color: #38a169; }
        .metric-warning .metric-value { color: #dd6b20; }
        .metric-bad .metric-value { color: #e53e3e; }
        .confusion-matrix {
            margin: 20px auto;
            max-width: 350px;
        }
        .confusion-matrix table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        .confusion-matrix th, .confusion-matrix td {
            padding: 10px;
            text-align: center;
            border: 1px solid #e2e8f0;
        }
        .confusion-matrix th {
            background: #edf2f7;
            font-weight: 600;
            color: #2d3748;
        }
        .confusion-matrix .tp { background: #c6f6d5; color: #22543d; }
        .confusion-matrix .tn { background: #c6f6d5; color: #22543d; }
        .confusion-matrix .fp { background: #fed7d7; color: #742a2a; }
        .confusion-matrix .fn { background: #fed7d7; color: #742a2a; }
        .confidence-breakdown {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        .confidence-item {
            flex: 1;
            min-width: 100px;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
        }
        .confidence-high {
            background-color: #bee3f8;
            color: #2a4365;
        }
        .confidence-medium {
            background-color: #fefcbf;
            color: #744210;
        }
        .confidence-low {
            background-color: #e2e8f0;
            color: #4a5568;
        }
        .confidence-count {
            font-size: 1.4rem;
            font-weight: bold;
        }
        .confidence-label {
            font-size: 0.75rem;
            margin-top: 4px;
        }
        .epoch-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            margin-top: 15px;
        }
        .epoch-table th {
            background: #edf2f7;
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            border-bottom: 2px solid #cbd5e0;
        }
        .epoch-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
        }
        .epoch-table tr:hover {
            background-color: #f7fafc;
        }
        .date-range {
            font-size: 0.75rem;
            color: #718096;
        }
        .sentiment-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
        }
        .sentiment-bullish {
            background-color: #c6f6d5;
            color: #22543d;
        }
        .sentiment-bearish {
            background-color: #fed7d7;
            color: #742a2a;
        }
        .confidence-tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 0.7rem;
            margin-left: 4px;
        }
        .correctness-correct {
            color: #38a169;
            font-weight: bold;
            font-size: 1.1rem;
        }
        .correctness-incorrect {
            color: #e53e3e;
            font-weight: bold;
            font-size: 1.1rem;
        }
        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 0.7rem;
            text-transform: uppercase;
        }
        .status-complete { background: #c6f6d5; color: #22543d; }
        .status-no_data { background: #fefcbf; color: #744210; }
        .status-incomplete { background: #fed7d7; color: #742a2a; }
        .status-failed { background: #e2e8f0; color: #4a5568; }
        .price-change {
            font-size: 0.8rem;
        }
        .price-positive { color: #38a169; }
        .price-negative { color: #e53e3e; }
        .warning-box {
            background: #fffaf0;
            border: 1px solid #ed8936;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 15px;
        }
        .warning-title {
            color: #c05621;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .warning-text {
            color: #744210;
            font-size: 0.85rem;
        }
        .footer {
            background: #edf2f7;
            padding: 15px;
            font-size: 0.75rem;
            color: #4a5568;
            text-align: center;
        }
        @media (max-width: 768px) {
            body { padding: 8px; font-size: 13px; }
            .header { padding: 15px; }
            .header h1 { font-size: 1.1rem; }
            .header .ticker { font-size: 1.6rem; }
            .section { padding: 12px; }
            .metrics-grid { grid-template-columns: repeat(2, 1fr); }
            .epoch-table { font-size: 0.75rem; }
            .epoch-table th, .epoch-table td { padding: 6px 4px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>Evaluation Report</h1>
            <div class="ticker">{{ ticker }}</div>
            <div class="timestamp">Generated: {{ generated_at }}</div>
        </header>

        <section class="section">
            <h2 class="section-title">Summary</h2>
            
            {% if warning %}
            <div class="warning-box">
                <div class="warning-title">⚠ Warning</div>
                <div class="warning-text">{{ warning }}</div>
            </div>
            {% endif %}
            
            <div class="metrics-grid">
                <div class="metric-box {{ accuracy_class }}">
                    <div class="metric-value">{{ accuracy_pct }}%</div>
                    <div class="metric-label">Accuracy</div>
                </div>
                <div class="metric-box {{ precision_class }}">
                    <div class="metric-value">{{ precision_pct }}%</div>
                    <div class="metric-label">Precision</div>
                </div>
                <div class="metric-box {{ recall_class }}">
                    <div class="metric-value">{{ recall_pct }}%</div>
                    <div class="metric-label">Recall</div>
                </div>
                <div class="metric-box {{ f1_class }}">
                    <div class="metric-value">{{ f1_pct }}%</div>
                    <div class="metric-label">F1 Score</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{{ completed_epochs }}/{{ total_epochs }}</div>
                    <div class="metric-label">Epochs</div>
                </div>
            </div>
            
            <h3 style="font-size: 0.9rem; color: #2d3748; margin-bottom: 10px;">Confusion Matrix</h3>
            <div class="confusion-matrix">
                <table>
                    <tr>
                        <th></th>
                        <th colspan="2">Actual</th>
                    </tr>
                    <tr>
                        <th>Predicted</th>
                        <th>Bullish</th>
                        <th>Bearish</th>
                    </tr>
                    <tr>
                        <th>Bullish</th>
                        <td class="tp">{{ tp }} (TP)</td>
                        <td class="fp">{{ fp }} (FP)</td>
                    </tr>
                    <tr>
                        <th>Bearish</th>
                        <td class="fn">{{ fn }} (FN)</td>
                        <td class="tn">{{ tn }} (TN)</td>
                    </tr>
                </table>
            </div>
            
            <h3 style="font-size: 0.9rem; color: #2d3748; margin: 20px 0 10px 0;">Confidence Breakdown</h3>
            <div class="confidence-breakdown">
                <div class="confidence-item confidence-high">
                    <div class="confidence-count">{{ high_confidence_count }}</div>
                    <div class="confidence-label">HIGH Confidence</div>
                </div>
                <div class="confidence-item confidence-medium">
                    <div class="confidence-count">{{ medium_confidence_count }}</div>
                    <div class="confidence-label">MEDIUM Confidence</div>
                </div>
                <div class="confidence-item confidence-low">
                    <div class="confidence-count">{{ low_confidence_count }}</div>
                    <div class="confidence-label">LOW Confidence</div>
                </div>
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">Per-Epoch Details</h2>
            <table class="epoch-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Look-Back Period</th>
                        <th>Prediction Period</th>
                        <th>Prediction</th>
                        <th>Actual</th>
                        <th>Result</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for epoch in epochs %}
                    <tr>
                        <td>{{ epoch.epoch_number }}</td>
                        <td>
                            <div class="date-range">{{ epoch.look_back_start }} to {{ epoch.look_back_end }}</div>
                        </td>
                        <td>
                            <div class="date-range">{{ epoch.prediction_start }} to {{ epoch.prediction_end }}</div>
                        </td>
                        <td>
                            {% if epoch.predicted_sentiment %}
                            <span class="sentiment-badge sentiment-{{ epoch.predicted_sentiment }}">
                                {{ epoch.predicted_sentiment | upper }}
                            </span>
                            {% if epoch.predicted_confidence %}
                            <span class="confidence-tag confidence-{{ epoch.predicted_confidence }}">
                                {{ epoch.predicted_confidence | upper }}
                            </span>
                            {% endif %}
                            {% else %}
                            <span style="color: #718096;">—</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if epoch.actual_direction %}
                            <span class="sentiment-badge sentiment-{{ epoch.actual_direction }}">
                                {{ epoch.actual_direction | upper }}
                            </span>
                            {% if epoch.price_change_pct is not none %}
                            <div class="price-change {{ 'price-positive' if epoch.price_change_pct >= 0 else 'price-negative' }}">
                                {{ '%+.2f' | format(epoch.price_change_pct) }}%
                            </div>
                            {% endif %}
                            {% else %}
                            <span style="color: #718096;">—</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if epoch.is_correct is not none %}
                            <span class="{{ 'correctness-correct' if epoch.is_correct else 'correctness-incorrect' }}">
                                {{ '✓' if epoch.is_correct else '✗' }}
                            </span>
                            {% else %}
                            <span style="color: #718096;">—</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="status-badge status-{{ epoch.status }}">
                                {{ epoch.status | replace('_', ' ') }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>

        <footer class="footer">
            Evaluation completed with {{ completed_epochs }} of {{ total_epochs }} epochs.
            Configuration: {{ num_epochs }} epochs requested.
        </footer>
    </div>
</body>
</html>"""


class EvaluationReportGenerator:
    """Generates HTML reports for evaluation results."""

    def __init__(self) -> None:
        """Initialize the report generator with Jinja2 environment."""
        self._env = Environment(loader=BaseLoader())
        self._template = self._env.from_string(EVALUATION_REPORT_TEMPLATE)

    def generate(
        self,
        metrics: EvaluationMetrics,
        results: list[EpochResult],
        config: EvaluationConfig,
    ) -> str:
        """Generate HTML report with metrics summary and per-epoch details.
        
        Args:
            metrics: Computed evaluation metrics
            results: List of epoch results
            config: Evaluation configuration
            
        Returns:
            HTML string for the evaluation report
        """
        context = self._build_context(metrics, results, config)
        return self._template.render(**context)

    def _build_context(
        self,
        metrics: EvaluationMetrics,
        results: list[EpochResult],
        config: EvaluationConfig,
    ) -> dict:
        """Build the template context from metrics and results."""
        # Format timestamp
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        # Calculate confidence breakdown
        high_count = sum(
            1 for r in results
            if r.predicted_confidence == ConfidenceLevel.HIGH
        )
        medium_count = sum(
            1 for r in results
            if r.predicted_confidence == ConfidenceLevel.MEDIUM
        )
        low_count = sum(
            1 for r in results
            if r.predicted_confidence == ConfidenceLevel.LOW
        )
        
        # Build epoch details
        epochs = []
        for result in results:
            epoch_data = {
                "epoch_number": result.epoch_number,
                "look_back_start": result.period.look_back.start.strftime("%Y-%m-%d"),
                "look_back_end": result.period.look_back.end.strftime("%Y-%m-%d"),
                "prediction_start": result.period.prediction.start.strftime("%Y-%m-%d"),
                "prediction_end": result.period.prediction.end.strftime("%Y-%m-%d"),
                "predicted_sentiment": (
                    result.predicted_sentiment.value
                    if result.predicted_sentiment else None
                ),
                "predicted_confidence": (
                    result.predicted_confidence.value
                    if result.predicted_confidence else None
                ),
                "actual_direction": (
                    result.actual_outcome.direction.value
                    if result.actual_outcome else None
                ),
                "price_change_pct": (
                    result.actual_outcome.price_change_pct
                    if result.actual_outcome else None
                ),
                "is_correct": result.is_correct,
                "status": result.status.value,
            }
            epochs.append(epoch_data)
        
        return {
            "ticker": config.ticker,
            "generated_at": generated_at,
            "warning": metrics.warning,
            # Metrics as percentages
            "accuracy_pct": f"{metrics.accuracy * 100:.1f}",
            "precision_pct": f"{metrics.precision * 100:.1f}",
            "recall_pct": f"{metrics.recall * 100:.1f}",
            "f1_pct": f"{metrics.f1_score * 100:.1f}",
            # Metric styling classes
            "accuracy_class": self._get_metric_class(metrics.accuracy),
            "precision_class": self._get_metric_class(metrics.precision),
            "recall_class": self._get_metric_class(metrics.recall),
            "f1_class": self._get_metric_class(metrics.f1_score),
            # Epoch counts
            "total_epochs": metrics.total_epochs,
            "completed_epochs": metrics.completed_epochs,
            "num_epochs": config.num_epochs,
            # Confusion matrix
            "tp": metrics.confusion_matrix.true_positive,
            "fp": metrics.confusion_matrix.false_positive,
            "tn": metrics.confusion_matrix.true_negative,
            "fn": metrics.confusion_matrix.false_negative,
            # Confidence breakdown
            "high_confidence_count": high_count,
            "medium_confidence_count": medium_count,
            "low_confidence_count": low_count,
            # Per-epoch details
            "epochs": epochs,
        }

    def _get_metric_class(self, value: float) -> str:
        """Get CSS class based on metric value."""
        if value >= 0.7:
            return "metric-good"
        elif value >= 0.5:
            return "metric-warning"
        else:
            return "metric-bad"
