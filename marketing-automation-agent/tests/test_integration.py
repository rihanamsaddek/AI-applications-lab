"""Integration tests — full workflow with mocked external APIs."""

import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from config.agent_config import AgentConfig, Influencer, InfluencerPlatforms
from content_fetchers.base_fetcher import ContentItem
from datetime import datetime


def make_mock_config(tmp_path) -> AgentConfig:
    """Create a minimal AgentConfig for testing."""
    config = AgentConfig(
        anthropic_api_key="fake-key",
        google_ai_studio_key=None,  # Disable image generation in tests
        database_path=str(tmp_path / "test.db"),
        images_path=str(tmp_path / "images"),
        log_path=str(tmp_path / "logs"),
        influencers=[
            Influencer(
                name="Test Influencer",
                platforms=InfluencerPlatforms(
                    rss="https://example.com/feed"
                ),
            )
        ],
    )
    return config


MOCK_RSS_ITEMS = [
    ContentItem(
        influencer_name="Test Influencer",
        platform="rss",
        content_text="AI automation is transforming enterprise workflows in 2026.",
        content_url="https://example.com/post1",
        title="AI Automation in 2026",
        engagement_score=0.0,
        fetched_at=datetime.utcnow(),
    )
]

MOCK_TOPICS_JSON = json.dumps({
    "topics": [
        {
            "title": "AI Automation in Enterprise",
            "summary": "AI is reshaping how businesses operate.",
            "why_engaging": "Relevant to all executive audiences.",
            "linkedin_angle": "5 automation wins you can implement this quarter",
            "source_urls": ["https://example.com/post1"],
        }
    ]
})


@pytest.mark.integration
class TestFullWorkflow:
    def test_preview_run_completes(self, tmp_path):
        """Test that preview_only=True completes without errors and returns posts."""
        from orchestration.daily_agent import DailyAgent

        config = make_mock_config(tmp_path)

        # Mock Claude response
        mock_message = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = MOCK_TOPICS_JSON
        mock_message.content = [mock_block]

        mock_post_message = MagicMock()
        mock_post_block = MagicMock()
        mock_post_block.type = "text"
        mock_post_block.text = "Great insights on AI automation!\n\n#GenerativeAI\n---STRATEGY---\nFocus on ROI."
        mock_post_message.content = [mock_post_block]

        mock_image_prompt_message = MagicMock()
        mock_image_prompt_block = MagicMock()
        mock_image_prompt_block.type = "text"
        mock_image_prompt_block.text = "Abstract isometric illustration of automation workflows."
        mock_image_prompt_message.content = [mock_image_prompt_block]

        with patch("anthropic.Anthropic") as mock_anthropic_cls:
            mock_client = MagicMock()
            mock_anthropic_cls.return_value = mock_client
            # First call: content analysis, subsequent calls: post generation, image prompt
            mock_client.messages.create.side_effect = [
                mock_message,
                mock_post_message,
                mock_image_prompt_message,
            ]

            # Mock RSS fetcher
            with patch.object(
                __import__("content_fetchers.rss_fetcher", fromlist=["RSSFetcher"]).RSSFetcher,
                "fetch_with_retry",
                return_value=MOCK_RSS_ITEMS,
            ):
                agent = DailyAgent(config)
                posts = agent.run_daily_workflow(preview_only=True)

        assert isinstance(posts, list)
        assert len(posts) >= 1
        assert posts[0].get("post_text")
        assert posts[0].get("topic_title") == "AI Automation in Enterprise"
