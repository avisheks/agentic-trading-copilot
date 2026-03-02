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
