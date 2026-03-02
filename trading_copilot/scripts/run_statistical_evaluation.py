"""Run statistical multi-run evaluation with mean and std-dev metrics.

This script executes multiple evaluation runs per (ticker, epoch) combination
to provide statistical analysis of prediction reliability.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml

from trading_copilot.config import ConfigManager
from trading_copilot.evaluation.config_models import EvaluationConfig
from trading_copilot.evaluation.epoch_runner import EpochRunner
from trading_copilot.evaluation.historical_data_fetcher import HistoricalDataFetcher
from trading_copilot.evaluation.metrics_calculator import MetricsCalculator
from trading_copilot.evaluation.multi_run_evaluation_runner import MultiRunEvaluationRunner
from trading_copilot.evaluation.outcome_fetcher import OutcomeFetcher
from trading_copilot.evaluation.report_generator import EvaluationReportGenerator
from trading_copilot.evaluation.statistical_report_generator import StatisticalReportGenerator
from trading_copilot.agents.news import NewsAgent
from trading_copilot.analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for statistical evaluation."""
    
    print("=" * 60)
    print("Trading Copilot - Statistical Evaluation Module")
    print("=" * 60)
    
    # Load configurations
    project_root = Path(__file__).parent.parent
    
    # Load app config to get tickers
    app_config_path = project_root / "config" / "app_config.yaml"
    with open(app_config_path, 'r') as f:
        app_config_data = yaml.safe_load(f)
    
    # Load evaluation config
    eval_config = EvaluationConfig.from_yaml(
        project_root / "config" / "evaluation_config.yaml"
    )
    
    # Determine tickers to evaluate
    if eval_config.evaluation.tickers:
        tickers = eval_config.evaluation.tickers
    else:
        tickers = app_config_data.get('tickers', ['AAPL'])
    
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Epochs: {eval_config.evaluation.num_epochs}")
    print(f"Runs per Epoch: {eval_config.evaluation.runs_per_epoch}")
    print(f"Max Parallelism: {eval_config.evaluation.max_parallelism}")
    print(f"Total Evaluations: {len(tickers) * eval_config.evaluation.num_epochs * eval_config.evaluation.runs_per_epoch}")
    print("=" * 60)
    
    # Initialize components
    print("\nInitializing components...")
    
    # Load sources config
    sources_config_path = project_root / "config" / "sources.yaml"
    config_manager = ConfigManager(config_path=sources_config_path)
    config_manager.load()
    sources = config_manager.get_sources_for_agent("news")
    
    # Create NewsAgent
    news_agent = NewsAgent(sources=sources)
    
    # Create SentimentAnalyzer  
    sentiment_analyzer = SentimentAnalyzer()
    
    # Create data fetchers
    historical_fetcher = HistoricalDataFetcher(news_agent=news_agent)
    outcome_fetcher = OutcomeFetcher()
    
    # Create epoch runner
    epoch_runner = EpochRunner(
        historical_fetcher=historical_fetcher,
        outcome_fetcher=outcome_fetcher,
        sentiment_analyzer=sentiment_analyzer,
    )
    
    # Create metrics calculator and report generator
    metrics_calculator = MetricsCalculator()
    report_generator = EvaluationReportGenerator()
    
    # Create multi-run evaluation runner
    multi_run_runner = MultiRunEvaluationRunner(
        epoch_runner=epoch_runner,
        metrics_calculator=metrics_calculator,
        report_generator=report_generator,
        config=eval_config,
    )
    
    print("Running evaluation for {} tickers across {} epochs with {} runs each...".format(
        len(tickers),
        eval_config.evaluation.num_epochs,
        eval_config.evaluation.runs_per_epoch,
    ))
    print("This may take several minutes...\n")
    
    # Run multi-ticker evaluation
    aggregated_report = await multi_run_runner.run_multi_ticker_evaluation(tickers)
    
    # Generate and save HTML report
    print("\n" + "=" * 60)
    print("GENERATING STATISTICAL REPORT")
    print("=" * 60)
    
    stat_report_generator = StatisticalReportGenerator()
    output_dir = eval_config.report.output_directory
    report_path = stat_report_generator.save_report(aggregated_report, output_dir)
    
    print(f"\n{'='*60}")
    print(f"Statistical HTML report saved to: {report_path}")
    print(f"{'='*60}\n")
    
    # Print summary
    print("Summary for All Tickers:")
    print("-" * 80)
    for ticker, stats in sorted(aggregated_report.ticker_statistics.items()):
        accuracy_pct = stats.mean_accuracy * 100
        std_pct = stats.std_accuracy * 100
        print(f"  {ticker}: {accuracy_pct:.1f}% ± {std_pct:.1f}% accuracy "
              f"({stats.completed_runs}/{stats.total_runs} runs completed)")
    
    # Close resources
    await news_agent.close()
    
    print("\n✓ Evaluation complete!")


if __name__ == "__main__":
    asyncio.run(main())