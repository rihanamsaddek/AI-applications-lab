"""YouTube content fetcher (requires YOUTUBE_API_KEY)."""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from .base_fetcher import BaseFetcher, ContentItem

logger = logging.getLogger(__name__)


class YouTubeFetcher(BaseFetcher):
    """Fetches recent videos from YouTube channels using Data API v3."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self._service = None

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _get_service(self):
        if self._service is None:
            try:
                from googleapiclient.discovery import build
                self._service = build("youtube", "v3", developerKey=self.api_key)
            except ImportError:
                logger.warning("[YouTube] google-api-python-client not installed. Run: pip install google-api-python-client")
                return None
        return self._service

    def fetch_for_influencer(
        self,
        influencer_name: str,
        youtube_handle: Optional[str] = None,
        **kwargs,
    ) -> List[ContentItem]:
        if not self.is_available() or not youtube_handle:
            return []

        service = self._get_service()
        if service is None:
            return []

        try:
            handle = youtube_handle.lstrip("@")
            published_after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

            # Search for recent videos
            search_resp = service.search().list(
                part="snippet",
                channelType="any",
                q=f"@{handle}" if not youtube_handle.startswith("@") else youtube_handle,
                type="video",
                publishedAfter=published_after,
                maxResults=5,
            ).execute()

            items = []
            for result in search_resp.get("items", []):
                snippet = result.get("snippet", {})
                video_id = result.get("id", {}).get("videoId", "")
                if not video_id:
                    continue

                title = snippet.get("title", "")
                description = snippet.get("description", "")[:500]
                published_str = snippet.get("publishedAt", "")

                published_at = None
                if published_str:
                    try:
                        published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                items.append(ContentItem(
                    influencer_name=influencer_name,
                    platform="youtube",
                    content_text=f"{title}\n\n{description}",
                    content_url=f"https://www.youtube.com/watch?v={video_id}",
                    title=title,
                    engagement_score=0.0,  # Would need extra API call for stats
                    published_at=published_at,
                ))

            logger.info(f"[YouTube] Fetched {len(items)} videos for {youtube_handle}")
            return items

        except Exception as e:
            logger.error(f"[YouTube] Error fetching videos for {youtube_handle}: {e}")
            return []
