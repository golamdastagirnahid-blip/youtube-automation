"""
Video Downloader
Multiple download methods with automatic fallback
"""

import os
import time
import requests
import yt_dlp
from src.config        import DOWNLOADS_DIR, VIDEO_QUALITY
from src.database      import Database
from src.proxy_manager import ProxyManager


class VideoDownloader:

    def __init__(self):
        self.db            = Database()
        self.proxy_manager = ProxyManager()

    def download_video(self, video_url, video_id):
        print(f"📥 Downloading: {video_id}")

        methods = [
            self._method_1_ios_client,
            self._method_2_android_client,
            self._method_3_tv_client,
            self._method_4_with_proxy,
            self._method_5_cookies_only,
        ]

        for i, method in enumerate(methods, 1):
            print(f"   🔄 Trying method {i}/{len(methods)}...")
            try:
                result = method(video_url, video_id)
                if result:
                    print(f"   ✅ Method {i} succeeded!")
                    return result
            except Exception as e:
                pass
            print(f"   ❌ Method {i} failed, trying next...")
            time.sleep(3)

        print("❌ All download methods failed")
        return None

    # ─────────────────────────────────────────────
    # Method 1: iOS Client (Most Powerful - Bypasses Geo)
    # ─────────────────────────────────────────────
    def _method_1_ios_client(self, video_url, video_id):
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")
        ydl_opts = {
            'format'         : VIDEO_QUALITY,
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : True,
            'no_warnings'    : True,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'extractor_args' : {
                'youtube': {
                    'player_client': ['ios'],
                }
            },
            'http_headers'   : {
                'User-Agent': (
                    'com.google.ios.youtube/19.29.1 '
                    '(iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X)'
                ),
            },
            'postprocessors' : [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        return self._run_download(ydl_opts, video_url, video_id)

    # ─────────────────────────────────────────────
    # Method 2: Android Client
    # ─────────────────────────────────────────────
    def _method_2_android_client(self, video_url, video_id):
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")
        ydl_opts = {
            'format'         : VIDEO_QUALITY,
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : True,
            'no_warnings'    : True,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'extractor_args' : {
                'youtube': {
                    'player_client': ['android'],
                }
            },
            'http_headers'   : {
                'User-Agent': (
                    'com.google.android.youtube/19.30.36'
                    '(Linux; U; Android 11) gzip'
                ),
            },
            'postprocessors' : [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        return self._run_download(ydl_opts, video_url, video_id)

    # ─────────────────────────────────────────────
    # Method 3: TV Client (Different IP Rules)
    # ─────────────────────────────────────────────
    def _method_3_tv_client(self, video_url, video_id):
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")
        ydl_opts = {
            'format'         : 'best[height<=720]/best',
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : True,
            'no_warnings'    : True,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'extractor_args' : {
                'youtube': {
                    'player_client': ['tv_embedded'],
                }
            },
            'postprocessors' : [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        return self._run_download(ydl_opts, video_url, video_id)

    # ─────────────────────────────────────────────
    # Method 4: iOS Client + Working Proxy
    # ─────────────────────────────────────────────
    def _method_4_with_proxy(self, video_url, video_id):
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        proxy = self.proxy_manager.get_working_proxy()
        if not proxy:
            print("   ⚠️ No working proxy found")
            return None

        print(f"   🔀 Using proxy: {proxy}")

        ydl_opts = {
            'format'         : VIDEO_QUALITY,
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : True,
            'no_warnings'    : True,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'proxy'          : proxy,
            'extractor_args' : {
                'youtube': {
                    'player_client': ['ios', 'android'],
                }
            },
            'postprocessors' : [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        return self._run_download(ydl_opts, video_url, video_id)

    # ─────────────────────────────────────────────
    # Method 5: Cookies Only (Last Resort)
    # ─────────────────────────────────────────────
    def _method_5_cookies_only(self, video_url, video_id):
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")
        ydl_opts = {
            'format'         : 'best[height<=480]/best',
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : False,
            'no_warnings'    : False,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'extractor_args' : {
                'youtube': {
                    'player_client': ['ios', 'android', 'tv_embedded'],
                }
            },
            'postprocessors' : [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        return self._run_download(ydl_opts, video_url, video_id)

    # ─────────────────────────────────────────────
    # Core Runner
    # ─────────────────────────────────────────────
    def _run_download(self, ydl_opts, video_url, video_id):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

            if not info:
                return None

            # Find video file
            video_file = None
            for ext in ['mp4', 'mkv', 'webm', 'avi']:
                path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(path):
                    video_file = path
                    break

            # Search by video_id in filename
            if not video_file:
                for f in os.listdir(DOWNLOADS_DIR):
                    if video_id in f and not f.endswith(
                        ('.jpg', '.png', '.webp', '.jpeg')
                    ):
                        video_file = os.path.join(DOWNLOADS_DIR, f)
                        break

            if not video_file:
                return None

            # Find thumbnail
            thumb = None
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(path):
                    thumb = path
                    break

            if not thumb:
                thumb = self._download_thumbnail(video_id)

            return {
                "video_id"         : video_id,
                "video_file"       : video_file,
                "thumbnail_file"   : thumb,
                "title"            : info.get('title', 'Unknown'),
                "description"      : info.get('description', ''),
                "channel"          : info.get('channel', 'Unknown'),
                "blocked_countries": self._get_blocked_countries(info),
            }

        except Exception:
            return None

    # ─────────────────────────────────────────────
    # Get Blocked Countries
    # ─────────────────────────────────────────────
    def _get_blocked_countries(self, info):
        region = info.get('region_restriction', {})
        if region:
            return region.get('blocked', [])
        return []

    # ─────────────────────────────────────────────
    # Download Thumbnail
    # ─────────────────────────────────────────────
    def _download_thumbnail(self, video_id):
        urls = [
            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
        ]
        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200 and len(r.content) > 1000:
                    path = os.path.join(DOWNLOADS_DIR, f"{video_id}.jpg")
                    with open(path, "wb") as fh:
                        fh.write(r.content)
                    return path
            except Exception:
                continue
        return None
