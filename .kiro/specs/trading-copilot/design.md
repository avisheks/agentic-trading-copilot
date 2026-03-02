# Design Document: Trading Copilot

## Overview

The Trading Copilot is a multi-agent system that provides stock sentiment analysis by orchestrating specialized research agents. The system follows an agent-based architecture where a central orchestrator coordinates News, Earnings, Macro, and Reddit agents to gather data concurrently, then synthesizes findings into a sentiment recommendation delivered via email.

The architecture prioritizes:
- **Modularity**: Each agent is independent and can be developed/tested in isolation
- **Resilience**: Partial failures don't block the entire pipeline; web search fallback ensures data availability
- **Extensibility**: New data sources and agents can be added via configuration
- **Traceability**: All recommendations are logged with full rationale and source citations for historical analysis
- **Source Attribution**: All findings include valid URLs linking to original sources

### Technology Stack

- **Language**: Python 3.11+ (excellent for data processing, rich ecosystem for financial APIs, strong async support)
- **Agent Framework**: AWS Strands Agents SDK for agent orchestration
- **LLM**: Claude (Anthropic) via Amazon Bedrock for sentiment analysis and summarization
- **Database**: SQLite for MVP (easily upgradeable to PostgreSQL)
- **Email**: SMTP with HTML templates (or Amazon SES for production)
- **Data Sources**: 
  - News: Google News RSS, CNBC RSS, Wall Street Journal RSS, Bloomberg RSS, MarketWatch RSS
  - Earnings: Alpha Vantage Earnings, Financial Modeling Prep
  - Macro: FRED API (Federal Reserve Economic Data)
  - Reddit: Reddit API, Google Search fallback for r/wallstreetbets, r/stocks, r/investing
- **Fallback**: Web search via RSS feeds and Google Search when API keys unavailable

## Architecture

```mermaid
flowchart TB
    subgraph Input
        User[User Input] --> |ticker, email| Orchestrator
    end
    
    subgraph Orchestrator[Trading Copilot Orchestrator]
        Validator[Ticker Validator]
        AgentCoordinator[Agent Coordinator]
        Aggregator[Report Aggregator]
        SentimentAnalyzer[Sentiment Analyzer]
        HistoryManager[History Manager]
    end
    
    subgraph Agents[Research Agents]
        NewsAgent[News Agent]
        EarningsAgent[Earnings Agent]
        MacroAgent[Macro Agent]
        RedditAgent[Reddit Agent]
    end
    
    subgraph DataSources[External Data Sources]
        NewsAPI[News APIs<br/>Google News, CNBC,<br/>WSJ, Bloomberg]
        EarningsAPI[Earnings APIs]
        MacroAPI[Macro APIs]
        RedditAPI[Reddit API]
        WebSearch[Web Search<br/>Fallback]
    end
    
    subgraph Storage
        ConfigFile[(Config File)]
        Database[(Recommendation DB)]
    end
    
    subgraph Output
        ReportGenerator[Report Generator]
        EmailService[Email Service]
    end
    
    Validator --> AgentCoordinator
    AgentCoordinator --> |concurrent| NewsAgent
    AgentCoordinator --> |concurrent| EarningsAgent
    AgentCoordinator --> |concurrent| MacroAgent
    AgentCoordinator --> |concurrent| RedditAgent
    
    NewsAgent --> |primary| NewsAPI
    NewsAgent --> |fallback| WebSearch
    EarningsAgent --> |primary| EarningsAPI
    EarningsAgent --> |fallback| WebSearch
    MacroAgent --> |primary| MacroAPI
    MacroAgent --> |fallback| WebSearch
    RedditAgent --> |primary| RedditAPI
    RedditAgent --> |fallback| WebSearch
    
    NewsAgent --> Aggregator
    EarningsAgent --> Aggregator
    MacroAgent --> Aggregator
    RedditAgent --> Aggregator
    
    ConfigFile --> Agents
    
    Aggregator --> SentimentAnalyzer
    HistoryManager --> SentimentAnalyzer
    Database --> HistoryManager
    
    SentimentAnalyzer --> ReportGenerator
    SentimentAnalyzer --> Database
    ReportGenerator --> EmailService
    EmailService --> |HTML Report| User
```

### Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant V as Validator
    participant H as History Manager
    participant NA as News Agent
    participant EA as Earnings Agent
    participant MA as Macro Agent
    participant RA as Reddit Agent
    participant S as Sentiment Analyzer
    participant R as Report Generator
    participant E as Email Service
    participant DB as Database
    
    U->>O: analyze(ticker, email)
    O->>V: validate(ticker)
    V-->>O: valid/invalid
    
    alt Invalid Ticker
        O-->>U: Error Response
    end
    
    par Concurrent Agent Execution
        O->>NA: research(ticker)
        O->>EA: research(ticker)
        O->>MA: research(ticker)
        O->>RA: research(ticker)
    end
    
    NA-->>O: NewsOutput
    EA-->>O: EarningsOutput
    MA-->>O: MacroOutput
    RA-->>O: RedditOutput
    
    O->>H: get_history(ticker)
    H->>DB: query
    DB-->>H: historical_records
    H-->>O: HistoricalReference
    
    O->>S: analyze(aggregated_data, history)
    S-->>O: SentimentResult
    
    O->>DB: save_recommendation
    O->>R: generate(sentiment_result)
    R-->>O: HTML Report
    O->>E: send(email, report)
    E-->>U: Email Delivered
```

## Components and Interfaces

### 1. Orchestrator (TradingCopilot)

The central coordinator that manages the entire analysis workflow.

```python
class TradingCopilot:
    """Main orchestrator for the trading analysis pipeline."""
    
    def __init__(self, config_path: str):
        """Initialize with path to data source configuration."""
        pass
    
    async def analyze(self, ticker: str, email: str) -> AnalysisResult:
        """
        Execute full analysis pipeline for a ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            email: Email address for report delivery
            
        Returns:
            AnalysisResult containing sentiment and metadata
            
        Raises:
            InvalidTickerError: If ticker validation fails
            ConfigurationError: If data sources are misconfigured
        """
        pass
    
    async def submit_feedback(self, recommendation_id: str, feedback: Feedback) -> None:
        """Record user feedback for a past recommendation."""
        pass
```

### 2. Ticker Validator

Validates stock ticker symbols against known exchanges.

```python
class TickerValidator:
    """Validates and normalizes stock ticker symbols."""
    
    def validate(self, ticker: str) -> ValidationResult:
        """
        Validate ticker against NYSE/NASDAQ listings.
        
        Args:
            ticker: Raw ticker input
            
        Returns:
            ValidationResult with normalized ticker or error details
        """
        pass
    
    def normalize(self, ticker: str) -> str:
        """Convert ticker to uppercase standard format."""
        pass
```

### 3. Research Agents

Base interface and specialized implementations for each research domain.

#### Data Source Strategy

Each agent implements a fallback strategy for data retrieval:

1. **Primary**: Use configured API sources (Alpha Vantage, Finnhub, FRED, Reddit API, etc.)
2. **Fallback**: If API keys are unavailable or API calls fail, use web search to gather information

```mermaid
flowchart TD
    A[Agent.research] --> B{API Keys Available?}
    B -->|Yes| C[Call API]
    B -->|No| D[Web Search Fallback]
    C --> E{API Success?}
    E -->|Yes| F[Parse API Response]
    E -->|No| D
    D --> G[Search Web for ticker + topic]
    G --> H[Parse Search Results]
    F --> I[Return Output with source URLs]
    H --> I
```

#### Web Search Fallback

When API keys are not configured or API calls fail, agents fall back to web search:

- **NewsAgent**: Fetches from multiple RSS feeds (Google News, CNBC, WSJ, Bloomberg, MarketWatch) and parses results
- **EarningsAgent**: Searches for `"{ticker} earnings report Q{quarter}"` and `"{ticker} earnings call transcript"`
- **MacroAgent**: Searches for `"{ticker} sector analysis"` and `"{ticker} macro factors"`
- **RedditAgent**: Uses Google Search with `site:reddit.com/r/{subreddit}` to find relevant discussions

The web search results are processed by Claude to extract structured data matching the expected output format. All results include source URLs linking to the original content.

```python
from abc import ABC, abstractmethod

class ResearchAgent(ABC):
    """Base class for all research agents."""
    
    def __init__(self, config: DataSourceConfig):
        """Initialize with data source configuration."""
        pass
    
    @abstractmethod
    async def research(self, ticker: str) -> ResearchOutput:
        """
        Execute research for the given ticker.
        
        Uses API sources if available, falls back to web search otherwise.
        All outputs include source URLs for traceability.
        
        Args:
            ticker: Validated stock ticker
            
        Returns:
            ResearchOutput with findings, metadata, and source URLs
        """
        pass
    
    @abstractmethod
    def get_agent_type(self) -> AgentType:
        """Return the type of this agent."""
        pass
    
    def _has_api_keys(self) -> bool:
        """Check if required API keys are configured."""
        pass
    
    async def _web_search_fallback(self, ticker: str, query: str) -> list[dict]:
        """
        Perform web search as fallback when APIs unavailable.
        
        Args:
            ticker: Stock ticker symbol
            query: Search query string
            
        Returns:
            List of search result dictionaries with title, url, snippet
        """
        pass
    
    def _parse_web_results(self, results: list[dict]) -> ResearchOutput:
        """Parse web search results into structured output using Claude."""
        pass


class NewsAgent(ResearchAgent):
    """Gathers and analyzes market news from multiple sources."""
    
    # Supported news sources
    NEWS_SOURCES = ["Google News", "CNBC", "Wall Street Journal", "Bloomberg", "MarketWatch"]
    
    async def research(self, ticker: str) -> NewsOutput:
        """
        Retrieve news articles from past 14 days from multiple sources.
        
        Falls back to RSS feeds if API keys unavailable.
        All articles include source URLs.
        """
        pass
    
    async def _research_via_api(self, ticker: str) -> NewsOutput:
        """Fetch news using configured API sources."""
        pass
    
    async def _research_via_rss_feeds(self, ticker: str) -> NewsOutput:
        """
        Fetch news using RSS feeds from multiple sources.
        
        Sources: Google News, CNBC, WSJ, Bloomberg, MarketWatch
        """
        pass
    
    def _combine_sources(self, results: dict[str, list[NewsArticle]]) -> list[NewsArticle]:
        """Combine articles from multiple sources into unified list."""
        pass
    
    def categorize_sentiment(self, article: NewsArticle) -> ArticleSentiment:
        """Classify article as positive, negative, or neutral."""
        pass
    
    def deduplicate(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """Remove duplicate or substantially similar articles."""
        pass


class EarningsAgent(ResearchAgent):
    """Analyzes company earnings data."""
    
    async def research(self, ticker: str) -> EarningsOutput:
        """
        Retrieve most recent earnings call data.
        
        Falls back to web search if API keys unavailable.
        Includes source URL to earnings report/transcript.
        """
        pass
    
    async def _research_via_api(self, ticker: str) -> EarningsOutput:
        """Fetch earnings using configured API sources."""
        pass
    
    async def _research_via_web_search(self, ticker: str) -> EarningsOutput:
        """Fetch earnings using web search fallback."""
        pass
    
    def compare_to_expectations(self, actual: EarningsData, expected: AnalystExpectations) -> EarningsComparison:
        """Determine if earnings beat/miss/met expectations."""
        pass


class MacroAgent(ResearchAgent):
    """Analyzes macro-economic trends."""
    
    async def research(self, ticker: str) -> MacroOutput:
        """
        Analyze macro factors relevant to ticker's sector.
        
        Falls back to web search if API keys unavailable.
        Includes source URLs for all macro data.
        """
        pass
    
    async def _research_via_api(self, ticker: str) -> MacroOutput:
        """Fetch macro data using configured API sources."""
        pass
    
    async def _research_via_web_search(self, ticker: str) -> MacroOutput:
        """Fetch macro data using web search fallback."""
        pass
    
    def identify_sector(self, ticker: str) -> Sector:
        """Determine the sector for macro analysis context."""
        pass


class RedditAgent(ResearchAgent):
    """Gathers sentiment from Reddit discussions."""
    
    # Target subreddits for stock discussions
    TARGET_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "StockMarket"]
    
    async def research(self, ticker: str) -> RedditOutput:
        """
        Retrieve Reddit posts mentioning the ticker from stock-related subreddits.
        
        Falls back to Google Search with site:reddit.com if API unavailable.
        All posts include URLs to original Reddit threads.
        """
        pass
    
    async def _research_via_api(self, ticker: str) -> RedditOutput:
        """Fetch Reddit posts using Reddit API."""
        pass
    
    async def _research_via_google_search(self, ticker: str) -> RedditOutput:
        """
        Fetch Reddit posts using Google Search fallback.
        
        Searches: site:reddit.com/r/{subreddit} {ticker}
        """
        pass
    
    def categorize_sentiment(self, post: RedditPost) -> ArticleSentiment:
        """
        Classify Reddit post sentiment based on content and engagement.
        
        Uses Reddit-specific keywords (moon, rocket, tendies, etc.)
        and engagement metrics (upvotes, comments).
        """
        pass
    
    def deduplicate(self, posts: list[RedditPost]) -> list[RedditPost]:
        """Remove duplicate posts (same URL or substantially similar title)."""
        pass
```

### 4. Sentiment Analyzer

Synthesizes all research into a final sentiment recommendation using Claude via Bedrock.

```python
class SentimentAnalyzer:
    """Analyzes aggregated research to produce sentiment using Claude."""
    
    def __init__(self, bedrock_client: BedrockClient):
        """Initialize with Bedrock client for Claude access."""
        pass
    
    def analyze(
        self, 
        aggregated: AggregatedReport, 
        history: HistoricalReference | None
    ) -> SentimentResult:
        """
        Produce sentiment analysis from aggregated data.
        
        Args:
            aggregated: Combined output from all agents (news, earnings, macro, reddit)
            history: Past recommendations for context (optional)
            
        Returns:
            SentimentResult with classification, rationale with citations, and source references
        """
        pass
    
    def calculate_confidence(
        self, 
        signals: list[Signal], 
        history_accuracy: float | None
    ) -> ConfidenceLevel:
        """Determine confidence level based on signal alignment and history."""
        pass
    
    def generate_rationale(
        self,
        sentiment: Sentiment,
        news: NewsOutput | None,
        earnings: EarningsOutput | None,
        macro: MacroOutput | None,
        reddit: RedditOutput | None
    ) -> str:
        """
        Generate sentiment rationale with explicit citations from sources.
        
        The rationale cites specific headlines, earnings data, macro factors,
        and Reddit discussions that support the sentiment classification.
        """
        pass
```

### 5. Report Generator

Creates HTML reports from analysis results with executive summary table and detailed sections.

```python
class ReportGenerator:
    """Generates HTML reports from analysis results."""
    
    def generate(self, result: SentimentResult, history: HistoricalReference | None) -> str:
        """
        Generate HTML report for a single ticker.
        
        Args:
            result: Complete sentiment analysis result
            history: Historical recommendations to include
            
        Returns:
            HTML string for email delivery
        """
        pass
    
    def generate_full_report(self, results: list[SentimentResult]) -> str:
        """
        Generate complete HTML report for multiple tickers.
        
        Includes:
        - Executive summary table at top with hyperlinks to detailed sections
        - Compact styling with reduced font size
        - All headlines as hyperlinks to source URLs
        - Navigation links back to summary
        - Source URLs for all findings
        
        Args:
            results: List of SentimentResult objects
            
        Returns:
            HTML string with summary table and detailed reports
        """
        pass
    
    def render_executive_summary_table(self, results: list[SentimentResult]) -> str:
        """
        Render executive summary table with one row per ticker.
        
        Columns: Ticker (hyperlink), Sentiment, Confidence, News Count, Key Signal
        """
        pass
    
    def render_ticker_section(self, result: SentimentResult, section_id: str) -> str:
        """
        Render detailed section for a single ticker.
        
        Includes back-to-top navigation link at bottom.
        """
        pass
    
    def render_news_section(self, news: NewsOutput | None, missing: bool) -> str:
        """
        Render news findings section.
        
        Headlines displayed as hyperlinks to source URLs.
        Shows source attribution for each article.
        """
        pass
    
    def render_reddit_section(self, reddit: RedditOutput | None, missing: bool) -> str:
        """
        Render Reddit sentiment section.
        
        Post titles displayed as hyperlinks to Reddit threads.
        Shows subreddit, score, and sentiment for each post.
        """
        pass
    
    def render_earnings_section(self, earnings: EarningsOutput | None, missing: bool) -> str:
        """
        Render earnings section.
        
        Correctly displays earnings data when available (not "missing earnings").
        Includes source URL to earnings report.
        """
        pass
    
    def render_sentiment_rationale(self, rationale: str) -> str:
        """Render sentiment rationale with citations."""
        pass
```

### 6. Email Service

Handles email delivery of reports.

```python
class EmailService:
    """Sends HTML reports via email."""
    
    def __init__(self, smtp_config: SMTPConfig):
        """Initialize with SMTP configuration."""
        pass
    
    async def send(self, to_email: str, subject: str, html_content: str) -> DeliveryResult:
        """
        Send HTML email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML report content
            
        Returns:
            DeliveryResult with status and message ID
        """
        pass
```

### 7. History Manager

Manages recommendation history and feedback.

```python
class HistoryManager:
    """Manages recommendation history and feedback."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        pass
    
    def save_recommendation(self, recommendation: Recommendation) -> str:
        """
        Save recommendation to database.
        
        Args:
            recommendation: Complete recommendation record
            
        Returns:
            Recommendation ID
        """
        pass
    
    def get_history(self, ticker: str, limit: int = 10) -> HistoricalReference:
        """
        Retrieve past recommendations for a ticker.
        
        Args:
            ticker: Stock ticker to query
            limit: Maximum records to return
            
        Returns:
            HistoricalReference with past recommendations
        """
        pass
    
    def add_feedback(self, recommendation_id: str, feedback: Feedback) -> None:
        """Associate feedback with a recommendation."""
        pass
    
    def calculate_accuracy(self, ticker: str) -> float | None:
        """Calculate historical accuracy for a ticker based on feedback."""
        pass
```

### 8. Configuration Manager

Loads and validates data source configuration.

```python
class ConfigManager:
    """Manages data source configuration."""
    
    def __init__(self, config_path: str):
        """Initialize with config file path."""
        pass
    
    def load(self) -> DataSourceConfig:
        """
        Load and validate configuration.
        
        Returns:
            Validated DataSourceConfig
            
        Raises:
            ConfigurationError: If config is invalid
        """
        pass
    
    def validate(self, config: dict) -> list[str]:
        """Return list of validation errors (empty if valid)."""
        pass
    
    def get_sources_for_agent(self, agent_type: AgentType) -> list[SourceConfig]:
        """Get configured data sources for an agent type."""
        pass
```

## Data Models

```python
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
class NewsArticle:
    headline: str
    source: str  # e.g., "Google News", "CNBC", "WSJ", "Bloomberg"
    published_at: datetime
    summary: str
    url: str  # Required: URL to original article
    sentiment: ArticleSentiment


@dataclass
class NewsOutput:
    ticker: str
    articles: list[NewsArticle]
    retrieved_at: datetime
    status: str  # "success", "partial", "no_data"
    data_source: str = "api"  # "api", "rss_feeds", or "web_search"
    sources_used: list[str] = None  # List of news sources queried
    error_message: str | None = None


@dataclass
class EarningsData:
    fiscal_quarter: str
    revenue: float
    eps: float
    guidance: str | None
    management_commentary: str | None
    report_date: datetime
    source_url: str | None = None  # URL to earnings report/transcript


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
    source_url: str | None = None  # URL to earnings source
    error_message: str | None = None


@dataclass
class MacroFactor:
    category: str  # "geopolitical", "interest_rates", "supply_chain", "trade"
    description: str
    impact: str  # "positive", "negative", "neutral"
    relevance: str  # Why this matters for the ticker
    source_url: str | None = None  # URL to source for this factor


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
    source_urls: list[str] = None  # URLs to macro data sources
    error_message: str | None = None


@dataclass
class RedditPost:
    """Represents a Reddit post about a stock."""
    title: str
    subreddit: str  # e.g., "wallstreetbets", "stocks", "investing"
    score: int  # Upvote count
    num_comments: int
    url: str  # Required: URL to original Reddit post
    created_at: datetime
    snippet: str  # Summary or first part of post content
    sentiment: ArticleSentiment


@dataclass
class RedditOutput:
    """Output from Reddit research agent."""
    ticker: str
    posts: list[RedditPost]
    retrieved_at: datetime
    status: str  # "success", "partial", "no_data", "error"
    data_source: str = "reddit"  # "reddit_api" or "google_search"
    subreddits_searched: list[str] = None  # List of subreddits queried
    error_message: str | None = None


@dataclass
class AggregatedReport:
    ticker: str
    news: NewsOutput | None
    earnings: EarningsOutput | None
    macro: MacroOutput | None
    reddit: RedditOutput | None
    aggregated_at: datetime
    missing_components: list[AgentType]


@dataclass
class Signal:
    source: AgentType
    direction: Sentiment
    strength: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class SentimentRationale:
    """Detailed rationale for sentiment with source citations."""
    summary: str  # Overall rationale summary
    news_citations: list[str]  # Specific news headlines cited
    earnings_citations: list[str]  # Earnings data points cited
    macro_citations: list[str]  # Macro factors cited
    reddit_citations: list[str]  # Reddit posts cited
    html_formatted: str  # HTML-formatted rationale with links


@dataclass
class SentimentResult:
    ticker: str
    sentiment: Sentiment
    confidence: ConfidenceLevel
    signals: list[Signal]
    summary: str
    rationale: SentimentRationale | None  # Detailed rationale with citations
    key_factors: list[str]
    risks: list[str]
    disclaimer: str
    analyzed_at: datetime
    aggregated_report: AggregatedReport


@dataclass
class HistoricalRecommendation:
    recommendation_id: str
    ticker: str
    sentiment: Sentiment
    confidence: ConfidenceLevel
    summary: str
    created_at: datetime
    feedback: Optional["Feedback"] = None


@dataclass
class HistoricalReference:
    ticker: str
    recommendations: list[HistoricalRecommendation]
    accuracy_rate: float | None  # Based on feedback
    is_first_analysis: bool


@dataclass
class Feedback:
    outcome: str  # "accurate", "inaccurate", "partially_accurate"
    actual_movement: str  # "up", "down", "flat"
    notes: str | None
    submitted_at: datetime


@dataclass
class Recommendation:
    ticker: str
    email: str
    sentiment_result: SentimentResult
    created_at: datetime


@dataclass
class SourceConfig:
    name: str
    api_endpoint: str
    api_key_env: str  # Environment variable name for API key
    added_at: datetime
    enabled: bool = True


@dataclass
class DataSourceConfig:
    news_sources: list[SourceConfig]
    earnings_sources: list[SourceConfig]
    macro_sources: list[SourceConfig]
    reddit_sources: list[SourceConfig]
    last_updated: datetime


@dataclass
class SMTPConfig:
    host: str
    port: int
    username: str
    password_env: str  # Environment variable name
    from_email: str
    use_tls: bool = True


@dataclass
class AnalysisResult:
    success: bool
    recommendation_id: str | None
    sentiment_result: SentimentResult | None
    error_message: str | None


@dataclass
class DeliveryResult:
    success: bool
    message_id: str | None
    error_message: str | None
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Ticker Normalization

*For any* ticker string input, the normalized output SHALL be the uppercase version of the input string.

**Validates: Requirements 1.4**

### Property 2: Invalid Ticker Error Handling

*For any* string that is not a valid NYSE or NASDAQ ticker symbol, the system SHALL return a ValidationResult with `is_valid=False` and a non-empty `error_message`.

**Validates: Requirements 1.2**

### Property 3: News Article Completeness

*For any* NewsArticle in the output, it SHALL contain non-empty values for headline, source, published_at, summary, and url fields.

**Validates: Requirements 2.2, 2.8**

### Property 4: News Deduplication

*For any* list of news articles processed by the deduplication function, the output list SHALL have no two articles with identical headlines, and the output length SHALL be less than or equal to the input length.

**Validates: Requirements 2.4**

### Property 5: News Sentiment Classification

*For any* NewsArticle in the output, the sentiment field SHALL be one of: POSITIVE, NEGATIVE, or NEUTRAL.

**Validates: Requirements 2.5**

### Property 6: News Date Range

*For any* NewsArticle in the output, the published_at date SHALL be within the past 14 days from the retrieval timestamp.

**Validates: Requirements 2.1**

### Property 7: News Multi-Source Retrieval

*For any* successful NewsOutput, the articles SHALL include content from multiple news sources (Google News, CNBC, WSJ, Bloomberg, MarketWatch), and the sources_used field SHALL list all sources queried.

**Validates: Requirements 2.6, 2.7**

### Property 8: Earnings Data Completeness

*For any* EarningsOutput with status "success", the earnings field SHALL contain non-null values for fiscal_quarter, revenue, eps, and report_date, and SHALL include a source_url linking to the earnings report.

**Validates: Requirements 3.2, 3.6**

### Property 9: Earnings Comparison Validity

*For any* EarningsOutput with both earnings data and analyst expectations, the comparison field SHALL be one of: BEAT, MISS, or MEET.

**Validates: Requirements 3.3**

### Property 10: Agent Failure Isolation

*For any* agent that fails during execution, the other agents SHALL complete their execution, and the AggregatedReport SHALL list the failed agent in missing_components while containing results from successful agents.

**Validates: Requirements 3.5, 4.5, 5.3**

### Property 11: Macro Analysis Completeness

*For any* MacroOutput with status "success", it SHALL contain a non-empty sector, at least one MacroFactor with source_url, and non-empty risks and opportunities lists.

**Validates: Requirements 5.1, 5.5, 5.6**

### Property 12: Reddit Post Completeness

*For any* RedditPost in the output, it SHALL contain non-empty values for title, subreddit, url (containing "reddit.com"), and created_at fields.

**Validates: Requirements 4.2, 4.6**

### Property 13: Reddit Sentiment Classification

*For any* RedditPost in the output, the sentiment field SHALL be one of: POSITIVE, NEGATIVE, or NEUTRAL.

**Validates: Requirements 4.3**

### Property 14: Reddit No-Data Handling

*For any* ticker with no recent Reddit discussions, the RedditOutput SHALL have an empty posts list and status of "no_data" with an appropriate error_message.

**Validates: Requirements 4.4**

### Property 15: Reddit Subreddit Coverage

*For any* successful RedditOutput, the subreddits_searched field SHALL include at least one of: wallstreetbets, stocks, investing, or StockMarket.

**Validates: Requirements 4.1**

### Property 16: Aggregation Completeness

*For any* AggregatedReport, it SHALL contain the ticker, outputs from all successful agents (news, earnings, macro, reddit) with their retrieved_at timestamps preserved, and an aggregated_at timestamp.

**Validates: Requirements 6.1, 6.4, 6.5**

### Property 17: Sentiment Result Completeness

*For any* SentimentResult, it SHALL contain: a sentiment value of BULLISH or BEARISH, a confidence level of HIGH/MEDIUM/LOW, a non-empty summary, a non-empty key_factors list, a risks list, and a disclaimer containing "not financial advice".

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6, 7.7**

### Property 18: Sentiment Rationale Citations

*For any* SentimentResult with a rationale, the rationale SHALL explicitly cite specific information from at least one of: news headlines, earnings data, Reddit discussions, or macro analysis that support the sentiment classification.

**Validates: Requirements 7.5**

### Property 19: Report Executive Summary Table

*For any* generated HTML report with multiple tickers, it SHALL contain an executive summary table at the top with one row per ticker, each containing: ticker name as hyperlink to detailed section, sentiment badge, confidence badge, and news count.

**Validates: Requirements 8.2**

### Property 20: Report Headlines as Hyperlinks

*For any* news headline displayed in the HTML report, it SHALL be rendered as a hyperlink (`<a>` tag) with href pointing to the article's source URL.

**Validates: Requirements 8.8**

### Property 21: Report URL Validity

*For any* URL in the generated HTML report (href attributes), it SHALL NOT contain placeholder domains (example.com, placeholder.com, test.com) and SHALL be a valid URL format.

**Validates: Requirements 8.9**

### Property 22: Report Navigation Links

*For any* ticker's detailed section in the HTML report, it SHALL include a navigation link at the bottom that links back to the executive summary table (href="#top" or similar anchor).

**Validates: Requirements 8.10**

### Property 23: Report Source URL Display

*For any* finding (news article, earnings data, macro factor, Reddit post) displayed in the HTML report, the source URL from which the information was collected SHALL be displayed or linked.

**Validates: Requirements 8.11**

### Property 24: Report Earnings Display Correctness

*For any* report generated from an AggregatedReport where earnings data is present (earnings field is not None and status is "success"), the HTML output SHALL NOT contain "missing earnings" or similar error indicators for that ticker.

**Validates: Requirements 8.12**

### Property 25: Report Structure

*For any* generated HTML report, it SHALL contain an executive summary section appearing before detailed sections, and SHALL be valid HTML with distinct section elements.

**Validates: Requirements 8.1, 8.3**

### Property 26: Report Error Indication

*For any* report generated from an AggregatedReport with non-empty missing_components, the HTML output SHALL contain visible indicators for each missing component.

**Validates: Requirements 8.5**

### Property 27: Web Search Fallback Activation

*For any* agent where API keys are not configured or API calls fail, the agent SHALL fall back to web search and return a valid output with the same structure as API-sourced data. The output data_source field SHALL indicate "web_search", "rss_feeds", or "google_search".

**Validates: Requirements 10.1, 10.2**

### Property 28: Web Search Data Integration

*For any* data retrieved via web search fallback, it SHALL be included in the AggregatedReport and used for downstream sentiment analysis, with source URLs preserved.

**Validates: Requirements 10.4**

### Property 29: End-to-End Without API Keys

*For any* analysis request when API keys are unavailable, the system SHALL complete end-to-end and generate a valid HTML report with real data (not mock data) using web search fallback.

**Validates: Requirements 10.5**

### Property 30: Config Validation

*For any* DataSourceConfig, it SHALL be parseable from the config file, and each SourceConfig SHALL contain non-empty api_endpoint, api_key_env, and added_at fields. Invalid configs SHALL produce validation errors.

**Validates: Requirements 9.1, 9.2, 9.5**

### Property 31: Config Source Round-Trip

*For any* data source added to the config and then removed, the system SHALL use the source while present and exclude it after removal, without requiring code changes.

**Validates: Requirements 9.3, 9.4**

### Property 32: Recommendation Storage Completeness

*For any* recommendation saved to the database, querying by its ID SHALL return the complete record including ticker, sentiment_result, and the full aggregated_report.

**Validates: Requirements 11.1, 11.2**

### Property 33: Feedback Association

*For any* feedback submitted for a recommendation_id, querying that recommendation SHALL return the associated feedback with outcome, actual_movement, and submitted_at.

**Validates: Requirements 11.3**

### Property 34: History Query Correctness

*For any* set of recommendations stored for a ticker within a date range, querying by that ticker and date range SHALL return exactly those recommendations.

**Validates: Requirements 11.4**

### Property 35: Database Failure Resilience

*For any* database write failure during recommendation storage, the system SHALL log the error and still deliver the email report successfully.

**Validates: Requirements 11.5**

### Property 36: Historical Reference Inclusion

*For any* ticker with existing recommendations in the database, the generated report SHALL include a HistoricalReference section containing past sentiment, date, and feedback for each historical recommendation.

**Validates: Requirements 12.1, 12.2, 12.3**

### Property 37: History Affects Confidence

*For any* ticker with historical recommendations that have accuracy feedback, the confidence calculation SHALL factor in the historical accuracy rate.

**Validates: Requirements 12.4**

### Property 38: First Analysis Indicator

*For any* ticker with no historical recommendations, the HistoricalReference SHALL have is_first_analysis=True.

**Validates: Requirements 12.5**

## Error Handling

### Input Validation Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `InvalidTickerError` | Ticker not found in NYSE/NASDAQ | Return ValidationResult with error message, do not proceed |
| `EmptyTickerError` | Empty or whitespace-only input | Return immediate error, no API calls |
| `InvalidEmailError` | Malformed email address | Return error before starting research |

### Data Source Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `APIConnectionError` | Network failure to data source | Retry with exponential backoff (3 attempts), then fall back to web search |
| `APIRateLimitError` | Rate limit exceeded | Wait and retry, fall back to web search if retries exhausted |
| `APIAuthenticationError` | Invalid or missing API credentials | Fall back to web search immediately |
| `APIKeyMissingError` | API key environment variable not set | Fall back to web search immediately |
| `DataParseError` | Unexpected API response format | Log raw response, fall back to web search |
| `WebSearchError` | Web search failed | Log error, mark agent as failed, continue with other agents |
| `RSSFeedError` | RSS feed unavailable or malformed | Try next RSS source, fall back to web search if all fail |

### Agent Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `AgentTimeoutError` | Agent exceeds time limit (30s) | Cancel agent, mark as failed, continue with others |
| `AgentExecutionError` | Unhandled exception in agent | Log stack trace, mark as failed, continue with others |
| `NewsAgentError` | News retrieval failed from all sources | Mark NEWS as missing, continue with other agents |
| `EarningsAgentError` | Earnings retrieval failed | Mark EARNINGS as missing, continue with other agents |
| `MacroAgentError` | Macro analysis failed | Mark MACRO as missing, continue with other agents |
| `RedditAgentError` | Reddit retrieval failed from all sources | Mark REDDIT as missing, continue with other agents |

### Database Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `DatabaseConnectionError` | Cannot connect to SQLite | Log error, continue with report delivery |
| `DatabaseWriteError` | Failed to save recommendation | Log error, continue with report delivery |
| `DatabaseQueryError` | Failed to query history | Log error, proceed without historical reference |

### Email Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `SMTPConnectionError` | Cannot connect to mail server | Retry 3 times, then return error to user |
| `EmailDeliveryError` | Email rejected by server | Log error, return failure status with details |

### Error Response Strategy

1. **Graceful Degradation**: System continues with available data when individual components fail
2. **Transparent Reporting**: All errors are reflected in the final report with clear indicators
3. **Logging**: All errors logged with context for debugging
4. **No Silent Failures**: User always receives feedback about what succeeded and what failed
5. **Fallback Chain**: API → Web Search → Mark as Missing (never blocks other agents)

## Testing Strategy

### Dual Testing Approach

The Trading Copilot uses both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, integration points, and error conditions
- **Property tests**: Verify universal properties across randomly generated inputs

### Property-Based Testing Configuration

- **Library**: Hypothesis (Python's leading PBT library)
- **Minimum iterations**: 100 per property test
- **Tag format**: `# Feature: trading-copilot, Property {N}: {property_text}`

### Test Categories

#### Unit Tests

1. **Ticker Validation**
   - Known valid tickers (AAPL, GOOGL, MSFT)
   - Known invalid tickers (XXXXX, 12345)
   - Edge cases (empty string, special characters)

2. **Agent Integration**
   - Mock API responses for each agent (News, Earnings, Macro, Reddit)
   - Timeout handling
   - Malformed response handling
   - Web search fallback triggering

3. **News Agent Multi-Source**
   - RSS feed parsing from each source (Google News, CNBC, WSJ, Bloomberg, MarketWatch)
   - Source combination and deduplication
   - URL extraction and validation

4. **Reddit Agent**
   - Google Search fallback for Reddit posts
   - Subreddit filtering
   - Sentiment classification with Reddit-specific keywords
   - URL validation (must contain reddit.com)

5. **Report Generation**
   - HTML structure validation
   - Executive summary table with hyperlinks
   - Headlines rendered as hyperlinks
   - Navigation links (back to top)
   - Source URL display
   - Earnings display correctness (no false "missing" indicators)
   - Mobile responsiveness (CSS validation)

6. **Sentiment Rationale**
   - Citation generation from news articles
   - Citation generation from Reddit posts
   - Citation generation from earnings data
   - Citation generation from macro factors

7. **Email Delivery**
   - SMTP connection mocking
   - Delivery confirmation handling

8. **Database Operations**
   - CRUD operations for recommendations
   - Query by ticker and date range
   - Feedback association

#### Property Tests

Each correctness property (1-38) will have a corresponding property-based test:

```python
from hypothesis import given, strategies as st, settings

# Feature: trading-copilot, Property 1: Ticker Normalization
@given(ticker=st.text(min_size=1, max_size=10))
@settings(max_examples=100)
def test_ticker_normalization(ticker):
    result = normalize_ticker(ticker)
    assert result == ticker.upper()

# Feature: trading-copilot, Property 4: News Deduplication
@given(articles=st.lists(st.builds(NewsArticle, ...)))
@settings(max_examples=100)
def test_news_deduplication(articles):
    result = deduplicate(articles)
    headlines = [a.headline for a in result]
    assert len(headlines) == len(set(headlines))  # No duplicates
    assert len(result) <= len(articles)

# Feature: trading-copilot, Property 12: Reddit Post Completeness
@given(post=st.builds(RedditPost, ...))
@settings(max_examples=100)
def test_reddit_post_completeness(post):
    assert post.title
    assert post.subreddit
    assert post.url
    assert "reddit.com" in post.url
    assert post.created_at is not None

# Feature: trading-copilot, Property 17: Sentiment Result Completeness
@given(report=st.builds(AggregatedReport, ...))
@settings(max_examples=100)
def test_sentiment_result_completeness(report):
    result = analyze_sentiment(report)
    assert result.sentiment in [Sentiment.BULLISH, Sentiment.BEARISH]
    assert result.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
    assert len(result.summary) > 0
    assert len(result.key_factors) > 0
    assert "not financial advice" in result.disclaimer.lower()

# Feature: trading-copilot, Property 20: Report Headlines as Hyperlinks
@given(articles=st.lists(st.builds(NewsArticle, ...), min_size=1))
@settings(max_examples=100)
def test_report_headlines_as_hyperlinks(articles):
    html = render_news_section(articles)
    for article in articles:
        # Each headline should be in an <a> tag with href
        assert f'href="{article.url}"' in html or f"href='{article.url}'" in html

# Feature: trading-copilot, Property 21: Report URL Validity
@given(result=st.builds(SentimentResult, ...))
@settings(max_examples=100)
def test_report_url_validity(result):
    html = generate_report(result)
    # No placeholder URLs
    assert "example.com" not in html
    assert "placeholder.com" not in html
    assert "test.com" not in html

# Feature: trading-copilot, Property 27: Web Search Fallback Activation
@given(ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu',))))
@settings(max_examples=100)
def test_web_search_fallback(ticker):
    # With no API keys configured
    agent = NewsAgent(sources=[])
    result = agent.research(ticker)
    assert result.data_source in ["web_search", "rss_feeds"]
```

### Test Data Generation

- **Tickers**: Generate random uppercase strings, mix of valid/invalid
- **News Articles**: Generate with random headlines, dates within/outside 14-day window, valid URLs
- **Reddit Posts**: Generate with random titles, subreddits from target list, reddit.com URLs
- **Earnings Data**: Generate with random financial figures, various comparison scenarios
- **Macro Factors**: Generate with random categories, impacts, and source URLs
- **Historical Data**: Generate recommendation histories with various feedback patterns

### Integration Testing

1. **End-to-End Flow**: Test complete pipeline with mocked external APIs
2. **End-to-End Without API Keys**: Test complete pipeline using web search fallback only
3. **Concurrent Agent Execution**: Verify all four agents (News, Earnings, Macro, Reddit) run in parallel
4. **Failure Scenarios**: Test various combinations of agent failures
5. **Database Persistence**: Verify data survives application restart
6. **Multi-Ticker Reports**: Test executive summary table generation with multiple tickers

### Test Environment

- **Mocking**: Use `unittest.mock` for external API calls
- **Database**: Use in-memory SQLite for fast test execution
- **Email**: Use mock SMTP server (e.g., `aiosmtpd`)
- **CI Integration**: Run all tests on every commit
