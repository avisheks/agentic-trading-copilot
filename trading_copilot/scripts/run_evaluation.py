#!/usr/bin/env python3
"""End-to-end evaluation runner script.

This script runs the evaluation module to backtest sentiment predictions
and generates an HTML report.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trading_copilot.agents.news import NewsAgent
from trading_copilot.analyzer import SentimentAnalyzer
from trading_copilot.config import ConfigManager
from trading_copilot.evaluation import (
    EvaluationConfig,
    EvaluationRunner,
    EvaluationReportGenerator,
)
from trading_copilot.evaluation.epoch_runner import EpochRunner
from trading_copilot.evaluation.historical_data_fetcher import HistoricalDataFetcher
from trading_copilot.evaluation.metrics_calculator import MetricsCalculator
from trading_copilot.evaluation.outcome_fetcher import OutcomeFetcher


async def run_evaluation(
    ticker: str = "AAPL",
    num_epochs: int = 5,
    max_parallelism: int = 2,
) -> None:
    """Run end-to-end evaluation and generate report.
    
    Args:
        ticker: Stock ticker to evaluate
        num_epochs: Number of epochs to run (default 5 for faster demo)
        max_parallelism: Max concurrent epoch executions
    """
    print(f"\n{'='*60}")
    print(f"Trading Copilot Evaluation Module")
    print(f"{'='*60}")
    print(f"Ticker: {ticker}")
    print(f"Epochs: {num_epochs}")
    print(f"Max Parallelism: {max_parallelism}")
    print(f"{'='*60}\n")
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    config_manager = ConfigManager(config_path=config_path)
    config_manager.load()
    sources = config_manager.get_sources_for_agent("news")
    
    # Initialize components
    print("Initializing components...")
    news_agent = NewsAgent(sources=sources)
    sentiment_analyzer = SentimentAnalyzer()
    historical_fetcher = HistoricalDataFetcher(news_agent)
    outcome_fetcher = OutcomeFetcher()
    metrics_calculator = MetricsCalculator()
    report_generator = EvaluationReportGenerator()
    
    epoch_runner = EpochRunner(
        historical_fetcher=historical_fetcher,
        outcome_fetcher=outcome_fetcher,
        sentiment_analyzer=sentiment_analyzer,
    )
    
    evaluation_runner = EvaluationRunner(
        epoch_runner=epoch_runner,
        metrics_calculator=metrics_calculator,
        report_generator=report_generator,
        max_parallelism=max_parallelism,
    )
    
    # Create evaluation config
    eval_config = EvaluationConfig(
        ticker=ticker,
        num_epochs=num_epochs,
        max_parallelism=max_parallelism,
    )
    
    # Run evaluation
    print(f"Running evaluation for {ticker} across {num_epochs} epochs...")
    print("This may take a few minutes...\n")
    
    try:
        report = await evaluation_runner.run(eval_config)
        
        # Print summary
        print(f"\n{'='*60}")
        print("EVALUATION RESULTS")
        print(f"{'='*60}")
        print(f"Ticker: {report.ticker}")
        print(f"Total Epochs: {report.metrics.total_epochs}")
        print(f"Completed Epochs: {report.metrics.completed_epochs}")
        print(f"\nMetrics:")
        print(f"  Accuracy:  {report.metrics.accuracy * 100:.1f}%")
        print(f"  Precision: {report.metrics.precision * 100:.1f}%")
        print(f"  Recall:    {report.metrics.recall * 100:.1f}%")
        print(f"  F1 Score:  {report.metrics.f1_score * 100:.1f}%")
        
        print(f"\nConfusion Matrix:")
        cm = report.metrics.confusion_matrix
        print(f"  True Positive:  {cm.true_positive}")
        print(f"  False Positive: {cm.false_positive}")
        print(f"  True Negative:  {cm.true_negative}")
        print(f"  False Negative: {cm.false_negative}")
        
        if report.metrics.warning:
            print(f"\n⚠️  Warning: {report.metrics.warning}")
        
        # Save HTML report
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"evaluation_report_{ticker}_{timestamp}.html"
        
        with open(report_path, "w") as f:
            f.write(report.html_content)
        
        print(f"\n{'='*60}")
        print(f"HTML report saved to: {report_path}")
        print(f"{'='*60}\n")
        
        # Print per-epoch summary
        print("Per-Epoch Results:")
        print("-" * 80)
        for result in report.epoch_results:
            status_icon = {
                "complete": "✓",
                "no_data": "○",
                "incomplete": "△",
                "failed": "✗",
            }.get(result.status.value, "?")
            
            if result.status.value == "complete":
                correct_icon = "✓" if result.is_correct else "✗"
                pred = result.predicted_sentiment.value if result.predicted_sentiment else "N/A"
                actual = result.actual_outcome.direction.value if result.actual_outcome else "N/A"
                print(f"  Epoch {result.epoch_number}: [{status_icon}] Predicted: {pred:8} | Actual: {actual:8} | {correct_icon}")
            else:
                print(f"  Epoch {result.epoch_number}: [{status_icon}] Status: {result.status.value}")
                if result.error_message:
                    print(f"           Error: {result.error_message[:60]}...")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        raise
    finally:
        await news_agent.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Trading Copilot evaluation")
    parser.add_argument("--ticker", default="AAPL", help="Stock ticker to evaluate")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--parallelism", type=int, default=2, help="Max parallel epochs")
    
    args = parser.parse_args()
    
    asyncio.run(run_evaluation(
        ticker=args.ticker,
        num_epochs=args.epochs,
        max_parallelism=args.parallelism,
    ))
