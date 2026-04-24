import os
import sys
import time
import random
import feedparser
import requests
from datetime   import datetime
from src.auth              import YouTubeAuth
from src.database          import Database
from src.downloader        import VideoDownloader
from src.uploader          import VideoUploader
from src.video_processor   import VideoProcessor
from src.thumbnail_generator import ThumbnailGenerator
from src.ai_generator      import AIGenerator


class YouTubeAutomation:

    def __init__(self):
        self.db            = Database()
        self.auth          = YouTubeAuth()
        self.downloader    = VideoDownloader()
        self.processor     = VideoProcessor()
        self.thumb_gen     = ThumbnailGenerator()
        self.ai            = AIGenerator()
        self.youtube       = None
        self.uploader      = None
        self.known_videos  = set()

    def setup(self):
        print("=" * 60)
        print("🎬 YouTube Automation")
        print("   Mode    : Sleep/Relax Content")
        print("   Target  : @TekoGopal-o6f5f")
        print("=" * 60)

        self.youtube = self.auth.authenticate()
        if not self.youtube:
            print("❌ Authentication failed!")
            return False

        target_id     = self.auth.get_target_channel_id()
        self.uploader = VideoUploader(self.youtube, target_id)
        return True

    # ─────────────────────────────────────────────
    # Process Single Video
    # ─────────────────────────────────────────────
    def process_video(self, video_info):
        vid_id    = video_info.get("video_id")
        video_url = video_info.get("url")
        title     = video_info.get("title", 
