import os
import sys
from src.auth       import YouTubeAuth
from src.database   import Database
from src.downloader import VideoDownloader
from src.uploader   import VideoUploader


class YouTubeAutomation:
    def __init__(self):
        self.db         = Database()
        self.auth       = YouTubeAuth()
        self.downloader = VideoDownloader()
        self.youtube    = None
        self.uploader   = None

    def setup(self):
        print("="*60)
        print("🎬 YouTube Automation")
        print("   Source  : @LOLGopal")
        print("   Target  : @TekoGopal-o6f5f")
        print("="*60)

        self.youtube = self.auth.authenticate()
        if not self.youtube:
            print("❌ Authentication failed!")
            return False

        target_id     = self.auth.get_target_channel_id()
        self.uploader = VideoUploader(self.youtube, target_id)
        return True

    def run(self):
        video_id    = os.environ.get("VIDEO_ID")
        video_url   = os.environ.get("VIDEO_URL")
        video_title = os.environ.get("VIDEO_TITLE", "Unknown")

        if not video_id or not video_url:
            print("❌ No video data received!")
            return

        print(f"\n🎯 New Video Detected")
        print(f"   Title : {video_title}")
        print(f"   ID    : {video_id}")

        if self.db.is_video_uploaded(video_id):
            print("⏭️ Already uploaded before. Skipping.")
            return

        if not self.setup():
            return

        print("\n📥 Downloading...")
        result = self.downloader.download_video(video_url, video_id)

        if not result:
            print("❌ Download failed")
            return

        print("\n📤 Uploading...")
        upload = self.uploader.upload_video(result)

        for key in ["video_file", "thumbnail_file"]:
            f = result.get(key)
            if f and os.path.exists(f):
                os.remove(f)

        if upload and upload.get("success"):
            print(f"\n✅ DONE! {upload['url']}")
        else:
            print("\n❌ Upload failed")

    def status(self):
        s = self.db.get_statistics()
        print(f"\n📊 Total Uploads: {s.get('total_uploads', 0)}")

    def auth_only(self):
        self.auth.authenticate()
        print(f"✅ Target Channel ID: {self.auth.get_target_channel_id()}")
        print(f"✅ Will upload to: @TekoGopal-o6f5f")


def main():
    tool    = YouTubeAutomation()
    command = sys.argv[1] if len(sys.argv) > 1 else "run"

    if   command == "run"   : tool.run()
    elif command == "status": tool.status()
    elif command == "auth"  : tool.auth_only()
    else: print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()