"""
Video Downloader - Audio Only
Uses worldwide proxies from proxifly
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

    def _load_proxies(self):
        """Load proxies from all countries"""
        all_proxies = []

        # Main full list
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
                    f"   ✅ Main: {len(lines)} proxies"
                )
        except Exception as e:
            print(f"   ⚠️ {e}")

        # Priority countries
        for country in [
            "BD", "IN", "SG", "ID",
            "PH", "VN", "TH", "MY"
        ]:
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
        print(f"   📦 Total: {len(all_proxies)} proxies")
        return all_proxies

    def _format_proxy(self, proxy):
        if not proxy:
            return None
        if proxy.startswith('http') or \
           proxy.startswith('socks'):
            return proxy
        return f"http://{proxy}"

    def download_audio(self, video_url, video_id):
        print(f"   🎵 Downloading: {video_id}")

        if not self.proxies:
            self._load_proxies()

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        proxies_to_try = self.proxies[:30]

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
                    'socket_timeout' : 10,
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
            if 'timeout' in err.lower():
                print(f"   ⏰ Timeout")
            elif 'Sign in' in err or 'bot' in err.lower():
                print(f"   🤖 Bot detected")
            elif 'Connection' in err:
                print(f"   🔌 Connection failed")
            else:
                print(f"   ⚠️ {err[:60]}")

        return None
