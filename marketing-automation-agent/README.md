# Marketing Automation Agent

An automated marketing agent that monitors 14 AI influencers daily, analyzes their content with Claude, generates 3 LinkedIn posts with Gemini-generated images, and publishes to a LinkedIn company or personal account.

## Features

- **Multi-platform monitoring**: RSS feeds (active now), Twitter, YouTube (activate with API keys)
- **AI-powered analysis**: Claude Opus 4.6 selects top 3 topics from all fetched content
- **Content generation**: Claude writes engaging LinkedIn posts (200-350 words each)
- **Image generation**: Gemini `gemini-3-pro-image-preview` creates unique images per post
- **Deduplication**: SQLite history prevents repeating topics from the last 30 days
- **Daily automation**: Cron job runs at 9 AM
- **Notifications**: Optional email/Slack alerts on success or failure
- **Graceful degradation**: Runs with just RSS + Anthropic keys; other platforms activate as you add keys

## Quick Start

### 1. Install Dependencies

```bash
cd marketing-automation-agent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example ../.env
# Edit ../.env with your credentials
```

Minimum required keys:
```bash
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_STUDIO_KEY=AIzaSy...   # For image generation
```

### 3. Validate APIs

```bash
python scripts/validate_apis.py
```

### 4. Test Run (No Posting)

```bash
python scripts/test_run.py
```

### 5. Full Run with LinkedIn Posting

First, set up LinkedIn credentials:
```bash
python scripts/setup_linkedin_oauth.py
```

Then run the agent:
```bash
python -m orchestration.daily_agent
```

### 6. Schedule Daily Automation

```bash
crontab -e
# Add the line from crontab.example (adjust paths)
```

## Project Structure

```
marketing-automation-agent/
├── config/
│   ├── agent_config.py      # All configuration management
│   └── influencers.yaml     # 14 influencers with platform handles
├── content_fetchers/
│   ├── base_fetcher.py      # Abstract base + ContentItem dataclass
│   ├── rss_fetcher.py       # RSS/Atom feeds (no API key needed)
│   ├── twitter_fetcher.py   # Twitter v2 (needs TWITTER_BEARER_TOKEN)
│   └── youtube_fetcher.py   # YouTube v3 (needs YOUTUBE_API_KEY)
├── content_storage/
│   ├── database.py          # SQLite for content + post history
│   └── cache_manager.py     # File-based API response cache
├── content_analysis/
│   └── content_analyzer.py  # Claude analyzes content, picks top 3 topics
├── content_generation/
│   ├── post_generator.py    # Claude writes LinkedIn posts
│   ├── image_prompter.py    # Claude creates Gemini image prompts
│   └── image_generator.py   # Gemini generates images
├── posting/
│   ├── linkedin_poster.py   # LinkedIn UGC API (text + image posts)
│   └── image_uploader.py    # LinkedIn 2-step image upload
├── orchestration/
│   ├── daily_agent.py       # Main workflow orchestrator
│   └── notification_handler.py  # Email + Slack notifications
├── utils/
│   └── logger.py            # Centralized logging
├── scripts/
│   ├── test_run.py          # Preview mode (no posting)
│   ├── validate_apis.py     # Check all API connections
│   └── setup_linkedin_oauth.py  # Interactive LinkedIn OAuth setup
├── tests/                   # Pytest unit and integration tests
├── data/                    # Runtime data (gitignored)
├── .env.example             # Environment variable template
├── requirements.txt
└── crontab.example
```

## Activating Optional Platforms

### Twitter/X
1. Create developer account: https://developer.twitter.com
2. Create a project and app
3. Copy Bearer Token to `.env`:
   ```
   TWITTER_BEARER_TOKEN=AAAA...
   ```

### YouTube
1. Enable YouTube Data API v3 in Google Cloud Console
2. Create an API key
3. Add to `.env`:
   ```
   YOUTUBE_API_KEY=AIzaSy...
   ```

### LinkedIn Posting
Run the setup script:
```bash
python scripts/setup_linkedin_oauth.py
```
Or manually:
1. Create LinkedIn app at https://www.linkedin.com/developers/apps
2. Add products: "Share on LinkedIn", "Sign In with LinkedIn using OpenID Connect"
3. Run OAuth flow, get access token and URN
4. Add to `.env`:
   ```
   LINKEDIN_ACCESS_TOKEN=AQV...
   LINKEDIN_ORG_URN=urn:li:organization:XXXXXXXX
   ```

## Cost Estimates

| Service | Cost/day | Notes |
|---------|----------|-------|
| Claude API (Opus 4.6) | ~$1.00 | Analysis + 3 posts + 3 image prompts |
| Gemini Image Generation | ~$0.06 | 3 images × $0.02 |
| Twitter API | $0 | Free tier sufficient |
| YouTube API | $0 | 10K quota units/day free |
| LinkedIn API | $0 | Free posting access |
| **Total** | **~$1.06/day** | ~$32/month |

## Troubleshooting

**No content fetched**: Check that influencers.yaml has RSS feeds configured. RSS is the only platform active without additional API keys.

**Image generation fails**: Verify `GOOGLE_AI_STUDIO_KEY` is set. The model `gemini-3-pro-image-preview` must be available in your Google AI Studio account.

**LinkedIn 401 error**: Your access token has expired (LinkedIn tokens last 60 days). Re-run `setup_linkedin_oauth.py`.

**Claude API errors**: Check your `ANTHROPIC_API_KEY` and ensure you have credits available.

**Check logs**: `tail -f data/logs/$(date +%Y%m%d).log`
