"""Quick test script — runs the full workflow in preview mode (no LinkedIn posting)."""

import sys
from pathlib import Path

# Allow running from scripts/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from config.agent_config import AgentConfig
from orchestration.daily_agent import DailyAgent


def main():
    parser = argparse.ArgumentParser(description="Test the marketing agent without posting to LinkedIn")
    parser.add_argument("--skip-images", action="store_true",
                        help="Skip image generation (faster testing)")
    args = parser.parse_args()

    print("=== Marketing Agent — Test Run (Preview Mode) ===")
    print("Posts will be GENERATED but NOT published to LinkedIn.\n")

    config = AgentConfig.from_env()
    is_valid, errors = config.validate()

    if not is_valid:
        print("Configuration errors:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    print(f"Anthropic API: {'✓ configured' if config.anthropic_api_key else '✗ missing'}")
    print(f"Gemini images: {'✓ configured' if config.can_generate_images() else '⚠ not configured'}")
    print(f"Twitter: {'✓ configured' if config.twitter_bearer_token else '⚠ not configured'}")
    print(f"YouTube: {'✓ configured' if config.youtube_api_key else '⚠ not configured'}")
    print(f"LinkedIn: {'✓ configured' if config.can_post_to_linkedin() else '⚠ not configured (preview only)'}")
    print(f"Influencers loaded: {len(config.influencers)}")
    rss_count = sum(1 for i in config.influencers if i.platforms.rss)
    print(f"  RSS feeds: {rss_count}")
    print()

    agent = DailyAgent(config)
    posts = agent.run_daily_workflow(preview_only=True)

    print(f"\n=== Test Complete: {len(posts)} posts generated ===")
    for i, post in enumerate(posts, 1):
        print(f"\n--- Post {i}: {post.get('topic_title', 'N/A')} ---")
        print(post.get("post_text", "")[:300] + "...")
        if post.get("image_path"):
            print(f"Image: {post['image_path']}")


if __name__ == "__main__":
    main()
