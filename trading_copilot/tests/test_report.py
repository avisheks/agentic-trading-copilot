"""Tests for Text Report Generator."""

from datetime import datetime, timezone

import pytest

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
from trading_copilot.report import TextReportGenerator, print_report


class TestTextReportGenerator:
    """Unit tests for TextReportGenerator."""

    def setup_method(self):
        self.generator = TextReportGenerator()

    def _create_sentiment_result(
        self,
        ticker: str = "AAPL",
        sentiment: Sentiment = Sentiment.BULLISH,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        num_articles: int = 5,
    ) -> SentimentResult:
        """Helper to create a SentimentResult for testing."""
        now = datetime.now(timezone.utc)

        articles = [
            NewsArticle(
                headline=f"Test headline {i}",
                source="Test Source",
                published_at=now,
                summary=f"Test summary {i}",
                url=f"https://test.com/{i}",
                sentiment=ArticleSentiment.POSITIVE if i % 2 == 0 else ArticleSentiment.NEGATIVE,
            )
            for i in range(num_articles)
        ]

        news_output = NewsOutput(
            ticker=ticker,
            articles=articles,
            retrieved_at=now,
            status="success",
        )

        aggregated = AggregatedReport(
            ticker=ticker,
            news=news_output,
            earnings=None,
            macro=None,
            aggregated_at=now,
            missing_components=[AgentType.EARNINGS, AgentType.MACRO],
        )

        signals = [
            Signal(
                source=AgentType.NEWS,
                direction=sentiment,
                strength=0.7,
                reasoning="Based on news analysis",
            )
        ]

        return SentimentResult(
            ticker=ticker,
            sentiment=sentiment,
            confidence=confidence,
            signals=signals,
            summary=f"Overall outlook for {ticker} is {sentiment.value}.",
            key_factors=["Positive news coverage", "Strong market sentiment"],
            risks=["Market volatility", "Missing earnings data"],
            disclaimer="This is not financial advice.",
            analyzed_at=now,
            aggregated_report=aggregated,
        )

    def test_generate_returns_string(self):
        """Generate returns a non-empty string."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_contains_ticker(self):
        """Report contains the ticker symbol."""
        result = self._create_sentiment_result(ticker="MSFT")
        report = self.generator.generate(result)

        assert "MSFT" in report

    def test_report_contains_executive_summary(self):
        """Report contains executive summary section."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        assert "EXECUTIVE SUMMARY" in report

    def test_report_contains_news_analysis(self):
        """Report contains news analysis section."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        assert "NEWS ANALYSIS" in report

    def test_report_contains_sentiment_recommendation(self):
        """Report contains sentiment recommendation section."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        assert "SENTIMENT RECOMMENDATION" in report

    def test_report_contains_disclaimer(self):
        """Report contains disclaimer section."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        assert "DISCLAIMER" in report
        assert "not financial advice" in report.lower()

    def test_report_shows_bullish_sentiment(self):
        """Report shows bullish sentiment correctly."""
        result = self._create_sentiment_result(sentiment=Sentiment.BULLISH)
        report = self.generator.generate(result)

        assert "BULLISH" in report

    def test_report_shows_bearish_sentiment(self):
        """Report shows bearish sentiment correctly."""
        result = self._create_sentiment_result(sentiment=Sentiment.BEARISH)
        report = self.generator.generate(result)

        assert "BEARISH" in report

    def test_report_shows_confidence_level(self):
        """Report shows confidence level."""
        result = self._create_sentiment_result(confidence=ConfidenceLevel.HIGH)
        report = self.generator.generate(result)

        assert "HIGH" in report

    def test_report_shows_key_factors(self):
        """Report shows key factors."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        assert "Key Factors" in report
        assert "Positive news coverage" in report

    def test_report_shows_risks(self):
        """Report shows risks."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        assert "Risks to Consider" in report
        assert "Market volatility" in report

    def test_report_shows_article_count(self):
        """Report shows article count."""
        result = self._create_sentiment_result(num_articles=10)
        report = self.generator.generate(result)

        assert "Articles analyzed: 10" in report

    def test_report_shows_sentiment_breakdown(self):
        """Report shows positive/negative/neutral breakdown."""
        result = self._create_sentiment_result(num_articles=6)
        report = self.generator.generate(result)

        assert "Positive:" in report
        assert "Negative:" in report
        assert "Neutral:" in report

    def test_report_shows_headlines(self):
        """Report shows recent headlines."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        assert "Recent Headlines" in report
        assert "Test headline" in report

    def test_report_handles_no_news(self):
        """Report handles missing news data gracefully."""
        now = datetime.now(timezone.utc)

        aggregated = AggregatedReport(
            ticker="AAPL",
            news=None,
            earnings=None,
            macro=None,
            aggregated_at=now,
            missing_components=[AgentType.NEWS],
        )

        result = SentimentResult(
            ticker="AAPL",
            sentiment=Sentiment.BEARISH,
            confidence=ConfidenceLevel.LOW,
            signals=[],
            summary="Limited data available.",
            key_factors=["No data"],
            risks=["Missing news data"],
            disclaimer="This is not financial advice.",
            analyzed_at=now,
            aggregated_report=aggregated,
        )

        report = self.generator.generate(result)

        assert "No recent news data available" in report

    def test_report_shows_partial_data_warning(self):
        """Report shows warning for partial data."""
        now = datetime.now(timezone.utc)

        news_output = NewsOutput(
            ticker="AAPL",
            articles=[
                NewsArticle(
                    headline="Test",
                    source="Test",
                    published_at=now,
                    summary="Test",
                    url="https://test.com",
                    sentiment=ArticleSentiment.NEUTRAL,
                )
            ],
            retrieved_at=now,
            status="partial",
        )

        aggregated = AggregatedReport(
            ticker="AAPL",
            news=news_output,
            earnings=None,
            macro=None,
            aggregated_at=now,
            missing_components=[],
        )

        result = SentimentResult(
            ticker="AAPL",
            sentiment=Sentiment.BULLISH,
            confidence=ConfidenceLevel.MEDIUM,
            signals=[],
            summary="Test summary",
            key_factors=["Test"],
            risks=["Test"],
            disclaimer="This is not financial advice.",
            analyzed_at=now,
            aggregated_report=aggregated,
        )

        report = self.generator.generate(result)

        assert "unavailable" in report.lower()

    def test_executive_summary_appears_before_details(self):
        """Executive summary appears before detailed sections."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        exec_pos = report.find("EXECUTIVE SUMMARY")
        news_pos = report.find("NEWS ANALYSIS")
        sentiment_pos = report.find("SENTIMENT RECOMMENDATION")

        assert exec_pos < news_pos
        assert exec_pos < sentiment_pos

    def test_disclaimer_appears_at_end(self):
        """Disclaimer appears at the end of the report."""
        result = self._create_sentiment_result()
        report = self.generator.generate(result)

        disclaimer_pos = report.find("DISCLAIMER")
        exec_pos = report.find("EXECUTIVE SUMMARY")
        news_pos = report.find("NEWS ANALYSIS")

        assert disclaimer_pos > exec_pos
        assert disclaimer_pos > news_pos


class TestPrintReport:
    """Tests for print_report function."""

    def test_print_report_outputs_to_console(self, capsys):
        """print_report outputs to console."""
        now = datetime.now(timezone.utc)

        aggregated = AggregatedReport(
            ticker="AAPL",
            news=None,
            earnings=None,
            macro=None,
            aggregated_at=now,
            missing_components=[],
        )

        result = SentimentResult(
            ticker="AAPL",
            sentiment=Sentiment.BULLISH,
            confidence=ConfidenceLevel.MEDIUM,
            signals=[],
            summary="Test summary",
            key_factors=["Test"],
            risks=["Test"],
            disclaimer="This is not financial advice.",
            analyzed_at=now,
            aggregated_report=aggregated,
        )

        print_report(result)

        captured = capsys.readouterr()
        assert "AAPL" in captured.out
        assert "EXECUTIVE SUMMARY" in captured.out
