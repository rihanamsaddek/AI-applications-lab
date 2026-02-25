"""Twitter/X content fetcher (requires TWITTER_BEARER_TOKEN)."""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from .base_fetcher import BaseFetcher, ContentItem

logger = logging.getLogger(__name__)


class TwitterFetcher(BaseFetcher):
    """Fetches recent tweets from influencer accounts using Twitter API v2."""

    def __init__(self, bearer_token: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.bearer_token = bearer_token
        self._client = None

    def is_available(self) -> bool:
        return bool(self.bearer_token)

    def _get_client(self):
        if self._client is None:
            try:
                import tweepy
                self._client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
            except ImportError:
                logger.warning("[Twitter] tweepy not installed. Run: pip install tweepy")
                return None
        return self._client

    def fetch_for_influencer(
        self,
        influencer_name: str,
        twitter_handle: Optional[str] = None,
        **kwargs,
    ) -> List[ContentItem]:
        if not self.is_available() or not twitter_handle:
            return []

        client = self._get_client()
        if client is None:
            return []

        try:
            import tweepy
            # Remove @ prefix if present
            handle = twitter_handle.lstrip("@")

            # Look up user ID
            user_resp = client.get_user(username=handle)
            if not user_resp.data:
                logger.warning(f"[Twitter] User not found: {handle}")
                return []

            user_id = user_resp.data.id
            start_time = datetime.now(timezone.utc) - timedelta(hours=48)

            tweets_resp = client.get_users_tweets(
                id=user_id,
                max_results=20,
                start_time=start_time,
                tweet_fields=["created_at", "public_metrics", "text"],
                exclude=["retweets", "replies"],
            )

            if not tweets_resp.data:
                return []

            items = []
            for tweet in tweets_resp.data:
                metrics = tweet.public_metrics or {}
                engagement = (
                    metrics.get("like_count", 0) * 1.0
                    + metrics.get("retweet_count", 0) * 2.0
                    + metrics.get("reply_count", 0) * 1.5
                )
                items.append(ContentItem(
                    influencer_name=influencer_name,
                    platform="twitter",
                    content_text=tweet.text,
                    content_url=f"https://twitter.com/{handle}/status/{tweet.id}",
                    engagement_score=engagement,
                    published_at=tweet.created_at,
                ))

            logger.info(f"[Twitter] Fetched {len(items)} tweets for @{handle}")
            return items

        except Exception as e:
            logger.error(f"[Twitter] Error fetching tweets for {twitter_handle}: {e}")
            return []
