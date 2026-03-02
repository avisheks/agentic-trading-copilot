"""Data models for Trading Copilot."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Sentiment(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentType(Enum):
    NEWS = "news"
    EARNINGS = "earnings"
    MACRO = "macro"
    REDDIT = "reddit"


class ArticleSentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EarningsComparison(Enum):
    BEAT = "beat"
    MISS = "miss"
    MEET = "meet"


@dataclass
class ValidationResult:
    is_valid: bool
    normalized_ticker: str | None
    error_message: str | None


@dataclass
class SourceConfig:
    name: str
    api_endpoint: str
    api_key_env: str
    added_at: datetime
    enabled: bool = True


@dataclass
class DataSourceConfig:
    news_sources: list[SourceConfig]
    earnings_sources: list[SourceConfig]
    macro_sources: list[SourceConfig]
    last_updated: datetime


@dataclass
class NewsArticle:
    headline: str
    source: str
    published_at: datetime
    summary: str
    url: str
    sentiment: ArticleSentiment


@dataclass
class NewsOutput:
    ticker: str
    articles: list[NewsArticle]
    retrieved_at: datetime
    status: str  # "success", "partial", "no_data"
    data_source: str = "api"  # "api" or "web_search"
    error_message: str | None = None


@dataclass
class EarningsData:
    fiscal_quarter: str
    revenue: float
    eps: float
    guidance: str | None
    management_commentary: str | None
    report_date: datetime


@dataclass
class AnalystExpectations:
    expected_revenue: float
    expected_eps: float


@dataclass
class EarningsOutput:
    ticker: str
    earnings: EarningsData | None
    expectations: AnalystExpectations | None
    comparison: EarningsComparison | None
    retrieved_at: datetime
    status: str
    data_source: str = "api"  # "api" or "web_search"
    error_message: str | None = None


@dataclass
class MacroFactor:
    category: str  # "geopolitical", "interest_rates", "supply_chain", "trade"
    description: str
    impact: str  # "positive", "negative", "neutral"
    relevance: str  # Why this matters for the ticker


@dataclass
class MacroOutput:
    ticker: str
    sector: str
    factors: list[MacroFactor]
    risks: list[str]
    opportunities: list[str]
    retrieved_at: datetime
    status: str
    data_source: str = "api"  # "api" or "web_search"
    error_message: str | None = None


@dataclass
class AggregatedReport:
    ticker: str
    news: NewsOutput | None
    earnings: EarningsOutput | None
    macro: MacroOutput | None
    aggregated_at: datetime
    missing_components: list[AgentType]


@dataclass
class Signal:
    source: AgentType
    direction: Sentiment
    strength: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class SentimentResult:
    ticker: str
    sentiment: Sentiment
    confidence: ConfidenceLevel
    signals: list[Signal]
    summary: str
    key_factors: list[str]
    risks: list[str]
    disclaimer: str
    analyzed_at: datetime
    aggregated_report: AggregatedReport
