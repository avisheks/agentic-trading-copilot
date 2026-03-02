"""Sentiment analyzer for Trading Copilot."""

from datetime import datetime, timezone

from trading_copilot.models import (
    AgentType,
    AggregatedReport,
    ArticleSentiment,
    ConfidenceLevel,
    NewsOutput,
    Sentiment,
    SentimentResult,
    Signal,
)


DEFAULT_DISCLAIMER = (
    "This analysis is for informational purposes only and is not financial advice. "
    "Past performance does not guarantee future results. Always conduct your own research "
    "and consult with a qualified financial advisor before making investment decisions."
)


class SentimentAnalyzer:
    """Analyzes aggregated research to produce sentiment."""

    def __init__(self, bedrock_client=None):
        """
        Initialize SentimentAnalyzer.

        Args:
            bedrock_client: Optional Bedrock client for Claude access.
                           If None, uses rule-based analysis.
        """
        self._bedrock_client = bedrock_client

    def analyze(
        self,
        aggregated: AggregatedReport,
        history=None,
    ) -> SentimentResult:
        """
        Produce sentiment analysis from aggregated data.

        Args:
            aggregated: Combined output from all agents
            history: Past recommendations for context (optional)

        Returns:
            SentimentResult with classification and rationale
        """
        signals = self._extract_signals(aggregated)
        sentiment = self._determine_sentiment(signals)
        confidence = self.calculate_confidence(signals, history)
        summary = self._generate_summary(aggregated, sentiment, signals)
        key_factors = self._extract_key_factors(aggregated, signals)
        risks = self._identify_risks(aggregated, signals)

        return SentimentResult(
            ticker=aggregated.ticker,
            sentiment=sentiment,
            confidence=confidence,
            signals=signals,
            summary=summary,
            key_factors=key_factors,
            risks=risks,
            disclaimer=DEFAULT_DISCLAIMER,
            analyzed_at=datetime.now(timezone.utc),
            aggregated_report=aggregated,
        )

    def _extract_signals(self, aggregated: AggregatedReport) -> list[Signal]:
        """Extract sentiment signals from aggregated data."""
        signals = []

        # Extract signal from news
        if aggregated.news and aggregated.news.status != "no_data":
            news_signal = self._analyze_news_signal(aggregated.news)
            if news_signal:
                signals.append(news_signal)

        # Extract signal from Reddit
        if aggregated.reddit and aggregated.reddit.status == "success":
            if aggregated.reddit.signal:
                signals.append(aggregated.reddit.signal)

        # Future: Extract signals from earnings and macro when implemented

        return signals

    def _analyze_news_signal(self, news: NewsOutput) -> Signal | None:
        """Analyze news articles to generate a signal."""
        if not news.articles:
            return None

        positive_count = sum(
            1 for a in news.articles if a.sentiment == ArticleSentiment.POSITIVE
        )
        negative_count = sum(
            1 for a in news.articles if a.sentiment == ArticleSentiment.NEGATIVE
        )
        total = len(news.articles)

        if total == 0:
            return None

        # Calculate sentiment direction and strength
        if positive_count > negative_count:
            direction = Sentiment.BULLISH
            strength = min(1.0, (positive_count - negative_count) / total + 0.5)
        elif negative_count > positive_count:
            direction = Sentiment.BEARISH
            strength = min(1.0, (negative_count - positive_count) / total + 0.5)
        else:
            # Neutral news slightly favors current trend, default to bearish for caution
            direction = Sentiment.BEARISH
            strength = 0.3

        reasoning = (
            f"Based on {total} news articles: "
            f"{positive_count} positive, {negative_count} negative, "
            f"{total - positive_count - negative_count} neutral."
        )

        return Signal(
            source=AgentType.NEWS,
            direction=direction,
            strength=round(strength, 2),
            reasoning=reasoning,
        )

    def _determine_sentiment(self, signals: list[Signal]) -> Sentiment:
        """Determine overall sentiment from signals."""
        if not signals:
            # Default to bearish when no data (conservative approach)
            return Sentiment.BEARISH

        # Weight signals by strength
        bullish_weight = sum(
            s.strength for s in signals if s.direction == Sentiment.BULLISH
        )
        bearish_weight = sum(
            s.strength for s in signals if s.direction == Sentiment.BEARISH
        )

        return Sentiment.BULLISH if bullish_weight > bearish_weight else Sentiment.BEARISH

    def calculate_confidence(
        self,
        signals: list[Signal],
        history=None,
    ) -> ConfidenceLevel:
        """
        Determine confidence level based on signal alignment and history.

        Args:
            signals: List of signals from different sources
            history: Historical reference with accuracy rate (optional)

        Returns:
            ConfidenceLevel (HIGH, MEDIUM, or LOW)
        """
        if not signals:
            return ConfidenceLevel.LOW

        # Check signal alignment
        directions = [s.direction for s in signals]
        all_agree = len(set(directions)) == 1

        # Calculate average strength
        avg_strength = sum(s.strength for s in signals) / len(signals)

        # Factor in history accuracy if available
        history_factor = 1.0
        if history and hasattr(history, 'accuracy_rate') and history.accuracy_rate is not None:
            history_factor = 0.5 + (history.accuracy_rate * 0.5)

        # Determine confidence
        adjusted_strength = avg_strength * history_factor

        if all_agree and adjusted_strength >= 0.7:
            return ConfidenceLevel.HIGH
        elif adjusted_strength >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _generate_summary(
        self,
        aggregated: AggregatedReport,
        sentiment: Sentiment,
        signals: list[Signal],
    ) -> str:
        """Generate a summary of the analysis."""
        ticker = aggregated.ticker
        sentiment_word = "bullish" if sentiment == Sentiment.BULLISH else "bearish"

        if not signals:
            return (
                f"Analysis for {ticker} is inconclusive due to limited data. "
                f"Defaulting to a cautious {sentiment_word} outlook."
            )

        # Build summary from signals
        signal_summaries = []
        for signal in signals:
            source_name = signal.source.value.capitalize()
            direction = "positive" if signal.direction == Sentiment.BULLISH else "negative"
            signal_summaries.append(f"{source_name} sentiment is {direction}")

        signals_text = "; ".join(signal_summaries)

        summary = (
            f"Overall outlook for {ticker} is {sentiment_word} for the next 1-2 weeks. "
            f"{signals_text}."
        )

        # Add Reddit citation if data available
        if aggregated.reddit and aggregated.reddit.status == "success" and aggregated.reddit.posts:
            post_count = len(aggregated.reddit.posts)
            subreddits = list(set(p.subreddit for p in aggregated.reddit.posts))
            subreddit_text = ", ".join(f"r/{s}" for s in subreddits[:3])
            if len(subreddits) > 3:
                subreddit_text += f" and {len(subreddits) - 3} more"
            summary += f" Reddit discussions from {subreddit_text} ({post_count} posts) were analyzed."

        return summary

    def _extract_key_factors(
        self,
        aggregated: AggregatedReport,
        signals: list[Signal],
    ) -> list[str]:
        """Extract key factors driving the sentiment."""
        factors = []

        # Add factors from news
        if aggregated.news and aggregated.news.articles:
            article_count = len(aggregated.news.articles)
            positive = sum(
                1 for a in aggregated.news.articles
                if a.sentiment == ArticleSentiment.POSITIVE
            )
            negative = sum(
                1 for a in aggregated.news.articles
                if a.sentiment == ArticleSentiment.NEGATIVE
            )

            if positive > negative:
                factors.append(f"Positive news coverage ({positive}/{article_count} articles)")
            elif negative > positive:
                factors.append(f"Negative news coverage ({negative}/{article_count} articles)")
            else:
                factors.append(f"Mixed news coverage ({article_count} articles)")

        # Add factors from Reddit
        if aggregated.reddit and aggregated.reddit.status == "success" and aggregated.reddit.posts:
            post_count = len(aggregated.reddit.posts)
            positive = sum(
                1 for p in aggregated.reddit.posts
                if p.sentiment == ArticleSentiment.POSITIVE
            )
            negative = sum(
                1 for p in aggregated.reddit.posts
                if p.sentiment == ArticleSentiment.NEGATIVE
            )

            if positive > negative:
                factors.append(f"Positive Reddit sentiment ({positive}/{post_count} posts)")
            elif negative > positive:
                factors.append(f"Negative Reddit sentiment ({negative}/{post_count} posts)")
            else:
                factors.append(f"Mixed Reddit sentiment ({post_count} posts)")

        # Add signal-based factors
        for signal in signals:
            if signal.strength >= 0.7:
                factors.append(f"Strong {signal.source.value} signal")

        if not factors:
            factors.append("Limited data available for analysis")

        return factors

    def _identify_risks(
        self,
        aggregated: AggregatedReport,
        signals: list[Signal],
    ) -> list[str]:
        """Identify risks that could change the outlook."""
        risks = []

        # Check for missing components
        if aggregated.missing_components:
            missing_names = [c.value for c in aggregated.missing_components]
            risks.append(f"Incomplete analysis: missing {', '.join(missing_names)} data")

        # Check for conflicting signals
        if signals:
            directions = set(s.direction for s in signals)
            if len(directions) > 1:
                risks.append("Conflicting signals from different data sources")

        # Check for low confidence signals
        low_confidence_signals = [s for s in signals if s.strength < 0.5]
        if low_confidence_signals:
            risks.append("Some signals have low confidence")

        # Check news-specific risks
        if aggregated.news:
            if aggregated.news.status == "partial":
                risks.append("Some news sources were unavailable")
            elif aggregated.news.status == "no_data":
                risks.append("No recent news data available")

        # Check Reddit-specific risks
        if aggregated.reddit:
            if aggregated.reddit.status == "partial":
                risks.append("Some Reddit sources were unavailable")
            elif aggregated.reddit.status == "no_data":
                risks.append("No recent Reddit data available")
            elif aggregated.reddit.status == "error":
                risks.append("Reddit data retrieval failed")

        if not risks:
            risks.append("Market conditions can change rapidly")

        return risks
