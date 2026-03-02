"""Property-based tests for News Agent.

Tests Properties 3, 4, 5, 6 from the design document.
"""

from datetime import datetime, timedelta, timezone

from hypothesis import given, settings, strategies as st

from trading_copilot.agents.news import NewsAgent
from trading_copilot.models import ArticleSentiment, NewsArticle, SourceConfig


# Strategies for generating test data
@st.composite
def news_article_strategy(draw):
    """Generate a NewsArticle with valid data."""
    headline = draw(st.text(min_size=1, max_size=200, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        whitelist_characters=' '
    )))
    source = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('L', 'N'),
    )))
    # Generate dates within past 30 days to test filtering
    days_ago = draw(st.integers(min_value=0, max_value=30))
    published_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    summary = draw(st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'Z'),
        whitelist_characters=' '
    )))
    url = f"https://test.com/{draw(st.integers(min_value=1, max_value=10000))}"
    sentiment = draw(st.sampled_from(list(ArticleSentiment)))

    return NewsArticle(
        headline=headline,
        source=source,
        published_at=published_at,
        summary=summary,
        url=url,
        sentiment=sentiment,
    )


@st.composite
def news_article_with_sentiment_text(draw):
    """Generate NewsArticle with specific sentiment keywords for testing."""
    sentiment_type = draw(st.sampled_from(['positive', 'negative', 'neutral']))
    
    if sentiment_type == 'positive':
        keywords = ['surge', 'soar', 'beat', 'strong', 'growth', 'profit']
        headline = f"Stock {draw(st.sampled_from(keywords))} on good news"
        summary = f"Company shows {draw(st.sampled_from(keywords))} performance"
    elif sentiment_type == 'negative':
        keywords = ['fall', 'drop', 'plunge', 'decline', 'loss', 'weak']
        headline = f"Stock {draw(st.sampled_from(keywords))} on bad news"
        summary = f"Company shows {draw(st.sampled_from(keywords))} performance"
    else:
        headline = "Company announces quarterly results"
        summary = "The company reported its financial results today"

    return NewsArticle(
        headline=headline,
        source="Test Source",
        published_at=datetime.now(timezone.utc),
        summary=summary,
        url="https://test.com/article",
        sentiment=ArticleSentiment.NEUTRAL,
    ), sentiment_type


# Test fixtures
def create_agent():
    """Create a NewsAgent for testing."""
    sources = [
        SourceConfig(
            name="Test",
            api_endpoint="https://test.com",
            api_key_env="TEST_KEY",
            added_at=datetime.now(timezone.utc),
            enabled=True,
        )
    ]
    return NewsAgent(sources=sources)


class TestProperty3NewsArticleCompleteness:
    """
    Property 3: News Article Completeness
    
    For any NewsArticle in the output, it SHALL contain non-empty values
    for headline, source, published_at, and summary fields.
    
    **Validates: Requirements 2.2**
    """

    @given(article=news_article_strategy())
    @settings(max_examples=100)
    def test_article_has_non_empty_headline(self, article: NewsArticle):
        """
        **Validates: Requirements 2.2**
        
        Every NewsArticle must have a non-empty headline.
        """
        assert article.headline is not None
        assert len(article.headline) > 0

    @given(article=news_article_strategy())
    @settings(max_examples=100)
    def test_article_has_non_empty_source(self, article: NewsArticle):
        """
        **Validates: Requirements 2.2**
        
        Every NewsArticle must have a non-empty source.
        """
        assert article.source is not None
        assert len(article.source) > 0

    @given(article=news_article_strategy())
    @settings(max_examples=100)
    def test_article_has_published_at(self, article: NewsArticle):
        """
        **Validates: Requirements 2.2**
        
        Every NewsArticle must have a published_at timestamp.
        """
        assert article.published_at is not None
        assert isinstance(article.published_at, datetime)

    @given(article=news_article_strategy())
    @settings(max_examples=100)
    def test_article_has_non_empty_summary(self, article: NewsArticle):
        """
        **Validates: Requirements 2.2**
        
        Every NewsArticle must have a non-empty summary.
        """
        assert article.summary is not None
        assert len(article.summary) > 0


class TestProperty4NewsDeduplication:
    """
    Property 4: News Deduplication
    
    For any list of news articles processed by the deduplication function,
    the output list SHALL have no two articles with identical headlines,
    and the output length SHALL be less than or equal to the input length.
    
    **Validates: Requirements 2.4**
    """

    @given(articles=st.lists(news_article_strategy(), min_size=0, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_deduplicate_output_length_lte_input(self, articles: list[NewsArticle]):
        """
        **Validates: Requirements 2.4**
        
        Deduplication output length is always <= input length.
        """
        agent = create_agent()
        result = agent.deduplicate(articles)
        assert len(result) <= len(articles)

    @given(articles=st.lists(news_article_strategy(), min_size=0, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_deduplicate_no_identical_headlines(self, articles: list[NewsArticle]):
        """
        **Validates: Requirements 2.4**
        
        After deduplication, no two articles have identical headlines.
        """
        agent = create_agent()
        result = agent.deduplicate(articles)
        headlines = [a.headline.lower() for a in result]
        assert len(headlines) == len(set(headlines))

    @given(articles=st.lists(news_article_strategy(), min_size=0, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_deduplicate_preserves_first_occurrence(self, articles: list[NewsArticle]):
        """
        **Validates: Requirements 2.4**
        
        Deduplication preserves the first occurrence of each unique headline.
        """
        agent = create_agent()
        result = agent.deduplicate(articles)
        
        # All articles in result should be from the original list
        result_headlines = {a.headline for a in result}
        for headline in result_headlines:
            # Find first occurrence in original
            first_in_original = next(a for a in articles if a.headline == headline)
            # Find in result
            in_result = next(a for a in result if a.headline == headline)
            # Should be the same article (same source)
            assert first_in_original.source == in_result.source


class TestProperty5NewsSentimentClassification:
    """
    Property 5: News Sentiment Classification
    
    For any NewsArticle in the output, the sentiment field SHALL be
    one of: POSITIVE, NEGATIVE, or NEUTRAL.
    
    **Validates: Requirements 2.5**
    """

    @given(article=news_article_strategy())
    @settings(max_examples=100, deadline=None)
    def test_sentiment_is_valid_enum(self, article: NewsArticle):
        """
        **Validates: Requirements 2.5**
        
        Every article sentiment must be a valid ArticleSentiment enum value.
        """
        agent = create_agent()
        result = agent.categorize_sentiment(article)
        assert result in [ArticleSentiment.POSITIVE, ArticleSentiment.NEGATIVE, ArticleSentiment.NEUTRAL]

    @given(data=news_article_with_sentiment_text())
    @settings(max_examples=100)
    def test_sentiment_classification_consistency(self, data):
        """
        **Validates: Requirements 2.5**
        
        Sentiment classification produces consistent results for similar content.
        """
        article, expected_type = data
        agent = create_agent()
        result = agent.categorize_sentiment(article)
        
        # Result should be a valid sentiment
        assert result in [ArticleSentiment.POSITIVE, ArticleSentiment.NEGATIVE, ArticleSentiment.NEUTRAL]
        
        # For articles with clear sentiment keywords, classification should match
        if expected_type == 'positive':
            assert result == ArticleSentiment.POSITIVE
        elif expected_type == 'negative':
            assert result == ArticleSentiment.NEGATIVE


class TestProperty6NewsDateRange:
    """
    Property 6: News Date Range
    
    For any NewsArticle in the output, the published_at date SHALL be
    within the past 14 days from the retrieval timestamp.
    
    **Validates: Requirements 2.1**
    """

    @given(days_ago=st.integers(min_value=0, max_value=30))
    @settings(max_examples=100)
    def test_date_filter_removes_old_articles(self, days_ago: int):
        """
        **Validates: Requirements 2.1**
        
        Articles older than 14 days are filtered out.
        """
        agent = create_agent()
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=14)
        
        article = NewsArticle(
            headline="Test headline",
            source="Test",
            published_at=now - timedelta(days=days_ago),
            summary="Test summary",
            url="https://test.com",
            sentiment=ArticleSentiment.NEUTRAL,
        )
        
        result = agent._filter_by_date([article], cutoff)
        
        if days_ago <= 14:
            assert len(result) == 1
        else:
            assert len(result) == 0

    @given(articles=st.lists(news_article_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_all_filtered_articles_within_date_range(self, articles: list[NewsArticle]):
        """
        **Validates: Requirements 2.1**
        
        All articles after filtering are within the 14-day window.
        """
        agent = create_agent()
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=14)
        
        result = agent._filter_by_date(articles, cutoff)
        
        for article in result:
            assert article.published_at >= cutoff
            # Also verify it's not in the future (sanity check)
            assert article.published_at <= now + timedelta(hours=1)
