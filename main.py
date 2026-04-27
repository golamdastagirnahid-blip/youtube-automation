"""
YouTube Automation - Main Entry Point
Handles sleep/relax content channels
Uses OAuth2 for clean authentication - No VPN needed
"""

import os
import sys
import json
import time
import shutil
import random
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
HAS_FFMPEG           = shutil.which("ffmpeg") is not None


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
        print("YouTube Automation")
        print("   Mode   : Sleep/Relax Content")
        print("   Target : @TekoGopal-o6f5f")
        print("=" * 60)

        if HAS_FFMPEG:
            print("FFmpeg: installed")
        else:
            print("WARNING: FFmpeg NOT found!")
            print("   Audio modify will be skipped")
            print("   Video creation will FAIL without FFmpeg")
            print("   Install FFmpeg or add it to PATH")

        self.youtube = self.auth.authenticate()
        if not self.youtube:
            print("=" * 60)
            print("AUTHENTICATION FAILED - CANNOT CONTINUE")
            print("")
            print("   Possible causes:")
            print("   1. token.json is corrupt (BOM encoding)")
            print("   2. Refresh token expired (7-day limit in Testing mode)")
            print("   3. client_secrets.json is missing or invalid")
            print("")
            print("   To fix:")
            print("   1. Run 'python main.py auth' locally")
            print("   2. Update YOUTUBE_TOKEN secret in GitHub")
            print("   3. Publish your OAuth app in Google Cloud Console")
            print("=" * 60)
            return False

        target_id     = self.auth.get_target_channel_id()
        self.uploader = VideoUploader(
            self.youtube, target_id
        )
        print(f"Target channel: {target_id}")
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
        import yt_dlp

        ydl_opts = {
            'quiet'         : True,
            'no_warnings'   : True,
            'skip_download' : True,
            'format'        : None,
            'noplaylist'    : True,
            'socket_timeout': 30,
        }

        if os.path.exists("cookies.txt"):
            try:
                with open("cookies.txt", "r") as f:
                    head = f.read(500)
                if "Netscape" in head or "\t" in head:
                    ydl_opts['cookiefile'] = 'cookies.txt'
            except Exception:
                pass

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    video_url,
                    download = False,
                    process  = False
                )

                if not info:
                    return 0

                is_live     = info.get('is_live', False)
                live_status = info.get('live_status', '')

                if is_live or live_status == 'is_live':
                    print(f"   Live stream - skipping")
                    return -1

                if live_status == 'is_upcoming':
                    print(f"   Upcoming - skipping")
                    return -2

                if live_status == 'post_live':
                    print(f"   Post-live - skipping")
                    return -1

                duration = info.get('duration', 0)

                if not duration or duration == 0:
                    print(f"   No duration found")
                    return 0

                print(
                    f"   Duration: "
                    f"{self.format_duration(duration)}"
                )
                return duration

        except Exception as e:
            err = str(e)
            if 'live' in err.lower():
                return -1
            print(f"Info error: {e}")

        print(f"   Fallback: android_vr client...")
        ydl_opts_fallback = {
            'quiet'          : True,
            'no_warnings'    : True,
            'skip_download'  : True,
            'format'         : None,
            'noplaylist'     : True,
            'socket_timeout' : 30,
            'extractor_args' : {
                'youtube': {
                    'player_client': ['android_vr'],
                }
            },
        }

        if os.path.exists("cookies.txt"):
            try:
                with open("cookies.txt", "r") as f:
                    head = f.read(500)
                if "Netscape" in head or "\t" in head:
                    ydl_opts_fallback['cookiefile'] = 'cookies.txt'
            except Exception:
                pass

        try:
            with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
                info = ydl.extract_info(
                    video_url,
                    download = False,
                    process  = False
                )

                if not info:
                    return 0

                is_live     = info.get('is_live', False)
                live_status = info.get('live_status', '')

                if is_live or live_status == 'is_live':
                    print(f"   Live stream - skipping")
                    return -1

                if live_status == 'is_upcoming':
                    print(f"   Upcoming - skipping")
                    return -2

                duration = info.get('duration', 0)

                if not duration or duration == 0:
                    print(f"   No duration found")
                    return 0

                print(
                    f"   Duration: "
                    f"{self.format_duration(duration)}"
                )
                return duration

        except Exception as e:
            err = str(e)
            if 'live' in err.lower():
                return -1
            print(f"Fallback error: {e}")
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
        print(f"Processing: {title}")
        print(f"   ID  : {vid_id}")
        print(f"   URL : {video_url}")
        print(f"{'='*60}")

        if self.db.is_video_uploaded(vid_id):
            print(f"Already uploaded: {vid_id}")
            return False

        if not HAS_FFMPEG:
            print("FATAL: FFmpeg not installed - cannot process video")
            print("   Install FFmpeg on the runner and add to PATH")
            return False

        print(f"\nChecking video info...")
        duration = self.get_video_info(video_url)

        if duration == -1:
            print(f"Live video - skipping")
            self.db.mark_video_uploaded(vid_id, {
                "title" : title,
                "reason": "live_video",
            })
            return False

        if duration == -2:
            print(f"Upcoming - skipping")
            return False

        if duration == 0:
            print(f"No duration - skipping")
            return False

        if duration < MIN_DURATION_SECONDS:
            print(
                f"Too short "
                f"({self.format_duration(duration)}) "
                f"- skipping"
            )
            self.db.mark_video_uploaded(vid_id, {
                "title" : title,
                "reason": "too_short",
            })
            return False

        print(f"\nDownloading audio...")
        audio_file = self.downloader.download_audio(
            video_url, vid_id
        )

        if not audio_file:
            print("Download failed")
            return False

        print(f"   Audio: {audio_file}")

        print(f"\nModifying audio...")
        modified_audio = self.processor.modify_audio(
            audio_file, vid_id
        )
        print(f"   Modified: {modified_audio}")

        print(f"\nGenerating AI metadata...")
        ai_title, ai_desc = self.ai.generate_metadata(title)
        print(f"   Title: {ai_title}")

        num_parts = max(
            1,
            -(-int(duration) // MAX_PART_SECONDS)
        )

        print(f"\nSplit plan:")
        print(
            f"   Duration: "
            f"{self.format_duration(duration)}"
        )
        print(f"   Parts   : {num_parts}")

        success_count = 0

        for part_num in range(1, num_parts + 1):

            print(f"\n{'-'*50}")
            print(f"Part {part_num}/{num_parts}")
            print(f"{'-'*50}")

            start_sec     = (part_num - 1) * MAX_PART_SECONDS
            end_sec       = min(
                part_num * MAX_PART_SECONDS,
                duration
            )
            part_duration = end_sec - start_sec

            print(
                f"   Time: "
                f"{self.format_duration(start_sec)} -> "
                f"{self.format_duration(end_sec)}"
            )

            print(f"\nGenerating thumbnail...")
            thumb_file = self.thumb_gen.generate(
                title    = ai_title,
                part_num = part_num if num_parts > 1
                           else None,
                duration = self.format_duration(
                    part_duration
                )
            )
            print(f"   Thumbnail: {thumb_file}")

            print(f"\nCreating video...")
            part_video = self.processor\
                .create_image_audio_video(
                    audio_file = modified_audio,
                    output_id  = f"{vid_id}_part{part_num}",
                    start_sec  = start_sec,
                    end_sec    = end_sec,
                    thumb_file = thumb_file
                )

            if not part_video:
                print(f"Failed part {part_num}")
                continue

            print(f"   Video: {part_video}")

            if num_parts > 1:
                part_title = (
                    f"{ai_title} "
                    f"| Part {part_num} of {num_parts}"
                )
            else:
                part_title = ai_title

            part_desc = (
                f"{ai_desc}\n\n"
                f"Duration: "
                f"{self.format_duration(part_duration)}\n"
            )
            if num_parts > 1:
                part_desc += (
                    f"Part {part_num} of {num_parts}\n"
                    f"Starts at: "
                    f"{self.format_duration(start_sec)}\n"
                )
            part_desc += (
                f"\nPerfect for:\n"
                f"- Deep Sleep\n"
                f"- Relaxation\n"
                f"- Study & Focus\n"
                f"- Meditation\n"
                f"- Stress Relief\n\n"
                f"Like & Subscribe!\n"
                f"Turn on notifications!\n\n"
                f"#sleep #relaxing #meditation "
                f"#study #focus #deepsleep "
                f"#rainsounds #whitenoise"
            )

            print(f"\nUploading Part {part_num}...")

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
                    f"   Part {part_num} OK: "
                    f"{upload_result['url']}"
                )
                success_count += 1
            else:
                print(f"   Part {part_num} upload failed")

            if part_video and os.path.exists(part_video):
                try:
                    os.remove(part_video)
                except Exception:
                    pass

            if part_num < num_parts:
                wait = random.randint(30, 60)
                print(f"\nWaiting {wait}s...")
                time.sleep(wait)

        for f in [audio_file, modified_audio]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

        if success_count > 0:
            self.db.mark_video_uploaded(vid_id, {
                "title"   : ai_title,
                "parts"   : num_parts,
                "uploaded": success_count,
                "duration": duration,
            })
            print(
                f"\nDone! "
                f"{success_count}/{num_parts} parts uploaded"
            )
            return True

        print(f"\nAll parts failed")
        return False

    def status(self):
        s = self.db.get_statistics()
        print(
            f"\nUploads: "
            f"{s.get('total_uploads', 0)}"
        )

    def auth_only(self):
        self.auth.authenticate()
        print(
            f"Target: "
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
            print("VIDEO_ID and VIDEO_URL required!")
            sys.exit(1)

        print(f"\nNew Video Detected")
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
