"""
Video Downloader - Audio Only
No cookies needed for worldwide public content
"""

import os
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

    def download_audio(self, video_url, video_id):
        print(f"   🎵 Downloading audio: {video_id}")

        output_path = os.path.join(
            DOWNLOADS_DIR,
            f"{video_id}.%(ext)s"
        )

        # Try multiple clients
        clients = ['android', 'ios', 'web']

        for client in clients:
            print(f"   🔄 Trying client: {client}")
            ydl_opts = {
                'format'         : (
                    'bestaudio[ext=m4a]/bestaudio'
                ),
                'outtmpl'        : output_path,
                'quiet'          : True,
                'no_warnings'    : True,
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

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(
                        video_url,
                        download=True
                    )

                # Find audio file
                audio_file = None
                for ext in ['m4a', 'mp3', 'opus', 'webm']:
                    path = os.path.join(
                        DOWNLOADS_DIR,
                        f"{video_id}.{ext}"
                    )
                    if os.path.exists(path):
                        audio_file = path
                        break

                if not audio_file:
                    for f in os.listdir(DOWNLOADS_DIR):
                        if video_id in f:
                            audio_file = os.path.join(
                                DOWNLOADS_DIR, f
                            )
                            break

                if audio_file:
                    size = os.path.getsize(audio_file)
                    print(
                        f"   ✅ Audio downloaded: "
                        f"{size // 1024 // 1024} MB"
                    )
                    return audio_file

            except Exception as e:
                print(f"   ❌ {client} failed: {e}")
                continue

        print(f"   ❌ All clients failed")
        return None
