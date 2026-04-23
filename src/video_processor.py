"""
Video Processor - Strong Content ID Bypass
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
        print(f"\n🎬 Processing video for Content ID bypass...")

        if not video_file or not os.path.exists(video_file):
            print("   ❌ Video file not found")
            return video_file

        output_file = os.path.join(
            self.processed_dir,
            f"{video_id}_processed.mp4"
        )

        if os.path.exists(output_file):
            os.remove(output_file)

        # Random strong speed change
        speed = random.choice([1.15, 1.12, 0.88, 0.85])

        # Random rotation (very slight)
        rotation = random.choice([0.5, 1.0, -0.5, -1.0])

        # Build filters
        vf = self._video_filters(speed, rotation)
        af = self._audio_filters(speed)

        print(f"   ⚡ Speed    : {speed}x")
        print(f"   🔄 Rotation : {rotation}°")
        print(f"   🔧 Video    : {vf}")
        print(f"   🔊 Audio    : {af}")

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
            print(f"   ⏳ Processing... (may take 3-6 minutes)")
            result = subprocess.run(
                cmd,
                capture_output = True,
                text           = True,
                timeout        = 1800
            )

            if result.returncode == 0 and \
               os.path.exists(output_file):
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
                print(f"   ❌ FFmpeg error")
                print(f"   {result.stderr[-300:]}")
                return video_file

        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout — using original")
            return video_file
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            return video_file

    # ─────────────────────────────────────────────
    # Strong Video Filters
    # ─────────────────────────────────────────────
    def _video_filters(self, speed=1.15, rotation=1.0):
        pts = 1.0 / speed

        # Random color shift values
        brightness = random.choice([0.04, 0.05, 0.06])
        contrast   = random.choice([1.03, 1.04, 1.05])
        saturation = random.choice([1.02, 1.03, 1.04])

        filters = [
            # 1. Flip horizontally
            "hflip",

            # 2. Slight rotation
            f"rotate={rotation}*PI/180:fillcolor=black",

            # 3. Zoom 5% (stronger than before)
            "scale=iw*1.05:ih*1.05",
            "crop=iw/1.05:ih/1.05",

            # 4. Stronger color modification
            f"eq=brightness={brightness}:"
            f"contrast={contrast}:"
            f"saturation={saturation}",

            # 5. Add slight blur then sharpen
            # (changes pixel fingerprint)
            "unsharp=3:3:0.5:3:3:0.0",

            # 6. Speed change
            f"setpts={pts:.4f}*PTS",
        ]

        return ",".join(filters)

    # ─────────────────────────────────────────────
    # Strong Audio Filters
    # ─────────────────────────────────────────────
    def _audio_filters(self, speed=1.15):
        # Stronger pitch shift
        pitch = random.choice([1.06, 1.08, 0.94, 0.92])

        # Random equalizer settings
        eq_freq = random.choice([800, 1000, 1200])
        eq_gain = random.choice([2, 3, -2, -3])

        filters = [
            # 1. Strong pitch shift
            f"asetrate=44100*{pitch}",
            "aresample=44100",

            # 2. Match speed
            f"atempo={speed:.4f}",

            # 3. Equalizer (changes audio fingerprint)
            f"equalizer=f={eq_freq}:width_type=o:"
            f"width=2:g={eq_gain}",

            # 4. Very subtle noise (changes waveform)
            "aeval=val(0)+random(0)*0.002|"
            "val(1)+random(1)*0.002:c=stereo",
        ]

        return ",".join(filters)

    # ─────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────
    def cleanup(self, video_id):
        processed = os.path.join(
            self.processed_dir,
            f"{video_id}_processed.mp4"
        )
        if os.path.exists(processed):
            os.remove(processed)
            print(f"   🧹 Cleaned processed file")
