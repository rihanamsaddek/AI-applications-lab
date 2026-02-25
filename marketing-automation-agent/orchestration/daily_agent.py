"""Main daily orchestration agent for the marketing automation pipeline."""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import colorama
from colorama import Fore, Style

from config.agent_config import AgentConfig
from content_fetchers.rss_fetcher import RSSFetcher
from content_fetchers.twitter_fetcher import TwitterFetcher
from content_fetchers.youtube_fetcher import YouTubeFetcher
from content_storage.database import Database
from content_storage.cache_manager import CacheManager
from content_analysis.content_analyzer import ContentAnalyzer, Topic
from content_generation.post_generator import PostGenerator
from content_generation.image_prompter import ImagePrompter
from content_generation.image_generator import ImageGenerator
from posting.linkedin_poster import LinkedInPoster
from posting.image_uploader import ImageUploader
from orchestration.notification_handler import NotificationHandler
from utils.logger import setup_logger

colorama.init(autoreset=True)

# Delay between LinkedIn posts to avoid spam detection (seconds)
POST_DELAY_SECONDS = 300  # 5 minutes


class DailyAgent:
    """Orchestrates the full daily marketing automation workflow."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = setup_logger("daily_agent", config.log_path, config.log_level)

        # Storage
        self.db = Database(config.database_path)
        self.cache = CacheManager()

        # Content fetchers
        self.rss_fetcher = RSSFetcher()
        self.twitter_fetcher = TwitterFetcher(bearer_token=config.twitter_bearer_token)
        self.youtube_fetcher = YouTubeFetcher(api_key=config.youtube_api_key)

        # Analysis & Generation
        self.analyzer = ContentAnalyzer(config.anthropic_api_key, config.model)
        self.post_generator = PostGenerator(config.anthropic_api_key, config.model)
        self.image_prompter = ImagePrompter(config.anthropic_api_key, config.model)

        # Image generation (optional)
        self.image_generator = (
            ImageGenerator(config.google_ai_studio_key, config.gemini_image_model)
            if config.can_generate_images()
            else None
        )

        # LinkedIn (optional)
        if config.can_post_to_linkedin():
            self.linkedin_poster = LinkedInPoster(
                config.linkedin_access_token, config.linkedin_author_urn
            )
            self.image_uploader = ImageUploader(
                config.linkedin_access_token, config.linkedin_author_urn
            )
        else:
            self.linkedin_poster = None
            self.image_uploader = None

        # Notifications
        self.notifier = NotificationHandler(
            notification_email=config.notification_email,
            smtp_server=config.smtp_server,
            smtp_port=config.smtp_port,
            smtp_username=config.smtp_username,
            smtp_password=config.smtp_password,
            slack_webhook_url=config.slack_webhook_url,
        )

    def run_daily_workflow(self, preview_only: bool = False) -> List[Dict]:
        """Execute the complete daily workflow.

        Args:
            preview_only: If True, generate posts and images but skip LinkedIn posting.

        Returns:
            List of generated post dicts.
        """
        self._print_header("Daily Marketing Agent")
        start_time = datetime.now()

        try:
            # Phase 1: Fetch content
            self._print_phase(1, "Fetching Influencer Content")
            all_content = self._fetch_all_content()
            if not all_content:
                self.logger.warning("No content fetched — check influencer config and API keys")
            self._print_ok(f"Fetched {len(all_content)} content items")

            # Phase 2: Store content
            self._print_phase(2, "Storing Content to Database")
            saved = self.db.save_content_batch(all_content)
            self._print_ok(f"Saved {saved} new items to database")

            # Phase 3: Load from DB (includes older content for context)
            recent_content = self.db.get_recent_content(hours=48)
            past_topics = self.db.get_recent_post_topics(days=30)
            self.logger.info(f"Loaded {len(recent_content)} recent items from DB; {len(past_topics)} past topics to avoid")

            # Phase 4: Analyze content with Claude
            self._print_phase(3, "Analyzing Content with Claude")
            topics = self.analyzer.analyze_daily_content(recent_content, past_topics)
            if not topics:
                raise RuntimeError("No topics selected — cannot continue")
            self._print_ok(f"Selected {len(topics)} topics")

            # Phase 5: Generate posts and images
            self._print_phase(4, "Generating Posts and Images")
            posts = []
            for i, topic in enumerate(topics):
                post_data = self._generate_post_and_image(topic, i + 1, len(topics))
                if post_data:
                    posts.append(post_data)

            self._print_ok(f"Generated {len(posts)} posts")

            # Phase 6: Publish to LinkedIn
            if preview_only:
                self._print_phase(5, "Preview Mode — Skipping LinkedIn Publishing")
                self._print_results(posts)
                self.notifier.send_preview_summary(posts)
            elif self.linkedin_poster:
                self._print_phase(5, "Publishing to LinkedIn")
                posts = self._publish_posts(posts)
            else:
                self._print_phase(5, "LinkedIn Not Configured — Saving Locally")
                self._print_results(posts)
                self.logger.info("Add LINKEDIN_ACCESS_TOKEN + LINKEDIN_ORG_URN to .env to enable posting")

            # Save posts to history
            for post in posts:
                self.db.save_post(
                    topic_title=post.get("topic_title", ""),
                    post_text=post.get("post_text", ""),
                    image_path=post.get("image_path"),
                    linkedin_post_id=post.get("linkedin_post_id"),
                    source_urls=post.get("source_urls", []),
                )

            elapsed = (datetime.now() - start_time).seconds
            self._print_footer(f"Completed in {elapsed}s")

            if not preview_only and self.linkedin_poster:
                self.notifier.send_success_summary(posts)

            return posts

        except Exception as e:
            self.logger.error(f"Daily workflow failed: {e}", exc_info=True)
            self.notifier.send_error_alert(str(e))
            raise

    def _fetch_all_content(self):
        """Fetch from all available platforms for all influencers."""
        all_content = []

        for influencer in self.config.influencers:
            name = influencer.name
            platforms = influencer.platforms

            # RSS (always try)
            if platforms.rss:
                items = self.rss_fetcher.fetch_with_retry(name, feed_url=platforms.rss)
                all_content.extend(items)

            # Twitter (if credentials available)
            if platforms.twitter and self.twitter_fetcher.is_available():
                items = self.twitter_fetcher.fetch_with_retry(name, twitter_handle=platforms.twitter)
                all_content.extend(items)

            # YouTube (if credentials available)
            if platforms.youtube and self.youtube_fetcher.is_available():
                items = self.youtube_fetcher.fetch_with_retry(name, youtube_handle=platforms.youtube)
                all_content.extend(items)

        return all_content

    def _generate_post_and_image(self, topic: Topic, num: int, total: int) -> Optional[Dict]:
        """Generate post text and image for a single topic."""
        self.logger.info(f"Generating post {num}/{total}: {topic.title}")

        # Generate post text
        post_data = self.post_generator.generate_post(topic)

        # Generate image
        image_path = None
        if self.image_generator:
            image_prompt = self.image_prompter.create_image_prompt(
                post_data["post_text"], topic.title
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(
                Path(self.config.images_path) / f"post_{timestamp}_{num}.png"
            )
            image_path = self.image_generator.generate_image(image_prompt, output_path)
            if image_path:
                self.logger.info(f"Image saved: {image_path}")
            else:
                self.logger.warning(f"Image generation failed for topic: {topic.title}")
        else:
            self.logger.info("Image generation skipped (GOOGLE_AI_STUDIO_KEY not configured)")

        return {
            **post_data,
            "image_path": image_path,
            "source_urls": topic.source_urls,
            "linkedin_post_id": None,
        }

    def _publish_posts(self, posts: List[Dict]) -> List[Dict]:
        """Publish posts to LinkedIn sequentially with a delay."""
        if not self.linkedin_poster.validate_credentials():
            self.logger.error("LinkedIn credentials invalid — aborting publish phase")
            return posts

        for i, post in enumerate(posts):
            self.logger.info(f"Publishing post {i + 1}/{len(posts)}: {post.get('topic_title')}")

            image_urn = None
            if post.get("image_path") and self.image_uploader:
                image_urn = self.image_uploader.upload_image(post["image_path"])

            if image_urn:
                result = self.linkedin_poster.create_image_post(post["post_text"], image_urn)
            else:
                result = self.linkedin_poster.create_text_post(post["post_text"])

            if result.get("success"):
                post["linkedin_post_id"] = result.get("post_id")
                self._print_ok(f"Post {i + 1} published (ID: {result.get('post_id')})")
            else:
                self.logger.error(f"Failed to publish post {i + 1}: {result.get('error')}")

            # Wait between posts (except after the last one)
            if i < len(posts) - 1:
                self.logger.info(f"Waiting {POST_DELAY_SECONDS}s before next post...")
                time.sleep(POST_DELAY_SECONDS)

        return posts

    def _print_results(self, posts: List[Dict]):
        """Print generated posts to console for review."""
        for i, post in enumerate(posts, 1):
            print(f"\n{Fore.CYAN}┌─ Post {i}: {post.get('topic_title', 'N/A')} ─────────────────────────┐{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{post.get('post_text', '')[:400]}...{Style.RESET_ALL}")
            if post.get("image_path"):
                print(f"{Fore.MAGENTA}Image: {post['image_path']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}└────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

    def _print_header(self, title: str):
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}  {title}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

    def _print_footer(self, message: str):
        print(f"\n{Fore.GREEN}{'=' * 70}")
        print(f"{Fore.GREEN}  ✓ {message}")
        print(f"{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}\n")

    def _print_phase(self, num: int, title: str):
        print(f"\n{Fore.YELLOW}[Phase {num}] {title}{Style.RESET_ALL}")
        print("-" * 70)
        self.logger.info(f"=== Phase {num}: {title} ===")

    def _print_ok(self, message: str):
        print(f"  {Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Marketing Automation Agent")
    parser.add_argument("--preview-only", action="store_true",
                        help="Generate posts without publishing to LinkedIn")
    args = parser.parse_args()

    try:
        config = AgentConfig.from_env()
        is_valid, errors = config.validate()
        if not is_valid:
            for err in errors:
                print(f"{Fore.RED}✗ Config error: {err}{Style.RESET_ALL}")
            sys.exit(1)

        agent = DailyAgent(config)
        agent.run_daily_workflow(preview_only=args.preview_only)

    except Exception as e:
        print(f"\n{Fore.RED}✗ Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
