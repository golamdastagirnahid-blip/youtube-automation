import os
import random
import requests
import yt_dlp

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

class VideoDownloader:
    def __init__(self):
        self.proxies = []

    def _load_proxies(self):
        sources = [
            "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/BD/data.txt",
            "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/IN/data.txt",
        ]
        all_proxies = []
        for url in sources:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    lines = [l.strip() for l in r.text.splitlines() if l.strip() and not l.startswith('#')]
                    all_proxies.extend(lines)
            except: continue
        random.shuffle(all_proxies)
        self.proxies = all_proxies
        print(f"   📦 Loaded {len(all_proxies)} BD/IN proxies")

    def _get_working_proxy(self):
        if not self.proxies: self._load_proxies()
        for p in self.proxies[:15]:
            proxy = f"http://{p}" if not p.startswith('http') else p
            try:
                r = requests.get("https://www.youtube.com", proxies={"http": proxy, "https": proxy}, timeout=5)
                if r.status_code in (200, 403):
                    print(f"   ✅ Proxy found: {proxy}")
                    return proxy
            except: continue
        return None

    def download_audio(self, video_url, video_id):
        print(f"   🎵 Downloading audio: {video_id}")
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")
        proxy = self._get_working_proxy()
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': output_path,
            'quiet': True,
            'proxy': proxy,
            'extractor_args': {'youtube': {'player_client': ['android']}},
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)
            
            for ext in ['m4a', 'mp3', 'webm']:
                path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(path): return path
        except Exception as e:
            print(f"   ⚠️ Download error: {e}")
        return None
