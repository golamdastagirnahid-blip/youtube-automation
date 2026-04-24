"""
Video Downloader - Audio Only
Uses cookies + Deno + EJS remote components
"""

import os
import yt_dlp

DOWNLOADS_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "downloads"
)

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

COOKIES_FILE = "cookies.txt"


class VideoDownloader:

    def download_audio(self, video_url, video_id):
        print(f"   🎵 Downloading: {video_id}")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        # Method 1: android client
        print(f"   🔄 Method 1: Android...")
        result = self._try_download(
            video_url, video_id,
            output_path, client='android'
        )
        if result:
            return result

        # Method 2: ios client
        print(f"   🔄 Method 2: iOS...")
        result = self._try_download(
            video_url, video_id,
            output_path, client='ios'
        )
        if result:
            return result

        # Method 3: web client
        print(f"   🔄 Method 3: Web...")
        result = self._try_download(
            video_url, video_id,
            output_path, client='web'
        )
        if result:
            return result

        # Method 4: tv client
        print(f"   🔄 Method 4: TV...")
        result = self._try_download(
            video_url, video_id,
            output_path, client='tv'
        )
        if result:
            return result

        print(f"   ❌ All methods failed")
        return None

    def _try_download(
        self, video_url, video_id,
        output_path, client='android'
    ):
        try:
            ydl_opts = {
                'format'           : (
                    'bestaudio[ext=m4a]/bestaudio/best'
                ),
                'outtmpl'          : output_path,
                'quiet'            : True,
                'no_warnings'      : True,
                'socket_timeout'   : 30,
                'remote_components': 'ejs:github',
                'extractor_args'   : {
                    'youtube': {
                        'player_client': [client],
                    }
                },
                'postprocessors'   : [{
                    'key'           : 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }],
            }

            # Add cookies if file exists
            if os.path.exists(COOKIES_FILE):
                ydl_opts['cookiefile'] = COOKIES_FILE

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(
                    video_url,
                    download=True
                )

            # Find downloaded file
            for ext in [
                'm4a', 'mp3', 'opus', 'webm', 'aac'
            ]:
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

            # Search by video_id
            for f in os.listdir(DOWNLOADS_DIR):
                if video_id in f and not f.endswith(
                    ('.jpg', '.png', '.webp', '.jpeg')
                ):
                    return os.path.join(
                        DOWNLOADS_DIR, f
                    )

        except Exception as e:
            print(
                f"   ⚠️ {client}: {str(e)[:80]}"
            )

        return None
