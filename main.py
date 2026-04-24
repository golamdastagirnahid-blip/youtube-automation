"""
YouTube Automation - Main Entry Point
Handles sleep/relax content channels
Features:
- Skip videos under 60 minutes
- Split videos over 4 hours into parts
- Static image + audio video creation
- AI generated thumbnails
- Small audio modification
"""

import os
import sys
import time
import random
import feedparser
import requests
from datetime import datetime

from src.auth              import YouTubeAuth
from src.database          import Database
from src.downloader        import VideoDownloader
from src.uploader          import VideoUploader
from src.video_processor   import VideoProcessor
from src.ai_generator      import AIGenerator
from src.thumbnail_generator import ThumbnailGenerator


# ─────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────
MIN_DURATION_SECONDS  = 60  * 60       # 60 minutes minimum
MAX_PART_SECONDS      = 4   * 60 * 60  # 4 hours per part
MAX_DURATION_SECONDS  = 24  * 60 * 60  # 24 hours maximum


class YouTubeAutomation:

    def __init__(self):
        self.db           = Database()
        self.auth         = YouTubeAuth()
        self.downloader   = VideoDownloader()
        self.processor    = VideoProcessor()
        self.ai           = AIGenerator()
        self.thumb_gen    = ThumbnailGenerator()
        self.youtube      = None
        self.uploader     = None
        self.known_videos = set()

    # ─────────────────────────────────────────────
    # Setup
    # ─────────────────────────────────────────────
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
        print(f"✅ Target channel: {target_id}")
        return True

    # ─────────────────────────────────────────────
    # Load Source Channels
    # ─────────────────────────────────────────────
    def load_channels(self):
        channels = []
        if os.path.exists("channels.txt"):
            with open("channels.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        channels.append(line)
        print(f"📋 Loaded {len(channels)} source channels")
        return channels

    # ─────────────────────────────────────────────
    # Check RSS Feed
    # ─────────────────────────────────────────────
    def check_rss(self, channel_id):
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
                            f"https://www.youtube.com"
                            f"/watch?v={vid_id}"
                        ),
                    })
                    self.known_videos.add(vid_id)

            return new_videos

        except Exception as e:
            print(f"⚠️ RSS error for {channel_id}: {e}")
            return []

    # ─────────────────────────────────────────────
    # Get Video Duration
    # ─────────────────────────────────────────────
    def get_video_duration(self, video_url):
        """Get duration in seconds using yt-dlp"""
        try:
            import yt_dlp
            ydl_opts = {
                'quiet'      : True,
                'no_warnings': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                duration = info.get('duration', 0)
                return duration
        except Exception as e:
            print(f"⚠️ Could not get duration: {e}")
            return 0

    # ─────────────────────────────────────────────
    # Format Duration
    # ─────────────────────────────────────────────
    def format_duration(self, seconds):
        hours   = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    # ─────────────────────────────────────────────
    # Process Single Video
    # ─────────────────────────────────────────────
    def process_video(self, video_info):
        vid_id    = video_info.get("video_id")
        video_url = video_info.get("url")
        title     = video_info.get("title", "Relaxing Video")

        print(f"\n{'='*60}")
        print(f"🎬 Processing: {title}")
        print(f"   ID  : {vid_id}")
        print(f"   URL : {video_url}")
        print(f"{'='*60}")

        # ── Check if already uploaded ──────────────
        if self.db.is_video_uploaded(vid_id):
            print(f"⏭️ Already uploaded: {vid_id}")
            return False

        # ── Check duration ─────────────────────────
        print(f"\n⏱️ Checking video duration...")
        duration = self.get_video_duration(video_url)

        if duration == 0:
            print(f"⚠️ Could not get duration — skipping")
            return False

        print(f"   Duration: {self.format_duration(duration)}")

        # Skip if less than 60 minutes
        if duration < MIN_DURATION_SECONDS:
            print(
                f"⏭️ Video too short "
                f"({self.format_duration(duration)}) "
                f"— minimum is 60 minutes — skipping"
            )
            self.db.mark_video_uploaded(vid_id, {
                "title" : title,
                "reason": "too_short",
                "duration": duration
            })
            return False

        # ── Download audio only ────────────────────
        print(f"\n📥 Downloading audio from source...")
        audio_file = self.downloader.download_audio(
            video_url, vid_id
        )

        if not audio_file:
            print("❌ Audio download failed")
            return False

        print(f"   ✅ Audio downloaded: {audio_file}")

        # ── Modify audio slightly ──────────────────
        print(f"\n🔊 Modifying audio...")
        modified_audio = self.processor.modify_audio(
            audio_file, vid_id
        )
        print(f"   ✅ Audio modified: {modified_audio}")

        # ── Generate AI metadata ───────────────────
        print(f"\n🤖 Generating AI title & description...")
        ai_title, ai_desc = self.ai.generate_metadata(title)
        print(f"   ✅ Title: {ai_title}")

        # ── Determine parts needed ─────────────────
        num_parts = max(1, -(-duration // MAX_PART_SECONDS))
        print(f"\n📊 Video split plan:")
        print(f"   Total duration : {self.format_duration(duration)}")
        print(f"   Part size      : {self.format_duration(MAX_PART_SECONDS)}")
        print(f"   Total parts    : {num_parts}")

        # ── Process each part ──────────────────────
        success_count = 0

        for part_num in range(1, num_parts + 1):

            print(f"\n{'─'*50}")
            print(f"🎬 Processing Part {part_num}/{num_parts}")
            print(f"{'─'*50}")

            # Calculate start and end time for this part
            start_sec = (part_num - 1) * MAX_PART_SECONDS
            end_sec   = min(
                part_num * MAX_PART_SECONDS,
                duration
            )
            part_duration = end_sec - start_sec

            print(
                f"   ⏱️ Part time: "
                f"{self.format_duration(start_sec)} → "
                f"{self.format_duration(end_sec)} "
                f"({self.format_duration(part_duration)})"
            )

            # ── Generate thumbnail for this part ───
            print(f"\n🖼️ Generating thumbnail for Part {part_num}...")
            thumb_file = self.thumb_gen.generate(
                title    = ai_title,
                part_num = part_num if num_parts > 1 else None,
                duration = self.format_duration(part_duration)
            )
            print(f"   ✅ Thumbnail: {thumb_file}")

            # ── Create video (image + audio) ───────
            print(f"\n🎥 Creating video (image + audio)...")
            part_video = self.processor.create_image_audio_video(
                audio_file  = modified_audio,
                output_id   = f"{vid_id}_part{part_num}",
                start_sec   = start_sec,
                end_sec     = end_sec,
                thumb_file  = thumb_file
            )

            if not part_video:
                print(f"❌ Failed to create Part {part_num}")
                continue

            print(f"   ✅ Video created: {part_video}")

            # ── Build part title ───────────────────
            if num_parts > 1:
                part_title = (
                    f"{ai_title} "
                    f"| Part {part_num} of {num_parts}"
                )
            else:
                part_title = ai_title

            # ── Build part description ─────────────
            part_desc = (
                f"{ai_desc}\n\n"
                f"⏱️ Duration: {self.format_duration(part_duration)}\n"
            )
            if num_parts > 1:
                part_desc += (
                    f"📌 Part {part_num} of {num_parts}\n"
                    f"🕐 Starts at: {self.format_duration(start_sec)}\n"
                )
            part_desc += (
                f"\n🎵 Perfect for:\n"
                f"✅ Deep Sleep\n"
                f"✅ Relaxation\n"
                f"✅ Study & Focus\n"
                f"✅ Meditation\n"
                f"✅ Stress Relief\n\n"
                f"👍 Like & Subscribe for more relaxing content!\n"
                f"🔔 Turn on notifications!\n\n"
                f"#sleep #relaxing #meditation #study #focus"
            )

            # ── Upload part ────────────────────────
            print(f"\n📤 Uploading Part {part_num}/{num_parts}...")
            print(f"   Title: {part_title}")

            upload_result = self.uploader.upload_video({
                "video_id"      : f"{vid_id}_part{part_num}",
                "video_file"    : part_video,
                "thumbnail_file": thumb_file,
                "title"         : part_title,
                "description"   : part_desc,
                "blocked_countries": [],
                "allowed_countries": [],
            })

            if upload_result and upload_result.get("success"):
                print(
                    f"   ✅ Part {part_num} uploaded: "
                    f"{upload_result['url']}"
                )
                success_count += 1
            else:
                print(f"   ❌ Part {part_num} upload failed")

            # ── Cleanup part video ─────────────────
            if os.path.exists(part_video):
                os.remove(part_video)

            # ── Wait between parts ─────────────────
            if part_num < num_parts:
                wait = random.randint(30, 60)
                print(f"\n⏳ Waiting {wait}s before next part...")
                time.sleep(wait)

        # ── Cleanup audio files ────────────────────
        for f in [audio_file, modified_audio]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

        # ── Mark as uploaded in database ──────────
        if success_count > 0:
            self.db.mark_video_uploaded(vid_id, {
                "title"      : ai_title,
                "parts"      : num_parts,
                "uploaded"   : success_count,
                "duration"   : duration,
            })
            print(
                f"\n✅ Complete! "
                f"{success_count}/{num_parts} parts uploaded"
            )
            return True

        print(f"\n❌ All parts failed")
        return False

    # ─────────────────────────────────────────────
    # Run Continuous Watch Mode
    # ─────────────────────────────────────────────
    def run_continuous(self):
        channels = self.load_channels()
        if not channels:
            print("❌ No channels in channels.txt!")
            return

        print(f"\n🚀 Watching {len(channels)} channels...")
        print(f"   Checking every 10 minutes")
        print(f"   Press Ctrl+C to stop\n")

        # Initialize known videos
        print("📋 Loading existing videos...")
        for channel_id in channels:
            self.check_rss(channel_id)
        print(f"   Tracking {len(self.known_videos)} existing videos\n")

        while True:
            try:
                now = datetime.now().strftime("%H:%M:%S")
                print(f"\n🔍 [{now}] Checking all channels...")

                all_new = []
                for channel_id in channels:
                    new = self.check_rss(channel_id)
                    if new:
                        print(
                            f"   🆕 {len(new)} new from "
                            f"{channel_id}"
                        )
                        all_new.extend(new)

                if all_new:
                    print(f"\n🆕 Total new: {len(all_new)} videos!")
                    for video in all_new:
                        self.process_video(video)
                else:
                    print(f"   No new videos found")

                # Wait 10 minutes
                wait = random.randint(580, 620)
                print(
                    f"\n   Next check in "
                    f"{wait // 60} minutes..."
                )
                time.sleep(wait)

            except KeyboardInterrupt:
                print("\n\n🛑 Stopped by user")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(60)

    # ─────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────
    def status(self):
        s = self.db.get_statistics()
        print(f"\n📊 Total Uploads: {s.get('total_uploads', 0)}")

    # ─────────────────────────────────────────────
    # Auth Only
    # ─────────────────────────────────────────────
    def auth_only(self):
        self.auth.authenticate()
        print(f"✅ Target: {self.auth.get_target_channel_id()}")


# ─────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────
def main():
    tool    = YouTubeAutomation()
    command = sys.argv[1] if len(sys.argv) > 1 else "watch"

    # ── GitHub Actions Mode ────────────────────────
    if command == "run":
        video_id    = os.environ.get("VIDEO_ID",    "")
        video_url   = os.environ.get("VIDEO_URL",   "")
        video_title = os.environ.get("VIDEO_TITLE", "Relaxing Video")

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
            tool.run_continuous()

    # ── Test Single Video ──────────────────────────
    elif command == "test":
        if len(sys.argv) < 4:
            print("Usage: python main.py test VIDEO_ID VIDEO_URL")
            return
        if tool.setup():
            tool.process_video({
                "video_id": sys.argv[2],
                "url"     : sys.argv[3],
                "title"   : "Test Relaxing Video",
            })

    # ── Status Mode ────────────────────────────────
    elif command == "status":
        tool.status()

    # ── Auth Mode ──────────────────────────────────
    elif command == "auth":
        tool.auth_only()

    else:
        print("Commands:")
        print("  python main.py run    - GitHub Actions mode")
        print("  python main.py watch  - Watch channels continuously")
        print("  python main.py test VIDEO_ID URL - Test one video")
        print("  python main.py status - Show statistics")
        print("  python main.py auth   - Authenticate YouTube")


if __name__ == "__main__":
    main()
