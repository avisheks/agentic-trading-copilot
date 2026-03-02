"""HTML report generator for Trading Copilot using Jinja2 templates."""

from datetime import datetime, timezone
from typing import Optional

from jinja2 import Environment, BaseLoader

from trading_copilot.models import (
    AgentType,
    ArticleSentiment,
    ConfidenceLevel,
    Sentiment,
    SentimentResult,
)


# Inline HTML template for mobile-responsive report
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Copilot Report - {{ result.ticker }}</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 1.8rem;
            margin-bottom: 10px;
        }
        .header .ticker {
            font-size: 2.5rem;
            font-weight: bold;
            letter-spacing: 2px;
        }
        .header .timestamp {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 10px;
        }
        .section {
            padding: 25px;
            border-bottom: 1px solid #e2e8f0;
        }
        .section:last-child {
            border-bottom: none;
        }
        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        .sentiment-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.1rem;
            text-transform: uppercase;
        }
        .sentiment-bullish {
            background-color: #c6f6d5;
            color: #22543d;
        }
        .sentiment-bearish {
            background-color: #fed7d7;
            color: #742a2a;
        }
        .confidence-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            margin-left: 10px;
        }
        .confidence-high {
            background-color: #bee3f8;
            color: #2a4365;
        }
        .confidence-medium {
            background-color: #fefcbf;
            color: #744210;
        }
        .confidence-low {
            background-color: #e2e8f0;
            color: #4a5568;
        }
        .summary-text {
            font-size: 1rem;
            color: #4a5568;
            margin: 15px 0;
        }
        .factors-list, .risks-list {
            list-style: none;
            padding: 0;
        }
        .factors-list li, .risks-list li {
            padding: 8px 0 8px 25px;
            position: relative;
        }
        .factors-list li::before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #38a169;
            font-weight: bold;
        }
        .risks-list li::before {
            content: "⚠";
            position: absolute;
            left: 0;
            color: #dd6b20;
        }
        .news-stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        .stat-box {
            flex: 1;
            min-width: 100px;
            padding: 15px;
            background: #f7fafc;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 1.8rem;
            font-weight: bold;
            color: #2d3748;
        }
        .stat-label {
            font-size: 0.85rem;
            color: #718096;
        }
        .stat-positive .stat-number { color: #38a169; }
        .stat-negative .stat-number { color: #e53e3e; }
        .stat-neutral .stat-number { color: #718096; }
        .article-list {
            list-style: none;
        }
        .article-item {
            padding: 15px;
            margin-bottom: 10px;
            background: #f7fafc;
            border-radius: 8px;
            border-left: 4px solid #e2e8f0;
        }
        .article-item.positive { border-left-color: #38a169; }
        .article-item.negative { border-left-color: #e53e3e; }
        .article-item.neutral { border-left-color: #718096; }
        .article-headline {
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 5px;
        }
        .article-meta {
            font-size: 0.85rem;
            color: #718096;
        }
        .signal-item {
            padding: 15px;
            margin-bottom: 10px;
            background: #f7fafc;
            border-radius: 8px;
        }
        .signal-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }
        .signal-direction {
            font-size: 1.5rem;
        }
        .signal-source {
            font-weight: 600;
            text-transform: capitalize;
        }
        .signal-strength {
            margin-left: auto;
            font-size: 0.9rem;
            color: #718096;
        }
        .signal-reasoning {
            font-size: 0.95rem;
            color: #4a5568;
        }
        .missing-section {
            background: #fffaf0;
            border: 1px solid #ed8936;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .missing-section-title {
            color: #c05621;
            font-weight: 600;
            margin-bottom: 5px;
        }
        .missing-section-text {
            color: #744210;
            font-size: 0.9rem;
        }
        .disclaimer {
            background: #edf2f7;
            padding: 20px;
            font-size: 0.85rem;
            color: #4a5568;
            text-align: center;
        }
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            .header {
                padding: 20px;
            }
            .header h1 {
                font-size: 1.4rem;
            }
            .header .ticker {
                font-size: 2rem;
            }
            .section {
                padding: 15px;
            }
            .news-stats {
                flex-direction: column;
            }
            .stat-box {
                min-width: auto;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>Trading Copilot Analysis Report</h1>
            <div class="ticker">{{ result.ticker }}</div>
            <div class="timestamp">Generated: {{ result.analyzed_at.strftime('%Y-%m-%d %H:%M UTC') }}</div>
        </header>

        <section class="section" id="executive-summary">
            <h2 class="section-title">Executive Summary</h2>
            <div>
                <span class="sentiment-badge sentiment-{{ result.sentiment.value }}">
                    {{ result.sentiment.value | upper }}
                </span>
                <span class="confidence-badge confidence-{{ result.confidence.value }}">
                    {{ result.confidence.value | upper }} Confidence
                </span>
            </div>
            <p class="summary-text">{{ result.summary }}</p>
            
            {% if result.key_factors %}
            <h3 style="margin-top: 20px; font-size: 1rem; color: #2d3748;">Key Factors</h3>
            <ul class="factors-list">
                {% for factor in result.key_factors %}
                <li>{{ factor }}</li>
                {% endfor %}
            </ul>
            {% endif %}
            
            {% if result.risks %}
            <h3 style="margin-top: 20px; font-size: 1rem; color: #2d3748;">Risks</h3>
            <ul class="risks-list">
                {% for risk in result.risks %}
                <li>{{ risk }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </section>

        <section class="section" id="news-findings">
            <h2 class="section-title">News Findings</h2>
            {% if missing_news %}
            <div class="missing-section">
                <div class="missing-section-title">⚠ News Data Unavailable</div>
                <div class="missing-section-text">{{ missing_news_message }}</div>
            </div>
            {% elif news_articles %}
            <div class="news-stats">
                <div class="stat-box">
                    <div class="stat-number">{{ news_articles | length }}</div>
                    <div class="stat-label">Total Articles</div>
                </div>
                <div class="stat-box stat-positive">
                    <div class="stat-number">{{ positive_count }}</div>
                    <div class="stat-label">Positive</div>
                </div>
                <div class="stat-box stat-negative">
                    <div class="stat-number">{{ negative_count }}</div>
                    <div class="stat-label">Negative</div>
                </div>
                <div class="stat-box stat-neutral">
                    <div class="stat-number">{{ neutral_count }}</div>
                    <div class="stat-label">Neutral</div>
                </div>
            </div>
            
            <h3 style="font-size: 1rem; color: #2d3748; margin-bottom: 15px;">Recent Headlines</h3>
            <ul class="article-list">
                {% for article in news_articles[:5] %}
                <li class="article-item {{ article.sentiment.value }}">
                    <div class="article-headline">{{ article.headline }}</div>
                    <div class="article-meta">
                        {{ article.source }} • {{ article.published_at.strftime('%Y-%m-%d') }}
                    </div>
                </li>
                {% endfor %}
            </ul>
            {% if news_articles | length > 5 %}
            <p style="color: #718096; font-size: 0.9rem; margin-top: 10px;">
                ... and {{ news_articles | length - 5 }} more articles
            </p>
            {% endif %}
            {% else %}
            <p style="color: #718096;">No recent news articles found for analysis.</p>
            {% endif %}
        </section>

        {% if show_earnings_section %}
        <section class="section" id="earnings-analysis">
            <h2 class="section-title">Earnings Analysis</h2>
            {% if missing_earnings %}
            <div class="missing-section">
                <div class="missing-section-title">⚠ Earnings Data Unavailable</div>
                <div class="missing-section-text">{{ missing_earnings_message }}</div>
            </div>
            {% else %}
            <p style="color: #718096;">Earnings data will be displayed here when available.</p>
            {% endif %}
        </section>
        {% endif %}

        {% if show_macro_section %}
        <section class="section" id="macro-trends">
            <h2 class="section-title">Macro Trends</h2>
            {% if missing_macro %}
            <div class="missing-section">
                <div class="missing-section-title">⚠ Macro Data Unavailable</div>
                <div class="missing-section-text">{{ missing_macro_message }}</div>
            </div>
            {% else %}
            <p style="color: #718096;">Macro analysis will be displayed here when available.</p>
            {% endif %}
        </section>
        {% endif %}

        <section class="section" id="sentiment-recommendation">
            <h2 class="section-title">Sentiment Recommendation</h2>
            {% if result.signals %}
            <h3 style="font-size: 1rem; color: #2d3748; margin-bottom: 15px;">Signal Analysis</h3>
            {% for signal in result.signals %}
            <div class="signal-item">
                <div class="signal-header">
                    <span class="signal-direction">{% if signal.direction.value == 'bullish' %}📈{% else %}📉{% endif %}</span>
                    <span class="signal-source">{{ signal.source.value }}</span>
                    <span class="signal-strength">{{ (signal.strength * 100) | int }}% strength</span>
                </div>
                <div class="signal-reasoning">{{ signal.reasoning }}</div>
            </div>
            {% endfor %}
            {% else %}
            <p style="color: #718096;">No detailed signals available for analysis.</p>
            {% endif %}
        </section>

        <footer class="disclaimer">
            {{ result.disclaimer }}
        </footer>
    </div>
</body>
</html>"""


class HTMLReportGenerator:
    """Generates HTML reports from sentiment analysis results using Jinja2."""

    def __init__(self):
        """Initialize the HTML report generator with Jinja2 environment."""
        self._env = Environment(loader=BaseLoader())
        self._template = self._env.from_string(HTML_TEMPLATE)

    def generate(self, result: SentimentResult) -> str:
        """
        Generate an HTML report for a single sentiment result.

        Args:
            result: SentimentResult from sentiment analysis

        Returns:
            HTML string for email delivery or web display
        """
        context = self._build_context(result)
        return self._template.render(**context)

    def _build_context(self, result: SentimentResult) -> dict:
        """Build the template context from a SentimentResult."""
        context = {
            "result": result,
            "news_articles": [],
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "missing_news": False,
            "missing_news_message": "",
            "show_earnings_section": False,
            "missing_earnings": False,
            "missing_earnings_message": "",
            "show_macro_section": False,
            "missing_macro": False,
            "missing_macro_message": "",
        }

        # Process news data
        news = result.aggregated_report.news
        if news and news.articles:
            context["news_articles"] = news.articles
            context["positive_count"] = sum(
                1 for a in news.articles if a.sentiment == ArticleSentiment.POSITIVE
            )
            context["negative_count"] = sum(
                1 for a in news.articles if a.sentiment == ArticleSentiment.NEGATIVE
            )
            context["neutral_count"] = (
                len(news.articles) - context["positive_count"] - context["negative_count"]
            )
        elif AgentType.NEWS in result.aggregated_report.missing_components:
            context["missing_news"] = True
            context["missing_news_message"] = (
                "News data could not be retrieved. The news agent encountered an error during execution."
            )

        # Check for missing components and show sections with error indicators
        missing = result.aggregated_report.missing_components

        if AgentType.EARNINGS in missing:
            context["show_earnings_section"] = True
            context["missing_earnings"] = True
            context["missing_earnings_message"] = (
                "Earnings data could not be retrieved. The earnings agent encountered an error during execution."
            )
        elif result.aggregated_report.earnings is not None:
            context["show_earnings_section"] = True

        if AgentType.MACRO in missing:
            context["show_macro_section"] = True
            context["missing_macro"] = True
            context["missing_macro_message"] = (
                "Macro analysis could not be retrieved. The macro agent encountered an error during execution."
            )
        elif result.aggregated_report.macro is not None:
            context["show_macro_section"] = True

        return context

    def generate_multi(self, results: list[SentimentResult]) -> str:
        """
        Generate an HTML report for multiple sentiment results.

        Args:
            results: List of SentimentResult objects

        Returns:
            HTML string with summary table and individual reports
        """
        if not results:
            return self._generate_empty_report()

        # For now, generate individual reports concatenated
        # A more sophisticated multi-report template could be added later
        reports = []
        for result in results:
            reports.append(self.generate(result))

        return "\n<hr style='margin: 40px 0; border: none; border-top: 3px solid #e2e8f0;'>\n".join(reports)

    def _generate_empty_report(self) -> str:
        """Generate an empty report placeholder."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Copilot Report</title>
</head>
<body>
    <div style="text-align: center; padding: 50px; font-family: sans-serif;">
        <h1>No Results Available</h1>
        <p>No sentiment analysis results were provided for report generation.</p>
    </div>
</body>
</html>"""
