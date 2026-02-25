"""Unit tests for content fetchers."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from content_fetchers.base_fetcher import ContentItem
from content_fetchers.rss_fetcher import RSSFetcher
from content_fetchers.twitter_fetcher import TwitterFetcher
from content_fetchers.youtube_fetcher import YouTubeFetcher

from datetime import timedelta

# Build test XMLs with dates within the last 24 hours (always recent)
def _recent_rss_date() -> str:
    """Return RFC 2822 date string for 6 hours ago."""
    dt = datetime.now(timezone.utc) - timedelta(hours=6)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def _recent_atom_date() -> str:
    """Return ISO 8601 date string for 6 hours ago."""
    dt = datetime.now(timezone.utc) - timedelta(hours=6)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class TestRSSFetcher:
    def setup_method(self):
        self.fetcher = RSSFetcher()

    def test_is_available(self):
        assert self.fetcher.is_available() is True

    def test_fetch_without_url_returns_empty(self):
        result = self.fetcher.fetch_for_influencer("Test Influencer")
        assert result == []

    def test_fetch_rss_feed(self):
        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>AI is changing everything</title>
      <link>https://example.com/post1</link>
      <description>A detailed look at how AI transforms industries.</description>
      <pubDate>{_recent_rss_date()}</pubDate>
    </item>
  </channel>
</rss>"""
        mock_resp = MagicMock()
        mock_resp.text = rss_xml
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_resp):
            result = self.fetcher.fetch_for_influencer(
                "Test Influencer", feed_url="https://example.com/feed"
            )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].title == "AI is changing everything"
        assert result[0].platform == "rss"
        assert result[0].influencer_name == "Test Influencer"

    def test_fetch_atom_feed(self):
        atom_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <entry>
    <title>Generative AI in 2026</title>
    <link href="https://example.com/atom-post1"/>
    <updated>{_recent_atom_date()}</updated>
    <summary>How GenAI is reshaping business in 2026.</summary>
  </entry>
</feed>"""
        mock_resp = MagicMock()
        mock_resp.text = atom_xml
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_resp):
            result = self.fetcher.fetch_for_influencer(
                "Atom Influencer", feed_url="https://example.com/atom"
            )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].title == "Generative AI in 2026"

    def test_fetch_http_error_returns_empty(self):
        with patch("requests.get", side_effect=Exception("Connection error")):
            result = self.fetcher.fetch_for_influencer(
                "Test", feed_url="https://example.com/feed"
            )
        assert result == []

    def test_strip_html(self):
        html = "<p>Hello <b>world</b>!</p>"
        result = RSSFetcher._strip_html(html)
        assert "<" not in result
        assert "Hello" in result
        assert "world" in result

    def test_content_item_structure(self):
        item = ContentItem(
            influencer_name="Ethan Mollick",
            platform="rss",
            content_text="AI is transforming education in unexpected ways.",
            content_url="https://example.com/post",
        )
        summary = item.to_summary()
        assert "Ethan Mollick" in summary
        assert "rss" in summary
        assert "https://example.com/post" in summary


class TestTwitterFetcher:
    def test_is_available_with_token(self):
        fetcher = TwitterFetcher(bearer_token="test_token")
        assert fetcher.is_available() is True

    def test_is_available_without_token(self):
        fetcher = TwitterFetcher(bearer_token=None)
        assert fetcher.is_available() is False

    def test_fetch_without_handle_returns_empty(self):
        fetcher = TwitterFetcher(bearer_token="test_token")
        result = fetcher.fetch_for_influencer("Test", twitter_handle=None)
        assert result == []

    def test_fetch_unavailable_returns_empty(self):
        fetcher = TwitterFetcher(bearer_token=None)
        result = fetcher.fetch_for_influencer("Test", twitter_handle="testuser")
        assert result == []


class TestYouTubeFetcher:
    def test_is_available_with_key(self):
        fetcher = YouTubeFetcher(api_key="test_key")
        assert fetcher.is_available() is True

    def test_is_available_without_key(self):
        fetcher = YouTubeFetcher(api_key=None)
        assert fetcher.is_available() is False

    def test_fetch_without_handle_returns_empty(self):
        fetcher = YouTubeFetcher(api_key="test_key")
        result = fetcher.fetch_for_influencer("Test", youtube_handle=None)
        assert result == []
