"""Tests for HTML Report Generator."""

from datetime import datetime, timezone

import pytest

from trading_copilot.html_report import HTMLReportGenerator
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


def create_sample_news_article(
    headline: str = "Test headline",
    sentiment: ArticleSentiment = ArticleSentiment.NEUTRAL,
) -> NewsArticle:
    """Create a sample news article for testing."""
    return NewsArticle(
        headline=headline,
        source="Test Source",
        published_at=datetime.now(timezone.utc),
        summary="Test summary",
        url="https://test.com/article",
        sentiment=sentiment,
    )


def create_sample_sentiment_result(
    ticker: str = "AAPL",
    sentiment: Sentiment = Sentiment.BULLISH,
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
    articles: list[NewsArticle] | None = None,
    missing_components: list[AgentType] | None = None,
) -> SentimentResult:
    """Create a sample sentiment result for testing."""
    if articles is None:
        articles = [
            create_sample_news_article("Positive news", ArticleSentiment.POSITIVE),
            create_sample_news_article("Negative news", ArticleSentiment.NEGATIVE),
            create_sample_news_article("Neutral news", ArticleSentiment.NEUTRAL),
        ]

    news_output = NewsOutput(
        ticker=ticker,
        articles=articles,
        retrieved_at=datetime.now(timezone.utc),
        status="success",
    )

    return SentimentResult(
        ticker=ticker,
        sentiment=sentiment,
        confidence=confidence,
        signals=[
            Signal(
                source=AgentType.NEWS,
                direction=sentiment,
                strength=0.75,
                reasoning="Strong positive news sentiment",
            )
        ],
        summary="Test summary for the analysis",
        key_factors=["Factor 1", "Factor 2"],
        risks=["Risk 1", "Risk 2"],
        disclaimer="This is not financial advice. Always do your own research.",
        analyzed_at=datetime.now(timezone.utc),
        aggregated_report=AggregatedReport(
            ticker=ticker,
            news=news_output,
            earnings=None,
            macro=None,
            aggregated_at=datetime.now(timezone.utc),
            missing_components=missing_components or [],
        ),
    )


class TestHTMLReportGenerator:
    """Tests for HTMLReportGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = HTMLReportGenerator()

    def test_generate_returns_html_string(self):
        """generate() returns a valid HTML string."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html

    def test_report_contains_ticker(self):
        """Report contains the ticker symbol."""
        result = create_sample_sentiment_result(ticker="MSFT")
        html = self.generator.generate(result)

        assert "MSFT" in html

    def test_report_contains_executive_summary_section(self):
        """Report contains executive summary section."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert "executive-summary" in html
        assert "Executive Summary" in html

    def test_report_contains_news_findings_section(self):
        """Report contains news findings section."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert "news-findings" in html
        assert "News Findings" in html

    def test_report_contains_sentiment_recommendation_section(self):
        """Report contains sentiment recommendation section."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert "sentiment-recommendation" in html
        assert "Sentiment Recommendation" in html

    def test_report_contains_disclaimer(self):
        """Report contains disclaimer text."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert "not financial advice" in html.lower()

    def test_report_shows_bullish_sentiment(self):
        """Report displays bullish sentiment correctly."""
        result = create_sample_sentiment_result(sentiment=Sentiment.BULLISH)
        html = self.generator.generate(result)

        assert "BULLISH" in html
        assert "sentiment-bullish" in html

    def test_report_shows_bearish_sentiment(self):
        """Report displays bearish sentiment correctly."""
        result = create_sample_sentiment_result(sentiment=Sentiment.BEARISH)
        html = self.generator.generate(result)

        assert "BEARISH" in html
        assert "sentiment-bearish" in html

    def test_report_shows_confidence_level(self):
        """Report displays confidence level."""
        result = create_sample_sentiment_result(confidence=ConfidenceLevel.HIGH)
        html = self.generator.generate(result)

        assert "HIGH" in html
        assert "confidence-high" in html

    def test_report_shows_key_factors(self):
        """Report displays key factors."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert "Factor 1" in html
        assert "Factor 2" in html

    def test_report_shows_risks(self):
        """Report displays risks."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert "Risk 1" in html
        assert "Risk 2" in html

    def test_report_shows_news_statistics(self):
        """Report displays news article statistics."""
        articles = [
            create_sample_news_article("Pos 1", ArticleSentiment.POSITIVE),
            create_sample_news_article("Pos 2", ArticleSentiment.POSITIVE),
            create_sample_news_article("Neg 1", ArticleSentiment.NEGATIVE),
            create_sample_news_article("Neutral 1", ArticleSentiment.NEUTRAL),
        ]
        result = create_sample_sentiment_result(articles=articles)
        html = self.generator.generate(result)

        # Should show total count
        assert "4" in html  # Total articles
        assert "stat-positive" in html
        assert "stat-negative" in html

    def test_report_shows_article_headlines(self):
        """Report displays article headlines."""
        articles = [
            create_sample_news_article("Apple Stock Surges on Earnings Beat"),
        ]
        result = create_sample_sentiment_result(articles=articles)
        html = self.generator.generate(result)

        assert "Apple Stock Surges on Earnings Beat" in html

    def test_report_shows_signal_analysis(self):
        """Report displays signal analysis."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert "Signal Analysis" in html
        assert "75%" in html  # Signal strength
        assert "Strong positive news sentiment" in html

    def test_executive_summary_appears_before_news(self):
        """Executive summary section appears before news findings."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        exec_pos = html.find("executive-summary")
        news_pos = html.find("news-findings")

        assert exec_pos < news_pos

    def test_report_is_mobile_responsive(self):
        """Report includes mobile-responsive CSS."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert "viewport" in html
        assert "@media" in html
        assert "max-width: 600px" in html


class TestHTMLReportErrorIndication:
    """Tests for error indication in HTML reports (Property 14)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = HTMLReportGenerator()

    def test_missing_news_shows_error_indicator(self):
        """Missing news component shows error indicator."""
        result = create_sample_sentiment_result(
            articles=[],
            missing_components=[AgentType.NEWS],
        )
        # Clear the news output to simulate missing data
        result.aggregated_report.news = None

        html = self.generator.generate(result)

        assert "missing-section" in html
        assert "News Data Unavailable" in html

    def test_missing_earnings_shows_error_indicator(self):
        """Missing earnings component shows error indicator."""
        result = create_sample_sentiment_result(
            missing_components=[AgentType.EARNINGS],
        )
        html = self.generator.generate(result)

        assert "Earnings Data Unavailable" in html

    def test_missing_macro_shows_error_indicator(self):
        """Missing macro component shows error indicator."""
        result = create_sample_sentiment_result(
            missing_components=[AgentType.MACRO],
        )
        html = self.generator.generate(result)

        assert "Macro Data Unavailable" in html

    def test_multiple_missing_components_show_all_errors(self):
        """Multiple missing components all show error indicators."""
        result = create_sample_sentiment_result(
            missing_components=[AgentType.EARNINGS, AgentType.MACRO],
        )
        html = self.generator.generate(result)

        assert "Earnings Data Unavailable" in html
        assert "Macro Data Unavailable" in html


class TestHTMLReportStructure:
    """Tests for HTML report structure (Property 13)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = HTMLReportGenerator()

    def test_report_is_valid_html(self):
        """Report is valid HTML with proper structure."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert html.startswith("<!DOCTYPE html>")
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html

    def test_report_has_distinct_sections(self):
        """Report has distinct section elements."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        # Count section elements
        section_count = html.count('<section class="section"')
        assert section_count >= 3  # At least executive summary, news, sentiment

    def test_report_sections_have_ids(self):
        """Report sections have unique IDs."""
        result = create_sample_sentiment_result()
        html = self.generator.generate(result)

        assert 'id="executive-summary"' in html
        assert 'id="news-findings"' in html
        assert 'id="sentiment-recommendation"' in html

    def test_report_has_proper_title(self):
        """Report has proper HTML title."""
        result = create_sample_sentiment_result(ticker="GOOGL")
        html = self.generator.generate(result)

        assert "<title>" in html
        assert "GOOGL" in html


class TestHTMLReportMultiple:
    """Tests for multi-result HTML reports."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = HTMLReportGenerator()

    def test_generate_multi_empty_list(self):
        """generate_multi() handles empty list."""
        html = self.generator.generate_multi([])

        assert "No Results Available" in html

    def test_generate_multi_single_result(self):
        """generate_multi() handles single result."""
        result = create_sample_sentiment_result(ticker="AAPL")
        html = self.generator.generate_multi([result])

        assert "AAPL" in html

    def test_generate_multi_multiple_results(self):
        """generate_multi() handles multiple results."""
        results = [
            create_sample_sentiment_result(ticker="AAPL"),
            create_sample_sentiment_result(ticker="GOOGL"),
        ]
        html = self.generator.generate_multi(results)

        assert "AAPL" in html
        assert "GOOGL" in html
