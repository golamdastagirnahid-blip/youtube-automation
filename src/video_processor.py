"""
Video Processor
- Extracts audio from source video
- Combines with background image
- Splits into 4 hour parts
- Modifies audio slightly
"""

import os
import subprocess
import json
from src.config import (
    DOWNLOADS_DIR,
    PROCESSED_DIR,
    BACKGROUND_IMAGE,
    PART_DURATION_HOURS,
    MIN_VIDEO_DURATION_MINUTES,
)


class VideoProcessor:

    def __init__(self):
        os.makedirs(PROCESSED_DIR, exist_ok=True)

    # ─────────────────────────────────────────────
    # Get Video Duration in Minutes
    # ─────────────────────────────────────────────
    def get_duration(self, video_file):
        """Get video duration in minutes using ffprobe"""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_file
            ]
            result = subprocess.run(
                cmd,
                capture_output = True,
                text           = True,
                timeout        = 60
            )
            data     = json.loads(result.stdout)
            duration = float(
                data.get("format", {}).get("duration", 0)
            )
            minutes  = duration / 60
            print(f"   ⏱️ Duration: {minutes:.1f} minutes "
                  f"({minutes/60:.1f} hours)")
            return minutes
        except Exception as e:
            print(f"   ⚠️ Could not get duration: {e}")
            return 0

    # ─────────────────────────────────────────────
    # Check If Video Meets Duration Requirements
    # ─────────────────────────────────────────────
    def is_valid_duration(self, video_file):
        """Check if video is at least 60 minutes"""
        minutes = self.get_duration(video_file)
        if minutes < MIN_VIDEO_DURATION_MINUTES:
            print(
                f"   ⏭️ Skipping: {minutes:.1f} min "
                f"(minimum {MIN_VIDEO_DURATION_MINUTES} min)"
            )
            return False, minutes
        return True, minutes

    # ─────────────────────────────────────────────
    # Main Process Function
    # ─────────────────────────────────────────────
    def process(self, video_file, video_id):
        """
        Process video:
        1. Check duration (skip if < 60 min)
        2. Extract audio with modification
        3. Combine with background image
        4. Split into 4 hour parts
        Returns list of processed part files
        """
        print(f"\n🎬 Processing video: {video_id}")

        if not video_file or not os.path.exists(video_file):
            print("   ❌ Video file not found")
            return []

        # ── Check Duration ─────────────────────────
        valid, total_minutes = self.is_valid_duration(video_file)
        if not valid:
            return []

        total_hours = total_minutes / 60
        print(f"   ✅ Valid duration: {total_hours:.1f} hours")

        # ── Calculate Parts ────────────────────────
        part_duration = PART_DURATION_HOURS * 3600  # seconds
        total_seconds = total_minutes * 60
        num_parts     = max(1, int(
            (total_seconds + part_duration - 1) // part_duration
        ))

        print(f"   📊 Will create {num_parts} part(s) "
              f"of {PART_DURATION_HOURS} hours each")

        # ── Check Background Image ─────────────────
        if not os.path.exists(BACKGROUND_IMAGE):
            print(f"   ❌ Background image not found: {BACKGROUND_IMAGE}")
            print(f"   ⚠️ Please upload assets/background.jpg")
            return []

        print(f"   🖼️ Background: {BACKGROUND_IMAGE}")

        # ── Process Each Part ──────────────────────
        parts = []

        for part_num in range(num_parts):
            start_sec = part_num * part_duration
            end_sec   = min(
                (part_num + 1) * part_duration,
                total_seconds
            )
            duration_sec = end_sec - start_sec

            # Skip very short last parts (less than 30 min)
            if duration_sec < 1800:
                print(f"   ⏭️ Skipping part {part_num + 1} "
                      f"(too short: {duration_sec/60:.0f} min)")
                continue

            print(f"\n   🎵 Processing Part {part_num + 1}/{num_parts}")
            print(f"      Start   : {self._format_time(start_sec)}")
            print(f"      End     : {self._format_time(end_sec)}")
            print(f"      Duration: {duration_sec/3600:.1f} hours")

            output_file = os.path.join(
                PROCESSED_DIR,
                f"{video_id}_part{part_num + 1}.mp4"
            )

            success = self._create_part(
                video_file   = video_file,
                output_file  = output_file,
                start_sec    = start_sec,
                duration_sec = duration_sec,
            )

            if success:
                parts.append({
                    "file"      : output_file,
                    "part_num"  : part_num + 1,
                    "total_parts": num_parts,
                    "start_sec" : start_sec,
                    "end_sec"   : end_sec,
                    "duration"  : duration_sec,
                })
                print(f"      ✅ Part {part_num + 1} ready!")
            else:
                print(f"      ❌ Part {part_num + 1} failed!")

        print(f"\n   🎉 Processing complete!")
        print(f"   📦 {len(parts)} parts ready for upload")
        return parts

    # ─────────────────────────────────────────────
    # Create Single Part
    # ─────────────────────────────────────────────
    def _create_part(
        self,
        video_file,
        output_file,
        start_sec,
        duration_sec,
    ):
        """
        Create one video part:
        - Background image as video
        - Source audio (modified)
        - Combined into MP4
        """
        try:
            # Audio filters for slight modification
            audio_filters = (
                # Slight pitch shift
                "asetrate=44100*1.02,"
                "aresample=44100,"
                # Slight speed change
                "atempo=1.02,"
                # Normalize audio
                "dynaudnorm=f=150:g=15"
            )

            cmd = [
                "ffmpeg",

                # Input 1: Background image (loop)
                "-loop", "1",
                "-i", BACKGROUND_IMAGE,

                # Input 2: Source audio segment
                "-ss", str(start_sec),
                "-t",  str(duration_sec),
                "-i", video_file,

                # Video settings (static image)
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                       "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",

                # Audio filters
                "-af", audio_filters,

                # Encoding settings
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "stillimage",  # Optimized for static image
                "-crf", "28",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",

                # Match duration to audio
                "-shortest",

                # Fast start for YouTube
                "-movflags", "+faststart",

                # Overwrite output
                "-y",
                output_file
            ]

            print(f"      ⏳ Creating part... "
                  f"(~{duration_sec/3600:.1f} hours of content)")

            result = subprocess.run(
                cmd,
                capture_output = True,
                text           = True,
                timeout        = 21600  # 6 hour timeout
            )

            if result.returncode == 0 and \
               os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"      📦 Size: {size // 1024 // 1024} MB")
                return True
            else:
                print(f"      ❌ FFmpeg error:")
                print(f"      {result.stderr[-300:]}")
                return False

        except subprocess.TimeoutExpired:
            print(f"      ⏰ Timeout creating part")
            return False
        except Exception as e:
            print(f"      ⚠️ Error: {e}")
            return False

    # ─────────────────────────────────────────────
    # Format Time Helper
    # ─────────────────────────────────────────────
    def _format_time(self, seconds):
        """Convert seconds to HH:MM:SS"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # ─────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────
    def cleanup(self, video_id):
        """Remove all processed parts after upload"""
        import glob
        pattern = os.path.join(
            PROCESSED_DIR,
            f"{video_id}_part*.mp4"
        )
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                print(f"   🧹 Removed: {f}")
            except Exception:
                pass
