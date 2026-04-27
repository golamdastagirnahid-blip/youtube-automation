import os
import sys
import json
from google.oauth2.credentials          import Credentials
from google_auth_oauthlib.flow          import InstalledAppFlow
from google.auth.transport.requests     import Request
from googleapiclient.discovery          import build
from src.config import CLIENT_SECRETS_FILE, AUTH_TOKEN_FILE

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

TARGET_CHANNEL_ID = "UC84Tv3bIItZ47ZCJeVsRhIQ"


def is_headless():
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return True
    if not os.environ.get("DISPLAY") and sys.platform != "win32":
        return True
    return False


class YouTubeAuth:

    def __init__(self):
        self.credentials = None
        self.youtube     = None

    def authenticate(self):
        print("Authenticating...")

        if os.path.exists(AUTH_TOKEN_FILE):
            try:
                with open(AUTH_TOKEN_FILE, "r", encoding="utf-8-sig") as f:
                    raw = f.read().strip()
                if raw.startswith("\xef\xbb\xbf"):
                    raw = raw[3:]
                token_data = json.loads(raw)
                self.credentials = Credentials.from_authorized_user_info(
                    token_data, SCOPES
                )
                print("   Token loaded from file")
            except json.JSONDecodeError as e:
                print(f"   token.json is invalid JSON: {e}")
                print(f"   Check your YOUTUBE_TOKEN secret for BOM/encoding issues")
                self.credentials = None
            except Exception as e:
                print(f"   Failed to load token: {e}")
                self.credentials = None
        else:
            print(f"   No token.json found at {AUTH_TOKEN_FILE}")

        if self.credentials and self.credentials.expired \
                and self.credentials.refresh_token:
            print("   Token expired, refreshing...")
            try:
                self.credentials.refresh(Request())
                self._save_token()
                print("   Token refreshed successfully")
            except Exception as e:
                print(f"   Token refresh FAILED: {e}")
                print(f"   Your refresh token may have expired.")
                print(f"   If your Google Cloud app is in 'Testing' mode,")
                print(f"      refresh tokens expire after 7 days.")
                print(f"   Fix: Go to Google Cloud Console -> OAuth consent screen")
                print(f"      -> Publish the app, then re-generate token.json")
                self.credentials = None

        if not self.credentials or not self.credentials.valid:
            if is_headless():
                print("=" * 60)
                print("AUTHENTICATION FAILED ON HEADLESS RUNNER")
                print("")
                print("   Cannot open browser for OAuth on CI/headless.")
                print("   Your token.json is missing or expired.")
                print("")
                print("   TO FIX:")
                print("   1. Run 'python main.py auth' on your LOCAL machine")
                print("   2. This will open a browser for Google login")
                print("   3. Copy the new token.json content")
                print("   4. Update the YOUTUBE_TOKEN secret in GitHub")
                print("=" * 60)
                return None
            else:
                print("   Opening browser for OAuth...")
                try:
                    if not os.path.exists(CLIENT_SECRETS_FILE):
                        print(f"   Missing {CLIENT_SECRETS_FILE}")
                        return None
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CLIENT_SECRETS_FILE, SCOPES
                    )
                    self.credentials = flow.run_local_server(port=8080)
                    self._save_token()
                    print("   New token obtained via browser")
                except Exception as e:
                    print(f"   Browser OAuth failed: {e}")
                    return None

        try:
            self.youtube = build(
                "youtube", "v3",
                credentials=self.credentials
            )
            print("YouTube API ready")

            response = self.youtube.channels().list(
                part="snippet", mine=True
            ).execute()
            items = response.get("items", [])
            if items:
                ch = items[0]
                print(f"   Logged in as: {ch['snippet']['title']} ({ch['id']})")
            else:
                print("   No channel found for this account")

            return self.youtube

        except Exception as e:
            print(f"Failed to build YouTube API: {e}")
            return None

    def _save_token(self):
        try:
            token_data = {
                "token"        : self.credentials.token,
                "refresh_token": self.credentials.refresh_token,
                "token_uri"    : self.credentials.token_uri,
                "client_id"    : self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "scopes"       : SCOPES
            }
            with open(AUTH_TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=4)
            print(f"   Token saved to {AUTH_TOKEN_FILE}")
        except Exception as e:
            print(f"   Could not save token: {e}")

    def get_target_channel_id(self):
        return TARGET_CHANNEL_ID
