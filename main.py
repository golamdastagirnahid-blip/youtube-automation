import os
import sys
import time
import random
import feedparser
import requests
from datetime import datetime
from src.auth            import YouTubeAuth
from src.database        import Database
from src.downloader      import VideoDownloader
from src.uploader        import VideoUploader
from src.video_processor import VideoProcessor


class YouTubeAutomation:

    def __init__(self):
        self.db            = Database()
        self.auth          = YouTubeAuth()
        self.downloader    = VideoDownloader()
        self.processor     = VideoProcessor()
        self.youtube       = None
        self.uploader      = None
        self.known_videos  = set()

    def setup(self):
        print("=" * 60)
        print("🎬 YouTube Automation")
        print("   Source  : @LOLGopal")
        print("   Target  : @TekoGopal-o6f5f")
        print("=" * 60)

        self.youtube = self.auth.authenticate()
        if not self.youtube:
            print("❌ Authentication failed!")
            return False

        target_id     = self.auth.get_target_channel_id()
        self.uploader = VideoUploader(self.youtube, target_id)
        return True

    def get_channel_id_from_handle(self, handle):
        """Convert @handle to channel ID using RSS"""
        try:
            url     = f"https://www.youtube.com/{handle}/videos"
            headers = {'User-Agent': 'Mozilla/5.0'}
            r       = requests.get(url, headers=headers, timeout=10)
            if 'channelId' in r.text:
                start = r.text.find('"channelId":"') + 13
                end   = r.text.find('"', start)
                return r.text[start:end]
        except Exception:
            pass
        return None

    def check_rss(self, channel_id):
        """Check RSS feed for new videos"""
        url = (
            f"https://www.youtube.com/feeds/videos.xml"
            f"?channel_id={channel_id}"
        )
        try:
            feed       = feedparser.parse(url)
            new_videos = []

            for entry in feed.entries[:5]:
                vid_id = entry.get("yt_videoid", "")
                if not vid_id:
                    link = entry.get("link", "")
                    if "v=" in link:
                        vid_id = link.split("v=")[1].split("&")[0]

                if vid_id and \
                   vid_id not in self.known_videos and \
                   not self.db.is_video_uploaded(vid_id):
                    new_videos.append({
                        "video_id": vid_id,
                        "title"   : entry.get("title", "Unknown"),
                        "url"     : (
                            f"https://www.youtube.com/watch?v={vid_id}"
                        ),
                    })
                    self.known_videos.add(vid_id)

            return new_videos

        except Exception as e:
            print(f"⚠️ RSS error: {e}")
            return []

    def process_video(self, video_info):
        """Download, process and upload a single video"""
        vid_id    = video_info.get("video_id")
        video_url = video_info.get("url")

        if self.db.is_video_uploaded(vid_id):
            print(f"⏭️ Already uploaded: {vid_id}")
            return False

        # ── Download ───────────────────────────────
        print(f"\n📥 Downloading...")
        result = self.downloader.download_video(video_url, vid_id)

        if not result:
            print("❌ Download failed")
            return False

        # ── Process (Content ID bypass) ────────────
        print(f"\n🎬 Processing for Content ID bypass...")
        processed_file = self.processor.process(
            result["video_file"],
            vid_id
        )
        result["video_file"] = processed_file

        # ── Upload ─────────────────────────────────
        print(f"\n📤 Uploading...")
        upload = self.uploader.upload_video(result)

        # ── Cleanup ────────────────────────────────
        for key in ["video_file", "thumbnail_file"]:
            f = result.get(key)
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

        # Cleanup processed file
        self.processor.cleanup(vid_id)

        if upload and upload.get("success"):
            print(f"\n✅ DONE! {upload['url']}")
            return True

        print("❌ Upload failed")
        return False

    def run_continuous(self, channel_id):
        """Run continuously - watch channel and upload"""
        print(f"\n🚀 Watching channel: {channel_id}")
        print(f"   Checking every 5 minutes...")
        print(f"   Press Ctrl+C to stop\n")

        # Initialize known videos
        print("📋 Loading existing videos...")
        self.check_rss(channel_id)
        print(f"   Tracking {len(self.known_videos)} existing videos")

        while True:
            try:
                now = datetime.now().strftime("%H:%M:%S")
                print(f"\n🔍 [{now}] Checking for new videos...")

                new_videos = self.check_rss(channel_id)

                if new_videos:
                    print(f"🆕 {len(new_videos)} new video(s) found!")

                    for video in new_videos:
                        delay = random.randint(300, 2700)
                        print(
                            f"⏳ Waiting "
                            f"{delay // 60}m {delay % 60}s "
                            f"before upload..."
                        )
                        time.sleep(delay)
                        self.process_video(video)

                else:
                    print(f"   No new videos")

                wait = random.randint(280, 320)
                print(f"   Next check in {wait // 60} minutes...")
                time.sleep(wait)

            except KeyboardInterrupt:
                print("\n\n🛑 Stopped by user")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(60)

    def run_once_local(self, video_id, video_url, video_title):
        """Process single video - for testing"""
        self.process_video({
            "video_id": video_id,
            "url"     : video_url,
            "title"   : video_title,
        })

    def status(self):
        s = self.db.get_statistics()
        print(f"\n📊 Total Uploads: {s.get('total_uploads', 0)}")

    def auth_only(self):
        self.auth.authenticate()
        print(f"✅ Target: {self.auth.get_target_channel_id()}")


def main():
    tool    = YouTubeAutomation()
    command = sys.argv[1] if len(sys.argv) > 1 else "watch"

    # ── GitHub Actions Mode ────────────────────────
    if command == "run":
        video_id    = os.environ.get("VIDEO_ID",    "")
        video_url   = os.environ.get("VIDEO_URL",   "")
        video_title = os.environ.get("VIDEO_TITLE", "Video")

        if not video_id or not video_url:
            print("❌ VIDEO_ID and VIDEO_URL required!")
            sys.exit(1)

        print(f"\n🎯 New Video Detected")
        print(f"   Title : {video_title}")
        print(f"   ID    : {video_id}")

        if tool.setup():
            tool.process_video({
                "video_id": video_id,
                "url"     : video_url,
                "title"   : video_title,
            })

    # ── Watch Mode ─────────────────────────────────
    elif command == "watch":
        if tool.setup():
            channels = []
            if os.path.exists("channels.txt"):
                with open("channels.txt") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            channels.append(line)

            if not channels:
                print("❌ No channels in channels.txt!")
                return

            channel_id = channels[0]
            print(f"📺 Source channel: {channel_id}")
            tool.run_continuous(channel_id)

    # ── Test Mode ──────────────────────────────────
    elif command == "test":
        if len(sys.argv) < 4:
            print("Usage: python main.py test VIDEO_ID VIDEO_URL")
            return
        if tool.setup():
            tool.run_once_local(
                sys.argv[2],
                sys.argv[3],
                "Test Video"
            )

    # ── Status Mode ────────────────────────────────
    elif command == "status":
        tool.status()

    # ── Auth Mode ──────────────────────────────────
    elif command == "auth":
        tool.auth_only()

    else:
        print("Commands:")
        print("  python main.py run    - GitHub Actions mode")
        print("  python main.py watch  - Watch channel continuously")
        print("  python main.py test VIDEO_ID URL - Test single video")
        print("  python main.py status - Show stats")
        print("  python main.py auth   - Authenticate")


if __name__ == "__main__":
    main()
