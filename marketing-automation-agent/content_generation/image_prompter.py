"""Generates Gemini image prompts from LinkedIn post content using Claude."""

import logging
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)


class ImagePrompter:
    """Uses Claude to create optimized image generation prompts."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def create_image_prompt(self, post_text: str, topic_title: str) -> str:
        """Generate a Gemini-optimized visual prompt for a LinkedIn post.

        Args:
            post_text: The LinkedIn post content.
            topic_title: Short title of the topic.

        Returns:
            A 1-2 sentence visual prompt suitable for image generation.
        """
        prompt = f"""You are a visual art director creating images for LinkedIn B2B posts.

LinkedIn Post:
{post_text[:600]}

Topic: {topic_title}

Create a detailed visual prompt for an AI image generator to create a professional, eye-catching image for this post.

Requirements:
- Abstract or conceptual imagery (NO text, NO specific people, NO logos, NO brands)
- Professional, modern, business-appropriate aesthetic
- Relevant visual metaphor for the topic (e.g., neural networks → glowing nodes, AI automation → gears + circuits)
- Color palette suggestion (blues/purples for trust/tech, greens for growth, oranges for innovation)
- Style guidance: "3D rendered", "isometric illustration", "minimalist digital art", "abstract data visualization", etc.
- LinkedIn-optimized: clean, high contrast, visually striking at small sizes
- 1-2 sentences maximum

Return ONLY the prompt text, nothing else."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            image_prompt = response.content[0].text.strip()
            logger.info(f"Generated image prompt for '{topic_title}'")
            return image_prompt
        except Exception as e:
            logger.error(f"Image prompt generation failed: {e}")
            return (
                f"Professional abstract visualization of {topic_title}, "
                "modern tech aesthetic with blue and purple gradients, "
                "clean minimalist 3D rendered style, suitable for LinkedIn."
            )
