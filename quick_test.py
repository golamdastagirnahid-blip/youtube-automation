"""
Quick Test Script
Run this locally to test if everything is working
"""

import os
import sys

print("=" * 60)
print("YouTube Automation - Quick Test")
print("=" * 60)
print()

# Test 1: Python
print("1. Python version:", sys.version.split()[0])

# Test 2: Check if we can import required modules
print("\n2. Testing imports...")
modules = {
    'yt_dlp': 'yt-dlp',
    'pytube': 'pytube',
    'youtube_dl': 'youtube-dl',
    'googleapiclient': 'google-api-python-client',
    'requests': 'requests',
    'PIL': 'Pillow',
}

for module, name in modules.items():
    try:
        __import__(module)
        print(f"   ✓ {name}")
    except ImportError:
        print(f"   ✗ {name} (not installed)")

# Test 3: Check FFmpeg
print("\n3. Testing FFmpeg...")
import shutil
ffmpeg = shutil.which('ffmpeg')
if ffmpeg:
    print(f"   ✓ FFmpeg found at {ffmpeg}")
else:
    print("   ✗ FFmpeg not found")

# Test 4: Test yt-dlp with a simple video
print("\n4. Testing yt-dlp with video...")
try:
    import yt_dlp
    video_url = "https://www.youtube.com/watch?v=YXJC6YKaQXE"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        if info:
            print(f"   ✓ Title: {info.get('title', 'Unknown')[:50]}...")
            print(f"   ✓ Duration: {info.get('duration', 0)} seconds")
        else:
            print("   ✗ No info returned")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Test pytube
print("\n5. Testing pytube with video...")
try:
    from pytube import YouTube
    video_url = "https://www.youtube.com/watch?v=YXJC6YKaQXE"

    yt = YouTube(video_url)
    print(f"   ✓ Title: {yt.title[:50]}...")
    print(f"   ✓ Duration: {yt.length} seconds")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
