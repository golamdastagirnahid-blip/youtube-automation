import os
import yt_dlp
import requests
from src.config import DOWNLOADS_DIR, VIDEO_QUALITY
from src.database import Database

class VideoDownloader:
    def __init__(self):
        self.db = Database()

    def download_video(self, video_url, video_id):
        print(f"📥 Downloading: {video_id}")

        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        ydl_opts = {
            'format': VIDEO_QUALITY,
            'outtmpl': output_path,
            'writethumbnail': True,
            'quiet': False,
            'no_warnings': True,
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

            video_file = None
            for ext in ['mp4', 'mkv', 'webm']:
                path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(path):
                    video_file = path
                    break

            thumb_file = self._download_thumbnail(video_id)

            self.db.mark_video_uploaded(video_id, {"title": info.get('title', 'Unknown')})

            return {
                "video_id": video_id,
                "video_file": video_file,
                "thumbnail_file": thumb_file,
                "title": info.get('title', 'Unknown'),
                "description": info.get('description', ''),
                "channel": info.get('channel', 'Unknown')
            }

        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

    def _download_thumbnail(self, video_id):
        urls = [
            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        ]
        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    path = os.path.join(DOWNLOADS_DIR, f"{video_id}.jpg")
                    with open(path, "wb") as f:
                        f.write(r.content)
                    return path
            except:
                continue
        return None