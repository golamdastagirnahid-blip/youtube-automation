"""
Video Downloader
Multiple download methods with automatic fallback
"""

import os
import time
import random
import subprocess
import requests
import yt_dlp
from src.config   import DOWNLOADS_DIR, VIDEO_QUALITY
from src.database import Database
from src.proxy_manager import ProxyManager


class VideoDownloader:

    def __init__(self):
        self.db            = Database()
        self.proxy_manager = ProxyManager()

    def download_video(self, video_url, video_id):
        print(f"📥 Downloading: {video_id}")

        # Try multiple methods
        methods = [
            self._method_1_direct,
            self._method_2_geo_bypass,
            self._method_3_with_proxy,
            self._method_4_invidious,
        ]

        for i, method in enumerate(methods, 1):
            print(f"   🔄 Trying method {i}/{len(methods)}...")
            result = method(video_url, video_id)
            if result:
                print(f"   ✅ Method {i} succeeded!")
                return result
            print(f"   ❌ Method {i} failed, trying next...")
            time.sleep(2)

        print("❌ All download methods failed")
        return None

    # ── Method 1: Direct Download ─────────
    def _method_1_direct(self, video_url, video_id):
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")
        ydl_opts = {
            'format'       : VIDEO_QUALITY,
            'outtmpl'      : output_path,
            'writethumbnail': True,
            'quiet'        : True,
            'no_warnings'  : True,
            'postprocessors': [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }
        return self._run_download(ydl_opts, video_url, video_id)

    # ── Method 2: Geo Bypass ──────────────
    def _method_2_geo_bypass(self, video_url, video_id):
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")
        ydl_opts = {
            'format'            : VIDEO_QUALITY,
            'outtmpl'           : output_path,
            'writethumbnail'    : True,
            'quiet'             : True,
            'no_warnings'       : True,
            'geo_bypass'        : True,
            'geo_bypass_country': 'US',
            'postprocessors'    : [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }
        return self._run_download(ydl_opts, video_url, video_id)

    # ── Method 3: With Proxy ──────────────
    def _method_3_with_proxy(self, video_url, video_id):
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        # Get working proxy
        proxy = self.proxy_manager.get_working_proxy()
        if not proxy:
            return None

        print(f"   🔀 Using proxy: {proxy}")

        ydl_opts = {
            'format'            : VIDEO_QUALITY,
            'outtmpl'           : output_path,
            'writethumbnail'    : True,
            'quiet'             : True,
            'no_warnings'       : True,
            'geo_bypass'        : True,
            'geo_bypass_country': 'US',
            'proxy'             : proxy,
            'postprocessors'    : [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }
        return self._run_download(ydl_opts, video_url, video_id)

    # ── Method 4: Via Invidious ───────────
    def _method_4_invidious(self, video_url, video_id):
        """
        Use Invidious (YouTube alternative frontend)
        to bypass geo restrictions
        """
        # List of public Invidious instances
        invidious_instances = [
            "https://invidious.snopyta.org",
            "https://invidious.kavin.rocks",
            "https://vid.puffyan.us",
            "https://invidious.namazso.eu",
            "https://invidious.flokinet.to",
            "https://yt.artemislena.eu",
            "https://invidious.nerdvpn.de",
        ]

        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        for instance in invidious_instances:
            invidious_url = f"{instance}/watch?v={video_id}"
            print(f"   🔄 Trying Invidious: {instance}")

            ydl_opts = {
                'format'      : 'best[height<=720]',
                'outtmpl'     : output_path,
                'quiet'       : True,
                'no_warnings' : True,
                'postprocessors': [{
                    'key'           : 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }],
            }

            result = self._run_download(ydl_opts, invidious_url, video_id)
            if result:
                # Also try to get thumbnail directly
                if not result.get('thumbnail_file'):
                    result['thumbnail_file'] = self._download_thumbnail(video_id)
                return result

            time.sleep(1)

        return None

    # ── Core Download Runner ──────────────
    def _run_download(self, ydl_opts, video_url, video_id):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

            # Find video file
            video_file = None
            for ext in ['mp4', 'mkv', 'webm', 'avi']:
                path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(path):
                    video_file = path
                    break

            if not video_file:
                # Search directory
                for f in os.listdir(DOWNLOADS_DIR):
                    if video_id in f and not f.endswith(
                        ('.jpg', '.png', '.webp')
                    ):
                        video_file = os.path.join(DOWNLOADS_DIR, f)
                        break

            if not video_file:
                return None

            # Get blocked countries
            blocked = self._get_blocked_countries(info)

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
                "blocked_countries": blocked,
            }

        except Exception as e:
            return None

    # ── Get Blocked Countries ─────────────
    def _get_blocked_countries(self, info):
        region = info.get('region_restriction', {})
        if region:
            return region.get('blocked', [])
        return []

    # ── Download Thumbnail ────────────────
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
                    with open(path, "wb") as f:
                        f.write(r.content)
                    return path
            except Exception:
                continue
        return None