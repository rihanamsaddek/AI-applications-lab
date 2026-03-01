"""Interactive LinkedIn OAuth 2.0 setup script.

This script guides you through:
1. Creating a LinkedIn app (if needed)
2. Getting an authorization code via browser
3. Exchanging it for an access token
4. Retrieving your person/organization URN
5. Saving credentials to .env
"""

import sys
import json
import webbrowser
import requests
import urllib.parse
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

REDIRECT_PORT = 8888
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler to capture the OAuth callback."""
    auth_code = None
    error = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self._respond("Authorization successful! You can close this tab.")
        elif "error" in params:
            OAuthCallbackHandler.error = params.get("error_description", ["Unknown error"])[0]
            self._respond(f"Authorization failed: {OAuthCallbackHandler.error}")
        else:
            self._respond("Unexpected callback — please check the URL.")

    def _respond(self, message: str):
        body = f"<html><body><h2>{message}</h2></body></html>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # Suppress server output


def capture_auth_code() -> str:
    """Start a local HTTP server to capture the OAuth callback."""
    server = HTTPServer(("localhost", REDIRECT_PORT), OAuthCallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()
    thread.join(timeout=120)

    if OAuthCallbackHandler.auth_code:
        return OAuthCallbackHandler.auth_code
    raise RuntimeError(OAuthCallbackHandler.error or "No authorization code received within timeout")


def exchange_code_for_token(client_id, client_secret, auth_code) -> str:
    """Exchange authorization code for an access token."""
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_person_urn(access_token) -> str:
    """Fetch the authenticated user's LinkedIn person URN."""
    resp = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    person_id = data.get("id")
    return f"urn:li:person:{person_id}"


def get_org_urns(access_token):
    """List organization URNs the user has admin access to."""
    resp = requests.get(
        "https://api.linkedin.com/v2/organizationAcls?q=roleAssignee",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        timeout=10,
    )
    if resp.status_code != 200:
        return []
    elements = resp.json().get("elements", [])
    return [e.get("organization") for e in elements if e.get("organization")]


def update_env(env_path: Path, key: str, value: str):
    """Update or append a key=value line in .env file."""
    content = env_path.read_text() if env_path.exists() else ""
    lines = content.splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n")


def main():
    print("=== LinkedIn OAuth 2.0 Setup ===\n")

    print("Step 1: LinkedIn App Configuration")
    print("  Go to: https://www.linkedin.com/developers/apps")
    print("  Create or select your app.")
    print("  Required products: 'Share on LinkedIn', 'Sign In with LinkedIn using OpenID Connect'")
    print(f"  Add this redirect URL to your app: {REDIRECT_URI}\n")

    client_id = input("Enter your LinkedIn App Client ID: ").strip()
    client_secret = input("Enter your LinkedIn App Client Secret: ").strip()

    print("\nStep 2: Authorization")
    scopes = "r_liteprofile r_emailaddress w_member_social"
    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urllib.parse.urlencode({
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "scope": scopes,
        })
    )
    print(f"Opening browser to: {auth_url}")
    webbrowser.open(auth_url)
    print("Waiting for authorization callback (120s timeout)...")

    try:
        auth_code = capture_auth_code()
        print(f"  ✓ Authorization code received")
    except Exception as e:
        print(f"  ✗ Failed to capture auth code: {e}")
        sys.exit(1)

    print("\nStep 3: Exchanging code for access token...")
    try:
        access_token = exchange_code_for_token(client_id, client_secret, auth_code)
        print(f"  ✓ Access token obtained: {access_token[:20]}...")
    except Exception as e:
        print(f"  ✗ Token exchange failed: {e}")
        sys.exit(1)

    print("\nStep 4: Fetching LinkedIn URNs...")
    try:
        person_urn = get_person_urn(access_token)
        print(f"  ✓ Person URN: {person_urn}")
    except Exception as e:
        print(f"  ✗ Could not fetch person URN: {e}")
        person_urn = ""

    org_urns = get_org_urns(access_token)
    org_urn = ""
    if org_urns:
        print(f"  ✓ Found {len(org_urns)} organization(s):")
        for i, urn in enumerate(org_urns):
            print(f"    [{i}] {urn}")
        choice = input("Select organization index for posting (or press Enter to skip): ").strip()
        if choice.isdigit() and int(choice) < len(org_urns):
            org_urn = org_urns[int(choice)]

    print("\nStep 5: Saving credentials to .env...")
    env_path = Path(__file__).parent.parent.parent / ".env"
    update_env(env_path, "LINKEDIN_ACCESS_TOKEN", access_token)
    if person_urn:
        update_env(env_path, "LINKEDIN_PERSON_URN", person_urn)
    if org_urn:
        update_env(env_path, "LINKEDIN_ORG_URN", org_urn)

    print(f"  ✓ Saved to: {env_path}")
    print("\n=== LinkedIn OAuth Setup Complete! ===")
    print("Run the agent with: python -m orchestration.daily_agent --preview-only")


if __name__ == "__main__":
    main()
