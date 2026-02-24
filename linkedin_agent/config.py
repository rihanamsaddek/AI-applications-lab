"""Configuration management for LinkedIn Marketing Agent."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class AgentConfig:
    """Configuration settings for the LinkedIn Marketing Agent."""

    # Anthropic API settings
    anthropic_api_key: str
    model: str = "claude-opus-4-6"
    max_tokens: int = 4096

    # LinkedIn API settings
    linkedin_access_token: Optional[str] = None
    linkedin_person_urn: Optional[str] = None

    # Document analysis settings
    documents_path: str = "./"

    # Content generation settings
    tone: str = "professional yet engaging"
    num_posts: int = 1

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables.

        Returns:
            AgentConfig instance with values from .env file
        """
        load_dotenv()

        # Required settings
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required in .env file")

        # Optional settings with defaults
        return cls(
            anthropic_api_key=anthropic_api_key,
            model=os.getenv("AGENT_MODEL", "claude-opus-4-6"),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
            linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
            linkedin_person_urn=os.getenv("LINKEDIN_PERSON_URN"),
            documents_path=os.getenv("DOCUMENTS_PATH", "./"),
            tone=os.getenv("CONTENT_TONE", "professional yet engaging"),
            num_posts=int(os.getenv("NUM_POSTS", "1"))
        )

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not self.anthropic_api_key:
            errors.append("Anthropic API key is required")

        if not self.linkedin_access_token and not self.linkedin_person_urn:
            errors.append("LinkedIn credentials are required for posting (can be skipped for preview-only mode)")

        return len(errors) == 0, errors


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = AgentConfig.from_env()
        is_valid, errors = config.validate()

        if is_valid:
            print("✓ Configuration loaded successfully")
            print(f"  Model: {config.model}")
            print(f"  Documents path: {config.documents_path}")
            print(f"  LinkedIn configured: {bool(config.linkedin_access_token)}")
        else:
            print("✗ Configuration errors:")
            for error in errors:
                print(f"  - {error}")

    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
