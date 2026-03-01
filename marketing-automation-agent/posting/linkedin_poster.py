"""LinkedIn posting module — supports text-only and image posts."""

import json
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

LINKEDIN_UGC_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_ME_URL = "https://api.linkedin.com/v2/me"


class LinkedInPoster:
    """Posts content to LinkedIn via the UGC API (text and image posts)."""

    def __init__(self, access_token: str, author_urn: str):
        """
        Args:
            access_token: LinkedIn OAuth 2.0 access token.
            author_urn: LinkedIn URN for the author
                        (e.g. 'urn:li:organization:123' or 'urn:li:person:abc').
        """
        self.access_token = access_token
        self.author_urn = author_urn
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def validate_credentials(self) -> bool:
        """Check that the access token is valid."""
        try:
            resp = requests.get(LINKEDIN_ME_URL, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                logger.info("LinkedIn credentials are valid")
                return True
            logger.error(f"LinkedIn auth failed: {resp.status_code} {resp.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"LinkedIn credential check error: {e}")
            return False

    def create_text_post(self, text: str, visibility: str = "PUBLIC") -> Dict:
        """Create a text-only LinkedIn post."""
        payload = {
            "author": self.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }
        return self._post(payload)

    def create_image_post(
        self,
        text: str,
        image_asset_urn: str,
        visibility: str = "PUBLIC",
    ) -> Dict:
        """Create a LinkedIn post with an attached image."""
        payload = {
            "author": self.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "media": image_asset_urn,
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }
        return self._post(payload)

    def _post(self, payload: dict) -> Dict:
        """Execute the LinkedIn post request."""
        try:
            resp = requests.post(
                LINKEDIN_UGC_URL,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30,
            )
            if resp.status_code == 201:
                post_id = resp.headers.get("X-RestLi-Id", "")
                logger.info(f"LinkedIn post published: {post_id}")
                return {"success": True, "post_id": post_id}
            else:
                logger.error(f"LinkedIn post failed: {resp.status_code} {resp.text[:300]}")
                return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as e:
            logger.error(f"LinkedIn post exception: {e}")
            return {"success": False, "error": str(e)}
