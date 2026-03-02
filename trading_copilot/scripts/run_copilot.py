#!/usr/bin/env python3
"""
Complete end-to-end runner for Trading Copilot.

Processes all tickers from app_config.yaml and sends email report if configured.

Usage:
    python scripts/run_copilot.py [--config PATH] [--mock]
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trading_copilot.agents.news import NewsAgent
from trading_copilot.agents.reddit import RedditAgent
from trading_copilot.analyzer import SentimentAnalyzer
from trading_copilot.config import AppConfigManager, ConfigManager
from trading_copilot.email_service import EmailService, SMTPConfig
from trading_copilot.html_report import HTMLReportGenerator
from trading_copilot.models import (
    AgentType,
    AggregatedReport,
    ArticleSentiment,
    NewsArticle,
    NewsOutput,
    RedditOutput,
    SentimentResult,
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


async def process_ticker(
    ticker: str, 
    use_mock: bool, 
    news_agent: NewsAgent | None,
    reddit_agent: RedditAgent | None,
    validator: TickerValidator,
    analyzer: SentimentAnalyzer
) -> SentimentResult | None:
    """Process a single ticker and return sentiment result."""
    # Validate ticker
    result = validator.validate(ticker)
    
    if not result.is_valid:
        print(f"  ✗ {ticker}: {result.error_message}")
        return None
    
    normalized_ticker = result.normalized_ticker
    print(f"  ✓ {ticker} validated as {normalized_ticker}")
    
    # Fetch news
    if use_mock:
        news_output = create_mock_news_output(normalized_ticker)
    else:
        try:
            news_output = await news_agent.research(normalized_ticker)
        except Exception as e:
            print(f"  ✗ {normalized_ticker}: Error fetching news - {e}")
            return None
    
    # Fetch Reddit data concurrently
    reddit_output: RedditOutput | None = None
    if reddit_agent and not use_mock:
        try:
            reddit_output = await reddit_agent.research(normalized_ticker)
        except Exception as e:
            print(f"  ⚠ {normalized_ticker}: Error fetching Reddit data - {e}")
            # Continue without Reddit data
    
    # Determine missing components
    missing_components = [AgentType.EARNINGS, AgentType.MACRO]
    if reddit_output is None or reddit_output.status in ("error", "no_data"):
        missing_components.append(AgentType.REDDIT)
    
    # Create aggregated report
    aggregated = AggregatedReport(
        ticker=normalized_ticker,
        news=news_output,
        earnings=None,
        macro=None,
        reddit=reddit_output,
        aggregated_at=datetime.now(timezone.utc),
        missing_components=missing_components,
    )
    
    # Analyze sentiment
    sentiment_result = analyzer.analyze(aggregated)
    
    return sentiment_result


async def run_copilot(use_mock: bool = False, config_path: Path = None):
    """Run the complete Trading Copilot pipeline."""
    print("=" * 60)
    print("TRADING COPILOT - FULL PIPELINE")
    print("=" * 60)
    print()
    
    # Load app config
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "app_config.yaml"
    
    try:
        app_config_manager = AppConfigManager(config_path)
        app_config = app_config_manager.load()
    except Exception as e:
        print(f"ERROR: Failed to load app config: {e}")
        return False
    
    tickers = app_config.tickers.symbols
    print(f"Tickers to analyze: {', '.join(tickers)}")
    print(f"Email delivery: {'ENABLED' if app_config.email.enabled else 'DISABLED'}")
    print(f"Report format: {app_config.report.format.upper()}")
    print()
    
    # Initialize components
    validator = TickerValidator()
    analyzer = SentimentAnalyzer()
    
    # Initialize news agent
    news_agent = None
    if not use_mock:
        # Check for API keys
        has_alpha_vantage = bool(os.environ.get("ALPHA_VANTAGE_API_KEY"))
        has_finnhub = bool(os.environ.get("FINNHUB_API_KEY"))
        
        if not has_alpha_vantage and not has_finnhub:
            print("INFO: No API keys found. Will use web search for news data.")
            print("(Set ALPHA_VANTAGE_API_KEY or FINNHUB_API_KEY for API access)")
            print()
        else:
            print(f"API keys found: Alpha Vantage={has_alpha_vantage}, Finnhub={has_finnhub}")
            print()
        
        # Load sources config and initialize agent (will use web search if no API keys)
        sources_config_path = Path(__file__).parent.parent / "config" / "sources.yaml"
        config_manager = ConfigManager(sources_config_path)
        config = config_manager.load()
        
        news_sources = config_manager.get_sources_for_agent("news")
        news_agent = NewsAgent(news_sources)
        
        # Initialize Reddit agent
        reddit_sources = config_manager.get_sources_for_agent("reddit")
        reddit_agent = RedditAgent(reddit_sources)
    
    if use_mock:
        print("Using MOCK data (no API keys required)")
        reddit_agent = None
    print()
    
    # Process all tickers
    print("Processing tickers...")
    results: list[SentimentResult] = []
    
    try:
        for ticker in tickers:
            result = await process_ticker(ticker, use_mock, news_agent, reddit_agent, validator, analyzer)
            if result:
                results.append(result)
        
        if not results:
            print()
            print("ERROR: No tickers were successfully processed.")
            return False
        
        print()
        print(f"Successfully processed {len(results)}/{len(tickers)} tickers")
        print()
        
        # Generate report
        print("Generating report...")
        if app_config.report.format == "html":
            report_generator = HTMLReportGenerator()
            report_content = report_generator.generate_full_report(results)
            content_type = "html"
        else:
            report_generator = TextReportGenerator()
            report_content = report_generator.generate_full_report(results)
            content_type = "text"
        
        print(f"  ✓ {content_type.upper()} report generated")
        print()
        
        # Save to file if configured
        if app_config.report.save_to_file and app_config.report.output_directory:
            output_dir = Path(app_config.report.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trading_copilot_report_{timestamp}.{'html' if content_type == 'html' else 'txt'}"
            output_path = output_dir / filename
            
            with open(output_path, 'w') as f:
                f.write(report_content)
            
            print(f"  ✓ Report saved to: {output_path}")
            print()
        
        # Display text report preview
        if content_type == "text":
            print("=" * 60)
            print("REPORT PREVIEW")
            print("=" * 60)
            print()
            print(report_content)
        
        # Send email if enabled
        if app_config.email.enabled:
            print("=" * 60)
            print("SENDING EMAIL REPORT")
            print("=" * 60)
            print()
            
            # Check for required email config
            if not all([
                app_config.email.smtp_host,
                app_config.email.smtp_port,
                app_config.email.smtp_username,
                app_config.email.from_email,
                app_config.email.to_emails,
            ]):
                print("ERROR: Email is enabled but configuration is incomplete.")
                print("Please check app_config.yaml email settings.")
                return False
            
            # Check for password environment variable
            if app_config.email.smtp_password_env:
                if not os.environ.get(app_config.email.smtp_password_env):
                    print(f"ERROR: Environment variable not set: {app_config.email.smtp_password_env}")
                    print("Set this variable with your SMTP password to send emails.")
                    return False
            
            # Create SMTP config
            smtp_config = SMTPConfig(
                host=app_config.email.smtp_host,
                port=app_config.email.smtp_port,
                username=app_config.email.smtp_username,
                password_env=app_config.email.smtp_password_env,
                from_email=app_config.email.from_email,
                use_tls=app_config.email.use_tls,
            )
            
            # Initialize email service
            email_service = EmailService(smtp_config)
            
            # Prepare email subject
            timestamp = datetime.now().strftime("%Y-%m-%d")
            subject = f"Trading Copilot Report - {timestamp}"
            
            # Send to all recipients
            success_count = 0
            for recipient in app_config.email.to_emails:
                print(f"Sending to {recipient}...")
                
                try:
                    delivery_result = await email_service.send_async(
                        to_email=recipient,
                        subject=subject,
                        html_content=report_content if content_type == "html" else f"<pre>{report_content}</pre>",
                    )
                    
                    if delivery_result.success:
                        print(f"  ✓ Email sent successfully")
                        success_count += 1
                    else:
                        print(f"  ✗ Failed to send: {delivery_result.error_message}")
                except Exception as e:
                    print(f"  ✗ Error: {e}")
            
            print()
            print(f"Email delivery: {success_count}/{len(app_config.email.to_emails)} successful")
            print()
        
        return True
        
    finally:
        # Clean up
        if news_agent:
            await news_agent.close()
        if reddit_agent:
            await reddit_agent.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Trading Copilot full pipeline")
    parser.add_argument("--config", default=None, help="Path to app_config.yaml")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of real APIs")
    args = parser.parse_args()
    
    config_path = Path(args.config) if args.config else None
    
    success = asyncio.run(run_copilot(args.mock, config_path))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()