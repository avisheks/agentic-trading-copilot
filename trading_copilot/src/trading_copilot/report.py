"""Text report generator for Trading Copilot."""

from datetime import datetime

from trading_copilot.models import (
    ArticleSentiment,
    ConfidenceLevel,
    Sentiment,
    SentimentResult,
)


class TextReportGenerator:
    """Generates formatted text reports from sentiment analysis results."""

    def __init__(self):
        """Initialize the text report generator."""
        self._section_separator = "=" * 60
        self._subsection_separator = "-" * 40

    def generate(self, result: SentimentResult) -> str:
        """
        Generate a complete text report.

        Args:
            result: SentimentResult from sentiment analysis

        Returns:
            Formatted text report string
        """
        sections = [
            self._render_header(result),
            self._render_executive_summary(result),
            self._render_news_findings(result),
            self._render_sentiment_recommendation(result),
            self._render_disclaimer(result),
        ]

        return "\n\n".join(sections)

    def _render_header(self, result: SentimentResult) -> str:
        """Render the report header."""
        lines = [
            self._section_separator,
            f"TRADING COPILOT ANALYSIS REPORT",
            f"Ticker: {result.ticker}",
            f"Generated: {result.analyzed_at.strftime('%Y-%m-%d %H:%M UTC')}",
            self._section_separator,
        ]
        return "\n".join(lines)

    def _render_executive_summary(self, result: SentimentResult) -> str:
        """Render the executive summary section."""
        sentiment_display = result.sentiment.value.upper()
        confidence_display = result.confidence.value.upper()

        lines = [
            "EXECUTIVE SUMMARY",
            self._subsection_separator,
            f"Sentiment: {sentiment_display}",
            f"Confidence: {confidence_display}",
            "",
            result.summary,
            "",
            "Key Factors:",
        ]

        for factor in result.key_factors:
            lines.append(f"  • {factor}")

        if result.risks:
            lines.append("")
            lines.append("Risks:")
            for risk in result.risks:
                lines.append(f"  • {risk}")

        return "\n".join(lines)

    def _render_news_findings(self, result: SentimentResult) -> str:
        """Render the news findings section."""
        lines = [
            "NEWS FINDINGS",
            self._subsection_separator,
        ]

        news = result.aggregated_report.news

        if not news or news.status == "no_data":
            lines.append("No recent news data available for analysis.")
            return "\n".join(lines)

        if news.error_message:
            lines.append(f"Note: {news.error_message}")
            lines.append("")

        articles = news.articles
        if not articles:
            lines.append("No articles found in the past 14 days.")
            return "\n".join(lines)

        # Summary statistics
        positive = sum(1 for a in articles if a.sentiment == ArticleSentiment.POSITIVE)
        negative = sum(1 for a in articles if a.sentiment == ArticleSentiment.NEGATIVE)
        neutral = len(articles) - positive - negative

        lines.append(f"Articles analyzed: {len(articles)}")
        lines.append(f"  Positive: {positive}")
        lines.append(f"  Negative: {negative}")
        lines.append(f"  Neutral: {neutral}")
        lines.append("")

        # Show top articles (up to 5)
        lines.append("Recent Headlines:")
        for article in articles[:5]:
            sentiment_icon = self._get_sentiment_icon(article.sentiment)
            date_str = article.published_at.strftime("%Y-%m-%d")
            lines.append(f"  {sentiment_icon} [{date_str}] {article.headline}")
            lines.append(f"      Source: {article.source}")

        if len(articles) > 5:
            lines.append(f"  ... and {len(articles) - 5} more articles")

        return "\n".join(lines)

    def _render_sentiment_recommendation(self, result: SentimentResult) -> str:
        """Render the sentiment recommendation section."""
        lines = [
            "SENTIMENT RECOMMENDATION",
            self._subsection_separator,
        ]

        # Main recommendation
        sentiment_word = "BULLISH" if result.sentiment == Sentiment.BULLISH else "BEARISH"
        confidence_word = result.confidence.value.upper()

        lines.append(f"Recommendation: {sentiment_word} ({confidence_word} confidence)")
        lines.append("")

        # Signals breakdown
        if result.signals:
            lines.append("Signal Analysis:")
            for signal in result.signals:
                direction = "↑" if signal.direction == Sentiment.BULLISH else "↓"
                strength_pct = int(signal.strength * 100)
                lines.append(f"  {direction} {signal.source.value.capitalize()}: {strength_pct}% strength")
                lines.append(f"      {signal.reasoning}")
        else:
            lines.append("No signals available for detailed analysis.")

        return "\n".join(lines)

    def _render_disclaimer(self, result: SentimentResult) -> str:
        """Render the disclaimer section."""
        lines = [
            self._section_separator,
            "DISCLAIMER",
            self._subsection_separator,
            result.disclaimer,
            self._section_separator,
        ]
        return "\n".join(lines)

    def _get_sentiment_icon(self, sentiment: ArticleSentiment) -> str:
        """Get an icon for article sentiment."""
        icons = {
            ArticleSentiment.POSITIVE: "+",
            ArticleSentiment.NEGATIVE: "-",
            ArticleSentiment.NEUTRAL: "○",
        }
        return icons.get(sentiment, "?")
