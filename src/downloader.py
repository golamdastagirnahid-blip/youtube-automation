"""
Video Downloader - Audio Only
Handles 12-24 hour videos (multi-GB files)
Uses android_vr fallback (no PO token needed)
Falls back to raw download if FFmpeg is unavailable
"""

import os
import sys
import shutil
import yt_dlp

DOWNLOADS_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "downloads"
)

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

COOKIES_FILE = "cookies.txt"

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def _cookies_valid():
    if not os.path.exists(COOKIES_FILE):
        return False
    try:
        with open(COOKIES_FILE, 'r') as f:
            first_lines = f.read(500)
        return '# Netscape HTTP Cookie File' in first_lines or '\t' in first_lines
    except Exception:
        return False


COOKIES_OK = _cookies_valid()


class ProgressLogger:
    """Logs download progress for large files"""

    def __init__(self):
        self.last_pct = -1

    def hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get(
                'total_bytes_estimate', 0
            )
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            if total > 0:
                pct = int(downloaded * 100 / total)
                if pct >= self.last_pct + 10:
                    self.last_pct = pct
                    dl_mb = downloaded / 1024 / 1024
                    tot_mb = total / 1024 / 1024
                    spd = (
                        f"{speed / 1024 / 1024:.1f} MB/s"
                        if speed else "..."
                    )
                    eta_str = (
                        f"{eta // 60}m {eta % 60}s"
                        if eta else "..."
                    )
                    print(
                        f"   📥 {pct}% — "
                        f"{dl_mb:.0f}/{tot_mb:.0f} MB "
                        f"@ {spd} — ETA {eta_str}"
                    )
                    sys.stdout.flush()

        elif d['status'] == 'finished':
            size = d.get('total_bytes') or d.get(
                'downloaded_bytes', 0
            )
            mb = size / 1024 / 1024
            print(f"   📥 100% — {mb:.0f} MB download complete")
            sys.stdout.flush()


class VideoDownloader:

    def download_audio(self, video_url, video_id):
        print(f"   🎵 Downloading: {video_id}")
        if HAS_FFMPEG:
            print(f"   ✅ FFmpeg found — will convert to m4a")
        else:
            print(f"   ⚠️ FFmpeg not found — will use raw audio")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        methods = [
            ("Auto (android_vr fallback)", None, False, False),
            ("Android + cookies", 'android', True, False),
            ("Android VR", 'android_vr', False, False),
            ("Media Connect", 'mediaconnect', False, False),
            ("Any format + cookies", 'android', True, True),
        ]

        for i, (name, client, cookies, any_fmt) in enumerate(methods, 1):
            print(f"   🔄 Method {i}: {name}...")
            result = self._try_download(
                video_url, video_id,
                output_path, client=client,
                use_cookies=cookies,
                any_format=any_fmt,
            )
            if result:
                return result

        print(f"   ❌ All download methods failed")
        return None

    def _try_download(
        self, video_url, video_id,
        output_path, client=None,
        use_cookies=False, any_format=False
    ):
        try:
            if any_format:
                fmt = 'best'
            else:
                fmt = 'bestaudio[ext=m4a]/bestaudio/best'

            progress = ProgressLogger()

            ydl_opts = {
                'format'           : fmt,
                'outtmpl'          : output_path,
                'quiet'            : True,
                'no_warnings'      : True,
                'noprogress'       : True,
                'progress_hooks'   : [progress.hook],
                'socket_timeout'   : 120,
                'retries'          : 15,
                'fragment_retries' : 15,
                'file_access_retries': 10,
                'extractor_retries': 5,
                'retry_sleep_functions': {
                    'http' : lambda n: 5 * (2 ** min(n, 5)),
                    'fragment': lambda n: 2 * (2 ** min(n, 4)),
                },
                'buffersize'       : 1024 * 1024,
                'http_chunk_size'  : 10 * 1024 * 1024,
                'continuedl'       : True,
                'nopart'           : False,
            }

            if HAS_FFMPEG:
                ydl_opts['postprocessors'] = [{
                    'key'           : 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }]

            if client:
                ydl_opts['extractor_args'] = {
                    'youtube': {
                        'player_client': [client],
                    }
                }

            if use_cookies and COOKIES_OK:
                ydl_opts['cookiefile'] = COOKIES_FILE

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(
                    video_url,
                    download=True
                )

            return self._find_downloaded(video_id)

        except Exception as e:
            err = str(e)
            client_name = client or 'auto'
            if 'No video formats found' in err:
                print(f"   ⚠️ {client_name}: No formats (PO token needed)")
            elif 'HTTP Error 403' in err:
                print(f"   ⚠️ {client_name}: 403 Forbidden (blocked)")
            elif 'HTTP Error 429' in err:
                print(f"   ⚠️ {client_name}: Rate limited")
            elif 'Sign in' in err or 'login' in err.lower():
                print(f"   ⚠️ {client_name}: Login required")
            else:
                print(f"   ⚠️ {client_name}: {err[:200]}")

        return None

    def _find_downloaded(self, video_id):
        for ext in [
            'm4a', 'mp3', 'opus', 'webm',
            'aac', 'ogg', 'mp4'
        ]:
            path = os.path.join(
                DOWNLOADS_DIR,
                f"{video_id}.{ext}"
            )
            if os.path.exists(path):
                size = os.path.getsize(path)
                if size < 1024:
                    print(f"   ⚠️ File too small ({size}B), skipping")
                    os.remove(path)
                    continue
                gb = size / 1024 / 1024 / 1024
                if gb >= 1.0:
                    print(f"   ✅ Downloaded: {gb:.2f} GB")
                else:
                    mb = size / 1024 / 1024
                    print(f"   ✅ Downloaded: {mb:.1f} MB")
                return path

        for f in os.listdir(DOWNLOADS_DIR):
            if video_id in f and not f.endswith(
                ('.jpg', '.png', '.webp', '.jpeg',
                 '.part', '.ytdl')
            ):
                fpath = os.path.join(DOWNLOADS_DIR, f)
                size = os.path.getsize(fpath)
                if size > 1024:
                    gb = size / 1024 / 1024 / 1024
                    if gb >= 1.0:
                        print(f"   ✅ Downloaded: {gb:.2f} GB")
                    else:
                        mb = size / 1024 / 1024
                        print(f"   ✅ Downloaded: {mb:.1f} MB")
                    return fpath

        return None
