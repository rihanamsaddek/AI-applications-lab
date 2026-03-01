"""Claude-powered content analysis to select the top 3 daily topics."""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

import anthropic

logger = logging.getLogger(__name__)

MAX_CONTENT_CHARS = 80_000  # Keep prompt within token budget


@dataclass
class Topic:
    """A topic selected for LinkedIn post generation."""
    title: str
    summary: str
    why_engaging: str
    linkedin_angle: str
    source_urls: List[str] = field(default_factory=list)


class ContentAnalyzer:
    """Analyzes fetched content with Claude to identify top posting topics."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-6", max_tokens: int = 4096):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def analyze_daily_content(
        self,
        content_items: List[Dict[str, Any]],
        past_topics: List[str],
    ) -> List[Topic]:
        """Use Claude to select the 3 most engaging topics from today's content."""
        if not content_items:
            logger.warning("No content items to analyze")
            return []

        content_block = self._format_content(content_items)
        past_topics_str = "\n".join(f"- {t}" for t in past_topics) if past_topics else "None"

        prompt = f"""You are a social media strategist for a company focused on generative AI for business.

Below is recent content collected from 14 AI influencers and thought leaders over the past 48 hours:

<influencer_content>
{content_block}
</influencer_content>

Topics covered in the past 30 days (AVOID these to prevent repetition):
{past_topics_str}

Your task: Select the **3 best topics** for LinkedIn posts targeting business professionals and executives interested in AI.

Selection criteria:
1. High relevance to B2B / enterprise AI adoption
2. Timeliness — breaking news, new tools, or emerging trends
3. Actionable insight — readers can apply this knowledge immediately
4. Diversity — choose 3 DISTINCT angles (e.g., a tool, a strategy, a case study)
5. Novelty — avoid topics covered in the last 30 days listed above

Return a JSON object with exactly this structure:
{{
  "topics": [
    {{
      "title": "Short, punchy topic title (max 10 words)",
      "summary": "2-3 sentence summary of the key insight",
      "why_engaging": "Why this resonates with a B2B executive audience",
      "linkedin_angle": "The unique angle or hook for the LinkedIn post",
      "source_urls": ["url1", "url2"]
    }}
  ]
}}

Return ONLY the JSON object. No extra text."""

        logger.info("Sending content to Claude for topic analysis...")
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                thinking={"type": "adaptive"},
                output_config={"effort": "high"},
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text blocks (skip thinking blocks)
            text = next(
                (b.text for b in response.content if b.type == "text"), ""
            )

            return self._parse_topics(text)

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return []

    def _format_content(self, items: List[Dict[str, Any]]) -> str:
        """Format content items for the prompt, respecting token limits."""
        lines = []
        total = 0
        for item in items:
            text = item.get("content_text", "")[:500]
            line = (
                f"[{item['influencer_name']} / {item['platform']}]\n"
                f"Title: {item.get('title', 'N/A')}\n"
                f"Content: {text}\n"
                f"URL: {item.get('content_url', '')}\n"
                f"Engagement: {item.get('engagement_score', 0):.0f}\n"
            )
            if total + len(line) > MAX_CONTENT_CHARS:
                lines.append("... (additional content truncated)")
                break
            lines.append(line)
            total += len(line)
        return "\n---\n".join(lines)

    def _parse_topics(self, text: str) -> List[Topic]:
        """Parse Claude's JSON response into Topic objects."""
        try:
            # Find JSON block
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")
            data = json.loads(text[start:end])
            topics = []
            for t in data.get("topics", [])[:3]:
                topics.append(Topic(
                    title=t.get("title", "AI Topic"),
                    summary=t.get("summary", ""),
                    why_engaging=t.get("why_engaging", ""),
                    linkedin_angle=t.get("linkedin_angle", ""),
                    source_urls=t.get("source_urls", []),
                ))
            logger.info(f"Selected {len(topics)} topics for today's posts")
            return topics
        except Exception as e:
            logger.error(f"Failed to parse topics from Claude response: {e}")
            logger.debug(f"Raw response: {text[:500]}")
            return []
