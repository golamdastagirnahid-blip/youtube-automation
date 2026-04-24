"""
Video Downloader - Audio Only
Uses OAuth2 authentication - No VPN or cookies needed
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


class VideoDownloader:

    def download_audio(self, video_url, video_id):
        """
        Download audio using OAuth2 token
        No VPN or cookies needed
        """
        print(f"   🎵 Downloading: {video_id}")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        # Method 1: OAuth2 (Strongest - acts like a TV app)
        print(f"   🔄 Method 1: OAuth2...")
        result = self._try_download(
            video_url, video_id, output_path,
            client='oauth2'
        )
        if result:
            return result

        # Method 2: Android client
        print(f"   🔄 Method 2: Android client...")
        result = self._try_download(
            video_url, video_id, output_path,
            client='android'
        )
        if result:
            return result

        # Method 3: iOS client
        print(f"   🔄 Method 3: iOS client...")
        result = self._try_download(
            video_url, video_id, output_path,
            client='ios'
        )
        if result:
            return result

        # Method 4: Web client
        print(f"   🔄 Method 4: Web client...")
        result = self._try_download(
            video_url, video_id, output_path,
            client='web'
        )
        if result:
            return result

        print(f"   ❌ All methods failed")
        return None

    def _try_download(
        self, video_url, video_id,
        output_path, client='oauth2'
    ):
        """Try downloading with specific client"""
        try:
            if client == 'oauth2':
                ydl_opts = {
                    'format'         : (
                        'bestaudio[ext=m4a]/bestaudio'
                    ),
                    'outtmpl'        : output_path,
                    'quiet'          : True,
                    'no_warnings'    : True,
                    'username'       : 'oauth2',
                    'password'       : '',
                    'socket_timeout' : 30,
                    'postprocessors' : [{
                        'key'            : 'FFmpegExtractAudio',
                        'preferredcodec' : 'm4a',
                    }],
                }
            else:
                ydl_opts = {
                    'format'         : (
                        'bestaudio[ext=m4a]/bestaudio'
                    ),
                    'outtmpl'        : output_path,
                    'quiet'          : True,
                    'no_warnings'    : True,
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
                        f"   ✅ Downloaded: "
                        f"{size // 1024 // 1024} MB"
                    )
                    return path

            # Search by video_id
            for f in os.listdir(DOWNLOADS_DIR):
                if video_id in f and not f.endswith(
                    ('.jpg', '.png', '.webp', '.jpeg')
                ):
                    return os.path.join(DOWNLOADS_DIR, f)

        except Exception as e:
            print(f"   ⚠️ {client}: {str(e)[:80]}")

        return None
