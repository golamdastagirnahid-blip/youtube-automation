"""
Quick Test Script - Fixed encoding
Run this locally to test if everything is working
"""

import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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
        print(f"   [OK] {name}")
    except ImportError:
        print(f"   [FAIL] {name} (not installed)")

# Test 3: Check FFmpeg
print("\n3. Testing FFmpeg...")
import shutil
ffmpeg = shutil.which('ffmpeg')
if ffmpeg:
    print(f"   [OK] FFmpeg found at {ffmpeg}")
else:
    print("   [FAIL] FFmpeg not found")

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
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            print(f"   [OK] Title: {title[:50]}...")
            print(f"   [OK] Duration: {duration} seconds")
        else:
            print("   [FAIL] No info returned")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 5: Test pytube
print("\n5. Testing pytube with video...")
try:
    from pytube import YouTube
    video_url = "https://www.youtube.com/watch?v=YXJC6YKaQXE"

    yt = YouTube(video_url)
    print(f"   [OK] Title: {yt.title[:50]}...")
    print(f"   [OK] Duration: {yt.length} seconds")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 6: Test youtube-dl
print("\n6. Testing youtube-dl with video...")
try:
    import youtube_dl
    video_url = "https://www.youtube.com/watch?v=YXJC6YKaQXE"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        if info:
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            print(f"   [OK] Title: {title[:50]}...")
            print(f"   [OK] Duration: {duration} seconds")
        else:
            print("   [FAIL] No info returned")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
