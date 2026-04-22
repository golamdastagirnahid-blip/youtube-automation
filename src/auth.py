import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from src.config import CLIENT_SECRETS_FILE, AUTH_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]

class YouTubeAuth:
    def __init__(self):
        self.credentials = None
        self.youtube = None

    def authenticate(self):
        print("🔐 Authenticating with YouTube...")

        if os.path.exists(AUTH_TOKEN_FILE):
            try:
                self.credentials = Credentials.from_authorized_user_file(AUTH_TOKEN_FILE, SCOPES)
                print("✅ Loaded saved token")
            except:
                self.credentials = None

        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
            self._save_token()

        if not self.credentials or not self.credentials.valid:
            if os.path.exists(CLIENT_SECRETS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                self.credentials = flow.run_local_server(port=8080)
                self._save_token()
                print("✅ Login successful")
            else:
                print("❌ client_secrets.json not found")
                return None

        self.youtube = build("youtube", "v3", credentials=self.credentials)
        print("✅ YouTube API ready")
        return self.youtube

    def _save_token(self):
        with open(AUTH_TOKEN_FILE, "w") as f:
            json.dump({
                "token": self.credentials.token,
                "refresh_token": self.credentials.refresh_token,
                "token_uri": self.credentials.token_uri,
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "scopes": SCOPES
            }, f, indent=4)

    def get_channel_info(self):
        if self.youtube:
            try:
                request = self.youtube.channels().list(part="snippet", mine=True)
                response = request.execute()
                print("📺 Channel:", response["items"][0]["snippet"]["title"])
            except Exception as e:
                print("⚠️ Could not get channel info")