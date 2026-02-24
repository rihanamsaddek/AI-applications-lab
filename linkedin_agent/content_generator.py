"""Content generator module for creating LinkedIn marketing campaigns using Claude."""

import anthropic
from typing import Dict, List
from datetime import datetime


class ContentGenerator:
    """Generates LinkedIn marketing content using Claude AI."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-6", max_tokens: int = 4096):
        """Initialize the content generator.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens for generation
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def analyze_business(self, business_docs_summary: str) -> str:
        """Analyze business documents to understand the company's focus.

        Args:
            business_docs_summary: Summary of analyzed business documents

        Returns:
            Business analysis summary
        """
        print("\n🔍 Analyzing business documents with Claude...")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze these business documents and provide a comprehensive business profile:

{business_docs_summary}

Please provide:
1. Core business focus and mission
2. Key products/services
3. Target audience
4. Unique value propositions
5. Areas of expertise
6. Current business context (if mentioned)

Format your response as a structured business profile."""
                }
            ]
        )

        analysis = response.content[0].text
        print("  ✓ Business analysis complete")
        return analysis

    def generate_marketing_post(
        self,
        business_analysis: str,
        tone: str = "professional yet engaging",
        focus_areas: List[str] = None
    ) -> Dict[str, str]:
        """Generate a LinkedIn marketing post.

        Args:
            business_analysis: Analysis of the business from documents
            tone: Desired tone for the post
            focus_areas: Specific topics to focus on

        Returns:
            Dictionary with 'post' content and 'reasoning'
        """
        print(f"\n✍️  Generating LinkedIn post...")

        focus_instruction = ""
        if focus_areas:
            focus_instruction = f"\nFocus on these areas: {', '.join(focus_areas)}"

        current_date = datetime.now().strftime("%B %d, %Y")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            messages=[
                {
                    "role": "user",
                    "content": f"""Based on this business analysis:

{business_analysis}

Create an engaging LinkedIn post for today ({current_date}) that:
1. Highlights the business's value proposition or expertise
2. Provides valuable insights or tips to the target audience
3. Uses a {tone} tone
4. Includes relevant hashtags (3-5)
5. Is between 150-300 characters for maximum engagement
6. Includes a clear call-to-action or thought-provoking question{focus_instruction}

Important LinkedIn best practices:
- Start with a hook that grabs attention
- Use short paragraphs and line breaks for readability
- Make it authentic and valuable, not salesy
- Include emojis sparingly and strategically
- End with engagement prompts (questions, calls-to-action)

Provide:
1. The LinkedIn post (ready to publish)
2. A brief explanation of the strategy behind this post"""
                }
            ]
        )

        content = response.content[0].text

        # Split into post and reasoning
        if "Strategy:" in content or "Explanation:" in content or "Reasoning:" in content:
            parts = content.split("\n\n")
            post = parts[0]
            reasoning = "\n\n".join(parts[1:])
        else:
            post = content
            reasoning = "Post generated based on business analysis"

        print("  ✓ Post generated successfully")

        return {
            "post": post.strip(),
            "reasoning": reasoning.strip(),
            "generated_at": current_date
        }

    def generate_campaign(
        self,
        business_docs_summary: str,
        num_posts: int = 1,
        tone: str = "professional yet engaging"
    ) -> List[Dict[str, str]]:
        """Generate a full marketing campaign with multiple posts.

        Args:
            business_docs_summary: Summary of business documents
            num_posts: Number of posts to generate
            tone: Desired tone for posts

        Returns:
            List of generated posts with metadata
        """
        print(f"\n🚀 Generating {num_posts} marketing post(s)...")

        # First, analyze the business
        business_analysis = self.analyze_business(business_docs_summary)

        # Generate posts
        posts = []
        for i in range(num_posts):
            print(f"\n📝 Generating post {i + 1}/{num_posts}...")
            post = self.generate_marketing_post(business_analysis, tone=tone)
            post["post_number"] = i + 1
            posts.append(post)

        return posts

    def refine_post(self, post_content: str, feedback: str) -> str:
        """Refine a post based on user feedback.

        Args:
            post_content: Original post content
            feedback: User feedback for refinement

        Returns:
            Refined post content
        """
        print("\n✨ Refining post based on feedback...")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": f"""Original LinkedIn Post:
{post_content}

User Feedback:
{feedback}

Please refine the post based on this feedback while maintaining LinkedIn best practices."""
                }
            ]
        )

        refined = response.content[0].text
        print("  ✓ Post refined")
        return refined.strip()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Test the content generator
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        generator = ContentGenerator(api_key)
        test_summary = """
        Business: AI Applications Workshop
        Focus: Teaching executives about generative AI applications in business
        Target: Executive education, business professionals
        """
        posts = generator.generate_campaign(test_summary, num_posts=1)
        for post in posts:
            print("\n" + "=" * 60)
            print("GENERATED POST:")
            print("=" * 60)
            print(post['post'])
            print("\n" + "-" * 60)
            print("STRATEGY:")
            print("-" * 60)
            print(post['reasoning'])
