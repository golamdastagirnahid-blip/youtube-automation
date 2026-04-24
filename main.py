import os
import sys
import time
from src.auth import YouTubeAuth
from src.database import Database
from src.downloader import VideoDownloader
from src.uploader import VideoUploader
from src.ai_generator import AIGenerator

class YouTubeAutomation:
    def __init__(self):
        self.db = Database()
        self.auth = YouTubeAuth()
        self.downloader = VideoDownloader()
        self.ai = AIGenerator()
        self.youtube = self.auth.authenticate()
        target_id = self.auth.get_target_channel_id()
        self.uploader = VideoUploader(self.youtube, target_id)

    def run_automation(self, video_id, video_url, original_title):
        # 1. Generate AI Metadata
        print("🤖 Generating AI Title & Description...")
        new_title, new_desc = self.ai.generate_metadata(original_title)
        
        # 2. Download
        result = self.downloader.download_video(video_url, video_id)
        if not result: return

        # 3. Update result with AI info
        result['title'] = new_title
        result['description'] = new_desc

        # 4. Upload
        print(f"📤 Uploading: {new_title}")
        self.uploader.upload_video(result)
        print("✅ Done!")

if __name__ == "__main__":
    bot = YouTubeAutomation()
    # Read from environment (GitHub Actions)
    v_id = os.environ.get("VIDEO_ID")
    v_url = os.environ.get("VIDEO_URL")
    v_title = os.environ.get("VIDEO_TITLE")
    
    if v_id and v_url:
        bot.run_automation(v_id, v_url, v_title)
