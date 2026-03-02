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
