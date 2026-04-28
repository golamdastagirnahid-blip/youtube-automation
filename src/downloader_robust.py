"""
Robust Video Downloader
Uses multiple fallback methods to download YouTube videos
"""

import os
import sys
import shutil
import subprocess
import requests
import re
import json
import time
from urllib.parse import urlparse, parse_qs

DOWNLOADS_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "downloads"
)

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

HAS_FFMPEG = shutil.which("ffmpeg") is not None


class ProgressLogger:
    def __init__(self):
        self.last_pct = -1

    def hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            if total > 0:
                pct = int(downloaded * 100 / total)
                if pct >= self.last_pct + 10:
                    self.last_pct = pct
                    dl_mb = downloaded / 1024 / 1024
                    tot_mb = total / 1024 / 1024
                    spd = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "..."
                    eta_str = f"{eta // 60}m {eta % 60}s" if eta else "..."
                    print(f"   DL {pct}% - {dl_mb:.0f}/{tot_mb:.0f} MB @ {spd} - ETA {eta_str}")
                    sys.stdout.flush()

        elif d['status'] == 'finished':
            size = d.get('total_bytes') or d.get('downloaded_bytes', 0)
            mb = size / 1024 / 1024
            print(f"   DL 100% - {mb:.0f} MB download complete")
            sys.stdout.flush()


def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:v\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_video_info(video_id):
    """Get video info using YouTube's noembed API"""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', 'Unknown'),
                'author': data.get('author_name', 'Unknown'),
                'thumbnail': data.get('thumbnail_url', '')
            }
    except Exception as e:
        print(f"   Warning: Could not get video info: {e}")

    return {
        'title': 'Unknown',
        'author': 'Unknown',
        'thumbnail': ''
    }


def download_with_yt_dlp(video_url, video_id, cookies_file=None):
    """Download using yt-dlp with multiple configurations"""
    try:
        import yt_dlp
    except ImportError:
        print("   yt-dlp not installed")
        return None

    output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

    # Multiple configurations to try
    configs = [
        {
            'name': 'Best audio with cookies',
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'use_cookies': True,
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'progress_hooks': [ProgressLogger().hook],
            'outtmpl': output_path,
            'socket_timeout': 120,
            'retries': 10,
            'fragment_retries': 10,
        },
        {
            'name': 'Web client with cookies',
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                },
            },
            'use_cookies': True,
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'progress_hooks': [ProgressLogger().hook],
            'outtmpl': output_path,
            'socket_timeout': 120,
            'retries': 10,
            'fragment_retries': 10,
        },
        {
            'name': 'Android client',
            'format': 'bestaudio/best',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                },
            },
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'progress_hooks': [ProgressLogger().hook],
            'outtmpl': output_path,
            'socket_timeout': 120,
            'retries': 10,
            'fragment_retries': 10,
        },
        {
            'name': 'iOS client',
            'format': 'bestaudio/best',
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios'],
                },
            },
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'progress_hooks': [ProgressLogger().hook],
            'outtmpl': output_path,
            'socket_timeout': 120,
            'retries': 10,
            'fragment_retries': 10,
        },
        {
            'name': 'Any format',
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'progress_hooks': [ProgressLogger().hook],
            'outtmpl': output_path,
            'socket_timeout': 120,
            'retries': 10,
            'fragment_retries': 10,
        },
    ]

    for config in configs:
        name = config.pop('name', 'Unknown')
        print(f"   Trying: {name}...")

        ydl_opts = config.copy()

        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file

        if HAS_FFMPEG and 'bestaudio' in ydl_opts.get('format', ''):
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)

            # Find downloaded file
            for ext in ['m4a', 'mp3', 'opus', 'webm', 'aac', 'ogg']:
                path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    if size > 1024:
                        print(f"   ✓ Downloaded: {size / 1024 / 1024:.1f} MB")
                        return path

            # Check for any file with video_id
            for f in os.listdir(DOWNLOADS_DIR):
                if video_id in f and not f.endswith(('.jpg', '.png', '.webp', '.part', '.ytdl')):
                    fpath = os.path.join(DOWNLOADS_DIR, f)
                    size = os.path.getsize(fpath)
                    if size > 1024:
                        print(f"   ✓ Downloaded: {size / 1024 / 1024:.1f} MB")
                        return fpath

        except Exception as e:
            err = str(e)
            if 'Sign in' in err or 'bot' in err.lower():
                print(f"   ✗ Bot detection - trying next method")
            elif 'HTTP Error 403' in err:
                print(f"   ✗ 403 Forbidden - trying next method")
            elif 'HTTP Error 429' in err:
                print(f"   ✗ Rate limited - waiting and retrying...")
                time.sleep(30)
            else:
                print(f"   ✗ Error: {err[:200]}")

    return None


def download_with_pytube(video_url, video_id):
    """Download using pytube as fallback"""
    try:
        from pytube import YouTube
        print("   Trying pytube...")

        yt = YouTube(video_url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        if audio_stream:
            output_path = audio_stream.download(output_path=DOWNLOADS_DIR, filename=f"{video_id}.mp4")

            # Convert to m4a if FFmpeg is available
            if HAS_FFMPEG:
                m4a_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.m4a")
                subprocess.run([
                    'ffmpeg', '-i', output_path,
                    '-c:a', 'aac', '-b:a', '192k',
                    '-y', m4a_path
                ], capture_output=True)

                if os.path.exists(m4a_path):
                    os.remove(output_path)
                    output_path = m4a_path

            size = os.path.getsize(output_path)
            print(f"   ✓ Downloaded: {size / 1024 / 1024:.1f} MB")
            return output_path

    except ImportError:
        print("   pytube not installed")
    except Exception as e:
        print(f"   ✗ pytube error: {e}")

    return None


def download_with_youtube_dl(video_url, video_id):
    """Download using youtube-dl as fallback"""
    try:
        import youtube_dl
        print("   Trying youtube-dl...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [ProgressLogger().hook],
        }

        if HAS_FFMPEG:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }]

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(video_url, download=True)

        for ext in ['m4a', 'mp3', 'opus', 'webm', 'aac']:
            path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
            if os.path.exists(path):
                size = os.path.getsize(path)
                if size > 1024:
                    print(f"   ✓ Downloaded: {size / 1024 / 1024:.1f} MB")
                    return path

    except ImportError:
        print("   youtube-dl not installed")
    except Exception as e:
        print(f"   ✗ youtube-dl error: {e}")

    return None


class VideoDownloader:
    def __init__(self):
        self.cookies_file = "cookies.txt"

    def download_audio(self, video_url, video_id):
        """Download audio using multiple fallback methods"""
        print(f"\n{'='*60}")
        print(f"Downloading: {video_id}")
        print(f"URL: {video_url}")
        print(f"{'='*60}")

        # Get video info
        info = get_video_info(video_id)
        print(f"Title: {info['title']}")
        print(f"Author: {info['author']}")

        # Check cookies
        cookies_ok = os.path.exists(self.cookies_file)
        print(f"Cookies: {'✓' if cookies_ok else '✗'}")
        print(f"FFmpeg: {'✓' if HAS_FFMPEG else '✗'}")

        # Try each method
        methods = [
            ("yt-dlp", lambda: download_with_yt_dlp(video_url, video_id, self.cookies_file if cookies_ok else None)),
            ("pytube", lambda: download_with_pytube(video_url, video_id)),
            ("youtube-dl", lambda: download_with_youtube_dl(video_url, video_id)),
        ]

        for method_name, method_func in methods:
            print(f"\n--- Trying {method_name} ---")
            result = method_func()
            if result:
                return result

        print(f"\n❌ All download methods failed")
        return None
