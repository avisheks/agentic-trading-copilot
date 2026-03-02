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
    tickers: list[str] = None,
    num_epochs: int = 5,
    max_parallelism: int = 2,
) -> None:
    """Run end-to-end evaluation and generate consolidated report.
    
    Args:
        tickers: List of stock tickers to evaluate (reads from config if None)
        num_epochs: Number of epochs to run (default 5 for faster demo)
        max_parallelism: Max concurrent epoch executions
    """
    # Load tickers from config if not provided
    if tickers is None:
        app_config_path = Path(__file__).parent.parent / "config" / "app_config.yaml"
        import yaml
        with open(app_config_path, 'r') as f:
            app_config = yaml.safe_load(f)
            tickers = app_config.get('tickers', ['AAPL'])
    
    print(f"\n{'='*60}")
    print(f"Trading Copilot Evaluation Module")
    print(f"{'='*60}")
    print(f"Tickers: {', '.join(tickers)}")
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
    
    # Run evaluations for all tickers
    print(f"Running evaluation for {len(tickers)} tickers across {num_epochs} epochs each...")
    print("This may take several minutes...\n")
    
    ticker_reports = []
    
    try:
        for ticker in tickers:
            print(f"\n{'='*60}")
            print(f"Evaluating {ticker}...")
            print(f"{'='*60}")
            
            # Create evaluation config for this ticker
            eval_config = EvaluationConfig(
                ticker=ticker,
                num_epochs=num_epochs,
                max_parallelism=max_parallelism,
            )
            
            try:
                report = await evaluation_runner.run(eval_config)
                
                # Store for consolidated report
                ticker_reports.append((report.metrics, report.epoch_results, eval_config))
                
                # Print summary
                print(f"\nTicker: {report.ticker}")
                print(f"Completed: {report.metrics.completed_epochs}/{report.metrics.total_epochs} epochs")
                print(f"Accuracy: {report.metrics.accuracy * 100:.1f}%")
                
                if report.metrics.warning:
                    print(f"⚠️  Warning: {report.metrics.warning}")
                    
            except Exception as e:
                print(f"❌ Evaluation failed for {ticker}: {e}")
                continue
        
        if not ticker_reports:
            print("\n❌ No successful evaluations to generate report")
            return
        
        # Generate consolidated multi-ticker report
        print(f"\n{'='*60}")
        print("GENERATING CONSOLIDATED REPORT")
        print(f"{'='*60}")
        
        consolidated_html = report_generator.generate_multi(ticker_reports)
        
        # Save consolidated HTML report
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"evaluation_report_multi_{timestamp}.html"
        
        with open(report_path, "w") as f:
            f.write(consolidated_html)
        
        print(f"\n{'='*60}")
        print(f"Consolidated HTML report saved to: {report_path}")
        print(f"{'='*60}\n")
        
        # Print summary for all tickers
        print("Summary for All Tickers:")
        print("-" * 80)
        for metrics, results, config in ticker_reports:
            print(f"  {config.ticker}: {metrics.accuracy * 100:.1f}% accuracy ({metrics.completed_epochs}/{metrics.total_epochs} epochs)")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        raise
    finally:
        await news_agent.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Trading Copilot evaluation")
    parser.add_argument("--tickers", nargs="+", help="Stock tickers to evaluate (default: from config)")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--parallelism", type=int, default=2, help="Max parallel epochs")
    
    args = parser.parse_args()
    
    asyncio.run(run_evaluation(
        tickers=args.tickers,
        num_epochs=args.epochs,
        max_parallelism=args.parallelism,
    ))
