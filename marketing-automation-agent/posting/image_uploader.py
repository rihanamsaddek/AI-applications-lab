"""LinkedIn image upload handler (2-step upload flow)."""

import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

REGISTER_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"


class ImageUploader:
    """Handles the LinkedIn 2-step image upload process."""

    def __init__(self, access_token: str, author_urn: str):
        self.access_token = access_token
        self.author_urn = author_urn
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def upload_image(self, image_path: str) -> Optional[str]:
        """Upload an image to LinkedIn and return its asset URN.

        Args:
            image_path: Local path to the image file (PNG/JPEG).

        Returns:
            LinkedIn asset URN (e.g. 'urn:li:digitalmediaAsset:...'), or None on failure.
        """
        # Step 1: Register the upload
        upload_url, asset_urn = self._register_upload()
        if not upload_url or not asset_urn:
            return None

        # Step 2: PUT the image binary to the upload URL
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            upload_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream",
            }
            put_resp = requests.put(
                upload_url,
                data=image_data,
                headers=upload_headers,
                timeout=60,
            )

            if put_resp.status_code in (200, 201):
                logger.info(f"Image uploaded successfully: {asset_urn}")
                return asset_urn
            else:
                logger.error(f"Image PUT failed: {put_resp.status_code} {put_resp.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"Image upload error: {e}")
            return None

    def _register_upload(self):
        """Step 1: Register the upload and get the upload URL + asset URN."""
        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": self.author_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }
        try:
            resp = requests.post(
                REGISTER_URL,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                value = data.get("value", {})
                upload_mechanism = value.get("uploadMechanism", {})
                # Navigate to the upload URL in the nested response
                com_key = "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
                upload_url = upload_mechanism.get(com_key, {}).get("uploadUrl")
                asset_urn = value.get("asset")
                if upload_url and asset_urn:
                    return upload_url, asset_urn
            logger.error(f"Register upload failed: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Register upload error: {e}")
        return None, None
