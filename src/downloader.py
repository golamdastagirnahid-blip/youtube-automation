"""
Video Downloader - Audio Only
Handles 12-24 hour videos (multi-GB files)
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

    def _list_formats(self, video_url):
        """Show what formats yt-dlp can see for each client."""
        clients = [
            (None, True),
            ('android_vr', True),
            ('android', True),
            ('ios', True),
            ('mediaconnect', True),
            (None, False),
        ]

        for client, use_cookies in clients:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'noplaylist': True,
                'socket_timeout': 30,
            }
            if client:
                opts['extractor_args'] = {
                    'youtube': {'player_client': [client]}
                }
            if use_cookies and COOKIES_OK:
                opts['cookiefile'] = COOKIES_FILE

            client_name = client or 'auto'
            cookie_str = '+cookies' if (use_cookies and COOKIES_OK) else ''

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(
                        video_url, download=False
                    )
                    fmts = info.get('formats', [])
                    if fmts:
                        audio_fmts = [
                            f for f in fmts
                            if f.get('acodec', 'none') != 'none'
                        ]
                        print(f"   [{client_name}{cookie_str}] {len(fmts)} formats, {len(audio_fmts)} audio")
                        for f in audio_fmts[:3]:
                            ext = f.get('ext', '?')
                            abr = f.get('abr', '?')
                            fid = f.get('format_id', '?')
                            acodec = f.get('acodec', '?')
                            print(f"     {fid}: {ext} {acodec} {abr}kbps")
                        return client, use_cookies, fmts
                    else:
                        print(f"   [{client_name}{cookie_str}] 0 formats returned")
            except Exception as e:
                err = str(e)[:150]
                print(f"   [{client_name}{cookie_str}] {err}")

        return None, False, []

    def download_audio(self, video_url, video_id):
        print(f"   Downloading: {video_id}")
        if HAS_FFMPEG:
            print(f"   FFmpeg: yes")
        else:
            print(f"   FFmpeg: no (raw audio)")
        if COOKIES_OK:
            print(f"   Cookies: loaded")
        else:
            print(f"   Cookies: none")

        print(f"   Scanning available formats...")
        best_client, best_cookies, fmts = self._list_formats(video_url)

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        if fmts:
            print(f"   Best client: {best_client or 'auto'} (cookies={'yes' if best_cookies else 'no'})")
            result = self._try_download_with_formats(
                video_url, video_id, output_path,
                best_client, best_cookies, fmts
            )
            if result:
                return result

        methods = [
            ("auto+cookies",          None,             True),
            ("android_vr+cookies",    'android_vr',     True),
            ("android+cookies",       'android',        True),
            ("ios+cookies",           'ios',            True),
            ("mediaconnect+cookies",  'mediaconnect',   True),
            ("auto (no cookies)",     None,             False),
            ("android_vr (no cookies)", 'android_vr',   False),
        ]

        for i, (name, client, cookies) in enumerate(methods, 1):
            print(f"   Method {i}/{len(methods)}: {name}...")
            for fmt in ['bestaudio/best', 'best']:
                result = self._try_download(
                    video_url, video_id,
                    output_path, client=client,
                    use_cookies=cookies,
                    fmt=fmt,
                )
                if result:
                    return result

        print(f"\n   === VERBOSE DIAGNOSTIC (last attempt) ===")
        result = self._try_download_verbose(
            video_url, video_id, output_path
        )
        if result:
            return result

        print(f"   ALL download methods failed")
        return None

    def _try_download_with_formats(
        self, video_url, video_id, output_path,
        client, use_cookies, fmts
    ):
        audio_fmts = [
            f for f in fmts
            if f.get('acodec', 'none') != 'none'
               and f.get('vcodec', 'none') == 'none'
        ]
        if not audio_fmts:
            audio_fmts = [
                f for f in fmts
                if f.get('acodec', 'none') != 'none'
            ]

        if audio_fmts:
            best = sorted(
                audio_fmts,
                key=lambda f: f.get('abr', 0) or 0,
                reverse=True
            )[0]
            fmt_id = best.get('format_id')
            print(f"   Trying format ID: {fmt_id}")
            result = self._try_download(
                video_url, video_id, output_path,
                client=client, use_cookies=use_cookies,
                fmt=fmt_id,
            )
            if result:
                return result

        for fmt in ['bestaudio/best', 'best']:
            result = self._try_download(
                video_url, video_id, output_path,
                client=client, use_cookies=use_cookies,
                fmt=fmt,
            )
            if result:
                return result

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
            }

            if HAS_FFMPEG and fmt not in ('best',):
                is_format_id = not any(
                    c in fmt for c in ['/', '[', ']']
                )
                if not is_format_id:
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
                print(f"     {client_name}: No formats found")
            elif 'Requested format is not available' in err:
                print(f"     {client_name}: Format '{fmt}' not available")
            elif 'HTTP Error 403' in err:
                print(f"     {client_name}: 403 Forbidden")
            elif 'HTTP Error 429' in err:
                print(f"     {client_name}: Rate limited")
            elif 'Sign in' in err or 'login' in err.lower() or 'bot' in err.lower():
                print(f"     {client_name}: Login/cookies required")
            elif 'ffmpeg' in err.lower() or 'postprocess' in err.lower():
                print(f"     {client_name}: FFmpeg error: {err[:200]}")
            else:
                print(f"     {client_name}: {err[:300]}")

        return None

    def _try_download_verbose(self, video_url, video_id, output_path):
        """Last resort: verbose yt-dlp output to see exactly what's happening."""
        try:
            ydl_opts = {
                'format'           : 'bestaudio/best',
                'outtmpl'          : output_path,
                'quiet'            : False,
                'verbose'          : True,
                'no_warnings'      : False,
                'socket_timeout'   : 120,
                'retries'          : 5,
                'continuedl'       : True,
            }

            if COOKIES_OK:
                ydl_opts['cookiefile'] = COOKIES_FILE

            ydl_opts['extractor_args'] = {
                'youtube': {'player_client': ['android_vr']}
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)

            return self._find_downloaded(video_id)
        except Exception as e:
            print(f"   VERBOSE error: {str(e)[:500]}")
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
                    print(f"   File too small ({size}B), skipping")
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
