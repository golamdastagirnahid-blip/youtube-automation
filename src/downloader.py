"""
Video Downloader
Downloads audio only from source videos
No proxy needed - worldwide copyright free content
"""

import os
import requests
import yt_dlp


DOWNLOADS_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "downloads"
)
COOKIES_FILE  = "cookies.txt"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)


class VideoDownloader:

    # ─────────────────────────────────────────────
    # Download Audio Only
    # ─────────────────────────────────────────────
    def download_audio(self, video_url, video_id):
        """
        Download audio only from video
        Returns path to audio file
        """
        print(f"   🎵 Downloading audio: {video_id}")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        ydl_opts = {
            # ── Audio only format ─────────────────
            'format'         : 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl'        : output_path,

            # ── Authentication ────────────────────
            'cookiefile'     : COOKIES_FILE,

            # ── Settings ──────────────────────────
            'quiet'          : False,
            'no_warnings'    : False,

            # ── Post processing ───────────────────
            'postprocessors' : [{
                'key'            : 'FFmpegExtractAudio',
                'preferredcodec' : 'm4a',
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    video_url,
                    download=True
                )

            # Find downloaded audio file
            audio_file = None

            for ext in ['m4a', 'mp3', 'opus', 'webm', 'aac']:
                path = os.path.join(
                    DOWNLOADS_DIR,
                    f"{video_id}.{ext}"
                )
                if os.path.exists(path):
                    audio_file = path
                    break

            # Search by video_id in filename
            if not audio_file:
                for f in os.listdir(DOWNLOADS_DIR):
                    if video_id in f:
                        audio_file = os.path.join(
                            DOWNLOADS_DIR, f
                        )
                        break

            if audio_file:
                size = os.path.getsize(audio_file)
                print(
                    f"   ✅ Audio: {audio_file} "
                    f"({size // 1024 // 1024} MB)"
                )
                return audio_file
            else:
                print(f"   ❌ Audio file not found")
                return None

        except Exception as e:
            print(f"   ❌ Download error: {e}")
            return None

    # ─────────────────────────────────────────────
    # Download Thumbnail
    # ─────────────────────────────────────────────
    def download_thumbnail(self, video_id):
        """Download thumbnail from YouTube"""
        urls = [
            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
        ]

        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200 and \
                   len(r.content) > 1000:
                    path = os.path.join(
                        DOWNLOADS_DIR,
                        f"{video_id}_thumb.jpg"
                    )
                    with open(path, "wb") as f:
                        f.write(r.content)
                    return path
            except Exception:
                continue

        return None

    # ─────────────────────────────────────────────
    # Download Video (kept for compatibility)
    # ─────────────────────────────────────────────
    def download_video(self, video_url, video_id):
        """
        Download full video
        Only used if audio-only mode fails
        """
        print(f"📥 Downloading video: {video_id}")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        ydl_opts = {
            'format'     : (
                'bestvideo[height<=1080][ext=mp4]'
                '+bestaudio[ext=m4a]'
                '/best[height<=1080]'
                '/best'
            ),
            'outtmpl'    : output_path,
            'cookiefile' : COOKIES_FILE,
            'quiet'      : False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    video_url,
                    download=True
                )

            # Find video file
            video_file = None
            for ext in ['mp4', 'mkv', 'webm']:
                path = os.path.join(
                    DOWNLOADS_DIR,
                    f"{video_id}.{ext}"
                )
                if os.path.exists(path):
                    video_file = path
                    break

            if video_file:
                return {
                    "video_id"      : video_id,
                    "video_file"    : video_file,
                    "title"         : info.get('title'),
                    "description"   : info.get('description'),
                    "thumbnail_file": self.download_thumbnail(
                        video_id
                    )
                }
            return None

        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
