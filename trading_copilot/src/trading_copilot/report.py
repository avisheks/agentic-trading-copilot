"""Text report generator for Trading Copilot."""

from datetime import datetime

from trading_copilot.models import (
    ArticleSentiment,
    ConfidenceLevel,
    Sentiment,
    SentimentResult,
)


class TextReportGenerator:
    """Generates formatted text reports from analysis results."""

    SEPARATOR = "=" * 60
    SUBSEPARATOR = "-" * 40

    def generate(self, result: SentimentResult) -> str:
        """
        Generate a formatted text report.

        Args:
            result: Complete sentiment analysis result

        Returns:
            Formatted text string for console output
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
            self.SEPARATOR,
            f"TRADING COPILOT ANALYSIS REPORT",
            f"Ticker: {result.ticker}",
            f"Generated: {result.analyzed_at.strftime('%Y-%m-%d %H:%M UTC')}",
            self.SEPARATOR,
        ]
        return "\n".join(lines)

    def _render_executive_summary(self, result: SentimentResult) -> str:
        """Render the executive summary section."""
        sentiment_emoji = "📈" if result.sentiment == Sentiment.BULLISH else "📉"
        sentiment_word = result.sentiment.value.upper()
        confidence_word = result.confidence.value.upper()

        lines = [
            "EXECUTIVE SUMMARY",
            self.SUBSEPARATOR,
            f"Outlook: {sentiment_emoji} {sentiment_word} ({confidence_word} confidence)",
            "",
            result.summary,
            "",
            "Key Factors:",
        ]

        for i, factor in enumerate(result.key_factors, 1):
            lines.append(f"  {i}. {factor}")

        return "\n".join(lines)

    def _render_news_findings(self, result: SentimentResult) -> str:
        """Render the news findings section."""
        lines = [
            "NEWS ANALYSIS",
            self.SUBSEPARATOR,
        ]

        news = result.aggregated_report.news
        if not news or news.status == "no_data":
            lines.append("No recent news data available.")
            return "\n".join(lines)

        # Summary stats
        total = len(news.articles)
        positive = sum(1 for a in news.articles if a.sentiment == ArticleSentiment.POSITIVE)
        negative = sum(1 for a in news.articles if a.sentiment == ArticleSentiment.NEGATIVE)
        neutral = total - positive - negative

        lines.extend([
            f"Articles analyzed: {total}",
            f"  Positive: {positive}",
            f"  Negative: {negative}",
            f"  Neutral: {neutral}",
            "",
        ])

        # Show top headlines
        if news.articles:
            lines.append("Recent Headlines:")
            for article in news.articles[:5]:
                sentiment_indicator = {
                    ArticleSentiment.POSITIVE: "[+]",
                    ArticleSentiment.NEGATIVE: "[-]",
                    ArticleSentiment.NEUTRAL: "[~]",
                }.get(article.sentiment, "[?]")
                lines.append(f"  {sentiment_indicator} {article.headline[:60]}...")

        if news.status == "partial":
            lines.append("")
            lines.append("Note: Some news sources were unavailable.")

        return "\n".join(lines)

    def _render_sentiment_recommendation(self, result: SentimentResult) -> str:
        """Render the sentiment recommendation section."""
        lines = [
            "SENTIMENT RECOMMENDATION",
            self.SUBSEPARATOR,
        ]

        # Main recommendation
        sentiment_word = result.sentiment.value.upper()
        confidence_word = result.confidence.value
        lines.append(f"Recommendation: {sentiment_word} for the next 1-2 weeks")
        lines.append(f"Confidence Level: {confidence_word.capitalize()}")
        lines.append("")

        # Signals
        if result.signals:
            lines.append("Signal Analysis:")
            for signal in result.signals:
                direction = "Bullish" if signal.direction == Sentiment.BULLISH else "Bearish"
                strength_pct = int(signal.strength * 100)
                lines.append(f"  • {signal.source.value.capitalize()}: {direction} ({strength_pct}% strength)")
                lines.append(f"    {signal.reasoning}")
            lines.append("")

        # Risks
        if result.risks:
            lines.append("Risks to Consider:")
            for risk in result.risks:
                lines.append(f"  ⚠ {risk}")

        return "\n".join(lines)

    def _render_disclaimer(self, result: SentimentResult) -> str:
        """Render the disclaimer section."""
        lines = [
            self.SEPARATOR,
            "DISCLAIMER",
            self.SUBSEPARATOR,
            result.disclaimer,
            self.SEPARATOR,
        ]
        return "\n".join(lines)


def print_report(result: SentimentResult) -> None:
    """Print a formatted report to console."""
    generator = TextReportGenerator()
    report = generator.generate(result)
    print(report)
