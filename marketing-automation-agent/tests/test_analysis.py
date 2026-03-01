"""Unit tests for content analysis module."""

import json
import pytest
from unittest.mock import MagicMock, patch

from content_analysis.content_analyzer import ContentAnalyzer, Topic


SAMPLE_CONTENT = [
    {
        "influencer_name": "Ethan Mollick",
        "platform": "rss",
        "content_text": "Large language models are reshaping how companies approach customer service.",
        "content_url": "https://example.com/1",
        "title": "LLMs in Customer Service",
        "engagement_score": 500.0,
    },
    {
        "influencer_name": "Anthropic",
        "platform": "rss",
        "content_text": "Claude's extended thinking capability enables deeper reasoning on complex tasks.",
        "content_url": "https://example.com/2",
        "title": "Extended Thinking in Claude",
        "engagement_score": 1200.0,
    },
]

SAMPLE_RESPONSE = json.dumps({
    "topics": [
        {
            "title": "LLMs in Enterprise Customer Service",
            "summary": "Companies are deploying LLMs to handle complex support queries.",
            "why_engaging": "Practical ROI story for decision-makers.",
            "linkedin_angle": "3 ways LLMs cut support costs by 40%",
            "source_urls": ["https://example.com/1"],
        },
        {
            "title": "Extended AI Reasoning for Business",
            "summary": "New reasoning models tackle multi-step business problems.",
            "why_engaging": "Directly applicable to strategic planning.",
            "linkedin_angle": "How extended thinking changes AI ROI calculations",
            "source_urls": ["https://example.com/2"],
        },
        {
            "title": "AI Adoption Patterns in 2025",
            "summary": "Research shows adoption varies significantly by industry.",
            "why_engaging": "Benchmarking opportunity for executives.",
            "linkedin_angle": "Is your industry ahead or behind in AI adoption?",
            "source_urls": [],
        },
    ]
})


class TestContentAnalyzer:
    def setup_method(self):
        self.analyzer = ContentAnalyzer(api_key="fake_key")

    def test_parse_valid_json(self):
        topics = self.analyzer._parse_topics(SAMPLE_RESPONSE)
        assert len(topics) == 3
        assert topics[0].title == "LLMs in Enterprise Customer Service"
        assert topics[1].source_urls == ["https://example.com/2"]

    def test_parse_empty_response(self):
        topics = self.analyzer._parse_topics("{}")
        assert topics == []

    def test_parse_malformed_json(self):
        topics = self.analyzer._parse_topics("not json at all")
        assert topics == []

    def test_parse_caps_at_three_topics(self):
        many_topics = json.dumps({
            "topics": [
                {"title": f"Topic {i}", "summary": "...", "why_engaging": "...",
                 "linkedin_angle": "...", "source_urls": []}
                for i in range(10)
            ]
        })
        topics = self.analyzer._parse_topics(many_topics)
        assert len(topics) <= 3

    def test_format_content_respects_limit(self):
        big_content = [
            {
                "influencer_name": "Test",
                "platform": "rss",
                "content_text": "x" * 1000,
                "content_url": "https://example.com",
                "title": "Title",
                "engagement_score": 0,
            }
        ] * 200  # 200 items × 1000 chars each
        formatted = self.analyzer._format_content(big_content)
        assert len(formatted) <= 80_000 + 2000  # Allow overhead for separator lines

    def test_analyze_with_mocked_claude(self):
        mock_response = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = SAMPLE_RESPONSE
        mock_response.content = [mock_block]

        with patch.object(self.analyzer.client.messages, "create", return_value=mock_response):
            topics = self.analyzer.analyze_daily_content(SAMPLE_CONTENT, past_topics=[])
        assert len(topics) == 3


class TestTopic:
    def test_topic_creation(self):
        topic = Topic(
            title="Test Topic",
            summary="A summary.",
            why_engaging="Engaging because...",
            linkedin_angle="The angle.",
            source_urls=["https://example.com"],
        )
        assert topic.title == "Test Topic"
        assert len(topic.source_urls) == 1
