"""HTML report generator for multi-run statistical evaluation results."""

from datetime import datetime, timezone
from pathlib import Path

from trading_copilot.evaluation.statistical_models import (
    AggregatedEvaluationReport,
    TickerStatistics,
)


class StatisticalReportGenerator:
    """Generates HTML reports with statistical metrics from multiple runs."""
    
    def generate_html(
        self,
        report: AggregatedEvaluationReport,
    ) -> str:
        """Generate comprehensive HTML report with statistical metrics.
        
        Args:
            report: Aggregated evaluation report with multi-run statistics
            
        Returns:
            HTML content as string
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        # Build HTML
        html_parts = [
            self._html_header(),
            self._html_summary_section(report, timestamp),
        ]
        
        # Add ticker sections
        for ticker, stats in sorted(report.ticker_statistics.items()):
            html_parts.append(self._html_ticker_section(ticker, stats))
        
        html_parts.append(self._html_footer())
        
        return "\n".join(html_parts)
    
    def save_report(
        self,
        report: AggregatedEvaluationReport,
        output_dir: str | Path,
    ) -> Path:
        """Generate and save HTML report to file.
        
        Args:
            report: Aggregated evaluation report
            output_dir: Directory to save report
            
        Returns:
            Path to saved report file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_report_statistical_{timestamp}.html"
        filepath = output_path / filename
        
        html_content = self.generate_html(report)
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        return filepath
    
    def _html_header(self) -> str:
        """Generate HTML header with styles."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Statistical Evaluation Report</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2rem; margin-bottom: 10px; }
        .header .subtitle { font-size: 1.1rem; opacity: 0.9; }
        .header .timestamp { font-size: 0.9rem; opacity: 0.8; margin-top: 10px; }
        .section { padding: 30px; border-bottom: 1px solid #e2e8f0; }
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        .ticker-header {
            background: #edf2f7;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .ticker-title {
            font-size: 1.8rem;
            font-weight: bold;
            color: #2d3748;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-box {
            padding: 20px;
            background: #f7fafc;
            border-radius: 8px;
            border-left: 4px solid #4299e1;
        }
        .stat-label {
            font-size: 0.85rem;
            color: #718096;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .stat-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #2d3748;
        }
        .stat-detail {
            font-size: 0.9rem;
            color: #4a5568;
            margin-top: 4px;
        }
        .metric-good { color: #38a169; }
        .metric-warning { color: #dd6b20; }
        .metric-bad { color: #e53e3e; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th {
            background: #edf2f7;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            border-bottom: 2px solid #cbd5e0;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
        }
        tr:hover { background-color: #f7fafc; }
        .confusion-matrix {
            max-width: 400px;
            margin: 20px auto;
        }
        .confusion-matrix td { text-align: center; font-weight: 600; }
        .cm-tp { background: #c6f6d5; color: #22543d; }
        .cm-fp { background: #fed7d7; color: #742a2a; }
        .cm-fn { background: #fed7d7; color: #742a2a; }
        .cm-tn { background: #c6f6d5; color: #22543d; }
        .footer {
            background: #edf2f7;
            padding: 20px;
            text-align: center;
            color: #4a5568;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>"""
    
    def _html_summary_section(self, report: AggregatedEvaluationReport, timestamp: str) -> str:
        """Generate summary section."""
        return f"""
    <div class="container">
        <header class="header">
            <h1>Statistical Evaluation Report</h1>
            <div class="subtitle">Multi-Run Analysis with Mean & Standard Deviation</div>
            <div class="timestamp">Generated: {timestamp}</div>
        </header>
        
        <section class="section">
            <h2 class="section-title">Summary</h2>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-label">Total Tickers</div>
                    <div class="stat-value">{report.total_tickers}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Epochs per Ticker</div>
                    <div class="stat-value">{report.total_epochs_per_ticker}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Runs per Epoch</div>
                    <div class="stat-value">{report.runs_per_epoch}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Total Evaluations</div>
                    <div class="stat-value">{report.total_tickers * report.total_epochs_per_ticker * report.runs_per_epoch}</div>
                </div>
            </div>
            
            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #2d3748;">Ticker Overview</h3>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Mean Accuracy</th>
                        <th>Std Dev</th>
                        <th>Mean Precision</th>
                        <th>Mean Recall</th>
                        <th>Mean F1</th>
                        <th>Completed Runs</th>
                    </tr>
                </thead>
                <tbody>
                    {self._html_ticker_summary_rows(report)}
                </tbody>
            </table>
        </section>
"""
    
    def _html_ticker_summary_rows(self, report: AggregatedEvaluationReport) -> str:
        """Generate ticker summary table rows."""
        rows = []
        for ticker, stats in sorted(report.ticker_statistics.items()):
            accuracy_class = self._get_metric_class(stats.mean_accuracy)
            rows.append(f"""
                    <tr>
                        <td><strong>{ticker}</strong></td>
                        <td class="{accuracy_class}">{stats.mean_accuracy:.1%}</td>
                        <td>{stats.std_accuracy:.1%}</td>
                        <td>{stats.precision_stats.mean:.1%}</td>
                        <td>{stats.recall_stats.mean:.1%}</td>
                        <td>{stats.f1_stats.mean:.1%}</td>
                        <td>{stats.completed_runs}/{stats.total_runs}</td>
                    </tr>""")
        return "\n".join(rows)
    
    def _html_ticker_section(self, ticker: str, stats: TickerStatistics) -> str:
        """Generate detailed section for a single ticker."""
        return f"""
        <section class="section">
            <div class="ticker-header">
                <div class="ticker-title">{ticker}</div>
            </div>
            
            <h3 style="margin-bottom: 15px; color: #2d3748;">Statistical Metrics</h3>
            <div class="stats-grid">
                {self._html_metric_box("Accuracy", stats.accuracy_stats)}
                {self._html_metric_box("Precision", stats.precision_stats)}
                {self._html_metric_box("Recall", stats.recall_stats)}
                {self._html_metric_box("F1 Score", stats.f1_stats)}
            </div>
            
            <h3 style="margin: 30px 0 15px 0; color: #2d3748;">Confusion Matrix (Aggregated)</h3>
            <table class="confusion-matrix">
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
                    <td class="cm-tp">{stats.total_true_positives} (TP)</td>
                    <td class="cm-fp">{stats.total_false_positives} (FP)</td>
                </tr>
                <tr>
                    <th>Bearish</th>
                    <td class="cm-fn">{stats.total_false_negatives} (FN)</td>
                    <td class="cm-tn">{stats.total_true_negatives} (TN)</td>
                </tr>
            </table>
            
            <h3 style="margin: 30px 0 15px 0; color: #2d3748;">Per-Epoch Statistics</h3>
            <table>
                <thead>
                    <tr>
                        <th>Epoch</th>
                        <th>Mean Accuracy</th>
                        <th>Std Dev</th>
                        <th>Consensus Prediction</th>
                        <th>Actual Outcome</th>
                        <th>Correct Runs</th>
                    </tr>
                </thead>
                <tbody>
                    {self._html_epoch_stats_rows(stats)}
                </tbody>
            </table>
        </section>
"""
    
    def _html_metric_box(self, label: str, stats) -> str:
        """Generate metric box HTML."""
        return f"""
                <div class="stat-box">
                    <div class="stat-label">{label}</div>
                    <div class="stat-value">{stats.mean:.1%}</div>
                    <div class="stat-detail">σ = {stats.std_dev:.1%}</div>
                    <div class="stat-detail">Range: {stats.min_value:.1%} - {stats.max_value:.1%}</div>
                    <div class="stat-detail">n = {stats.sample_size}</div>
                </div>"""
    
    def _html_epoch_stats_rows(self, stats: TickerStatistics) -> str:
        """Generate epoch statistics table rows."""
        rows = []
        for epoch_stat in stats.epoch_statistics:
            accuracy_class = self._get_metric_class(epoch_stat.accuracy.mean)
            consensus = str(epoch_stat.consensus_prediction) if epoch_stat.consensus_prediction else "—"
            actual = str(epoch_stat.actual_outcome) if epoch_stat.actual_outcome else "—"
            
            rows.append(f"""
                    <tr>
                        <td>{epoch_stat.epoch_number}</td>
                        <td class="{accuracy_class}">{epoch_stat.accuracy.mean:.1%}</td>
                        <td>{epoch_stat.accuracy.std_dev:.1%}</td>
                        <td>{consensus.upper() if consensus != "—" else consensus}</td>
                        <td>{actual.upper() if actual != "—" else actual}</td>
                        <td>{epoch_stat.num_correct}/{epoch_stat.num_total}</td>
                    </tr>""")
        return "\n".join(rows)
    
    def _html_footer(self) -> str:
        """Generate HTML footer."""
        return """
        <footer class="footer">
            Statistical Evaluation Report - Trading Copilot<br>
            Multi-run analysis provides mean and standard deviation metrics for prediction reliability
        </footer>
    </div>
</body>
</html>"""
    
    def _get_metric_class(self, value: float) -> str:
        """Get CSS class for metric value."""
        if value >= 0.7:
            return "metric-good"
        elif value >= 0.5:
            return "metric-warning"
        else:
            return "metric-bad"