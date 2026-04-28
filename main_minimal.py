"""
YouTube Automation - Minimal Version
Uses only basic dependencies
"""

import os
import sys
import json
import time
import subprocess
import shutil
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


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
                    data["statistics"] = {"total_uploads": 0}
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
        return video_id in self.data.get("uploaded_videos", [])

    def mark_video_uploaded(self, video_id, info={}):
        if video_id not in self.data.get("uploaded_videos", []):
            self.data["uploaded_videos"].append(video_id)
            self.data["statistics"]["total_uploads"] += 1
            today = datetime.now().strftime("%Y-%m-%d")
            self.data["daily_counts"][today] = (
                self.data["daily_counts"].get(today, 0) + 1
            )
            self.save()

    def get_statistics(self):
        return self.data.get("statistics", {"total_uploads": 0})


# ─────────────────────────────────────────────────────────
# Simple Downloader
# ─────────────────────────────────────────────────────────
class SimpleDownloader:

    def __init__(self):
        self.downloads_dir = "downloads"
        os.makedirs(self.downloads_dir, exist_ok=True)

    def download_audio(self, video_url, video_id):
        """Download audio using yt-dlp"""
        print(f"\nDownloading audio: {video_id}")
        print(f"URL: {video_url}")

        output_path = os.path.join(self.downloads_dir, f"{video_id}.%(ext)s")

        # Try different formats
        formats = [
            'bestaudio[ext=m4a]/bestaudio/best',
            'bestaudio/best',
            'best',
        ]

        for fmt in formats:
            print(f"Trying format: {fmt}...")

            cmd = [
                'yt-dlp',
                '-f', fmt,
                '-o', output_path,
                '--no-warnings',
                '--quiet',
                '--progress',
                video_url
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600
                )

                if result.returncode == 0:
                    # Find downloaded file
                    for ext in ['m4a', 'mp3', 'opus', 'webm', 'aac']:
                        path = os.path.join(self.downloads_dir, f"{video_id}.{ext}")
                        if os.path.exists(path):
                            size = os.path.getsize(path)
                            if size > 1024:
                                print(f"Downloaded: {size / 1024 / 1024:.1f} MB")
                                return path

                    # Check for any file with video_id
                    for f in os.listdir(self.downloads_dir):
                        if video_id in f and not f.endswith(('.jpg', '.png', '.webp', '.part', '.ytdl')):
                            fpath = os.path.join(self.downloads_dir, f)
                            size = os.path.getsize(fpath)
                            if size > 1024:
                                print(f"Downloaded: {size / 1024 / 1024:.1f} MB")
                                return fpath
                else:
                    print(f"Failed: {result.stderr[-200:]}")

            except subprocess.TimeoutExpired:
                print("Download timeout")
            except Exception as e:
                print(f"Error: {e}")

        print("All download methods failed")
        return None


# ─────────────────────────────────────────────────────────
# Simple Video Processor
# ─────────────────────────────────────────────────────────
class SimpleVideoProcessor:

    def __init__(self):
        self.processed_dir = "processed"
        os.makedirs(self.processed_dir, exist_ok=True)
        self.has_ffmpeg = shutil.which("ffmpeg") is not None

    def modify_audio(self, audio_file, video_id):
        """Modify audio using FFmpeg"""
        if not self.has_ffmpeg:
            print("FFmpeg not found - skipping audio modify")
            return audio_file

        output = os.path.join(self.processed_dir, f"{video_id}_modified.m4a")

        cmd = [
            'ffmpeg',
            '-i', audio_file,
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y',
            output
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=7200
            )
            if result.returncode == 0 and os.path.exists(output):
                print("Audio modified OK")
                return output
            else:
                print(f"Audio modify failed: {result.stderr[-200:]}")
                return audio_file
        except Exception as e:
            print(f"Audio error: {e}")
            return audio_file

    def create_video(self, audio_file, output_id, thumb_file):
        """Create video from audio and thumbnail"""
        if not self.has_ffmpeg:
            print("FFmpeg not found - cannot create video")
            return None

        output = os.path.join(self.processed_dir, f"{output_id}.mp4")

        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', thumb_file,
            '-i', audio_file,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-y',
            output
        ]

        try:
            print("Creating video...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=86400
            )

            if result.returncode == 0 and os.path.exists(output):
                size = os.path.getsize(output)
                print(f"Video created: {size / 1024 / 1024:.1f} MB")
                return output
            else:
                print(f"Video creation failed: {result.stderr[-500:]}")
                return None

        except Exception as e:
            print(f"Video creation error: {e}")
            return None


# ─────────────────────────────────────────────────────────
# Simple Thumbnail Generator
# ─────────────────────────────────────────────────────────
class SimpleThumbnailGenerator:

    def __init__(self):
        self.thumbnails_dir = "thumbnails"
        os.makedirs(self.thumbnails_dir, exist_ok=True)

    def generate(self, title, part_num=None, duration="4h"):
        """Generate a simple thumbnail"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create image
            img = Image.new('RGB', (1280, 720), color='#1a1a2e')
            draw = ImageDraw.Draw(img)

            # Add title
            try:
                font = ImageFont.truetype('arial.ttf', 48)
            except:
                font = ImageFont.load_default()

            text = title[:50]
            if part_num:
                text = f"{text} | Part {part_num}"

            # Draw text centered
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (1280 - text_width) / 2
            y = (720 - text_height) / 2

            draw.text((x, y), text, fill='white', font=font)

            # Save
            output = os.path.join(self.thumbnails_dir, f"thumb_{int(time.time())}.jpg")
            img.save(output, 'JPEG', quality=90)

            print(f"Thumbnail created: {output}")
            return output

        except Exception as e:
            print(f"Thumbnail error: {e}")
            return None


# ─────────────────────────────────────────────────────────
# Simple Uploader
# ─────────────────────────────────────────────────────────
class SimpleUploader:

    def __init__(self):
        pass

    def upload_video(self, video_info):
        """Upload video to YouTube"""
        print("\n=== YouTube Upload ===")
        print("Note: This is a placeholder for the actual upload")
        print("The actual upload requires OAuth2 authentication")
        print("Please ensure CLIENT_SECRETS and YOUTUBE_TOKEN are set")
        print(f"Video: {video_info.get('video_file')}")
        print(f"Title: {video_info.get('title')}")
        print("=== Upload Placeholder ===")

        # Return success for testing
        return {
            "success": True,
            "video_id": "test_id",
            "url": "https://youtu.be/test"
        }


# ─────────────────────────────────────────────────────────
# Main Class
# ─────────────────────────────────────────────────────────
class YouTubeAutomation:

    def __init__(self):
        self.db         = Database()
        self.downloader = SimpleDownloader()
        self.processor  = SimpleVideoProcessor()
        self.thumb_gen  = SimpleThumbnailGenerator()
        self.uploader   = SimpleUploader()

    def process_video(self, video_info):
        vid_id    = video_info.get("video_id")
        video_url = video_info.get("url")
        title     = video_info.get("title", "Relaxing Video")

        print(f"\n{'='*60}")
        print(f"Processing: {title}")
        print(f"   ID  : {vid_id}")
        print(f"   URL : {video_url}")
        print(f"{'='*60}")

        if self.db.is_video_uploaded(vid_id):
            print(f"Already uploaded: {vid_id}")
            return False

        # Download audio
        print(f"\nDownloading audio...")
        audio_file = self.downloader.download_audio(video_url, vid_id)

        if not audio_file:
            print("Download failed")
            return False

        print(f"   Audio: {audio_file}")

        # Modify audio
        print(f"\nModifying audio...")
        modified_audio = self.processor.modify_audio(audio_file, vid_id)
        print(f"   Modified: {modified_audio}")

        # Generate thumbnail
        print(f"\nGenerating thumbnail...")
        thumb_file = self.thumb_gen.generate(title)
        print(f"   Thumbnail: {thumb_file}")

        # Create video
        print(f"\nCreating video...")
        video_file = self.processor.create_video(
            modified_audio,
            f"{vid_id}_video",
            thumb_file
        )

        if not video_file:
            print("Video creation failed")
            return False

        print(f"   Video: {video_file}")

        # Upload
        print(f"\nUploading...")
        upload_result = self.uploader.upload_video({
            "video_file": video_file,
            "title": title,
            "description": f"{title}\n\nDuration: 4 hours\n\n#sleep #relaxing #meditation",
        })

        if upload_result and upload_result.get("success"):
            print(f"Upload OK: {upload_result['url']}")
            self.db.mark_video_uploaded(vid_id, {"title": title})
            return True

        print("Upload failed")
        return False


# ─────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────
def main():
    tool = YouTubeAutomation()
    command = sys.argv[1] if len(sys.argv) > 1 else "run"

    if command == "run":
        video_id    = os.environ.get("VIDEO_ID",    "")
        video_url   = os.environ.get("VIDEO_URL",   "")
        video_title = os.environ.get("VIDEO_TITLE", "Relaxing Video")

        if not video_id or not video_url:
            print("VIDEO_ID and VIDEO_URL required!")
            sys.exit(1)

        print(f"\nNew Video Detected")
        print(f"   Title : {video_title}")
        print(f"   ID    : {video_id}")

        tool.process_video({
            "video_id": video_id,
            "url"     : video_url,
            "title"   : video_title,
        })

    elif command == "status":
        s = tool.db.get_statistics()
        print(f"\nUploads: {s.get('total_uploads', 0)}")

    else:
        print("Commands:")
        print("  python main_minimal.py run")
        print("  python main_minimal.py status")


if __name__ == "__main__":
    main()
