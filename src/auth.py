import os
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


class YouTubeAuth:

    def __init__(self):
        self.credentials = None
        self.youtube     = None

    def authenticate(self):
        print("🔐 Authenticating...")

        if os.path.exists(AUTH_TOKEN_FILE):
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    AUTH_TOKEN_FILE, SCOPES
                )
            except Exception:
                self.credentials = None

        if self.credentials and self.credentials.expired \
                and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                self._save_token()
            except Exception:
                self.credentials = None

        if not self.credentials or not self.credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            self.credentials = flow.run_local_server(port=8080)
            self._save_token()

        self.youtube = build("youtube", "v3", credentials=self.credentials)
        print("✅ YouTube API ready")
        return self.youtube

    def _save_token(self):
        with open(AUTH_TOKEN_FILE, "w") as f:
            json.dump({
                "token"        : self.credentials.token,
                "refresh_token": self.credentials.refresh_token,
                "token_uri"    : self.credentials.token_uri,
                "client_id"    : self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "scopes"       : SCOPES
            }, f, indent=4)

    def get_target_channel_id(self):
        return TARGET_CHANNEL_ID