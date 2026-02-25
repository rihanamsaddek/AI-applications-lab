"""Validate all API credentials before running the agent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.agent_config import AgentConfig


def check_anthropic(config: AgentConfig):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        resp = client.messages.create(
            model=config.model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )
        print(f"  ✓ Anthropic API: Connected (model: {config.model})")
        return True
    except Exception as e:
        print(f"  ✗ Anthropic API: {e}")
        return False


def check_gemini(config: AgentConfig):
    if not config.google_ai_studio_key:
        print("  ⚠ Gemini: GOOGLE_AI_STUDIO_KEY not set — image generation disabled")
        return False
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.google_ai_studio_key)
        models = list(genai.list_models())
        print(f"  ✓ Gemini API: Connected ({len(models)} models available)")
        return True
    except Exception as e:
        print(f"  ✗ Gemini API: {e}")
        return False


def check_rss(config: AgentConfig):
    rss_influencers = [i for i in config.influencers if i.platforms.rss]
    if not rss_influencers:
        print("  ⚠ RSS: No RSS feeds configured in influencers.yaml")
        return False
    try:
        import feedparser
        first = rss_influencers[0]
        feed = feedparser.parse(first.platforms.rss)
        count = len(feed.entries)
        print(f"  ✓ RSS: Accessible (tested {first.name}: {count} entries found)")
        return True
    except Exception as e:
        print(f"  ✗ RSS: {e}")
        return False


def check_twitter(config: AgentConfig):
    if not config.twitter_bearer_token:
        print("  ⚠ Twitter: TWITTER_BEARER_TOKEN not set — Twitter fetching disabled")
        return False
    try:
        import tweepy
        client = tweepy.Client(bearer_token=config.twitter_bearer_token)
        resp = client.get_user(username="AnthropicAI")
        if resp.data:
            print(f"  ✓ Twitter API: Connected (test user: @AnthropicAI)")
            return True
        print("  ✗ Twitter: No data returned")
        return False
    except ImportError:
        print("  ✗ Twitter: tweepy not installed (pip install tweepy)")
        return False
    except Exception as e:
        print(f"  ✗ Twitter API: {e}")
        return False


def check_linkedin(config: AgentConfig):
    if not config.linkedin_access_token:
        print("  ⚠ LinkedIn: LINKEDIN_ACCESS_TOKEN not set — posting disabled (preview-only mode)")
        return False
    try:
        import requests
        resp = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {config.linkedin_access_token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            name = resp.json().get("localizedFirstName", "")
            print(f"  ✓ LinkedIn API: Connected (user: {name})")
            return True
        print(f"  ✗ LinkedIn API: HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"  ✗ LinkedIn API: {e}")
        return False


def main():
    print("=== Marketing Agent — API Validation ===\n")
    config = AgentConfig.from_env()
    print(f"Loaded {len(config.influencers)} influencers\n")

    results = {
        "Anthropic (Claude)": check_anthropic(config),
        "Google Gemini (images)": check_gemini(config),
        "RSS feeds": check_rss(config),
        "Twitter/X": check_twitter(config),
        "LinkedIn": check_linkedin(config),
    }

    print("\n=== Summary ===")
    for name, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")

    required_ok = results["Anthropic (Claude)"]
    if not required_ok:
        print("\n✗ Required APIs failed. Fix Anthropic API key before running the agent.")
        sys.exit(1)
    else:
        print("\n✓ Minimum requirements met. Run: python -m orchestration.daily_agent --preview-only")


if __name__ == "__main__":
    main()
