"""Abstract base class for all content fetchers."""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContentItem:
    """A single piece of content fetched from an influencer platform."""
    influencer_name: str
    platform: str
    content_text: str
    content_url: str
    title: Optional[str] = None
    engagement_score: float = 0.0
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    def to_summary(self, max_chars: int = 500) -> str:
        """Return a short, formatted summary for use in prompts."""
        title_part = f"[{self.title}] " if self.title else ""
        text = self.content_text[:max_chars]
        if len(self.content_text) > max_chars:
            text += "..."
        return (
            f"Source: {self.influencer_name} ({self.platform})\n"
            f"{title_part}{text}\n"
            f"URL: {self.content_url}\n"
            f"Engagement: {self.engagement_score:.0f}"
        )


class BaseFetcher(ABC):
    """Base class for all platform content fetchers."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this fetcher has the required credentials."""

    @abstractmethod
    def fetch_for_influencer(self, influencer_name: str, **kwargs) -> List[ContentItem]:
        """Fetch recent content for a single influencer."""

    def fetch_with_retry(self, influencer_name: str, **kwargs) -> List[ContentItem]:
        """Fetch content with exponential backoff on transient errors."""
        for attempt in range(self.max_retries):
            try:
                return self.fetch_for_influencer(influencer_name, **kwargs)
            except Exception as e:
                wait = 2 ** attempt
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"[{self.__class__.__name__}] Attempt {attempt + 1} failed for "
                        f"'{influencer_name}': {e}. Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        f"[{self.__class__.__name__}] All {self.max_retries} attempts failed "
                        f"for '{influencer_name}': {e}"
                    )
        return []
