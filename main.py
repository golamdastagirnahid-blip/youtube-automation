"""
YouTube Automation - Main Entry Point
Handles sleep/relax content channels
"""

import os
import sys
import json
import time
import random
import requests
from datetime import datetime


# ─────────────────────────────────────────────────────────
# Database Class
# ─────────────────────────────────────────────────────────
class Database:

    def __init__(self):
        self.db_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "database.json"
        )
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r") as f:
                    data = json.load(f)
                if "uploaded_videos" not in data:
                    data["uploaded_videos"] = []
                if "daily_counts" not in data:
                    data["daily_counts"] = {}
                if "statistics" not in data:
                    data["statistics"] = {
                        "total_uploads": 0
                    }
                if "queued" not in data:
                    data["queued"] = []
                return data
            except Exception:
                pass
        return {
            "uploaded_videos": [],
            "daily_counts"   : {},
            "statistics"     : {"total_uploads": 0},
            "queued"         : [],
        }

    def save(self):
        with open(self.db_file, "w") as f:
            json.dump(self.data, f, indent=4)

    def is_video_uploaded(self, video_id):
        return video_id in self.data.get(
            "uploaded_videos", []
        )

    def mark_video_uploaded(self, video_id, info={}):
        if video_id not in self.data.get(
            "uploaded_videos", []
        ):
            self.data["uploaded_videos"].append(video_id)
            self.data["statistics"]["total_uploads"] += 1
            today = datetime.now().strftime("%Y-%m-%d")
            self.data["daily_counts"][today] = (
                self.data["daily_counts"].get(today, 0) + 1
            )
            self.save()

    def get_statistics(self):
        return self.data.get(
            "statistics",
            {"total_uploads": 0}
        )


# ─────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────
from src.auth                import YouTubeAuth
from src.downloader          import VideoDownloader
from src.uploader            import VideoUploader
from src.video_processor     import VideoProcessor
from src.ai_generator        import AIGenerator
from src.thumbnail_generator import ThumbnailGenerator


# ─────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────
BASE_DIR             = os.path.dirname(os.path.abspath(__file__))
MIN_DURATION_SECONDS = 60  * 60
MAX_PART_SECONDS     = 4   * 60 * 60
MAX_DURATION_SECONDS = 24  * 60 * 60


# ─────────────────────────────────────────────────────────
# Proxy Helper
# ─────────────────────────────────────────────────────────
def load_all_proxies():
    """Load proxies from ALL countries"""
    all_proxies = []

    # Main full list first
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/proxifly/"
            "free-proxy-list/main/proxies/all/data.txt",
            timeout=15
        )
        if r.status_code == 200:
            lines = [
                l.strip()
                for l in r.text.splitlines()
                if l.strip() and not l.startswith('#')
            ]
            all_proxies.extend(lines)
            print(f"   ✅ Main list: {len(lines)} proxies")
    except Exception as e:
        print(f"   ⚠️ Main list error: {e}")

    # Priority country lists
    for country in ["BD", "IN", "SG", "ID", "PH", "VN"]:
        try:
            url = (
                f"https://raw.githubusercontent.com/"
                f"proxifly/free-proxy-list/main/"
                f"proxies/countries/{country}/data.txt"
            )
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                lines = [
                    l.strip()
                    for l in r.text.splitlines()
                    if l.strip() and not l.startswith('#')
                ]
                all_proxies.extend(lines)
        except Exception:
            continue

    random.shuffle(all_proxies)
    print(f"   📦 Total proxies: {len(all_proxies)}")
    return all_proxies


def format_proxy(proxy):
    """Format proxy URL correctly"""
    if not proxy:
        return None
    if proxy.startswith('http') or \
       proxy.startswith('socks'):
        return proxy
    return f"http://{proxy}"


# ─────────────────────────────────────────────────────────
# Main Class
# ─────────────────────────────────────────────────────────
class YouTubeAutomation:

    def __init__(self):
        self.db         = Database()
        self.auth       = YouTubeAuth()
        self.downloader = VideoDownloader()
        self.processor  = VideoProcessor()
        self.ai         = AIGenerator()
        self.thumb_gen  = ThumbnailGenerator()
        self.youtube    = None
        self.uploader   = None

    # ─────────────────────────────────────────────
    # Setup
    # ─────────────────────────────────────────────
    def setup(self):
        print("=" * 60)
        print("🎬 YouTube Automation")
        print("   Mode   : Sleep/Relax Content")
        print("   Target : @TekoGopal-o6f5f")
        print("=" * 60)

        self.youtube = self.auth.authenticate()
        if not self.youtube:
            print("❌ Authentication failed!")
            return False

        target_id     = self.auth.get_target_channel_id()
        self.uploader = VideoUploader(
            self.youtube, target_id
        )
        print(f"✅ Target channel: {target_id}")
        return True

    # ─────────────────────────────────────────────
    # Format Duration
    # ─────────────────────────────────────────────
    def format_duration(self, seconds):
        hours   = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

    # ─────────────────────────────────────────────
    # Get Video Info
    # ─────────────────────────────────────────────
    def get_video_info(self, video_url):
        """
        Get duration using worldwide proxies.
        Returns:
            duration → normal video
            -1       → live
            -2       → upcoming
             0       → error
        """
        import yt_dlp

        print(f"   🌍 Loading proxies...")
        all_proxies = load_all_proxies()

        for i, raw_proxy in enumerate(all_proxies[:20], 1):
            proxy = format_proxy(raw_proxy)
            print(f"   🔄 [{i}/20] {proxy}")

            ydl_opts = {
                'quiet'          : True,
                'no_warnings'    : True,
                'skip_download'  : True,
                'format'         : None,
                'noplaylist'     : True,
                'proxy'          : proxy,
                'socket_timeout' : 15,
                'extractor_args' : {
                    'youtube': {
                        'player_client': ['android'],
                    }
                },
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(
                        video_url,
                        download = False,
                        process  = False
                    )

                    if not info:
                        continue

                    is_live     = info.get('is_live', False)
                    live_status = info.get('live_status', '')

                    if is_live or live_status == 'is_live':
                        print(f"   🔴 Live — skipping")
                        return -1

                    if live_status == 'is_upcoming':
                        print(f"   📅 Upcoming — skipping")
                        return -2

                    if live_status == 'post_live':
                        print(f"   📺 Post-live — skipping")
                        return -1

                    duration = info.get('duration', 0)
                    if duration and duration > 0:
                        print(
                            f"   ✅ Duration: "
                            f"{self.format_duration(duration)}"
                        )
                        return duration

            except Exception as e:
                err = str(e)
                if 'live' in err.lower():
                    return -1
                continue

        print(f"⚠️ Could not get duration")
        return 0

    # ─────────────────────────────────────────────
    # Process Single Video
    # ─────────────────────────────────────────────
    def process_video(self, video_info):
        vid_id    = video_info.get("video_id")
        video_url = video_info.get("url")
        title     = video_info.get(
            "title", "Relaxing Video"
        )

        print(f"\n{'='*60}")
        print(f"🎬 Processing: {title}")
        print(f"   ID  : {vid_id}")
        print(f"   URL : {video_url}")
        print(f"{'='*60}")

        # Already uploaded?
        if self.db.is_video_uploaded(vid_id):
            print(f"⏭️ Already uploaded: {vid_id}")
            return False

        # Get video info
        print(f"\n⏱️ Checking video info...")
        duration = self.get_video_info(video_url)

        if duration == -1:
            print(f"⏭️ Live video — skipping")
            self.db.mark_video_uploaded(vid_id, {
                "title" : title,
                "reason": "live_video",
            })
            return False

        if duration == -2:
            print(f"⏭️ Upcoming — skipping")
            return False

        if duration == 0:
            print(f"⚠️ No duration — skipping")
            return False

        if duration < MIN_DURATION_SECONDS:
            print(
                f"⏭️ Too short "
                f"({self.format_duration(duration)}) "
                f"— skipping"
            )
            self.db.mark_video_uploaded(vid_id, {
                "title" : title,
                "reason": "too_short",
            })
            return False

        # Download audio
        print(f"\n📥 Downloading audio...")
        audio_file = self.downloader.download_audio(
            video_url, vid_id
        )

        if not audio_file:
            print("❌ Audio download failed")
            return False

        print(f"   ✅ Audio: {audio_file}")

        # Modify audio
        print(f"\n🔊 Modifying audio...")
        modified_audio = self.processor.modify_audio(
            audio_file, vid_id
        )
        print(f"   ✅ Modified: {modified_audio}")

        # AI metadata
        print(f"\n🤖 Generating AI metadata...")
        ai_title, ai_desc = self.ai.generate_metadata(title)
        print(f"   ✅ Title: {ai_title}")

        # Calculate parts
        num_parts = max(
            1,
            -(-int(duration) // MAX_PART_SECONDS)
        )

        print(f"\n📊 Split plan:")
        print(
            f"   Duration: "
            f"{self.format_duration(duration)}"
        )
        print(f"   Parts   : {num_parts}")

        success_count = 0

        for part_num in range(1, num_parts + 1):

            print(f"\n{'─'*50}")
            print(f"🎬 Part {part_num}/{num_parts}")
            print(f"{'─'*50}")

            start_sec     = (part_num - 1) * MAX_PART_SECONDS
            end_sec       = min(
                part_num * MAX_PART_SECONDS,
                duration
            )
            part_duration = end_sec - start_sec

            print(
                f"   ⏱️ "
                f"{self.format_duration(start_sec)} → "
                f"{self.format_duration(end_sec)}"
            )

            # Thumbnail
            print(f"\n🖼️ Generating thumbnail...")
            thumb_file = self.thumb_gen.generate(
                title    = ai_title,
                part_num = part_num if num_parts > 1
                           else None,
                duration = self.format_duration(
                    part_duration
                )
            )
            print(f"   ✅ Thumbnail: {thumb_file}")

            # Create video
            print(f"\n🎥 Creating video...")
            part_video = self.processor\
                .create_image_audio_video(
                    audio_file = modified_audio,
                    output_id  = f"{vid_id}_part{part_num}",
                    start_sec  = start_sec,
                    end_sec    = end_sec,
                    thumb_file = thumb_file
                )

            if not part_video:
                print(f"❌ Failed part {part_num}")
                continue

            print(f"   ✅ Video: {part_video}")

            # Build title
            if num_parts > 1:
                part_title = (
                    f"{ai_title} "
                    f"| Part {part_num} of {num_parts}"
                )
            else:
                part_title = ai_title

            # Build description
            part_desc = (
                f"{ai_desc}\n\n"
                f"⏱️ Duration: "
                f"{self.format_duration(part_duration)}\n"
            )
            if num_parts > 1:
                part_desc += (
                    f"📌 Part {part_num} of {num_parts}\n"
                    f"🕐 Starts at: "
                    f"{self.format_duration(start_sec)}\n"
                )
            part_desc += (
                f"\n🎵 Perfect for:\n"
                f"✅ Deep Sleep\n"
                f"✅ Relaxation\n"
                f"✅ Study & Focus\n"
                f"✅ Meditation\n"
                f"✅ Stress Relief\n\n"
                f"👍 Like & Subscribe!\n"
                f"🔔 Turn on notifications!\n\n"
                f"#sleep #relaxing #meditation "
                f"#study #focus #deepsleep "
                f"#rainsounds #whitenoise"
            )

            # Upload
            print(f"\n📤 Uploading Part {part_num}...")

            upload_result = self.uploader.upload_video({
                "video_id"         : (
                    f"{vid_id}_part{part_num}"
                ),
                "video_file"       : part_video,
                "thumbnail_file"   : thumb_file,
                "title"            : part_title,
                "description"      : part_desc,
                "blocked_countries": [],
                "allowed_countries": [],
            })

            if upload_result and \
               upload_result.get("success"):
                print(
                    f"   ✅ Part {part_num}: "
                    f"{upload_result['url']}"
                )
                success_count += 1
            else:
                print(f"   ❌ Part {part_num} failed")

            # Cleanup part video
            if part_video and os.path.exists(part_video):
                try:
                    os.remove(part_video)
                except Exception:
                    pass

            # Wait between parts
            if part_num < num_parts:
                wait = random.randint(30, 60)
                print(f"\n⏳ Waiting {wait}s...")
                time.sleep(wait)

        # Cleanup audio
        for f in [audio_file, modified_audio]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

        # Save to database
        if success_count > 0:
            self.db.mark_video_uploaded(vid_id, {
                "title"   : ai_title,
                "parts"   : num_parts,
                "uploaded": success_count,
                "duration": duration,
            })
            print(
                f"\n✅ Done! "
                f"{success_count}/{num_parts} parts"
            )
            return True

        print(f"\n❌ All parts failed")
        return False

    def status(self):
        s = self.db.get_statistics()
        print(
            f"\n📊 Uploads: "
            f"{s.get('total_uploads', 0)}"
        )

    def auth_only(self):
        self.auth.authenticate()
        print(
            f"✅ Target: "
            f"{self.auth.get_target_channel_id()}"
        )


# ─────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────
def main():
    tool    = YouTubeAutomation()
    command = sys.argv[1] if len(sys.argv) > 1 else "run"

    if command == "run":
        video_id    = os.environ.get("VIDEO_ID",    "")
        video_url   = os.environ.get("VIDEO_URL",   "")
        video_title = os.environ.get(
            "VIDEO_TITLE", "Relaxing Video"
        )

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

    elif command == "status":
        tool.status()

    elif command == "auth":
        tool.auth_only()

    else:
        print("Commands:")
        print("  python main.py run")
        print("  python main.py status")
        print("  python main.py auth")


if __name__ == "__main__":
    main()
