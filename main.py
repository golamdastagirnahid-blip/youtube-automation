"""
YouTube Automation Tool - Triggered by Google Apps Script
"""

import os
import sys
from src.auth import YouTubeAuth
from src.database import Database
from src.downloader import VideoDownloader
from src.uploader import VideoUploader

class YouTubeAutomation:
    def __init__(self):
        self.db = Database()
        self.auth = YouTubeAuth()
        self.downloader = VideoDownloader()

    def setup(self):
        print("="*60)
        print("🎬 YouTube Automation Started")
        print("="*60)
        
        self.youtube = self.auth.authenticate()
        if not self.youtube:
            print("❌ Authentication failed!")
            return False
            
        self.auth.get_channel_info()
        self.uploader = VideoUploader(self.youtube)
        return True

    def run(self):
        video_id    = os.environ.get("VIDEO_ID")
        video_url   = os.environ.get("VIDEO_URL")
        video_title = os.environ.get("VIDEO_TITLE", "Unknown Video")

        if not video_id or not video_url:
            print("❌ No video data received from trigger!")
            return

        print(f"\n🎯 New Video Detected")
        print(f"   Title : {video_title}")
        print(f"   ID    : {video_id}")

        if self.db.is_video_uploaded(video_id):
            print("⏭️ This video has already been uploaded before.")
            return

        if self.setup():
            result = self.downloader.download_video(video_url, video_id)
            if result:
                self.uploader.upload_video(result)
            else:
                print("❌ Download failed")

    def status(self):
        stats = self.db.get_statistics()
        print("\n📊 Current Status:")
        print(f"   Total Uploads : {stats.get('total_uploads', 0)}")


def main():
    tool = YouTubeAutomation()
    command = sys.argv[1] if len(sys.argv) > 1 else "run"

    if command == "run":
        tool.run()
    elif command == "status":
        tool.status()
    elif command == "auth":
        tool.auth.authenticate()
        tool.auth.get_channel_info()


if __name__ == "__main__":
    main()