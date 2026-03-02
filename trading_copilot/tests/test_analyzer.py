"""Tests for Sentiment Analyzer."""

from datetime import datetime, timezone

import pytest

from trading_copilot.analyzer import DEFAULT_DISCLAIMER, SentimentAnalyzer
from trading_copilot.models import (
    AgentType,
    AggregatedReport,
    ArticleSentiment,
    ConfidenceLevel,
    NewsArticle,
    NewsOutput,
    Sentiment,
    Signal,
)


class TestSentimentAnalyzer:
    """Unit tests for SentimentAnalyzer."""

    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def _create_news_output(
        self,
        ticker: str,
        positive: int = 0,
        negative: int = 0,
        neutral: int = 0,
        status: str = "success",
    ) -> NewsOutput:
        """Helper to create NewsOutput with specified sentiment distribution."""
        articles = []
        now = datetime.now(timezone.utc)

        for i in range(positive):
            articles.append(
                NewsArticle(
                    headline=f"Positive headline {i}",
                    source="Test",
                    published_at=now,
                    summary="Positive summary",
                    url=f"https://test.com/pos{i}",
                    sentiment=ArticleSentiment.POSITIVE,
                )
            )

        for i in range(negative):
            articles.append(
                NewsArticle(
                    headline=f"Negative headline {i}",
                    source="Test",
                    published_at=now,
                    summary="Negative summary",
                    url=f"https://test.com/neg{i}",
                    sentiment=ArticleSentiment.NEGATIVE,
                )
            )

        for i in range(neutral):
            articles.append(
                NewsArticle(
                    headline=f"Neutral headline {i}",
                    source="Test",
                    published_at=now,
                    summary="Neutral summary",
                    url=f"https://test.com/neu{i}",
                    sentiment=ArticleSentiment.NEUTRAL,
                )
            )

        return NewsOutput(
            ticker=ticker,
            articles=articles,
            retrieved_at=now,
            status=status,
        )

    def _create_aggregated_report(
        self,
        ticker: str,
        news: NewsOutput | None = None,
        missing: list[AgentType] | None = None,
    ) -> AggregatedReport:
        """Helper to create AggregatedReport."""
        return AggregatedReport(
            ticker=ticker,
            news=news,
            earnings=None,
            macro=None,
            aggregated_at=datetime.now(timezone.utc),
            missing_components=missing or [],
        )

    def test_analyze_returns_sentiment_result(self):
        """Analyze returns a complete SentimentResult."""
        news = self._create_news_output("AAPL", positive=5, negative=2)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert result.ticker == "AAPL"
        assert result.sentiment in [Sentiment.BULLISH, Sentiment.BEARISH]
        assert result.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
        assert len(result.summary) > 0
        assert len(result.key_factors) > 0
        assert len(result.risks) > 0
        assert "not financial advice" in result.disclaimer.lower()

    def test_analyze_bullish_on_positive_news(self):
        """Analyzer returns bullish sentiment for mostly positive news."""
        news = self._create_news_output("AAPL", positive=8, negative=2)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert result.sentiment == Sentiment.BULLISH

    def test_analyze_bearish_on_negative_news(self):
        """Analyzer returns bearish sentiment for mostly negative news."""
        news = self._create_news_output("AAPL", positive=2, negative=8)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert result.sentiment == Sentiment.BEARISH

    def test_analyze_bearish_on_no_data(self):
        """Analyzer returns bearish sentiment when no data available."""
        report = self._create_aggregated_report(
            "AAPL",
            news=None,
            missing=[AgentType.NEWS],
        )

        result = self.analyzer.analyze(report)

        assert result.sentiment == Sentiment.BEARISH
        assert result.confidence == ConfidenceLevel.LOW

    def test_disclaimer_always_present(self):
        """Disclaimer is always included in result."""
        news = self._create_news_output("AAPL", positive=5)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert result.disclaimer == DEFAULT_DISCLAIMER
        assert "not financial advice" in result.disclaimer.lower()

    def test_signals_extracted_from_news(self):
        """Signals are extracted from news data."""
        news = self._create_news_output("AAPL", positive=5, negative=2)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert len(result.signals) > 0
        news_signal = next(
            (s for s in result.signals if s.source == AgentType.NEWS), None
        )
        assert news_signal is not None
        assert news_signal.direction == Sentiment.BULLISH

    def test_confidence_high_when_signals_agree(self):
        """Confidence is high when all signals agree with high strength."""
        news = self._create_news_output("AAPL", positive=10, negative=0)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert result.confidence == ConfidenceLevel.HIGH

    def test_confidence_low_when_no_signals(self):
        """Confidence is low when no signals available."""
        report = self._create_aggregated_report(
            "AAPL",
            news=self._create_news_output("AAPL", status="no_data"),
        )

        result = self.analyzer.analyze(report)

        assert result.confidence == ConfidenceLevel.LOW

    def test_key_factors_include_news_coverage(self):
        """Key factors include news coverage information."""
        news = self._create_news_output("AAPL", positive=5, negative=2, neutral=3)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert any("news" in f.lower() for f in result.key_factors)

    def test_risks_include_missing_components(self):
        """Risks include missing data components."""
        news = self._create_news_output("AAPL", positive=5)
        report = self._create_aggregated_report(
            "AAPL",
            news=news,
            missing=[AgentType.EARNINGS, AgentType.MACRO],
        )

        result = self.analyzer.analyze(report)

        assert any("missing" in r.lower() for r in result.risks)

    def test_risks_include_partial_data(self):
        """Risks include partial data warning."""
        news = self._create_news_output("AAPL", positive=5, status="partial")
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert any("unavailable" in r.lower() for r in result.risks)

    def test_summary_contains_ticker(self):
        """Summary contains the ticker symbol."""
        news = self._create_news_output("AAPL", positive=5)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert "AAPL" in result.summary

    def test_summary_contains_sentiment_direction(self):
        """Summary contains the sentiment direction."""
        news = self._create_news_output("AAPL", positive=8, negative=2)
        report = self._create_aggregated_report("AAPL", news=news)

        result = self.analyzer.analyze(report)

        assert "bullish" in result.summary.lower() or "bearish" in result.summary.lower()


class TestCalculateConfidence:
    """Tests for confidence calculation."""

    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_low_confidence_with_no_signals(self):
        """Returns LOW confidence when no signals."""
        confidence = self.analyzer.calculate_confidence([], None)
        assert confidence == ConfidenceLevel.LOW

    def test_high_confidence_with_strong_aligned_signals(self):
        """Returns HIGH confidence when signals are strong and aligned."""
        signals = [
            Signal(
                source=AgentType.NEWS,
                direction=Sentiment.BULLISH,
                strength=0.9,
                reasoning="Strong positive news",
            ),
        ]

        confidence = self.analyzer.calculate_confidence(signals, None)
        assert confidence == ConfidenceLevel.HIGH

    def test_medium_confidence_with_moderate_signals(self):
        """Returns MEDIUM confidence with moderate signal strength."""
        signals = [
            Signal(
                source=AgentType.NEWS,
                direction=Sentiment.BULLISH,
                strength=0.6,
                reasoning="Moderate positive news",
            ),
        ]

        confidence = self.analyzer.calculate_confidence(signals, None)
        assert confidence == ConfidenceLevel.MEDIUM

    def test_low_confidence_with_weak_signals(self):
        """Returns LOW confidence with weak signals."""
        signals = [
            Signal(
                source=AgentType.NEWS,
                direction=Sentiment.BULLISH,
                strength=0.3,
                reasoning="Weak positive news",
            ),
        ]

        confidence = self.analyzer.calculate_confidence(signals, None)
        assert confidence == ConfidenceLevel.LOW
