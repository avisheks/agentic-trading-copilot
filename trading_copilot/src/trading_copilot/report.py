"""Text report generator for Trading Copilot."""

from datetime import datetime, timezone

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

    def generate_table(self, results: list[SentimentResult]) -> str:
        """
        Generate a tabular summary report for multiple tickers.

        Args:
            results: List of SentimentResult objects

        Returns:
            Formatted table string with one row per ticker
        """
        if not results:
            return "No results to display."

        # Define column widths
        col_ticker = 8
        col_sentiment = 10
        col_confidence = 12
        col_news = 6
        col_signals = 40

        # Build header
        header = (
            f"{'TICKER':<{col_ticker}} | "
            f"{'SENTIMENT':<{col_sentiment}} | "
            f"{'CONFIDENCE':<{col_confidence}} | "
            f"{'NEWS':<{col_news}} | "
            f"{'KEY SIGNAL':<{col_signals}}"
        )
        separator = "-" * len(header)

        lines = [
            self._section_separator,
            "TRADING COPILOT SUMMARY TABLE",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            self._section_separator,
            "",
            header,
            separator,
        ]

        # Build rows
        for result in results:
            ticker = result.ticker[:col_ticker]
            sentiment = result.sentiment.value.upper()
            confidence = result.confidence.value.upper()

            # Count news articles
            news_count = "N/A"
            if result.aggregated_report.news and result.aggregated_report.news.articles:
                news_count = str(len(result.aggregated_report.news.articles))

            # Get primary signal reasoning (truncated)
            key_signal = "No signals"
            if result.signals:
                signal = result.signals[0]
                direction = "↑" if signal.direction == Sentiment.BULLISH else "↓"
                key_signal = f"{direction} {signal.reasoning}"
                if len(key_signal) > col_signals:
                    key_signal = key_signal[: col_signals - 3] + "..."

            row = (
                f"{ticker:<{col_ticker}} | "
                f"{sentiment:<{col_sentiment}} | "
                f"{confidence:<{col_confidence}} | "
                f"{news_count:<{col_news}} | "
                f"{key_signal:<{col_signals}}"
            )
            lines.append(row)

        lines.append(separator)
        lines.append("")
        lines.append(f"Total tickers analyzed: {len(results)}")
        lines.append("")
        lines.append(self._section_separator)
        lines.append("DISCLAIMER: This is not financial advice. Always do your own research.")
        lines.append(self._section_separator)

        return "\n".join(lines)

    def generate_full_report(self, results: list[SentimentResult]) -> str:
        """
        Generate a complete report with summary table followed by detailed reports.

        Args:
            results: List of SentimentResult objects

        Returns:
            Formatted report with table summary and detailed analysis per ticker
        """
        if not results:
            return "No results to display."

        sections = []

        # Add summary table (without its own disclaimer)
        table_lines = self._generate_table_without_disclaimer(results)
        sections.append(table_lines)

        # Add detailed reports section header
        sections.append("")
        sections.append(self._section_separator)
        sections.append("DETAILED ANALYSIS BY TICKER")
        sections.append(self._section_separator)

        # Add detailed report for each ticker
        for result in results:
            detailed = self._generate_detailed_report(result)
            sections.append("")
            sections.append(detailed)

        # Add final disclaimer
        sections.append("")
        sections.append(self._section_separator)
        sections.append("DISCLAIMER: This is not financial advice. Always do your own research.")
        sections.append(self._section_separator)

        return "\n".join(sections)

    def _generate_table_without_disclaimer(self, results: list[SentimentResult]) -> str:
        """Generate table without disclaimer (for use in combined reports)."""
        col_ticker = 8
        col_sentiment = 10
        col_confidence = 12
        col_news = 6
        col_signals = 40

        header = (
            f"{'TICKER':<{col_ticker}} | "
            f"{'SENTIMENT':<{col_sentiment}} | "
            f"{'CONFIDENCE':<{col_confidence}} | "
            f"{'NEWS':<{col_news}} | "
            f"{'KEY SIGNAL':<{col_signals}}"
        )
        separator = "-" * len(header)

        lines = [
            self._section_separator,
            "TRADING COPILOT SUMMARY TABLE",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            self._section_separator,
            "",
            header,
            separator,
        ]

        for result in results:
            ticker = result.ticker[:col_ticker]
            sentiment = result.sentiment.value.upper()
            confidence = result.confidence.value.upper()

            news_count = "N/A"
            if result.aggregated_report.news and result.aggregated_report.news.articles:
                news_count = str(len(result.aggregated_report.news.articles))

            key_signal = "No signals"
            if result.signals:
                signal = result.signals[0]
                direction = "↑" if signal.direction == Sentiment.BULLISH else "↓"
                key_signal = f"{direction} {signal.reasoning}"
                if len(key_signal) > col_signals:
                    key_signal = key_signal[: col_signals - 3] + "..."

            row = (
                f"{ticker:<{col_ticker}} | "
                f"{sentiment:<{col_sentiment}} | "
                f"{confidence:<{col_confidence}} | "
                f"{news_count:<{col_news}} | "
                f"{key_signal:<{col_signals}}"
            )
            lines.append(row)

        lines.append(separator)
        lines.append("")
        lines.append(f"Total tickers analyzed: {len(results)}")

        return "\n".join(lines)

    def _generate_detailed_report(self, result: SentimentResult) -> str:
        """Generate detailed report for a single ticker (without disclaimer)."""
        sections = [
            self._render_header(result),
            self._render_executive_summary(result),
            self._render_news_findings(result),
            self._render_sentiment_recommendation(result),
        ]
        return "\n\n".join(sections)

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
            if article.url:
                lines.append(f"      URL: {article.url}")

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
