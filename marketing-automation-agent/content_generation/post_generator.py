"""LinkedIn post generator powered by Claude."""

import logging
from datetime import datetime
from typing import Dict

import anthropic

from content_analysis.content_analyzer import Topic

logger = logging.getLogger(__name__)


class PostGenerator:
    """Generates LinkedIn posts from selected topics using Claude."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-6", max_tokens: int = 4096):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def generate_post(self, topic: Topic) -> Dict[str, str]:
        """Generate a LinkedIn post for a given topic.

        Returns a dict with keys: 'post_text', 'reasoning', 'generated_at'.
        """
        today = datetime.now().strftime("%B %d, %Y")

        prompt = f"""You are writing a LinkedIn post for a company that helps executives adopt generative AI for their businesses.

Today's date: {today}

Topic: {topic.title}
Summary: {topic.summary}
LinkedIn angle: {topic.linkedin_angle}
Why engaging: {topic.why_engaging}
Source references: {', '.join(topic.source_urls) if topic.source_urls else 'General industry knowledge'}

Write a compelling LinkedIn post (200-350 words) following these requirements:

STRUCTURE:
1. Hook (first 1-2 lines) — a bold statement, surprising stat, or thought-provoking question. This must stop the scroll.
2. Body — 2-4 short paragraphs or a bulleted list with actionable insights
3. Close — a call-to-action or engaging question to drive comments
4. Hashtags — 3-5 relevant hashtags on the last line

STYLE:
- Professional yet conversational tone
- Short paragraphs (2-3 sentences max) for mobile readability
- Use line breaks generously
- Do NOT be salesy or promotional
- Do NOT mention specific competitors by name
- Give credit to the broader conversation without copying any source verbatim

OUTPUT FORMAT:
First, write the complete LinkedIn post ready to publish.
Then, on a new line, write "---STRATEGY---"
Then write 1-2 sentences explaining the strategic angle of this post.

Write the post now:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                thinking={"type": "adaptive"},
                output_config={"effort": "high"},
                messages=[{"role": "user", "content": prompt}],
            )

            text = next(
                (b.text for b in response.content if b.type == "text"), ""
            ).strip()

            # Split post from strategy
            if "---STRATEGY---" in text:
                post_text, reasoning = text.split("---STRATEGY---", 1)
            else:
                post_text = text
                reasoning = ""

            return {
                "post_text": post_text.strip(),
                "reasoning": reasoning.strip(),
                "generated_at": today,
                "topic_title": topic.title,
            }

        except Exception as e:
            logger.error(f"Post generation failed for topic '{topic.title}': {e}")
            return {
                "post_text": f"Exciting developments in {topic.title}. Stay tuned for more insights! #GenerativeAI",
                "reasoning": "Fallback post due to generation error",
                "generated_at": today,
                "topic_title": topic.title,
            }
