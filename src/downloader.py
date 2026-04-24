"""
Video Downloader - Audio Only
Uses BD/IN proxies from proxifly repo
Same proxy system that worked for Gopal Bhar
"""

import os
import random
import requests
import yt_dlp


DOWNLOADS_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "downloads"
)

os.makedirs(DOWNLOADS_DIR, exist_ok=True)


class VideoDownloader:

    def __init__(self):
        self.proxies = []

    # ─────────────────────────────────────────────
    # Load BD/IN Proxies
    # ─────────────────────────────────────────────
    def _load_proxies(self):
        sources = [
            "https://raw.githubusercontent.com/proxifly/"
            "free-proxy-list/main/proxies/countries/BD/data.txt",
            "https://raw.githubusercontent.com/proxifly/"
            "free-proxy-list/main/proxies/countries/IN/data.txt",
        ]

        all_proxies = []
        for url in sources:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    lines = [
                        l.strip()
                        for l in r.text.splitlines()
                        if l.strip() and
                        not l.startswith('#')
                    ]
                    all_proxies.extend(lines)
                    print(
                        f"   📦 Loaded {len(lines)} "
                        f"proxies from {url.split('/')[-2]}"
                    )
            except Exception as e:
                print(f"   ⚠️ Proxy load error: {e}")

        random.shuffle(all_proxies)
        self.proxies = all_proxies
        print(f"   📦 Total proxies: {len(all_proxies)}")

    # ─────────────────────────────────────────────
    # Get Working Proxy
    # ─────────────────────────────────────────────
    def _get_working_proxy(self):
        if not self.proxies:
            self._load_proxies()

        print(f"   🔍 Testing proxies...")

        for p in self.proxies[:20]:
            proxy = f"http://{p}" if not p.startswith('http') \
                    else p
            try:
                r = requests.get(
                    "https://www.youtube.com",
                    proxies={
                        "http" : proxy,
                        "https": proxy
                    },
                    timeout  = 5,
                    headers  = {"User-Agent": "Mozilla/5.0"}
                )
                if r.status_code in (200, 403):
                    print(f"   ✅ Working proxy: {proxy}")
                    return proxy
            except Exception:
                continue

        # Use random if none tested
        if self.proxies:
            p = random.choice(self.proxies)
            proxy = f"http://{p}" if not p.startswith('http') \
                    else p
            print(f"   🎲 Random proxy: {proxy}")
            return proxy

        return None

    # ─────────────────────────────────────────────
    # Download Audio
    # ─────────────────────────────────────────────
    def download_audio(self, video_url, video_id):
        print(f"   🎵 Downloading audio: {video_id}")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        proxy = self._get_working_proxy()

        # Method 1: Android + Proxy
        print(f"   🔄 Method 1: Android client + proxy")
        ydl_opts = {
            'format'         : 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl'        : output_path,
            'quiet'          : True,
            'no_warnings'    : True,
            'extractor_args' : {
                'youtube': {
                    'player_client': ['android'],
                }
            },
            'postprocessors' : [{
                'key'            : 'FFmpegExtractAudio',
                'preferredcodec' : 'm4a',
            }],
        }

        if proxy:
            ydl_opts['proxy'] = proxy

        result = self._try_download(
            ydl_opts, video_url, video_id
        )
        if result:
            return result

        # Method 2: iOS + Proxy
        print(f"   🔄 Method 2: iOS client + proxy")
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['ios'],
            }
        }
        result = self._try_download(
            ydl_opts, video_url, video_id
        )
        if result:
            return result

        # Method 3: New proxy + Android
        print(f"   🔄 Method 3: Fresh proxy + Android")
        new_proxy = self._get_working_proxy()
        if new_proxy:
            ydl_opts['proxy'] = new_proxy
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android'],
            }
        }
        result = self._try_download(
            ydl_opts, video_url, video_id
        )
        if result:
            return result

        print(f"   ❌ All methods failed")
        return None

    # ─────────────────────────────────────────────
    # Try Download
    # ─────────────────────────────────────────────
    def _try_download(self, ydl_opts, video_url, video_id):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(
                    video_url,
                    download=True
                )

            # Find audio file
            for ext in ['m4a', 'mp3', 'opus', 'webm', 'aac']:
                path = os.path.join(
                    DOWNLOADS_DIR,
                    f"{video_id}.{ext}"
                )
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    print(
                        f"   ✅ Audio: "
                        f"{size // 1024 // 1024} MB"
                    )
                    return path

            # Search by video_id
            for f in os.listdir(DOWNLOADS_DIR):
                if video_id in f and not f.endswith(
                    ('.jpg', '.png', '.webp')
                ):
                    return os.path.join(DOWNLOADS_DIR, f)

        except Exception as e:
            print(f"   ⚠️ Error: {e}")

        return None
