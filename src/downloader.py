import os
import yt_dlp
from src.config import DOWNLOADS_DIR, VIDEO_QUALITY

class VideoDownloader:
    def download_video(self, video_url, video_id):
        print(f"📥 Downloading: {video_id} (Direct Link)")
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': True,
            # No proxy needed for these channels
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
            filename = os.path.join(DOWNLOADS_DIR, f"{video_id}.mp4")
            if os.path.exists(filename):
                return {
                    "video_id": video_id,
                    "video_file": filename,
                    "title": info.get('title'),
                    "description": info.get('description'),
                    "thumbnail_file": self._get_thumb(video_id)
                }
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None

    def _get_thumb(self, video_id):
        # Basic thumbnail logic
        return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
