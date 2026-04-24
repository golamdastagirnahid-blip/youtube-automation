"""
Video Downloader - Audio Only
Uses PO Token to bypass bot detection
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

    def _get_extractor_args(self, client='web'):
        """Build extractor args with PO token"""
        po_token     = os.environ.get("PO_TOKEN",     "")
        visitor_data = os.environ.get("VISITOR_DATA", "")

        args = {
            'youtube': {
                'player_client': [client],
            }
        }

        if po_token and client == 'web':
            args['youtube']['po_token'] = [
                f'web+{po_token}'
            ]

        if visitor_data and client == 'web':
            args['youtube']['visitor_data'] = [
                visitor_data
            ]

        return args

    def download_audio(self, video_url, video_id):
        """Download audio with PO token fallback"""
        print(f"   🎵 Downloading: {video_id}")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        # Method 1: Web client with PO token
        print(f"   🔄 Method 1: Web + PO Token...")
        ydl_opts = {
            'format'         : 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl'        : output_path,
            'quiet'          : True,
            'no_warnings'    : True,
            'extractor_args' : self._get_extractor_args('web'),
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

        # Method 2: Android client
        print(f"   🔄 Method 2: Android client...")
        ydl_opts['extractor_args'] = (
            self._get_extractor_args('android')
        )
        result = self._try_download(
            ydl_opts, video_url, video_id
        )
        if result:
            return result

        # Method 3: iOS client
        print(f"   🔄 Method 3: iOS client...")
        ydl_opts['extractor_args'] = (
            self._get_extractor_args('ios')
        )
        result = self._try_download(
            ydl_opts, video_url, video_id
        )
        if result:
            return result

        print(f"   ❌ All methods failed")
        return None

    def _try_download(self, ydl_opts, video_url, video_id):
        """Try downloading with given options"""
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
                        f"   ✅ Downloaded: "
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
