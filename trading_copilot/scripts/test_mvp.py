#!/usr/bin/env python3
"""
End-to-end MVP test script for Trading Copilot.

Tests the complete pipeline:
1. Ticker validation
2. News agent research (with real API or mock data)
3. Sentiment analysis
4. Report generation

Usage:
    python scripts/test_mvp.py [--ticker TICKER] [--mock]
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trading_copilot.agents.news import NewsAgent
from trading_copilot.analyzer import SentimentAnalyzer
from trading_copilot.config import ConfigManager
from trading_copilot.models import (
    AgentType,
    AggregatedReport,
    ArticleSentiment,
    NewsArticle,
    NewsOutput,
)
from trading_copilot.report import TextReportGenerator
from trading_copilot.validator import TickerValidator


def create_mock_news_output(ticker: str) -> NewsOutput:
    """Create mock news data for testing without API keys."""
    now = datetime.now(timezone.utc)
    
    mock_articles = [
        NewsArticle(
            headline=f"{ticker} Reports Strong Q4 Earnings, Beats Expectations",
            source="Financial Times",
            published_at=now - timedelta(days=1),
            summary=f"{ticker} exceeded analyst expectations with record revenue growth driven by strong product demand.",
            url="https://example.com/article1",
            sentiment=ArticleSentiment.POSITIVE,
        ),
        NewsArticle(
            headline=f"Analysts Upgrade {ticker} Stock to Buy Rating",
            source="Bloomberg",
            published_at=now - timedelta(days=2),
            summary=f"Multiple Wall Street analysts have upgraded {ticker} citing strong fundamentals and growth potential.",
            url="https://example.com/article2",
            sentiment=ArticleSentiment.POSITIVE,
        ),
        NewsArticle(
            headline=f"{ticker} Announces New Product Launch for 2025",
            source="Reuters",
            published_at=now - timedelta(days=3),
            summary=f"{ticker} unveiled plans for an innovative new product line expected to drive future growth.",
            url="https://example.com/article3",
            sentiment=ArticleSentiment.POSITIVE,
        ),
        NewsArticle(
            headline=f"Market Volatility Affects Tech Stocks Including {ticker}",
            source="CNBC",
            published_at=now - timedelta(days=5),
            summary="Broader market uncertainty has led to fluctuations in tech sector valuations.",
            url="https://example.com/article4",
            sentiment=ArticleSentiment.NEUTRAL,
        ),
        NewsArticle(
            headline=f"Supply Chain Concerns May Impact {ticker} Production",
            source="Wall Street Journal",
            published_at=now - timedelta(days=7),
            summary="Industry analysts warn of potential supply chain disruptions affecting tech manufacturers.",
            url="https://example.com/article5",
            sentiment=ArticleSentiment.NEGATIVE,
        ),
    ]
    
    return NewsOutput(
        ticker=ticker,
        articles=mock_articles,
        retrieved_at=now,
        status="success",
        error_message=None,
    )


async def run_mvp_test(ticker: str = "AAPL", use_mock: bool = False):
    """Run the complete MVP pipeline."""
    print("=" * 60)
    print("TRADING COPILOT MVP TEST")
    print("=" * 60)
    print()
    
    # Step 1: Validate ticker
    print("Step 1: Validating ticker...")
    validator = TickerValidator()
    result = validator.validate(ticker)
    
    if not result.is_valid:
        print(f"  ERROR: {result.error_message}")
        return False
    
    normalized_ticker = result.normalized_ticker
    print(f"  ✓ Ticker '{ticker}' validated and normalized to '{normalized_ticker}'")
    print()
    
    # Step 2: Fetch news
    print("Step 2: Fetching news data...")
    
    if use_mock:
        print("  Using mock data (no API keys required)")
        news_output = create_mock_news_output(normalized_ticker)
    else:
        # Check for API keys
        has_alpha_vantage = bool(os.environ.get("ALPHA_VANTAGE_API_KEY"))
        has_finnhub = bool(os.environ.get("FINNHUB_API_KEY"))
        
        if not has_alpha_vantage and not has_finnhub:
            print("  WARNING: No API keys found. Using mock data.")
            print("  Set ALPHA_VANTAGE_API_KEY or FINNHUB_API_KEY for real data.")
            news_output = create_mock_news_output(normalized_ticker)
        else:
            print(f"  API keys found: Alpha Vantage={has_alpha_vantage}, Finnhub={has_finnhub}")
            
            # Load config and create news agent
            config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
            config_manager = ConfigManager(config_path)
            config = config_manager.load()
            
            news_sources = config_manager.get_sources_for_agent("news")
            news_agent = NewsAgent(news_sources)
            
            try:
                news_output = await news_agent.research(normalized_ticker)
            finally:
                await news_agent.close()
    
    print(f"  ✓ Retrieved {len(news_output.articles)} articles")
    print(f"  Status: {news_output.status}")
    if news_output.error_message:
        print(f"  Note: {news_output.error_message}")
    print()
    
    # Step 3: Create aggregated report
    print("Step 3: Creating aggregated report...")
    aggregated = AggregatedReport(
        ticker=normalized_ticker,
        news=news_output,
        earnings=None,  # Not implemented yet
        macro=None,     # Not implemented yet
        aggregated_at=datetime.now(timezone.utc),
        missing_components=[AgentType.EARNINGS, AgentType.MACRO],
    )
    print(f"  ✓ Aggregated report created")
    print(f"  Missing components: {[c.value for c in aggregated.missing_components]}")
    print()
    
    # Step 4: Analyze sentiment
    print("Step 4: Analyzing sentiment...")
    analyzer = SentimentAnalyzer()
    sentiment_result = analyzer.analyze(aggregated)
    
    print(f"  ✓ Sentiment: {sentiment_result.sentiment.value.upper()}")
    print(f"  ✓ Confidence: {sentiment_result.confidence.value.upper()}")
    print()
    
    # Step 5: Generate report
    print("Step 5: Generating report...")
    report_generator = TextReportGenerator()
    report = report_generator.generate(sentiment_result)
    
    print("  ✓ Report generated successfully")
    print()
    
    # Display the report
    print("=" * 60)
    print("GENERATED REPORT")
    print("=" * 60)
    print()
    print(report)
    
    return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Trading Copilot MVP")
    parser.add_argument("--ticker", default="AAPL", help="Stock ticker to analyze")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of real APIs")
    args = parser.parse_args()
    
    success = asyncio.run(run_mvp_test(args.ticker, args.mock))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
