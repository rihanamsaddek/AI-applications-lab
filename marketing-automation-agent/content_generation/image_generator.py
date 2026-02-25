"""Image generator using Google Gemini (gemini-3-pro-image-preview) via Google AI Studio."""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generates images using the Gemini image generation model via Google AI Studio."""

    def __init__(self, api_key: str, model: str = "gemini-3-pro-image-preview"):
        self.api_key = api_key
        self.model_name = model
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized Gemini model: {self.model_name}")
            except ImportError:
                raise RuntimeError(
                    "google-generativeai not installed. Run: pip install google-generativeai"
                )
        return self._model

    def generate_image(
        self,
        prompt: str,
        output_path: str,
    ) -> Optional[str]:
        """Generate an image and save it to output_path.

        Args:
            prompt: Visual description for image generation.
            output_path: File path to save the generated PNG image.

        Returns:
            Path to saved image, or None on failure.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(3):
            try:
                model = self._get_model()
                import google.generativeai as genai

                safe_prompt = (
                    f"{prompt} "
                    "Professional, business-appropriate, abstract, no text overlay, no people."
                )

                logger.info(f"Generating image (attempt {attempt + 1}): {safe_prompt[:80]}...")

                response = model.generate_content(
                    contents=safe_prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_modalities=["TEXT", "IMAGE"],
                    ),
                )

                # Extract image bytes from response
                image_bytes = self._extract_image_bytes(response)
                if image_bytes:
                    with open(output_path, "wb") as f:
                        f.write(image_bytes)
                    logger.info(f"Image saved: {output_path} ({len(image_bytes):,} bytes)")
                    return output_path
                else:
                    logger.warning(f"No image in response (attempt {attempt + 1})")
                    # Simplify prompt for retry
                    prompt = self._simplify_prompt(prompt)

            except Exception as e:
                logger.error(f"Image generation attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    return None

        return None

    def _extract_image_bytes(self, response) -> Optional[bytes]:
        """Extract raw image bytes from a Gemini response."""
        try:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        return part.inline_data.data
        except Exception as e:
            logger.debug(f"Error extracting image bytes: {e}")
        return None

    def _simplify_prompt(self, prompt: str) -> str:
        """Simplify a prompt by taking only the first sentence."""
        simplified = prompt.split(".")[0].strip()
        return simplified or "Abstract professional business technology visualization"
