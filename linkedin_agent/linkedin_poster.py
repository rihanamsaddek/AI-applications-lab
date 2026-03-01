"""LinkedIn poster module for publishing content to LinkedIn."""

import requests
from typing import Dict, Optional
import json


class LinkedInPoster:
    """Handles posting content to LinkedIn via their API."""

    def __init__(self, access_token: str, person_urn: str):
        """Initialize the LinkedIn poster.

        Args:
            access_token: LinkedIn API access token
            person_urn: LinkedIn person URN (format: urn:li:person:XXXXXXXX)
        """
        self.access_token = access_token
        self.person_urn = person_urn
        self.api_url = "https://api.linkedin.com/v2/ugcPosts"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def create_post(self, text: str, visibility: str = "PUBLIC") -> Dict:
        """Create and publish a post on LinkedIn.

        Args:
            text: The post content
            visibility: Post visibility ("PUBLIC" or "CONNECTIONS")

        Returns:
            Response from LinkedIn API
        """
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        try:
            print(f"\n📤 Posting to LinkedIn...")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )

            if response.status_code == 201:
                print("  ✓ Post published successfully!")
                return {
                    "success": True,
                    "post_id": response.headers.get("X-RestLi-Id"),
                    "response": response.json()
                }
            else:
                print(f"  ✗ Failed to post: {response.status_code}")
                print(f"  Response: {response.text}")
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }

        except Exception as e:
            print(f"  ✗ Error posting to LinkedIn: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_post_with_url(
        self,
        text: str,
        url: str,
        title: str,
        description: str = "",
        visibility: str = "PUBLIC"
    ) -> Dict:
        """Create a post with a shared URL/article.

        Args:
            text: The post commentary
            url: URL to share
            title: Title for the shared content
            description: Description for the shared content
            visibility: Post visibility

        Returns:
            Response from LinkedIn API
        """
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": description
                            },
                            "originalUrl": url,
                            "title": {
                                "text": title
                            }
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        try:
            print(f"\n📤 Posting to LinkedIn with URL...")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )

            if response.status_code == 201:
                print("  ✓ Post with URL published successfully!")
                return {
                    "success": True,
                    "post_id": response.headers.get("X-RestLi-Id"),
                    "response": response.json()
                }
            else:
                print(f"  ✗ Failed to post: {response.status_code}")
                print(f"  Response: {response.text}")
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }

        except Exception as e:
            print(f"  ✗ Error posting to LinkedIn: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def validate_credentials(self) -> bool:
        """Validate LinkedIn API credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            print("\n🔑 Validating LinkedIn credentials...")
            # Try to access the user profile endpoint
            url = "https://api.linkedin.com/v2/me"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                print("  ✓ LinkedIn credentials are valid")
                return True
            else:
                print(f"  ✗ Invalid credentials: {response.status_code}")
                return False

        except Exception as e:
            print(f"  ✗ Error validating credentials: {e}")
            return False


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Test the LinkedIn poster (requires valid credentials)
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.getenv("LINKEDIN_PERSON_URN")

    if access_token and person_urn:
        poster = LinkedInPoster(access_token, person_urn)
        is_valid = poster.validate_credentials()

        if is_valid:
            print("\nLinkedIn integration is ready!")
        else:
            print("\nPlease check your LinkedIn credentials")
    else:
        print("LinkedIn credentials not found in .env file")
