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
            line-height: 1.4;
            color: #333;
            background-color: #f5f5f5;
            padding: 15px;
            font-size: 14px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 1.3rem;
            margin-bottom: 8px;
        }
        .header .ticker {
            font-size: 2rem;
            font-weight: bold;
            letter-spacing: 1.5px;
        }
        .header .timestamp {
            font-size: 0.8rem;
            opacity: 0.85;
            margin-top: 8px;
        }
        .section {
            padding: 18px;
            border-bottom: 1px solid #e2e8f0;
        }
        .section:last-child {
            border-bottom: none;
        }
        .section-title {
            font-size: 1rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }
        .sentiment-badge {
            display: inline-block;
            padding: 5px 14px;
            border-radius: 14px;
            font-weight: 600;
            font-size: 0.9rem;
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
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.75rem;
            margin-left: 8px;
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
            font-size: 0.9rem;
            color: #4a5568;
            margin: 12px 0;
            line-height: 1.5;
        }
        .factors-list, .risks-list {
            list-style: none;
            padding: 0;
            margin: 8px 0;
        }
        .factors-list li, .risks-list li {
            padding: 6px 0 6px 22px;
            position: relative;
            font-size: 0.85rem;
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
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }
        .stat-box {
            flex: 1;
            min-width: 85px;
            padding: 10px;
            background: #f7fafc;
            border-radius: 6px;
            text-align: center;
        }
        .stat-number {
            font-size: 1.4rem;
            font-weight: bold;
            color: #2d3748;
        }
        .stat-label {
            font-size: 0.75rem;
            color: #718096;
            margin-top: 2px;
        }
        .stat-positive .stat-number { color: #38a169; }
        .stat-negative .stat-number { color: #e53e3e; }
        .stat-neutral .stat-number { color: #718096; }
        .article-list {
            list-style: none;
            margin: 0;
            padding: 0;
        }
        .article-item {
            padding: 6px 10px;
            margin-bottom: 4px;
            background: #f7fafc;
            border-radius: 4px;
            border-left: 2px solid #e2e8f0;
        }
        .article-item.positive { border-left-color: #38a169; }
        .article-item.negative { border-left-color: #e53e3e; }
        .article-item.neutral { border-left-color: #718096; }
        .article-headline {
            font-weight: 500;
            color: #2d3748;
            margin-bottom: 2px;
            font-size: 0.8rem;
            line-height: 1.3;
        }
        .article-meta {
            font-size: 0.7rem;
            color: #718096;
        }
        .signal-item {
            padding: 10px 12px;
            margin-bottom: 8px;
            background: #f7fafc;
            border-radius: 6px;
        }
        .signal-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        .signal-direction {
            font-size: 1.2rem;
        }
        .signal-source {
            font-weight: 600;
            text-transform: capitalize;
            font-size: 0.85rem;
        }
        .signal-strength {
            margin-left: auto;
            font-size: 0.75rem;
            color: #718096;
        }
        .signal-reasoning {
            font-size: 0.85rem;
            color: #4a5568;
            line-height: 1.4;
        }
        .missing-section {
            background: #fffaf0;
            border: 1px solid #ed8936;
            border-radius: 6px;
            padding: 10px 12px;
            margin: 8px 0;
        }
        .missing-section-title {
            color: #c05621;
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 0.85rem;
        }
        .missing-section-text {
            color: #744210;
            font-size: 0.8rem;
        }
        .disclaimer {
            background: #edf2f7;
            padding: 15px;
            font-size: 0.75rem;
            color: #4a5568;
            text-align: center;
            line-height: 1.5;
        }
        .back-to-top {
            text-align: center;
            padding: 15px;
            border-top: 1px solid #e2e8f0;
        }
        .back-to-top a {
            color: #4299e1;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .back-to-top a:hover {
            text-decoration: underline;
        }
        @media (max-width: 600px) {
            body {
                padding: 8px;
                font-size: 13px;
            }
            .header {
                padding: 15px;
            }
            .header h1 {
                font-size: 1.1rem;
            }
            .header .ticker {
                font-size: 1.6rem;
            }
            .section {
                padding: 12px;
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
            
            {% if sentiment_rationale %}
            <div style="margin-top: 20px; padding: 15px; background: #f7fafc; border-left: 3px solid #4299e1; border-radius: 6px;">
                <h3 style="font-size: 0.95rem; color: #2d3748; margin-bottom: 10px; font-weight: 600;">
                    📊 Sentiment Rationale
                </h3>
                <div style="font-size: 0.85rem; color: #4a5568; line-height: 1.6;">
                    {{ sentiment_rationale }}
                </div>
            </div>
            {% endif %}
            
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
            
            <h3 style="font-size: 0.9rem; color: #2d3748; margin-bottom: 10px;">Recent Headlines ({{ news_articles | length }} articles)</h3>
            <ul class="article-list">
                {% for article in news_articles %}
                <li class="article-item {{ article.sentiment.value }}">
                    <div class="article-headline">
                        {% if article.url %}
                        <a href="{{ article.url }}" target="_blank" rel="noopener noreferrer" style="color: #2563eb; text-decoration: none; font-weight: 500;">
                            {{ article.headline }}
                        </a>
                        {% else %}
                        {{ article.headline }}
                        {% endif %}
                    </div>
                    <div class="article-meta">
                        {{ article.source }} • {{ article.published_at.strftime('%Y-%m-%d') }}
                    </div>
                </li>
                {% endfor %}
            </ul>
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
            <p style="color: #718096;">Earnings data available but not yet rendered.</p>
            {% endif %}
        </section>
        {% endif %}

        {% if show_macro_section %}
        <section class="section" id="macro-analysis">
            <h2 class="section-title">Macro Analysis</h2>
            {% if missing_macro %}
            <div class="missing-section">
                <div class="missing-section-title">⚠ Macro Data Unavailable</div>
                <div class="missing-section-text">{{ missing_macro_message }}</div>
            </div>
            {% else %}
            <p style="color: #718096;">Macro data available but not yet rendered.</p>
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
            
            # Generate sentiment rationale citing specific articles
            context["sentiment_rationale"] = self._generate_sentiment_rationale(
                result.sentiment,
                news.articles,
                context["positive_count"],
                context["negative_count"],
                context["neutral_count"]
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

    def generate_full_report(self, results: list[SentimentResult]) -> str:
        """
        Generate a complete HTML report with summary table and detailed analysis.

        Args:
            results: List of SentimentResult objects

        Returns:
            HTML string with summary table followed by detailed reports
        """
        if not results:
            return self._generate_empty_report()

        # Generate summary table
        summary_table = self._generate_summary_table(results)
        
        # Generate individual detailed reports with IDs and back-to-top links
        detailed_reports = []
        for result in results:
            report = self.generate(result)
            # Wrap report with ID anchor and add back-to-top link
            wrapped_report = f'''
<div id="ticker-{result.ticker}" style="margin-bottom: 40px;">
    {report}
    <div style="text-align: center; padding: 15px; background: white; border-radius: 6px; margin-top: 20px;">
        <a href="#top" style="color: #4299e1; text-decoration: none; font-size: 0.9rem; font-weight: 500;">
            ↑ Back to Summary
        </a>
    </div>
</div>'''
            detailed_reports.append(wrapped_report)
        
        # Combine with proper structure
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Copilot Report - Multi-Ticker Analysis</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
            margin: 0;
        }}
        html {{
            scroll-behavior: smooth;
        }}
    </style>
</head>
<body>
    <div id="top"></div>
    {summary_table}
    <div style="margin: 40px 0;"></div>
    {"".join(detailed_reports)}
</body>
</html>"""

    def _generate_summary_table(self, results: list[SentimentResult]) -> str:
        """Generate HTML summary table for multiple tickers."""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        
        table_rows = []
        for result in results:
            # Get sentiment styling
            sentiment_class = "bullish" if result.sentiment == Sentiment.BULLISH else "bearish"
            sentiment_text = result.sentiment.value.upper()
            
            # Get confidence styling
            confidence_class = result.confidence.value
            confidence_text = result.confidence.value.upper()
            
            # Count news articles
            news_count = "N/A"
            if result.aggregated_report.news and result.aggregated_report.news.articles:
                news_count = str(len(result.aggregated_report.news.articles))
            
            # Get primary signal
            signal_text = "No signals"
            if result.signals:
                signal = result.signals[0]
                direction_icon = "📈" if signal.direction == Sentiment.BULLISH else "📉"
                signal_text = f"{direction_icon} {signal.reasoning[:80]}{'...' if len(signal.reasoning) > 80 else ''}"
            
            table_rows.append(f"""
                <tr>
                    <td class="ticker-cell"><a href="#ticker-{result.ticker}" style="color: #2d3748; text-decoration: none;">{result.ticker}</a></td>
                    <td><span class="sentiment-badge sentiment-{sentiment_class}">{sentiment_text}</span></td>
                    <td><span class="confidence-badge confidence-{confidence_class}">{confidence_text}</span></td>
                    <td class="text-center">{news_count}</td>
                    <td class="signal-cell">{signal_text}</td>
                </tr>
            """)
        
        return f"""
<div style="max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden;">
    <style>
        .summary-header {{
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .summary-title {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .summary-timestamp {{
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        .summary-content {{
            padding: 30px;
        }}
        .summary-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .summary-table th {{
            background-color: #edf2f7;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            border-bottom: 2px solid #cbd5e0;
        }}
        .summary-table td {{
            padding: 15px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .summary-table tr:hover {{
            background-color: #f7fafc;
        }}
        .ticker-cell {{
            font-weight: bold;
            font-size: 1.1rem;
            color: #2d3748;
        }}
        .text-center {{
            text-align: center;
        }}
        .signal-cell {{
            font-size: 0.9rem;
            color: #4a5568;
        }}
        .sentiment-badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 16px;
            font-weight: bold;
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        .sentiment-bullish {{
            background-color: #c6f6d5;
            color: #22543d;
        }}
        .sentiment-bearish {{
            background-color: #fed7d7;
            color: #742a2a;
        }}
        .confidence-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
        }}
        .confidence-high {{
            background-color: #bee3f8;
            color: #2a4365;
        }}
        .confidence-medium {{
            background-color: #fefcbf;
            color: #744210;
        }}
        .confidence-low {{
            background-color: #e2e8f0;
            color: #4a5568;
        }}
        .total-count {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f7fafc;
            border-radius: 8px;
            text-align: center;
            color: #4a5568;
        }}
        .section-divider {{
            margin: 30px 0;
            padding: 20px;
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            text-align: center;
            font-size: 1.3rem;
            font-weight: 600;
        }}
        @media (max-width: 768px) {{
            .summary-table {{
                font-size: 0.85rem;
            }}
            .summary-table th, .summary-table td {{
                padding: 10px 5px;
            }}
            .signal-cell {{
                display: none;
            }}
            .summary-table th:last-child {{
                display: none;
            }}
        }}
    </style>
    
    <header class="summary-header">
        <div class="summary-title">Trading Copilot Summary</div>
        <div class="summary-timestamp">Generated: {timestamp}</div>
    </header>
    
    <div class="summary-content">
        <table class="summary-table">
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Sentiment</th>
                    <th>Confidence</th>
                    <th class="text-center">News</th>
                    <th>Key Signal</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        
        <div class="total-count">
            <strong>Total tickers analyzed: {len(results)}</strong>
        </div>
    </div>
    
    <div class="section-divider">
        Detailed Analysis by Ticker
    </div>
</div>
"""

    def _generate_sentiment_rationale(
        self,
        sentiment: Sentiment,
        articles: list,
        positive_count: int,
        negative_count: int,
        neutral_count: int
    ) -> str:
        """
        Generate a detailed rationale for the sentiment, citing specific news articles.
        
        Args:
            sentiment: The overall sentiment (BULLISH or BEARISH)
            articles: List of NewsArticle objects
            positive_count: Number of positive articles
            negative_count: Number of negative articles
            neutral_count: Number of neutral articles
            
        Returns:
            HTML-formatted rationale string
        """
        from trading_copilot.models import ArticleSentiment
        
        total = len(articles)
        if total == 0:
            return "No news articles available for analysis."
        
        # Calculate percentages
        positive_pct = (positive_count / total) * 100
        negative_pct = (negative_count / total) * 100
        neutral_pct = (neutral_count / total) * 100
        
        # Start rationale
        rationale_parts = []
        
        # Overall sentiment statement
        if sentiment == Sentiment.BULLISH:
            rationale_parts.append(
                f"<strong>The {sentiment.value.upper()} sentiment is based on analysis of {total} recent news articles, "
                f"with {positive_count} ({positive_pct:.0f}%) showing positive sentiment, "
                f"{negative_count} ({negative_pct:.0f}%) negative, and {neutral_count} ({neutral_pct:.0f}%) neutral.</strong>"
            )
        else:
            rationale_parts.append(
                f"<strong>The {sentiment.value.upper()} sentiment is based on analysis of {total} recent news articles, "
                f"with {negative_count} ({negative_pct:.0f}%) showing negative sentiment, "
                f"{positive_count} ({positive_pct:.0f}%) positive, and {neutral_count} ({neutral_pct:.0f}%) neutral.</strong>"
            )
        
        rationale_parts.append("<br><br>")
        
        # Get relevant articles for citation
        if sentiment == Sentiment.BULLISH:
            # Cite positive articles
            positive_articles = [a for a in articles if a.sentiment == ArticleSentiment.POSITIVE][:3]
            if positive_articles:
                rationale_parts.append("<strong>Key Positive Indicators:</strong><br>")
                for i, article in enumerate(positive_articles, 1):
                    source = article.source if hasattr(article, 'source') else 'Unknown'
                    rationale_parts.append(
                        f"{i}. <em>\"{article.headline[:100]}{'...' if len(article.headline) > 100 else ''}\"</em> "
                        f"({source}) - This article reflects positive market sentiment.<br>"
                    )
            
            # Mention negative articles as risks if present
            if negative_count > 0:
                negative_articles = [a for a in articles if a.sentiment == ArticleSentiment.NEGATIVE][:2]
                rationale_parts.append(f"<br><strong>Note:</strong> Despite the overall bullish sentiment, "
                                     f"{negative_count} articles expressed concerns, including:<br>")
                for i, article in enumerate(negative_articles, 1):
                    source = article.source if hasattr(article, 'source') else 'Unknown'
                    rationale_parts.append(
                        f"• <em>\"{article.headline[:80]}{'...' if len(article.headline) > 80 else ''}\"</em> ({source})<br>"
                    )
        else:
            # Cite negative articles
            negative_articles = [a for a in articles if a.sentiment == ArticleSentiment.NEGATIVE][:3]
            if negative_articles:
                rationale_parts.append("<strong>Key Negative Indicators:</strong><br>")
                for i, article in enumerate(negative_articles, 1):
                    source = article.source if hasattr(article, 'source') else 'Unknown'
                    rationale_parts.append(
                        f"{i}. <em>\"{article.headline[:100]}{'...' if len(article.headline) > 100 else ''}\"</em> "
                        f"({source}) - This article reflects negative market sentiment.<br>"
                    )
            
            # Mention positive articles if present
            if positive_count > 0:
                positive_articles = [a for a in articles if a.sentiment == ArticleSentiment.POSITIVE][:2]
                rationale_parts.append(f"<br><strong>Note:</strong> Despite the overall bearish sentiment, "
                                     f"{positive_count} articles showed positive signals, including:<br>")
                for i, article in enumerate(positive_articles, 1):
                    source = article.source if hasattr(article, 'source') else 'Unknown'
                    rationale_parts.append(
                        f"• <em>\"{article.headline[:80]}{'...' if len(article.headline) > 80 else ''}\"</em> ({source})<br>"
                    )
        
        return "".join(rationale_parts)

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
