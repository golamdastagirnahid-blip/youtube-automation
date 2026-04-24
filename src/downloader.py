"""
Video Downloader - Audio Only
Uses proxies from ALL countries via proxifly
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

# All available country codes from proxifly
PROXY_COUNTRIES = [
    "BD", "IN", "SG", "US", "GB", "DE", "FR",
    "NL", "CA", "AU", "JP", "KR", "BR", "AR",
    "MX", "TR", "ID", "PH", "VN", "TH", "PK",
    "NG", "KE", "ZA", "EG", "RU", "UA", "PL",
    "CZ", "HU", "RO", "BG", "HR", "RS", "SK",
    "AT", "CH", "SE", "NO", "DK", "FI", "PT",
    "ES", "IT", "GR", "IL", "AE", "SA", "IR",
    "HK", "TW", "MY", "MM", "KH", "LK", "NP",
]


class VideoDownloader:

    def __init__(self):
        self.proxies = []

    def _load_proxies(self):
        """Load proxies from ALL countries"""
        print(f"   🌍 Loading proxies from all countries...")

        # First try the main proxy list
        all_proxies = []

        # Try main proxifly list
        try:
            r = requests.get(
                "https://raw.githubusercontent.com/proxifly/"
                "free-proxy-list/main/proxies/all/data.txt",
                timeout=15
            )
            if r.status_code == 200:
                lines = [
                    l.strip()
                    for l in r.text.splitlines()
                    if l.strip() and
                    not l.startswith('#')
                ]
                all_proxies.extend(lines)
                print(
                    f"   ✅ Main list: "
                    f"{len(lines)} proxies"
                )
        except Exception as e:
            print(f"   ⚠️ Main list failed: {e}")

        # Also load from specific countries
        priority_countries = [
            "BD", "IN", "SG", "ID",
            "PH", "VN", "TH", "MY"
        ]
        for country in priority_countries:
            try:
                url = (
                    f"https://raw.githubusercontent.com/"
                    f"proxifly/free-proxy-list/main/"
                    f"proxies/countries/{country}/data.txt"
                )
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    lines = [
                        l.strip()
                        for l in r.text.splitlines()
                        if l.strip() and
                        not l.startswith('#')
                    ]
                    all_proxies.extend(lines)
            except Exception:
                continue

        random.shuffle(all_proxies)
        self.proxies = all_proxies
        print(
            f"   📦 Total proxies loaded: "
            f"{len(all_proxies)}"
        )
        return all_proxies

    def _format_proxy(self, proxy):
        """Format proxy URL"""
        if not proxy:
            return None
        if proxy.startswith('http') or \
           proxy.startswith('socks'):
            return proxy
        return f"http://{proxy}"

    def download_audio(self, video_url, video_id):
        """Download audio using rotating proxies"""
        print(f"   🎵 Downloading: {video_id}")

        if not self.proxies:
            self._load_proxies()

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        # Try up to 20 different proxies
        proxies_to_try = self.proxies[:20]

        for i, raw_proxy in enumerate(proxies_to_try, 1):
            proxy = self._format_proxy(raw_proxy)
            print(
                f"   🔄 [{i}/{len(proxies_to_try)}] "
                f"{proxy}"
            )

            for client in ['android', 'ios']:
                ydl_opts = {
                    'format'         : (
                        'bestaudio[ext=m4a]/bestaudio'
                    ),
                    'outtmpl'        : output_path,
                    'quiet'          : True,
                    'no_warnings'    : True,
                    'proxy'          : proxy,
                    'socket_timeout' : 30,
                    'extractor_args' : {
                        'youtube': {
                            'player_client': [client],
                        }
                    },
                    'postprocessors' : [{
                        'key'            : 'FFmpegExtractAudio',
                        'preferredcodec' : 'm4a',
                    }],
                }

                result = self._try_download(
                    ydl_opts, video_url, video_id
                )
                if result:
                    return result

        print(f"   ❌ All proxies failed")
        return None

    def _try_download(self, ydl_opts, video_url, video_id):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(
                    video_url,
                    download=True
                )

            for ext in ['m4a', 'mp3', 'opus', 'webm', 'aac']:
                path = os.path.join(
                    DOWNLOADS_DIR,
                    f"{video_id}.{ext}"
                )
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    print(
                        f"   ✅ Downloaded: "
                        f"{size // 1024 // 1024} MB"
                    )
                    return path

            for f in os.listdir(DOWNLOADS_DIR):
                if video_id in f and not f.endswith(
                    ('.jpg', '.png', '.webp', '.jpeg')
                ):
                    return os.path.join(DOWNLOADS_DIR, f)

        except Exception as e:
            err = str(e)
            if 'Sign in' in err or 'bot' in err.lower():
                print(f"   ⚠️ Bot detected")
            elif 'timeout' in err.lower():
                print(f"   ⚠️ Timeout")
            else:
                print(f"   ⚠️ {err[:80]}")

        return None
