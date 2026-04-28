"""
Simple Download Test
Tests download methods without full automation
"""

import os
import sys
import subprocess
import time

def test_python():
    """Test Python installation"""
    print("=== Testing Python ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print("✓ Python OK\n")

def test_ffmpeg():
    """Test FFmpeg installation"""
    print("=== Testing FFmpeg ===")
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"FFmpeg version: {result.stdout.split()[2]}")
            print("✓ FFmpeg OK\n")
            return True
        else:
            print("✗ FFmpeg not found\n")
            return False
    except Exception as e:
        print(f"✗ FFmpeg error: {e}\n")
        return False

def test_yt_dlp():
    """Test yt-dlp installation"""
    print("=== Testing yt-dlp ===")
    try:
        import yt_dlp
        print(f"yt-dlp version: {yt_dlp.version.__version__}")
        print("✓ yt-dlp OK\n")
        return True
    except ImportError as e:
        print(f"✗ yt-dlp not installed: {e}\n")
        return False

def test_pytube():
    """Test pytube installation"""
    print("=== Testing pytube ===")
    try:
        from pytube import YouTube
        print("pytube imported successfully")
        print("✓ pytube OK\n")
        return True
    except ImportError as e:
        print(f"✗ pytube not installed: {e}\n")
        return False

def test_youtube_dl():
    """Test youtube-dl installation"""
    print("=== Testing youtube-dl ===")
    try:
        import youtube_dl
        print("youtube-dl imported successfully")
        print("✓ youtube-dl OK\n")
        return True
    except ImportError as e:
        print(f"✗ youtube-dl not installed: {e}\n")
        return False

def test_yt_dlp_info(video_url):
    """Test yt-dlp info extraction"""
    print(f"=== Testing yt-dlp info extraction ===")
    print(f"Video URL: {video_url}")

    try:
        import yt_dlp

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'socket_timeout': 30,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            if info:
                print(f"Title: {info.get('title', 'Unknown')}")
                print(f"Duration: {info.get('duration', 0)} seconds")
                print(f"View count: {info.get('view_count', 0)}")
                print("✓ yt-dlp info extraction OK\n")
                return True
            else:
                print("✗ No info returned\n")
                return False

    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False

def test_pytube_info(video_url):
    """Test pytube info extraction"""
    print(f"=== Testing pytube info extraction ===")
    print(f"Video URL: {video_url}")

    try:
        from pytube import YouTube

        yt = YouTube(video_url)
        print(f"Title: {yt.title}")
        print(f"Duration: {yt.length} seconds")
        print(f"Views: {yt.views}")
        print("✓ pytube info extraction OK\n")
        return True

    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False

def test_yt_dlp_download(video_url, video_id):
    """Test yt-dlp download (small test)"""
    print(f"=== Testing yt-dlp download ===")
    print(f"Video URL: {video_url}")
    print(f"Video ID: {video_id}")

    try:
        import yt_dlp

        # Create downloads directory
        downloads_dir = "downloads"
        os.makedirs(downloads_dir, exist_ok=True)

        output_path = os.path.join(downloads_dir, f"{video_id}.%(ext)s")

        ydl_opts = {
            'format': 'worstaudio',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'max_downloads': 1,
        }

        print("Downloading (worst quality for test)...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(video_url, download=True)

        # Check if file was downloaded
        for ext in ['m4a', 'mp3', 'opus', 'webm', 'aac']:
            path = os.path.join(downloads_dir, f"{video_id}.{ext}")
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"Downloaded: {size / 1024 / 1024:.2f} MB")
                print("✓ yt-dlp download OK\n")
                return True

        print("✗ No file downloaded\n")
        return False

    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("YouTube Automation - Diagnostic Test")
    print("=" * 60)
    print()

    # Get video URL from environment or use default
    video_url = os.environ.get("VIDEO_URL", "https://www.youtube.com/watch?v=YXJC6YKaQXE")
    video_id = os.environ.get("VIDEO_ID", "YXJC6YKaQXE")

    # Test basic components
    test_python()
    has_ffmpeg = test_ffmpeg()
    has_yt_dlp = test_yt_dlp()
    has_pytube = test_pytube()
    has_youtube_dl = test_youtube_dl()

    # Test info extraction
    if has_yt_dlp:
        test_yt_dlp_info(video_url)

    if has_pytube:
        test_pytube_info(video_url)

    # Test download (only if yt-dlp is available)
    if has_yt_dlp:
        test_yt_dlp_download(video_url, video_id)

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Python: ✓")
    print(f"FFmpeg: {'✓' if has_ffmpeg else '✗'}")
    print(f"yt-dlp: {'✓' if has_yt_dlp else '✗'}")
    print(f"pytube: {'✓' if has_pytube else '✗'}")
    print(f"youtube-dl: {'✓' if has_youtube_dl else '✗'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
