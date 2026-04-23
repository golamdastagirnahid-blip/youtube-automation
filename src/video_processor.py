"""
Video Processor
Modifies video to bypass Content ID detection
Uses FFmpeg for all modifications
"""

import os
import subprocess
import random
from src.config import DOWNLOADS_DIR


class VideoProcessor:

    def __init__(self):
        self.processed_dir = os.path.join(
            os.path.dirname(DOWNLOADS_DIR),
            "processed"
        )
        os.makedirs(self.processed_dir, exist_ok=True)

    # ─────────────────────────────────────────────
    # Main Process Function
    # ─────────────────────────────────────────────
    def process(self, video_file, video_id):
        """
        Apply all modifications to bypass Content ID
        Returns path to processed video
        """
        print(f"\n🎬 Processing video for Content ID bypass...")

        if not video_file or not os.path.exists(video_file):
            print("   ❌ Video file not found for processing")
            return video_file

        output_file = os.path.join(
            self.processed_dir,
            f"{video_id}_processed.mp4"
        )

        # If already processed
        if os.path.exists(output_file):
            os.remove(output_file)

        # Pick random speed
        speed = random.choice([1.03, 1.05, 0.97, 0.95])

        # Build video filters
        vf = self._video_filters(speed)

        # Build audio filters
        af = self._audio_filters(speed)

        print(f"   🔧 Video filter : {vf}")
        print(f"   🔊 Audio filter : {af}")
        print(f"   ⚡ Speed        : {speed}x")

        cmd = [
            "ffmpeg",
            "-i",      video_file,
            "-vf",     vf,
            "-af",     af,
            "-c:v",    "libx264",
            "-preset", "fast",
            "-crf",    "23",
            "-c:a",    "aac",
            "-b:a",    "128k",
            "-movflags", "+faststart",
            "-y",
            output_file
        ]

        try:
            print(f"   ⏳ Processing... (may take 2-5 minutes)")
            result = subprocess.run(
                cmd,
                capture_output = True,
                text           = True,
                timeout        = 1800  # 30 min timeout
            )

            if result.returncode == 0 and os.path.exists(output_file):
                orig_size = os.path.getsize(video_file)
                proc_size = os.path.getsize(output_file)
                print(f"   ✅ Processing complete!")
                print(
                    f"   📦 Original  : "
                    f"{orig_size  // 1024 // 1024} MB"
                )
                print(
                    f"   📦 Processed : "
                    f"{proc_size  // 1024 // 1024} MB"
                )
                return output_file

            else:
                print(f"   ❌ FFmpeg error:")
                print(f"   {result.stderr[-500:]}")
                print(f"   ⚠️ Using original file instead")
                return video_file

        except subprocess.TimeoutExpired:
            print(f"   ⏰ Processing timed out — using original")
            return video_file

        except Exception as e:
            print(f"   ⚠️ Processing error: {e}")
            print(f"   ⚠️ Using original file instead")
            return video_file

    # ─────────────────────────────────────────────
    # Video Filters
    # ─────────────────────────────────────────────
    def _video_filters(self, speed=1.05):
        """
        Build video filter chain:
        1. Horizontal flip  → defeats Content ID
        2. Zoom 103%        → changes pixel positions
        3. Brightness tweak → changes color values
        4. Speed change     → changes frame timing
        """
        pts = 1.0 / speed

        filters = [
            # 1. Flip horizontally
            "hflip",

            # 2. Zoom in 3% then crop back to original size
            "scale=iw*1.03:ih*1.03",
            "crop=iw/1.03:ih/1.03",

            # 3. Slight color adjustment
            "eq=brightness=0.02:contrast=1.02:saturation=1.01",

            # 4. Speed adjustment
            f"setpts={pts:.4f}*PTS",
        ]

        return ",".join(filters)

    # ─────────────────────────────────────────────
    # Audio Filters
    # ─────────────────────────────────────────────
    def _audio_filters(self, speed=1.05):
        """
        Build audio filter chain:
        1. Pitch shift   → defeats audio Content ID
        2. Speed match   → matches video speed
        """
        # Slight pitch shift up
        pitch = 1.03

        filters = [
            # 1. Change pitch slightly
            f"asetrate=44100*{pitch}",
            "aresample=44100",

            # 2. Match audio speed to video speed
            f"atempo={speed:.4f}",
        ]

        return ",".join(filters)

    # ─────────────────────────────────────────────
    # Cleanup Processed Files
    # ─────────────────────────────────────────────
    def cleanup(self, video_id):
        """Remove processed file after upload"""
        processed = os.path.join(
            self.processed_dir,
            f"{video_id}_processed.mp4"
        )
        if os.path.exists(processed):
            os.remove(processed)
            print(f"   🧹 Cleaned processed file")
