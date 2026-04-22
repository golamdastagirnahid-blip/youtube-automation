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
            'format'          : VIDEO_QUALITY,
            'outtmpl'         : output_path,
            'writethumbnail'  : True,
            'quiet'           : False,
            'no_warnings'     : True,
            'geo_bypass'      : True,
            'geo_bypass_country': 'US',
            'postprocessors'  : [{
                'key'            : 'FFmpegVideoConvertor',
                'preferedformat' : 'mp4'
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

            # ✅ Extract blocked countries from source video
            blocked_countries = self._get_blocked_countries(info)
            if blocked_countries:
                print(f"🌍 Source blocked countries: {blocked_countries}")
            else:
                print(f"🌍 No country restrictions on source video")

            # Find video file
            video_file = None
            for ext in ['mp4', 'mkv', 'webm']:
                path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(path):
                    video_file = path
                    break

            # Find thumbnail
            thumb_file = self._download_thumbnail(video_id)

            if video_file:
                return {
                    "video_id"        : video_id,
                    "video_file"      : video_file,
                    "thumbnail_file"  : thumb_file,
                    "title"           : info.get('title', 'Unknown'),
                    "description"     : info.get('description', ''),
                    "channel"         : info.get('channel', 'Unknown'),
                    "blocked_countries": blocked_countries,  # ✅ Pass to uploader
                }

            print("❌ Video file not found after download")
            return None

        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

    def _get_blocked_countries(self, info):
        """
        Extract blocked countries from video info
        yt-dlp returns availability info in different formats
        """
        blocked = []

        # Method 1: Check availability
        availability = info.get('availability', '')
        if availability == 'needs_auth':
            return []

        # Method 2: Check format availability
        formats = info.get('formats', [])
        for fmt in formats:
            if fmt.get('has_drm'):
                return []

        # Method 3: Direct check from info
        # yt-dlp stores geo restriction info here
        chapters = info.get('chapters', [])

        # Method 4: Check from raw data
        # Look for blocked countries in all available fields
        raw_data = info

        # Check automatic captions or subtitles for region info
        region_restriction = raw_data.get('region_restriction', {})
        if region_restriction:
            blocked = region_restriction.get('blocked', [])
            return blocked

        # Method 5: Check from tags or description for region info
        tags = info.get('tags', [])
        for tag in tags:
            if 'country' in tag.lower():
                pass

        return blocked

    def _download_thumbnail(self, video_id):
        urls = [
            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        ]
        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200 and len(r.content) > 1000:
                    path = os.path.join(DOWNLOADS_DIR, f"{video_id}.jpg")
                    with open(path, "wb") as f:
                        f.write(r.content)
                    return path
            except:
                continue
        return None