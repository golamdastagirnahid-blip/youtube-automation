"""
Video Uploader
Uploads processed videos to YouTube
"""

import os
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
                print(f"   ⚠️ Channel mismatch!")
        except Exception as e:
            print(f"   ⚠️ {e}")
        return False

    def upload_video(self, video_info):
        video_file = video_info.get("video_file")
        if not video_file or not os.path.exists(video_file):
            print("❌ Video file not found")
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
        self._verify_channel()

        body = {
            "snippet": {
                "title"      : title,
                "description": desc,
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
            mimetype  = "video/mp4",
            resumable = True
        )

        try:
            response = self.youtube.videos().insert(
                part       = "snippet,status",
                body       = body,
                media_body = media
            ).execute()

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
                except Exception as e:
                    print(f"⚠️ Thumbnail: {e}")

            return {
                "success" : True,
                "video_id": uploaded_id,
                "url"     : f"https://youtu.be/{uploaded_id}"
            }

        except HttpError as e:
            print(f"❌ Upload failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
