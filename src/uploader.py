"""
Video Uploader
Uploads processed videos to YouTube
"""

import os
import time
from googleapiclient.http   import MediaFileUpload
from googleapiclient.errors import HttpError
from src.config             import (
    DEFAULT_PRIVACY,
    DEFAULT_CATEGORY,
    DEFAULT_LANGUAGE,
)


class VideoUploader:

    def __init__(self, youtube, target_channel_id=None):
        self.youtube           = youtube
        self.target_channel_id = target_channel_id

    def _verify_channel(self):
        try:
            response = self.youtube.channels().list(
                part = "snippet",
                mine = True
            ).execute()
            items = response.get("items", [])
            if items:
                for item in items:
                    ch_id   = item.get("id", "")
                    ch_name = item.get(
                        "snippet", {}
                    ).get("title", "")
                    print(f"   📺 {ch_name} ({ch_id})")
                    if ch_id == self.target_channel_id:
                        print(f"   ✅ Correct channel!")
                        return True
                print(f"   ❌ Channel mismatch!")
                print(f"      Expected: {self.target_channel_id}")
                print(f"      Got: {[i['id'] for i in items]}")
                return False
            else:
                print(f"   ❌ No channels found for this account")
                return False
        except HttpError as e:
            print(f"   ❌ Channel verify API error: {e}")
            if e.resp.status == 401:
                print(f"   ❌ Token is INVALID or EXPIRED")
            elif e.resp.status == 403:
                print(f"   ❌ Permission denied — check OAuth scopes")
            return False
        except Exception as e:
            print(f"   ❌ Channel verify error: {e}")
            return False

    def upload_video(self, video_info):
        video_file = video_info.get("video_file")
        if not video_file or not os.path.exists(video_file):
            print("❌ Video file not found")
            return None

        file_size = os.path.getsize(video_file)
        if file_size < 1024:
            print(f"❌ Video file too small ({file_size} bytes) — likely corrupt")
            return None

        title = video_info.get("title", "Relaxing Video")
        desc  = video_info.get("description", (
            "🎵 Perfect for Deep Sleep & Relaxation\n\n"
            "✅ Deep Sleep\n"
            "✅ Relaxation\n"
            "✅ Study & Focus\n"
            "✅ Meditation\n\n"
            "👍 Like & Subscribe!\n"
            "#sleep #relaxing #meditation"
        ))

        print(f"\n📤 Uploading: {title[:50]}")
        print(f"   📁 File: {video_file} ({file_size // 1024 // 1024} MB)")

        # Verify channel BEFORE uploading
        if not self._verify_channel():
            print("❌ ABORTING upload — channel verification failed")
            print("   This means authentication is broken or wrong account.")
            return None

        body = {
            "snippet": {
                "title"      : title[:100],
                "description": desc[:5000],
                "tags"       : [
                    "sleep music", "relaxing",
                    "deep sleep",  "meditation",
                    "rain sounds", "white noise",
                ],
                "categoryId"          : DEFAULT_CATEGORY,
                "defaultLanguage"     : DEFAULT_LANGUAGE,
                "defaultAudioLanguage": DEFAULT_LANGUAGE,
            },
            "status": {
                "privacyStatus"          : DEFAULT_PRIVACY,
                "selfDeclaredMadeForKids": False,
                "embeddable"             : True,
            }
        }

        media = MediaFileUpload(
            video_file,
            mimetype   = "video/mp4",
            resumable  = True,
            chunksize  = 50 * 1024 * 1024,
        )

        try:
            request = self.youtube.videos().insert(
                part       = "snippet,status",
                body       = body,
                media_body = media
            )

            # Resumable upload with progress
            response = None
            retry_count = 0
            max_retries = 10
            last_pct = -1

            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        pct = int(status.progress() * 100)
                        if pct >= last_pct + 10:
                            last_pct = pct
                            print(f"   📤 Upload progress: {pct}%")
                    retry_count = 0
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504] and retry_count < max_retries:
                        retry_count += 1
                        wait = min(retry_count * 10, 120)
                        print(f"   ⚠️ Server error {e.resp.status}, retry {retry_count}/{max_retries} in {wait}s...")
                        time.sleep(wait)
                    else:
                        raise

            uploaded_id = response.get("id")
            print(f"✅ Uploaded: https://youtu.be/{uploaded_id}")

            # Set thumbnail
            thumb = video_info.get("thumbnail_file")
            if thumb and os.path.exists(thumb):
                try:
                    self.youtube.thumbnails().set(
                        videoId    = uploaded_id,
                        media_body = MediaFileUpload(
                            thumb,
                            mimetype="image/jpeg"
                        )
                    ).execute()
                    print("🖼️ Thumbnail set!")
                except HttpError as e:
                    if "not verified" in str(e).lower():
                        print("⚠️ Thumbnail: Channel not verified (need 100k+ subs or verification)")
                    else:
                        print(f"⚠️ Thumbnail failed: {e}")
                except Exception as e:
                    print(f"⚠️ Thumbnail error: {e}")

            return {
                "success" : True,
                "video_id": uploaded_id,
                "url"     : f"https://youtu.be/{uploaded_id}"
            }

        except HttpError as e:
            error_msg = str(e)
            print(f"❌ Upload HTTP error: {e}")
            if e.resp.status == 401:
                print("   ❌ CAUSE: Token expired or invalid")
                print("   FIX: Re-generate token.json and update YOUTUBE_TOKEN secret")
            elif e.resp.status == 403:
                if "quotaExceeded" in error_msg:
                    print("   ❌ CAUSE: YouTube API daily quota exceeded (10,000 units)")
                    print("   FIX: Wait 24 hours or request quota increase")
                elif "forbidden" in error_msg.lower():
                    print("   ❌ CAUSE: Upload permission denied")
                    print("   FIX: Check OAuth scopes include youtube.upload")
                else:
                    print(f"   ❌ CAUSE: Forbidden — {error_msg}")
            elif e.resp.status == 400:
                print(f"   ❌ CAUSE: Bad request — check title/description/tags")
            else:
                print(f"   ❌ HTTP {e.resp.status}")
            return None
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
