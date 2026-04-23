"""
Video Downloader
Multiple download methods with automatic fallback
Uses fresh BD/IN proxies from proxifly repo
"""

import os
import time
import random
import requests
import yt_dlp
from src.config        import DOWNLOADS_DIR, VIDEO_QUALITY
from src.database      import Database
from src.proxy_manager import ProxyManager


class VideoDownloader:

    def __init__(self):
        self.db            = Database()
        self.proxy_manager = ProxyManager()
        self.bd_in_proxies = []

    # ─────────────────────────────────────────────────────
    # Load Fresh BD/IN Proxies at Start
    # ─────────────────────────────────────────────────────
    def load_proxies(self):
        """Load fresh proxies from Bangladesh and India"""
        sources = {
            "BD": "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/BD/data.txt",
            "IN": "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/IN/data.txt",
        }

        all_proxies = []
        print("🔄 Loading fresh BD/IN proxies...")

        for country, url in sources.items():
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    lines = [
                        line.strip()
                        for line in r.text.splitlines()
                        if line.strip() and not line.startswith('#')
                    ]
                    for line in lines:
                        # Handle both formats:
                        # socks5://1.2.3.4:1080
                        # 1.2.3.4:1080
                        if line.startswith("http") or line.startswith("socks"):
                            all_proxies.append(line)
                        else:
                            all_proxies.append(f"http://{line}")

                    print(f"   ✅ {country}: {len(lines)} proxies loaded")
                else:
                    print(f"   ⚠️ {country}: Failed to fetch (status {r.status_code})")
            except Exception as e:
                print(f"   ⚠️ {country}: Error - {e}")

        random.shuffle(all_proxies)
        self.bd_in_proxies = all_proxies
        print(f"   📦 Total proxies ready: {len(all_proxies)}")
        return all_proxies

    # ─────────────────────────────────────────────────────
    # Test a Single Proxy
    # ─────────────────────────────────────────────────────
    def test_proxy(self, proxy, timeout=8):
        """Test if proxy can reach YouTube"""
        try:
            proxies = {"http": proxy, "https": proxy}
            r = requests.get(
                "https://www.youtube.com",
                proxies=proxies,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            return r.status_code in (200, 403)
        except Exception:
            return False

    # ─────────────────────────────────────────────────────
    # Get Best Working Proxy
    # ─────────────────────────────────────────────────────
    def get_best_proxy(self):
        """Find a working proxy from BD/IN list"""

        # Load proxies if empty
        if not self.bd_in_proxies:
            self.load_proxies()

        if not self.bd_in_proxies:
            print("   ❌ No proxies available")
            return None

        print(f"   🔍 Testing proxies (pool size: {len(self.bd_in_proxies)})...")

        # Test up to 20 proxies
        tested   = 0
        max_test = min(20, len(self.bd_in_proxies))

        for proxy in list(self.bd_in_proxies):
            if tested >= max_test:
                break
            tested += 1

            print(f"   🔍 Testing [{tested}/{max_test}]: {proxy}")
            if self.test_proxy(proxy):
                print(f"   ✅ Working proxy: {proxy}")
                return proxy
            else:
                # Remove dead proxy
                if proxy in self.bd_in_proxies:
                    self.bd_in_proxies.remove(proxy)

        # Reload and try again if all failed
        print("   🔄 All tested proxies failed — reloading...")
        self.load_proxies()

        if self.bd_in_proxies:
            proxy = random.choice(self.bd_in_proxies)
            print(f"   🎲 Using random proxy: {proxy}")
            return proxy

        return None

    # ─────────────────────────────────────────────────────
    # Main Download Function
    # ─────────────────────────────────────────────────────
    def download_video(self, video_url, video_id):
        print(f"📥 Downloading: {video_id}")

        # Load fresh proxies at start
        self.load_proxies()

        methods = [
            self._method_1_proxy_ios,
            self._method_2_proxy_android,
            self._method_3_proxy_rotate,
            self._method_4_ios_no_proxy,
            self._method_5_android_no_proxy,
            self._method_6_all_clients,
        ]

        for i, method in enumerate(methods, 1):
            print(f"\n   🔄 Trying method {i}/{len(methods)}...")
            try:
                result = method(video_url, video_id)
                if result:
                    print(f"   ✅ Method {i} succeeded!")
                    return result
            except Exception as e:
                print(f"   ⚠️ Method {i} error: {e}")

            print(f"   ❌ Method {i} failed, trying next...")
            time.sleep(3)

        print("\n❌ All download methods failed")
        return None

    # ─────────────────────────────────────────────────────
    # Method 1: Best Proxy + iOS Client
    # ─────────────────────────────────────────────────────
    def _method_1_proxy_ios(self, video_url, video_id):
        proxy = self.get_best_proxy()
        if not proxy:
            return None

        print(f"   🔀 Proxy: {proxy} | Client: iOS")
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        ydl_opts = {
            'format'         : VIDEO_QUALITY,
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : True,
            'no_warnings'    : True,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'proxy'          : proxy,
            'socket_timeout' : 30,
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

    # ─────────────────────────────────────────────────────
    # Method 2: Best Proxy + Android Client
    # ─────────────────────────────────────────────────────
    def _method_2_proxy_android(self, video_url, video_id):
        proxy = self.get_best_proxy()
        if not proxy:
            return None

        print(f"   🔀 Proxy: {proxy} | Client: Android")
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        ydl_opts = {
            'format'         : VIDEO_QUALITY,
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : True,
            'no_warnings'    : True,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'proxy'          : proxy,
            'socket_timeout' : 30,
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

    # ─────────────────────────────────────────────────────
    # Method 3: Rotate Multiple Proxies + iOS
    # ─────────────────────────────────────────────────────
    def _method_3_proxy_rotate(self, video_url, video_id):
        """Try multiple different proxies one by one"""
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        # Get up to 5 different proxies to try
        proxies_to_try = []
        pool = list(self.bd_in_proxies)
        random.shuffle(pool)

        for proxy in pool[:5]:
            proxies_to_try.append(proxy)

        if not proxies_to_try:
            return None

        for proxy in proxies_to_try:
            print(f"   🔀 Rotating proxy: {proxy}")

            ydl_opts = {
                'format'         : VIDEO_QUALITY,
                'outtmpl'        : output_path,
                'writethumbnail' : True,
                'quiet'          : True,
                'no_warnings'    : True,
                'cookiefile'     : 'cookies.txt',
                'geo_bypass'     : True,
                'proxy'          : proxy,
                'socket_timeout' : 20,
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

            result = self._run_download(ydl_opts, video_url, video_id)
            if result:
                return result

            time.sleep(2)

        return None

    # ─────────────────────────────────────────────────────
    # Method 4: iOS Client Without Proxy
    # ─────────────────────────────────────────────────────
    def _method_4_ios_no_proxy(self, video_url, video_id):
        print(f"   📱 Client: iOS (no proxy)")
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        ydl_opts = {
            'format'         : VIDEO_QUALITY,
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : True,
            'no_warnings'    : True,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'socket_timeout' : 30,
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

    # ─────────────────────────────────────────────────────
    # Method 5: Android Client Without Proxy
    # ─────────────────────────────────────────────────────
    def _method_5_android_no_proxy(self, video_url, video_id):
        print(f"   🤖 Client: Android (no proxy)")
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        ydl_opts = {
            'format'         : VIDEO_QUALITY,
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : True,
            'no_warnings'    : True,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'socket_timeout' : 30,
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

    # ─────────────────────────────────────────────────────
    # Method 6: All Clients Combined (Last Resort)
    # ─────────────────────────────────────────────────────
    def _method_6_all_clients(self, video_url, video_id):
        print(f"   🔥 All clients combined (last resort)")
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

        # Try with a random proxy from pool
        proxy = None
        if self.bd_in_proxies:
            proxy = random.choice(self.bd_in_proxies)
            print(f"   🔀 Random proxy: {proxy}")

        ydl_opts = {
            'format'         : 'best[height<=720]/best',
            'outtmpl'        : output_path,
            'writethumbnail' : True,
            'quiet'          : False,
            'no_warnings'    : False,
            'cookiefile'     : 'cookies.txt',
            'geo_bypass'     : True,
            'socket_timeout' : 60,
            'retries'        : 5,
            'extractor_args' : {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                }
            },
            'postprocessors' : [{
                'key'           : 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        # Add proxy if available
        if proxy:
            ydl_opts['proxy'] = proxy

        return self._run_download(ydl_opts, video_url, video_id)

    # ─────────────────────────────────────────────────────
    # Core Download Runner
    # ─────────────────────────────────────────────────────
    def _run_download(self, ydl_opts, video_url, video_id):
        try:
            os.makedirs(DOWNLOADS_DIR, exist_ok=True)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

            if not info:
                return None

            # ── Find Video File ───────────────────────────
            video_file = None

            # Check common extensions
            for ext in ['mp4', 'mkv', 'webm', 'avi', 'mov']:
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
                print("   ⚠️ Video file not found after download")
                return None

            print(f"   📁 Video file: {video_file}")

            # ── Find Thumbnail ────────────────────────────
            thumb = None
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(path):
                    thumb = path
                    break

            # Download thumbnail if not found
            if not thumb:
                thumb = self._download_thumbnail(video_id)

            return {
                "video_id"         : video_id,
                "video_file"       : video_file,
                "thumbnail_file"   : thumb,
                "title"            : info.get('title',       'Unknown'),
                "description"      : info.get('description', ''),
                "channel"          : info.get('channel',     'Unknown'),
                "blocked_countries": self._get_blocked_countries(info),
            }

        except Exception as e:
            print(f"   ⚠️ Download error: {e}")
            return None

    # ─────────────────────────────────────────────────────
    # Get Blocked Countries from Video Info
    # ─────────────────────────────────────────────────────
    def _get_blocked_countries(self, info):
        try:
            region = info.get('region_restriction', {})
            if region:
                return region.get('blocked', [])
        except Exception:
            pass
        return []

    # ─────────────────────────────────────────────────────
    # Download Thumbnail Manually
    # ─────────────────────────────────────────────────────
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
                    print(f"   🖼️ Thumbnail downloaded: {path}")
                    return path
            except Exception:
                continue
        return None
