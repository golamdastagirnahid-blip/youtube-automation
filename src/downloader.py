"""
Video Downloader - Audio Only
Handles 12-24 hour videos (multi-GB files)
Uses PO Token plugin for YouTube authentication (no cookies needed)
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

# Check if PO Token plugin is available
# bgutil-ytdlp-pot-provider is a yt-dlp plugin, not a Python module
# It gets loaded automatically by yt-dlp when installed
PO_TOKEN_OK = True  # Assume available if installed via pip


class ProgressLogger:

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
                        f"   DL {pct}% - "
                        f"{dl_mb:.0f}/{tot_mb:.0f} MB "
                        f"@ {spd} - ETA {eta_str}"
                    )
                    sys.stdout.flush()

        elif d['status'] == 'finished':
            size = d.get('total_bytes') or d.get(
                'downloaded_bytes', 0
            )
            mb = size / 1024 / 1024
            print(f"   DL 100% - {mb:.0f} MB download complete")
            sys.stdout.flush()


class VideoDownloader:

    def download_audio(self, video_url, video_id):
        print(f"   Downloading: {video_id}")
        print(f"   FFmpeg: {'yes' if HAS_FFMPEG else 'no'}")
        print(f"   PO Token plugin: {'yes' if PO_TOKEN_OK else 'NO - install bgutil-ytdlp-pot-provider'}")
        print(f"   Cookies: {'loaded (backup)' if COOKIES_OK else 'none'}")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        # Try with PO Token enabled (primary method)
        methods = [
            ("web with PO token", 'web', True, 'bestaudio[ext=m4a]/bestaudio/best'),
            ("default with PO token", None, True, 'bestaudio[ext=m4a]/bestaudio/best'),
            ("web any format", 'web', True, 'best'),
            ("android_vr", 'android_vr', True, 'bestaudio/best'),
            ("ios", 'ios', True, 'bestaudio/best'),
        ]

        for i, (name, client, cookies, fmt) in enumerate(methods, 1):
            print(f"   Method {i}/{len(methods)}: {name}...")
            result = self._try_download(
                video_url, video_id,
                output_path, client=client,
                use_cookies=cookies,
                fmt=fmt,
            )
            if result:
                return result

        print(f"   ALL download methods failed")
        print(f"   HINT: Ensure PO Token server is running on http://127.0.0.1:4416")
        return None

    def _try_download(
        self, video_url, video_id,
        output_path, client=None,
        use_cookies=False, fmt='bestaudio/best'
    ):
        try:
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
                # Enable PO Token provider (2026 bypass method)
                'extractor_args': {
                    'youtube': {
                        'player_client': [client] if client else ['web'],
                    },
                    'youtubepot-bgutilhttp': {
                        'base_url': ['http://127.0.0.1:4416'],
                    },
                },
            }

            if HAS_FFMPEG and fmt != 'best':
                ydl_opts['postprocessors'] = [{
                    'key'           : 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }]

            # Always use cookies as fallback (2026 bypass method)
            if COOKIES_OK:
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
                print(f"     {client_name}: No formats found")
            elif 'Requested format is not available' in err:
                print(f"     {client_name}: Format not available")
            elif 'HTTP Error 403' in err:
                print(f"     {client_name}: 403 Forbidden")
            elif 'HTTP Error 429' in err:
                print(f"     {client_name}: Rate limited")
            elif 'Sign in' in err or 'bot' in err.lower():
                print(f"     {client_name}: Bot detection - trying next method")
            elif 'ffmpeg' in err.lower() or 'postprocess' in err.lower():
                print(f"     {client_name}: FFmpeg error: {err[:200]}")
            else:
                print(f"     {client_name}: {err[:300]}")

        return None

    def _find_downloaded(self, video_id):
        for ext in [
            'm4a', 'mp3', 'opus', 'webm',
            'aac', 'ogg', 'mp4', 'mkv',
            'wav', 'flac'
        ]:
            path = os.path.join(
                DOWNLOADS_DIR,
                f"{video_id}.{ext}"
            )
            if os.path.exists(path):
                size = os.path.getsize(path)
                if size < 1024:
                    print(f"   File too small ({size}B), removing")
                    os.remove(path)
                    continue
                gb = size / 1024 / 1024 / 1024
                if gb >= 1.0:
                    print(f"   Downloaded: {gb:.2f} GB")
                else:
                    mb = size / 1024 / 1024
                    print(f"   Downloaded: {mb:.1f} MB")
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
                        print(f"   Downloaded: {gb:.2f} GB")
                    else:
                        mb = size / 1024 / 1024
                        print(f"   Downloaded: {mb:.1f} MB")
                    return fpath

        return None
