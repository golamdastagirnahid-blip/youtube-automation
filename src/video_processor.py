"""
Video Processor
Creates image+audio video and modifies audio
"""

import os
import random
import shutil
import subprocess


PROCESSED_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "processed"
)

os.makedirs(PROCESSED_DIR, exist_ok=True)

HAS_FFMPEG = shutil.which("ffmpeg") is not None


class VideoProcessor:

    def modify_audio(self, audio_file, video_id):
        if not audio_file or not os.path.exists(audio_file):
            return audio_file

        if not HAS_FFMPEG:
            print("   FFmpeg not found - skipping audio modify")
            return audio_file

        output = os.path.join(
            PROCESSED_DIR,
            f"{video_id}_modified.m4a"
        )

        pitch = random.choice([1.02, 1.03, 0.97, 0.98])
        speed = random.choice([1.02, 1.03, 0.97, 0.98])

        cmd = [
            "ffmpeg",
            "-i",    audio_file,
            "-af",   (
                f"asetrate=44100*{pitch},"
                f"aresample=44100,"
                f"atempo={speed}"
            ),
            "-c:a",  "aac",
            "-b:a",  "192k",
            "-y",    output
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=7200
            )
            if result.returncode == 0 and \
               os.path.exists(output):
                print(f"   Audio modified OK")
                return output
            else:
                print(f"   Audio modify failed - using original")
                if result.stderr:
                    print(f"   FFmpeg: {result.stderr[-200:]}")
                return audio_file
        except Exception as e:
            print(f"   Audio error: {e}")
            return audio_file

    def create_image_audio_video(
        self,
        audio_file,
        output_id,
        start_sec,
        end_sec,
        thumb_file
    ):
        if not HAS_FFMPEG:
            print("   FATAL: FFmpeg not installed - cannot create video")
            print("   Install FFmpeg on the runner or add it to PATH")
            return None

        if not audio_file or not os.path.exists(audio_file):
            print("   Audio file missing")
            return None

        if not thumb_file or not os.path.exists(thumb_file):
            print("   Thumbnail missing")
            return None

        output = os.path.join(
            PROCESSED_DIR,
            f"{output_id}.mp4"
        )

        duration = end_sec - start_sec

        print(
            f"   Creating video: "
            f"{duration//3600:.0f}h "
            f"{(duration%3600)//60:.0f}m"
        )

        cmd = [
            "ffmpeg",
            "-loop",       "1",
            "-i",          thumb_file,
            "-ss",         str(int(start_sec)),
            "-t",          str(int(duration)),
            "-i",          audio_file,
            "-c:v",        "libx264",
            "-preset",     "ultrafast",
            "-crf",        "28",
            "-tune",       "stillimage",
            "-c:a",        "aac",
            "-b:a",        "192k",
            "-t",          str(int(duration)),
            "-pix_fmt",    "yuv420p",
            "-movflags",   "+faststart",
            "-shortest",
            "-y",
            output
        ]

        try:
            print(f"   Processing... (this may take a while)")
            result = subprocess.run(
                cmd,
                capture_output = True,
                text           = True,
                timeout        = 86400
            )

            if result.returncode == 0 and \
               os.path.exists(output):
                size = os.path.getsize(output)
                print(
                    f"   Video created: "
                    f"{size // 1024 // 1024} MB"
                )
                return output
            else:
                print(f"   FFmpeg failed:")
                if result.stderr:
                    print(f"   {result.stderr[-500:]}")
                return None

        except subprocess.TimeoutExpired:
            print(f"   Timeout creating video!")
            return None
        except Exception as e:
            print(f"   Video creation error: {e}")
            return None

    def cleanup(self, video_id):
        for suffix in [
            "_modified.m4a",
            "_part1.mp4",
            "_part2.mp4",
            "_part3.mp4",
            "_part4.mp4",
        ]:
            f = os.path.join(PROCESSED_DIR, f"{video_id}{suffix}")
            if os.path.exists(f):
                os.remove(f)
