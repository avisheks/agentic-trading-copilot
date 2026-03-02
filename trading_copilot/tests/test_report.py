"""Tests for the text report generator."""

import pytest
from datetime import datetime, timezone

from trading_copilot.models import (
    AgentType,
    AggregatedReport,
    ArticleSentiment,
    ConfidenceLevel,
    NewsArticle,
    NewsOutput,
    Sentiment,
    SentimentResult,
    Signal,
)
from trading_copilot.report import TextReportGenerator


class TestGenerateTable:
    """Tests for generate_table method."""

    @pytest.fixture
    def generator(self):
        """Create a TextReportGenerator instance."""
        return TextReportGenerator()

    @pytest.fixture
    def sample_results(self):
        """Create sample sentiment results for multiple tickers."""
        results = []
        for ticker, sentiment, confidence in [
            ("AAPL", Sentiment.BULLISH, ConfidenceLevel.HIGH),
            ("GOOGL", Sentiment.BEARISH, ConfidenceLevel.MEDIUM),
            ("MSFT", Sentiment.BULLISH, ConfidenceLevel.LOW),
        ]:
            news = NewsOutput(
                ticker=ticker,
                articles=[
                    NewsArticle(
                        headline=f"{ticker} news headline",
                        source="Reuters",
                        published_at=datetime(2026, 2, 25, 10, 0, tzinfo=timezone.utc),
                        summary="Summary",
                        url="https://example.com",
                        sentiment=ArticleSentiment.POSITIVE,
                    )
                ],
                retrieved_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
                status="success",
            )
            aggregated = AggregatedReport(
                ticker=ticker,
                news=news,
                earnings=None,
                macro=None,
                reddit=None,
                aggregated_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
                missing_components=[AgentType.EARNINGS, AgentType.MACRO],
            )
            result = SentimentResult(
                ticker=ticker,
                sentiment=sentiment,
                confidence=confidence,
                signals=[
                    Signal(
                        source=AgentType.NEWS,
                        direction=sentiment,
                        strength=0.7,
                        reasoning=f"Based on {ticker} news analysis.",
                    )
                ],
                summary=f"Outlook for {ticker}.",
                key_factors=["News coverage"],
                risks=["Market volatility"],
                disclaimer="Not financial advice.",
                analyzed_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
                aggregated_report=aggregated,
            )
            results.append(result)
        return results

    def test_generate_table_returns_string(self, generator, sample_results):
        """Test that generate_table returns a non-empty string."""
        table = generator.generate_table(sample_results)
        assert isinstance(table, str)
        assert len(table) > 0

    def test_generate_table_contains_all_tickers(self, generator, sample_results):
        """Test that table contains all ticker symbols."""
        table = generator.generate_table(sample_results)
        assert "AAPL" in table
        assert "GOOGL" in table
        assert "MSFT" in table

    def test_generate_table_contains_header(self, generator, sample_results):
        """Test that table contains header row."""
        table = generator.generate_table(sample_results)
        assert "TICKER" in table
        assert "SENTIMENT" in table
        assert "CONFIDENCE" in table

    def test_generate_table_shows_sentiment_values(self, generator, sample_results):
        """Test that table shows sentiment values."""
        table = generator.generate_table(sample_results)
        assert "BULLISH" in table
        assert "BEARISH" in table

    def test_generate_table_shows_confidence_values(self, generator, sample_results):
        """Test that table shows confidence values."""
        table = generator.generate_table(sample_results)
        assert "HIGH" in table
        assert "MEDIUM" in table
        assert "LOW" in table

    def test_generate_table_shows_news_count(self, generator, sample_results):
        """Test that table shows news article count."""
        table = generator.generate_table(sample_results)
        # Each ticker has 1 article
        lines = table.split("\n")
        data_lines = [l for l in lines if "AAPL" in l or "GOOGL" in l or "MSFT" in l]
        for line in data_lines:
            assert "1" in line  # 1 article per ticker

    def test_generate_table_shows_total_count(self, generator, sample_results):
        """Test that table shows total tickers analyzed."""
        table = generator.generate_table(sample_results)
        assert "Total tickers analyzed: 3" in table

    def test_generate_table_contains_disclaimer(self, generator, sample_results):
        """Test that table contains disclaimer."""
        table = generator.generate_table(sample_results)
        assert "DISCLAIMER" in table
        assert "not financial advice" in table

    def test_generate_table_empty_list(self, generator):
        """Test generate_table with empty list."""
        table = generator.generate_table([])
        assert "No results to display" in table

    def test_generate_table_single_result(self, generator, sample_results):
        """Test generate_table with single result."""
        table = generator.generate_table([sample_results[0]])
        assert "AAPL" in table
        assert "Total tickers analyzed: 1" in table


class TestGenerateFullReport:
    """Tests for generate_full_report method."""

    @pytest.fixture
    def generator(self):
        """Create a TextReportGenerator instance."""
        return TextReportGenerator()

    @pytest.fixture
    def sample_results(self):
        """Create sample sentiment results for multiple tickers."""
        results = []
        for ticker, sentiment, confidence in [
            ("AAPL", Sentiment.BULLISH, ConfidenceLevel.HIGH),
            ("GOOGL", Sentiment.BEARISH, ConfidenceLevel.MEDIUM),
        ]:
            news = NewsOutput(
                ticker=ticker,
                articles=[
                    NewsArticle(
                        headline=f"{ticker} news headline",
                        source="Reuters",
                        published_at=datetime(2026, 2, 25, 10, 0, tzinfo=timezone.utc),
                        summary="Summary",
                        url="https://example.com",
                        sentiment=ArticleSentiment.POSITIVE,
                    )
                ],
                retrieved_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
                status="success",
            )
            aggregated = AggregatedReport(
                ticker=ticker,
                news=news,
                earnings=None,
                macro=None,
                reddit=None,
                aggregated_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
                missing_components=[AgentType.EARNINGS, AgentType.MACRO],
            )
            result = SentimentResult(
                ticker=ticker,
                sentiment=sentiment,
                confidence=confidence,
                signals=[
                    Signal(
                        source=AgentType.NEWS,
                        direction=sentiment,
                        strength=0.7,
                        reasoning=f"Based on {ticker} news analysis.",
                    )
                ],
                summary=f"Outlook for {ticker}.",
                key_factors=["News coverage"],
                risks=["Market volatility"],
                disclaimer="Not financial advice.",
                analyzed_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
                aggregated_report=aggregated,
            )
            results.append(result)
        return results

    def test_full_report_contains_summary_table(self, generator, sample_results):
        """Test that full report contains summary table."""
        report = generator.generate_full_report(sample_results)
        assert "TRADING COPILOT SUMMARY TABLE" in report
        assert "TICKER" in report
        assert "SENTIMENT" in report

    def test_full_report_contains_detailed_section_header(self, generator, sample_results):
        """Test that full report contains detailed analysis header."""
        report = generator.generate_full_report(sample_results)
        assert "DETAILED ANALYSIS BY TICKER" in report

    def test_full_report_contains_all_ticker_details(self, generator, sample_results):
        """Test that full report contains detailed reports for all tickers."""
        report = generator.generate_full_report(sample_results)
        assert "Ticker: AAPL" in report
        assert "Ticker: GOOGL" in report

    def test_full_report_contains_executive_summaries(self, generator, sample_results):
        """Test that full report contains executive summaries."""
        report = generator.generate_full_report(sample_results)
        assert "EXECUTIVE SUMMARY" in report
        assert "Outlook for AAPL" in report
        assert "Outlook for GOOGL" in report

    def test_full_report_contains_news_findings(self, generator, sample_results):
        """Test that full report contains news findings sections."""
        report = generator.generate_full_report(sample_results)
        assert "NEWS FINDINGS" in report

    def test_full_report_contains_single_disclaimer(self, generator, sample_results):
        """Test that full report has disclaimer at the end only."""
        report = generator.generate_full_report(sample_results)
        # Should have exactly one disclaimer at the end
        assert report.count("DISCLAIMER") == 1
        assert report.rstrip().endswith("=" * 60)

    def test_full_report_table_before_details(self, generator, sample_results):
        """Test that summary table appears before detailed reports."""
        report = generator.generate_full_report(sample_results)
        table_pos = report.find("TRADING COPILOT SUMMARY TABLE")
        details_pos = report.find("DETAILED ANALYSIS BY TICKER")
        assert table_pos < details_pos

    def test_full_report_empty_list(self, generator):
        """Test generate_full_report with empty list."""
        report = generator.generate_full_report([])
        assert "No results to display" in report


class TestTextReportGenerator:
    """Tests for TextReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a TextReportGenerator instance."""
        return TextReportGenerator()

    @pytest.fixture
    def sample_news_output(self):
        """Create sample news output."""
        return NewsOutput(
            ticker="AAPL",
            articles=[
                NewsArticle(
                    headline="Apple Reports Strong Q4 Earnings",
                    source="Reuters",
                    published_at=datetime(2026, 2, 25, 10, 0, tzinfo=timezone.utc),
                    summary="Apple exceeded analyst expectations.",
                    url="https://example.com/1",
                    sentiment=ArticleSentiment.POSITIVE,
                ),
                NewsArticle(
                    headline="iPhone Sales Beat Estimates",
                    source="Bloomberg",
                    published_at=datetime(2026, 2, 24, 14, 0, tzinfo=timezone.utc),
                    summary="iPhone sales surpassed forecasts.",
                    url="https://example.com/2",
                    sentiment=ArticleSentiment.POSITIVE,
                ),
            ],
            retrieved_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
            status="success",
        )

    @pytest.fixture
    def sample_aggregated_report(self, sample_news_output):
        """Create sample aggregated report."""
        return AggregatedReport(
            ticker="AAPL",
            news=sample_news_output,
            earnings=None,
            macro=None,
            reddit=None,
            aggregated_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
            missing_components=[AgentType.EARNINGS, AgentType.MACRO],
        )

    @pytest.fixture
    def sample_sentiment_result(self, sample_aggregated_report):
        """Create sample sentiment result."""
        return SentimentResult(
            ticker="AAPL",
            sentiment=Sentiment.BULLISH,
            confidence=ConfidenceLevel.MEDIUM,
            signals=[
                Signal(
                    source=AgentType.NEWS,
                    direction=Sentiment.BULLISH,
                    strength=0.67,
                    reasoning="Based on 2 news articles: 2 positive.",
                )
            ],
            summary="Overall outlook for AAPL is bullish.",
            key_factors=["Positive news coverage (2/2 articles)"],
            risks=["Incomplete analysis: missing earnings, macro data"],
            disclaimer="This is not financial advice.",
            analyzed_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
            aggregated_report=sample_aggregated_report,
        )

    def test_generate_returns_string(self, generator, sample_sentiment_result):
        """Test that generate returns a non-empty string."""
        report = generator.generate(sample_sentiment_result)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_contains_ticker(self, generator, sample_sentiment_result):
        """Test that report contains the ticker symbol."""
        report = generator.generate(sample_sentiment_result)
        assert "AAPL" in report

    def test_report_contains_executive_summary(self, generator, sample_sentiment_result):
        """Test that report contains executive summary section."""
        report = generator.generate(sample_sentiment_result)
        assert "EXECUTIVE SUMMARY" in report

    def test_report_contains_news_findings(self, generator, sample_sentiment_result):
        """Test that report contains news findings section."""
        report = generator.generate(sample_sentiment_result)
        assert "NEWS FINDINGS" in report

    def test_report_contains_sentiment_recommendation(self, generator, sample_sentiment_result):
        """Test that report contains sentiment recommendation section."""
        report = generator.generate(sample_sentiment_result)
        assert "SENTIMENT RECOMMENDATION" in report

    def test_report_contains_disclaimer(self, generator, sample_sentiment_result):
        """Test that report contains disclaimer section."""
        report = generator.generate(sample_sentiment_result)
        assert "DISCLAIMER" in report
        assert "not financial advice" in report

    def test_report_shows_sentiment(self, generator, sample_sentiment_result):
        """Test that report displays sentiment correctly."""
        report = generator.generate(sample_sentiment_result)
        assert "BULLISH" in report

    def test_report_shows_confidence(self, generator, sample_sentiment_result):
        """Test that report displays confidence level."""
        report = generator.generate(sample_sentiment_result)
        assert "MEDIUM" in report

    def test_report_shows_key_factors(self, generator, sample_sentiment_result):
        """Test that report displays key factors."""
        report = generator.generate(sample_sentiment_result)
        assert "Positive news coverage" in report

    def test_report_shows_risks(self, generator, sample_sentiment_result):
        """Test that report displays risks."""
        report = generator.generate(sample_sentiment_result)
        assert "missing earnings" in report

    def test_report_shows_news_statistics(self, generator, sample_sentiment_result):
        """Test that report shows news article statistics."""
        report = generator.generate(sample_sentiment_result)
        assert "Articles analyzed: 2" in report
        assert "Positive: 2" in report

    def test_report_shows_headlines(self, generator, sample_sentiment_result):
        """Test that report shows article headlines."""
        report = generator.generate(sample_sentiment_result)
        assert "Apple Reports Strong Q4 Earnings" in report
        assert "Reuters" in report

    def test_report_shows_signal_analysis(self, generator, sample_sentiment_result):
        """Test that report shows signal analysis."""
        report = generator.generate(sample_sentiment_result)
        assert "Signal Analysis" in report
        assert "News:" in report
        assert "67%" in report

    def test_executive_summary_appears_first(self, generator, sample_sentiment_result):
        """Test that executive summary appears before other sections."""
        report = generator.generate(sample_sentiment_result)
        exec_pos = report.find("EXECUTIVE SUMMARY")
        news_pos = report.find("NEWS FINDINGS")
        sentiment_pos = report.find("SENTIMENT RECOMMENDATION")
        disclaimer_pos = report.find("DISCLAIMER")

        assert exec_pos < news_pos
        assert news_pos < sentiment_pos
        assert sentiment_pos < disclaimer_pos

    def test_report_with_no_news(self, generator, sample_aggregated_report):
        """Test report generation when no news data available."""
        sample_aggregated_report.news = NewsOutput(
            ticker="AAPL",
            articles=[],
            retrieved_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
            status="no_data",
        )

        result = SentimentResult(
            ticker="AAPL",
            sentiment=Sentiment.BEARISH,
            confidence=ConfidenceLevel.LOW,
            signals=[],
            summary="Analysis for AAPL is inconclusive.",
            key_factors=["Limited data available"],
            risks=["No recent news data available"],
            disclaimer="This is not financial advice.",
            analyzed_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
            aggregated_report=sample_aggregated_report,
        )

        report = generator.generate(result)
        assert "No recent news data available" in report

    def test_bearish_sentiment_display(self, generator, sample_aggregated_report):
        """Test that bearish sentiment is displayed correctly."""
        result = SentimentResult(
            ticker="AAPL",
            sentiment=Sentiment.BEARISH,
            confidence=ConfidenceLevel.HIGH,
            signals=[
                Signal(
                    source=AgentType.NEWS,
                    direction=Sentiment.BEARISH,
                    strength=0.8,
                    reasoning="Negative news dominates.",
                )
            ],
            summary="Outlook is bearish.",
            key_factors=["Negative coverage"],
            risks=["Market volatility"],
            disclaimer="This is not financial advice.",
            analyzed_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
            aggregated_report=sample_aggregated_report,
        )

        report = generator.generate(result)
        assert "BEARISH" in report
        assert "HIGH" in report
