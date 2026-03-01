"""Configuration management for Marketing Automation Agent."""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict
from dotenv import load_dotenv


@dataclass
class InfluencerPlatforms:
    """Platforms available for a given influencer."""
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    linkedin: Optional[str] = None
    rss: Optional[str] = None


@dataclass
class Influencer:
    """An influencer to monitor."""
    name: str
    platforms: InfluencerPlatforms


@dataclass
class AgentConfig:
    """Configuration for the Marketing Automation Agent."""

    # Anthropic API
    anthropic_api_key: str
    model: str = "claude-opus-4-6"
    max_tokens: int = 4096

    # Google AI Studio (Gemini image generation)
    google_ai_studio_key: Optional[str] = None
    gemini_image_model: str = "gemini-3-pro-image-preview"
    google_cloud_project_number: Optional[str] = None

    # Twitter/X API (optional)
    twitter_bearer_token: Optional[str] = None

    # YouTube Data API (optional)
    youtube_api_key: Optional[str] = None

    # LinkedIn API (optional)
    linkedin_access_token: Optional[str] = None
    linkedin_org_urn: Optional[str] = None
    linkedin_person_urn: Optional[str] = None

    # Notification settings (optional)
    notification_email: Optional[str] = None
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    slack_webhook_url: Optional[str] = None

    # Storage
    database_path: str = "data/database/marketing_agent.db"
    images_path: str = "data/images"

    # Logging
    log_level: str = "INFO"
    log_path: str = "data/logs"

    # Influencers (loaded from YAML)
    influencers: List[Influencer] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables and influencers YAML."""
        # Locate .env file
        project_root = Path(__file__).parent.parent.parent
        dotenv_path = project_root / ".env"
        if dotenv_path.exists():
            load_dotenv(dotenv_path)
        else:
            load_dotenv()

        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required in .env file")

        config = cls(
            anthropic_api_key=anthropic_api_key,
            model=os.getenv("AGENT_MODEL", "claude-opus-4-6"),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
            google_ai_studio_key=os.getenv("GOOGLE_AI_STUDIO_KEY"),
            gemini_image_model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview"),
            google_cloud_project_number=os.getenv("GOOGLE_CLOUD_PROJECT_NUMBER"),
            twitter_bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
            linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
            linkedin_org_urn=os.getenv("LINKEDIN_ORG_URN"),
            linkedin_person_urn=os.getenv("LINKEDIN_PERSON_URN"),
            notification_email=os.getenv("NOTIFICATION_EMAIL"),
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            database_path=os.getenv("DATABASE_PATH", "data/database/marketing_agent.db"),
            images_path=os.getenv("IMAGES_PATH", "data/images"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_path=os.getenv("LOG_PATH", "data/logs"),
        )

        # Load influencers from YAML
        config.influencers = cls._load_influencers()
        return config

    @staticmethod
    def _load_influencers() -> List[Influencer]:
        """Load influencer list from config/influencers.yaml."""
        yaml_path = Path(__file__).parent / "influencers.yaml"
        if not yaml_path.exists():
            return []

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        influencers = []
        for item in data.get("influencers", []):
            platforms_data = item.get("platforms", {})
            influencers.append(Influencer(
                name=item["name"],
                platforms=InfluencerPlatforms(
                    twitter=platforms_data.get("twitter"),
                    youtube=platforms_data.get("youtube"),
                    linkedin=platforms_data.get("linkedin"),
                    rss=platforms_data.get("rss"),
                )
            ))
        return influencers

    @property
    def linkedin_author_urn(self) -> Optional[str]:
        """Return the best available LinkedIn URN for posting."""
        return self.linkedin_org_urn or self.linkedin_person_urn

    def can_post_to_linkedin(self) -> bool:
        """Check if LinkedIn posting is configured."""
        return bool(self.linkedin_access_token and self.linkedin_author_urn)

    def can_generate_images(self) -> bool:
        """Check if image generation is configured."""
        return bool(self.google_ai_studio_key)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration, returning (is_valid, error_list)."""
        errors = []
        warnings = []

        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")

        if not self.google_ai_studio_key:
            warnings.append("GOOGLE_AI_STUDIO_KEY not set — image generation disabled")

        if not self.linkedin_access_token:
            warnings.append("LINKEDIN_ACCESS_TOKEN not set — LinkedIn posting disabled (preview-only mode)")

        if not self.influencers:
            warnings.append("No influencers loaded from config/influencers.yaml")

        rss_influencers = [i for i in self.influencers if i.platforms.rss]
        if not rss_influencers:
            warnings.append("No influencers have RSS feeds configured")

        if warnings:
            for w in warnings:
                print(f"  ⚠ Warning: {w}")

        return len(errors) == 0, errors
