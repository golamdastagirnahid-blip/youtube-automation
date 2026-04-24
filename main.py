"""
YouTube Automation - Sleep/Relax Content
Features:
- Skip videos under 60 minutes
- Split long videos into parts
- Static image + audio video creation
- AI generated thumbnails
- Small audio modification
"""

import os
import sys
import json
import time
import random
import subprocess
import feedparser
import requests
import yt_dlp
from datetime import datetime


# ─────────────────────────────────────────────────────────
# Built-in Database (avoids import issues)
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
                for key, default in [
                    ("uploaded_videos", []),
                    ("daily_counts", {}),
                    ("statistics", {"total_uploads": 0}),
                    ("queued", []),
                ]:
                    if key not in data:
                        data[key] = default
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

    def mark_video_uploaded(self, video_id, info=None):
        if video_id not in self.data["uploaded_videos"]:
            self.data["uploaded_videos"].append(video_id)
            self.data["statistics"]["total_uploads"] += 1
            today = datetime.now().strftime("%Y-%m-%d")
            self.data["daily_counts"][today] = (
                self.data["daily_counts"].get(today, 0) + 1
            )
            self.save()

    def get_statistics(self):
        return self.data.get(
            "statistics", {"total_uploads": 0}
        )


# ─────────────────────────────────────────────────────────
# Built-in AI Generator
# ─────────────────────────────────────────────────────────
class AIGenerator:

    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.url     = "https://openrouter.ai/api/v1/chat/completions"

    def generate_metadata(self, original_title):
        if not self.api_key:
            print("   ⚠️ No AI key - using original title")
            return original_title, (
                "Relaxing sounds for deep sleep "
                "and relaxation."
            )

        prompt = (
            f"Create a viral YouTube title and a short "
            f"3-line description for a relaxing sleep "
            f"video. Original title: '{original_title}'"
            f". Return ONLY valid JSON: "
            f'{{"title": "...", "description": "..."}}'
        )

        try:
            r = requests.post(
                self.url,
                headers={
                    "Authorization"  : (
                        f"Bearer {self.api_key}"
                    ),
                    "Content-Type"   : "application/json",
                },
                json={
                    "model"  : (
                        "google/gemini-2.0-flash-exp:free"
                    ),
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                },
                timeout=30,
            )
            data    = r.json()
            content = data["choices"][0]["message"]["content"]
            # Clean response
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            metadata = json.loads(content.strip())
            return (
                metadata.get("title", original_title),
                metadata.get("description", ""),
            )
        except Exception as e:
            print(f"   ⚠️ AI error: {e}")
            return (
                f"🎵 {original_title}",
                "Relaxing sounds for sleep and focus.",
            )


# ─────────────────────────────────────────────────────────
# Built-in Thumbnail Generator
# ─────────────────────────────────────────────────────────
class ThumbnailGenerator:

    def __init__(self):
        self.thumb_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "thumbnails"
        )
        os.makedirs(self.thumb_dir, exist_ok=True)

    def generate(self, title, part_num=None, duration=""):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            print("   ⚠️ Pillow not installed")
            return None

        width, height = 1280, 720

        # Random gradient color
        colors = [
            ((10, 10, 50), (60, 60, 120)),
            ((20, 10, 40), (70, 30, 90)),
            ((10, 30, 50), (30, 80, 120)),
            ((30, 10, 10), (100, 40, 40)),
            ((10, 40, 30), (40, 120, 80)),
        ]
        c1, c2 = random.choice(colors)

        img  = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Draw gradient
        for y in range(height):
            ratio  = y / height
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Add text
        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/"
                "DejaVuSans-Bold.ttf",
                48
            )
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/"
                "DejaVuSans.ttf",
                28
            )
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Title text
        display_title = title[:50]
        bbox = draw.textbbox(
            (0, 0), display_title, font=font_large
        )
        text_w = bbox[2] - bbox[0]
        x      = (width - text_w) // 2
        draw.text(
            (x, 200),
            display_title,
            fill="white",
            font=font_large,
        )

        # Part number
        if part_num:
            part_text = f"Part {part_num}"
            bbox2 = draw.textbbox(
                (0, 0), part_text, font=font_small
            )
            tw2   = bbox2[2] - bbox2[0]
            draw.text(
                ((width - tw2) // 2, 300),
                part_text,
                fill=(255, 200, 100),
                font=font_small,
            )

        # Duration
        if duration:
            bbox3 = draw.textbbox(
                (0, 0), duration, font=font_small
            )
            tw3   = bbox3[2] - bbox3[0]
            draw.text(
                ((width - tw3) // 2, 360),
                duration,
                fill=(200, 200, 200),
                font=font_small,
            )

        # Sleep icons
        icons = ["🌙", "✨", "💤", "🎵", "🌧️"]
        icon  = random.choice(icons)
        draw.text(
            (width - 120, 20),
            icon,
            fill="white",
            font=font_large,
        )

        # Save
        output = os.path.join(
            self.thumb_dir, "thumb_generated.jpg"
        )
        img.save(output, quality=95)
        return output

        except Exception as e:
            print(f"   ⚠️ Thumbnail error: {e}")
            return None


# ─────────────────────────────────────────────────────────
# Built-in Audio Downloader
# ─────────────────────────────────────────────────────────
class AudioDownloader:

    def __init__(self):
        self.download_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "downloads"
        )
        os.makedirs(self.download_dir, exist_ok=True)

    def download_audio(self, video_url, video_id):
        output = os.path.join(
            self.download_dir, f"{video_id}.%(ext)s"
        )
        ydl_opts = {
            "format"      : "bestaudio/best",
            "outtmpl"     : output,
            "postprocessors": [{
                "key"          : "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet"       : True,
            "no_warnings" : True,
            "socket_timeout": 30,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    video_url, download=True
                )

            audio_file = os.path.join(
                self.download_dir,
                f"{video_id}.mp3"
            )
            if os.path.exists(audio_file):
                return audio_file

            # Search for any audio file
            for f in os.listdir(self.download_dir):
                if video_id in f and f.endswith(
                    (".mp3", ".m4a", ".opus", ".wav")
                ):
                    return os.path.join(
                        self.download_dir, f
                    )

            return None

        except Exception as e:
            print(f"   ❌ Download error: {e}")
            return None


# ─────────────────────────────────────────────────────────
# Built-in Audio Modifier
# ─────────────────────────────────────────────────────────
class AudioModifier:

    def __init__(self):
        self.download_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "downloads"
        )

    def modify(self, audio_file, video_id):
        output = os.path.join(
            self.download_dir,
            f"{video_id}_modified.mp3"
        )

        # Small pitch shift
        pitch = random.choice([1.02, 1.03, 0.98, 0.97])

        cmd = [
            "ffmpeg",
            "-i",       audio_file,
            "-af", (
                f"asetrate=44100*{pitch},"
                f"aresample=44100,"
                f"equalizer=f=1000:width_type=o:"
                f"width=2:g=1"
            ),
            "-c:a",     "libmp3lame",
            "-b:a",     "128k",
            "-y",
            output,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output = True,
                text           = True,
                timeout        = 600,
            )
            if result.returncode == 0 and \
               os.path.exists(output):
                return output
            else:
                return audio_file
        except Exception:
            return audio_file


# ─────────────────────────────────────────────────────────
# Built-in Video Creator (Image + Audio)
# ─────────────────────────────────────────────────────────
class VideoCreator:

    def __init__(self):
        self.processed_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "processed"
        )
        os.makedirs(self.processed_dir, exist_ok=True)

    def create(
        self, audio_file, thumb_file,
        output_id, start_sec=0, end_sec=0
    ):
        output = os.path.join(
            self.processed_dir,
            f"{output_id}.mp4"
        )

        cmd = [
            "ffmpeg",
            "-loop",  "1",
            "-i",     thumb_file,
            "-i",     audio_file,
        ]

        # Add time restrictions for parts
        if start_sec > 0 or end_sec > 0:
            duration = end_sec - start_sec
            cmd.extend(["-ss", str(start_sec)])
            cmd.extend(["-t", str(duration)])

        cmd.extend([
            "-c:v",    "libx264",
            "-tune",   "stillimage",
            "-c:a",    "aac",
            "-b:a",    "128k",
            "-pix_fmt","yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            "-y",
            output,
        ])

        try:
            print(
                f"   ⏳ Creating video "
                f"(may take minutes)..."
            )
            result = subprocess.run(
                cmd,
                capture_output = True,
                text           = True,
                timeout        = 3600,
            )

            if result.returncode == 0 and \
               os.path.exists(output):
                size = os.path.getsize(output)
                print(
                    f"   ✅ Video: "
                    f"{size // 1024 // 1024} MB"
                )
                return output
            else:
                print(f"   ❌ FFmpeg error")
                if result.stderr:
                    print(
                        f"   {result.stderr[-300:]}"
                    )
                return None

        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout creating video")
            return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None


# ─────────────────────────────────────────────────────────
# Main Automation Class
# ─────────────────────────────────────────────────────────
MIN_DURATION  = 60 * 60      # 60 minutes
MAX_PART      = 4 * 60 * 60  # 4 hours per part


class YouTubeAutomation:

    def __init__(self):
        self.db       = Database()
        self.ai       = AIGenerator()
        self.thumb_gen = ThumbnailGenerator()
        self.downloader = AudioDownloader()
        self.modifier  = AudioModifier()
        self.creator   = VideoCreator()
        self.youtube   = None
        self.uploader  = None

    def setup(self):
        print("=" * 60)
        print("🎬 YouTube Automation")
        print("   Mode    : Sleep/Relax Content")
        print("   Target  : @TekoGopal-o6f5f")
        print("=" * 60)

        # YouTube Auth
        try:
            from src.auth import YouTubeAuth
            self.auth = YouTubeAuth()
            self.youtube = self.auth.authenticate()
            if not self.youtube:
                print("❌ Auth failed!")
                return False
            from src.uploader import VideoUploader
            target_id = self.auth.get_target_channel_id()
            self.uploader = VideoUploader(
                self.youtube, target_id
            )
            print(f"✅ Channel: {target_id}")
            return True
        except Exception as e:
            print(f"❌ Setup error: {e}")
            return False

    def get_duration(self, url):
        try:
            ydl_opts = {
                "quiet"       : True,
                "no_warnings" : True,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info     = ydl.extract_info(url, download=False)
                duration = info.get("duration", 0)
                title    = info.get("title", "Unknown")
                return duration, title
        except Exception:
            return 0, "Unknown"

    def format_time(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"

    def process_video(self, video_info):
        vid_id  = video_info.get("video_id")
        url     = video_info.get("url")
        title   = video_info.get("title", "Relaxing")

        print(f"\n{'='*60}")
        print(f"🎬 {title}")
        print(f"   ID: {vid_id}")
        print(f"{'='*60}")

        # Check if already uploaded
        if self.db.is_video_uploaded(vid_id):
            print("⏭️ Already uploaded")
            return False

        # Check duration
        print(f"\n⏱️ Checking duration...")
        duration, real_title = self.get_duration(url)
        if duration == 0:
            print("⚠️ Could not get duration")
            return False

        duration_str = self.format_time(duration)
        print(f"   Duration: {duration_str}")

        if duration < MIN_DURATION:
            print(
                f"⏭️ Too short "
                f"({duration_str}) — minimum 60m"
            )
            self.db.mark_video_uploaded(vid_id)
            return False

        # Use real title if available
        if real_title and real_title != "Unknown":
            title = real_title

        # Download audio
        print(f"\n📥 Downloading audio...")
        audio = self.downloader.download_audio(url, vid_id)
        if not audio:
            print("❌ Audio download failed")
            return False
        print(f"   ✅ Audio: {audio}")

        # Modify audio
        print(f"\n🔊 Modifying audio...")
        mod_audio = self.modifier.modify(audio, vid_id)
        print(f"   ✅ Modified")

        # AI metadata
        print(f"\n🤖 Generating AI title...")
        ai_title, ai_desc = self.ai.generate_metadata(title)
        print(f"   ✅ Title: {ai_title}")

        # Split into parts
        num_parts = max(
            1, -(-duration // MAX_PART)
        )
        print(f"\n📊 Parts: {num_parts}")
        success = 0

        for part in range(1, num_parts + 1):
            print(
                f"\n{'─'*40}\n"
                f"🎬 Part {part}/{num_parts}\n"
                f"{'─'*40}"
            )

            start = (part - 1) * MAX_PART
            end   = min(part * MAX_PART, duration)
            part_dur = self.format_time(end - start)

            # Generate thumbnail
            print(f"🖼️ Thumbnail...")
            thumb = self.thumb_gen.generate(
                title    = ai_title,
                part_num = part if num_parts > 1 else None,
                duration = part_dur,
            )

            if not thumb:
                print("   ⚠️ Using fallback thumbnail")
                thumb = self._create_fallback_thumb(
                    ai_title, part
                )

            # Create video
            print(f"🎥 Creating video...")
            video = self.creator.create(
                mod_audio, thumb,
                f"{vid_id}_p{part}",
                start, end,
            )

            if not video:
                print(f"❌ Failed Part {part}")
                continue

            # Build titles
            if num_parts > 1:
                p_title = (
                    f"{ai_title} | Part {part}/{num_parts}"
                )
            else:
                p_title = ai_title

            p_desc = (
                f"{ai_desc}\n\n"
                f"⏱️ Duration: {part_dur}\n"
                f"🎵 Perfect for:\n"
                f"✅ Deep Sleep\n"
                f"✅ Relaxation\n"
                f"✅ Study & Focus\n"
                f"✅ Meditation\n"
                f"✅ Stress Relief\n\n"
                f"👍 Like & Subscribe!\n"
                f"🔔 Turn on notifications!\n\n"
                f"#sleep #relaxing #meditation"
            )

            # Upload
            print(f"\n📤 Uploading...")
            result = self.uploader.upload_video({
                "video_id"      : f"{vid_id}_p{part}",
                "video_file"    : video,
                "thumbnail_file": thumb,
                "title"         : p_title,
                "description"   : p_desc,
                "blocked_countries": [],
                "allowed_countries": [],
            })

            if result and result.get("success"):
                print(f"✅ {result['url']}")
                success += 1
            else:
                print(f"❌ Upload failed")

            # Cleanup video file
            if os.path.exists(video):
                os.remove(video)

            # Wait between parts
            if part < num_parts:
                wait = random.randint(30, 60)
                print(f"⏳ Wait {wait}s...")
                time.sleep(wait)

        # Cleanup
        for f in [audio, mod_audio]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

        if success > 0:
            self.db.mark_video_uploaded(vid_id)
            print(
                f"\n✅ Done! "
                f"{success}/{num_parts} uploaded"
            )
            return True

        print(f"\n❌ All parts failed")
        return False

    def _create_fallback_thumb(self, title, part):
        """Create a simple colored thumbnail"""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            return None

        img  = Image.new("RGB", (1280, 720), (20, 20, 60))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/"
                "DejaVuSans-Bold.ttf", 40
            )
        except Exception:
            font = ImageFont.load_default()

        text = f"{title[:40]} Part {part}"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw   = bbox[2] - bbox[0]
        draw.text(
            ((1280 - tw) // 2, 300),
            text,
            fill="white",
            font=font,
        )

        output = os.path.join(
            self.thumb_dir
            if hasattr(self, "thumb_dir")
            else "thumbnails",
            "fallback.jpg"
        )
        os.makedirs(
            os.path.dirname(output), exist_ok=True
        )
        img.save(output, quality=90)
        return output


# ─────────────────────────────────────────────────────────
# Main Entry
# ─────────────────────────────────────────────────────────
def main():
    tool    = YouTubeAutomation()
    command = sys.argv[1] if len(sys.argv) > 1 else "run"

    if command == "run":
        vid_id  = os.environ.get("VIDEO_ID", "")
        vid_url = os.environ.get("VIDEO_URL", "")
        vid_title = os.environ.get(
            "VIDEO_TITLE", "Relaxing Video"
        )

        if not vid_id or not vid_url:
            print("❌ VIDEO_ID and VIDEO_URL required!")
            sys.exit(1)

        print(f"\n🎯 New Video:")
        print(f"   Title: {vid_title}")
        print(f"   ID   : {vid_id}")

        if tool.setup():
            tool.process_video({
                "video_id": vid_id,
                "url"     : vid_url,
                "title"   : vid_title,
            })

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
                print("❌ No channels!")
                return
            print(f"📺 Watching {len(channels)} channels")

    elif command == "test":
        if len(sys.argv) < 3:
            print("Usage: python main.py test VIDEO_URL")
            return
        if tool.setup():
            vid_url = sys.argv[2]
            vid_id  = vid_url.split("v=")[-1][:11]
            tool.process_video({
                "video_id": vid_id,
                "url"     : vid_url,
                "title"   : "Test Video",
            })

    elif command == "auth":
        try:
            from src.auth import YouTubeAuth
            auth = YouTubeAuth()
            auth.authenticate()
            print(f"✅ Target: {auth.get_target_channel_id()}")
        except Exception as e:
            print(f"❌ Auth error: {e}")

    else:
        print("Commands:")
        print("  python main.py run    - GitHub Actions mode")
        print("  python main.py watch  - Watch channels")
        print("  python main.py test URL - Test single video")
        print("  python main.py auth   - Authenticate")


if __name__ == "__main__":
    main()
