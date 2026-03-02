"""Reddit research agent for Trading Copilot."""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from trading_copilot.agents.base import (
    AgentExecutionError,
    ResearchAgent,
    WebSearchError,
)
from trading_copilot.models import AgentType, ArticleSentiment, RedditSourceConfig, Sentiment, Signal, SourceConfig


# Default subreddits if not configured
DEFAULT_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "StockMarket"]


class RedditPost:
    """Represents a Reddit post about a stock."""

    def __init__(
        self,
        title: str,
        subreddit: str,
        score: int,
        num_comments: int,
        url: str,
        created_at: datetime,
        snippet: str = "",
    ):
        self.title = title
        self.subreddit = subreddit
        self.score = score
        self.num_comments = num_comments
        self.url = url
        self.created_at = created_at
        self.snippet = snippet
        self.sentiment = ArticleSentiment.NEUTRAL


class RedditOutput:
    """Output from Reddit research."""

    def __init__(
        self,
        ticker: str,
        posts: list[RedditPost],
        retrieved_at: datetime,
        status: str,
        data_source: str = "reddit",
        error_message: Optional[str] = None,
        signal: Optional[Signal] = None,
    ):
        self.ticker = ticker
        self.posts = posts
        self.retrieved_at = retrieved_at
        self.status = status
        self.data_source = data_source
        self.error_message = error_message
        self.signal = signal


class RedditAgent(ResearchAgent):
    """Gathers sentiment from Reddit discussions."""

    def __init__(self, sources: list[SourceConfig]):
        """Initialize RedditAgent."""
        super().__init__(sources)
        self._http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
        )
        # Extract subreddits from config, fall back to defaults
        self._subreddits = self._get_subreddits_from_config(sources)

    def _get_subreddits_from_config(self, sources: list[SourceConfig]) -> list[str]:
        """Extract subreddits from source configuration."""
        for source in sources:
            if isinstance(source, RedditSourceConfig) and source.subreddits:
                return source.subreddits
        return DEFAULT_SUBREDDITS

    def get_agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.REDDIT

    async def research(
        self,
        ticker: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> RedditOutput:
        """
        Retrieve Reddit posts mentioning the ticker.

        Args:
            ticker: Validated stock ticker symbol
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)

        Returns:
            RedditOutput with posts from relevant subreddits
        """
        try:
            posts = await self._search_reddit(ticker, start_date, end_date)

            if not posts:
                return RedditOutput(
                    ticker=ticker,
                    posts=[],
                    retrieved_at=datetime.now(timezone.utc),
                    status="no_data",
                    error_message="No Reddit posts found",
                )

            # Filter by date range
            if start_date is not None and end_date is not None:
                # Filter to inclusive date range when parameters provided
                filtered_posts = [
                    p for p in posts
                    if start_date <= p.created_at.date() <= end_date
                ]
            else:
                # Default: filter to past 7 days
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
                filtered_posts = [p for p in posts if p.created_at >= cutoff_date]

            # Analyze sentiment
            for post in filtered_posts:
                post.sentiment = self._categorize_sentiment(post)

            # Generate signal from posts
            signal = self._generate_signal(filtered_posts)

            status = "success" if filtered_posts else "no_data"

            return RedditOutput(
                ticker=ticker,
                posts=filtered_posts,
                retrieved_at=datetime.now(timezone.utc),
                status=status,
                signal=signal,
            )

        except Exception as e:
            return RedditOutput(
                ticker=ticker,
                posts=[],
                retrieved_at=datetime.now(timezone.utc),
                status="error",
                error_message=str(e),
            )

    async def _search_reddit(
        self,
        ticker: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[RedditPost]:
        """
        Search Reddit using Google search with site:reddit.com.

        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)

        Returns:
            List of RedditPost objects
        """
        posts = []

        # Search in configured subreddits
        for subreddit in self._subreddits:
            try:
                # Use Google search to find Reddit posts
                query = f"site:reddit.com/r/{subreddit} {ticker}"
                search_url = f"https://www.google.com/search?q={query}&num=10"
                
                # Add date filter if date range is provided
                # Google search date filter format: tbs=cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY
                if start_date is not None and end_date is not None:
                    date_min = start_date.strftime("%m/%d/%Y")
                    date_max = end_date.strftime("%m/%d/%Y")
                    search_url += f"&tbs=cdr:1,cd_min:{date_min},cd_max:{date_max}"

                response = await self._http_client.get(search_url)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")

                # Parse Google search results for Reddit links
                for result in soup.select("div.g")[:5]:  # Top 5 results per subreddit
                    try:
                        link_elem = result.select_one("a")
                        if not link_elem or "reddit.com" not in link_elem.get("href", ""):
                            continue

                        title_elem = result.select_one("h3")
                        title = title_elem.text if title_elem else ""

                        snippet_elem = result.select_one("div.VwiC3b")
                        snippet = snippet_elem.text if snippet_elem else ""

                        url = link_elem.get("href", "")

                        # Create post (we don't have score/comments from Google search)
                        post = RedditPost(
                            title=title,
                            subreddit=subreddit,
                            score=0,  # Not available from Google search
                            num_comments=0,  # Not available from Google search
                            url=url,
                            created_at=datetime.now(timezone.utc),  # Approximate
                            snippet=snippet,
                        )
                        posts.append(post)

                    except Exception:
                        continue

            except Exception:
                continue

        return posts

    def _categorize_sentiment(self, post: RedditPost) -> ArticleSentiment:
        """
        Classify Reddit post sentiment.

        Args:
            post: RedditPost object

        Returns:
            ArticleSentiment (POSITIVE, NEGATIVE, or NEUTRAL)
        """
        text = f"{post.title} {post.snippet}".lower()

        # Reddit-specific keywords
        positive_keywords = [
            "moon", "rocket", "bullish", "calls", "buy", "long",
            "tendies", "gains", "breakout", "rally", "pump",
            "undervalued", "gem", "opportunity", "strong",
        ]
        negative_keywords = [
            "crash", "dump", "puts", "sell", "short", "bearish",
            "overvalued", "bubble", "bagholding", "loss", "down",
            "warning", "concern", "risk", "avoid",
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        # High score indicates popular/upvoted post (more bullish)
        if post.score > 100:
            positive_count += 1

        if positive_count > negative_count:
            return ArticleSentiment.POSITIVE
        elif negative_count > positive_count:
            return ArticleSentiment.NEGATIVE
        return ArticleSentiment.NEUTRAL
    def _generate_signal(self, posts: list[RedditPost]) -> Signal | None:
        """
        Generate aggregated sentiment signal from posts.

        Direction: Majority sentiment across posts (engagement-weighted)
        Strength: Weighted by engagement (score + comments)

        Args:
            posts: List of RedditPost objects with sentiment already classified

        Returns:
            Signal with source=REDDIT, direction, and strength, or None if no posts
        """
        if not posts:
            return None

        # Weight by engagement (score + comments + 1 to avoid zero weight)
        weighted_positive = sum(
            (p.score + p.num_comments + 1)
            for p in posts
            if p.sentiment == ArticleSentiment.POSITIVE
        )
        weighted_negative = sum(
            (p.score + p.num_comments + 1)
            for p in posts
            if p.sentiment == ArticleSentiment.NEGATIVE
        )

        total_weight = weighted_positive + weighted_negative
        if total_weight == 0:
            return None

        # Direction based on weighted majority
        if weighted_positive > weighted_negative:
            direction = Sentiment.BULLISH
            strength = weighted_positive / total_weight
        else:
            direction = Sentiment.BEARISH
            strength = weighted_negative / total_weight

        return Signal(
            source=AgentType.REDDIT,
            direction=direction,
            strength=min(strength, 1.0),
            reasoning=f"Based on {len(posts)} Reddit posts",
        )



    async def close(self):
        """Close the HTTP client."""
        await self._http_client.aclose()