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
                    print(
                        f"   📺 Channel: "
                        f"{ch_name} ({ch_id})"
                    )
                    if ch_id == self.target_channel_id:
                        print(f"   ✅ Correct channel!")
                        return True
                print(f"   ⚠️ Channel mismatch!")
                return False
        except Exception as e:
            print(f"   ⚠️ Verify error: {e}")
            return False

    def _get_region_restriction(self, video_info):
        blocked = video_info.get("blocked_countries", [])
        allowed = video_info.get("allowed_countries", [])
        if blocked:
            return (
                {"regionRestriction": {"blocked": blocked}},
                f"{len(blocked)} countries blocked"
            )
        elif allowed:
            return (
                {"regionRestriction": {"allowed": allowed}},
                f"{len(allowed)} countries allowed"
            )
        return {}, "No restriction (worldwide)"

    def upload_video(self, video_info):
        video_file = video_info.get("video_file")
        if not video_file or not os.path.exists(video_file):
            print("❌ Video file not found")
            return None

        title = video_info.get("title", "Relaxing Video")
        desc  = video_info.get("description", (
            "🎵 Perfect for:\n"
            "✅ Deep Sleep\n"
            "✅ Relaxation\n"
            "✅ Study & Focus\n"
            "✅ Meditation\n\n"
            "👍 Like & Subscribe!\n"
            "🔔 Turn on notifications!\n\n"
            "#sleep #relaxing #meditation #study"
        ))

        restriction, region_desc = (
            self._get_region_restriction(video_info)
        )

        print(f"\n📤 Uploading to YouTube")
        print(f"   Target : {self.target_channel_id}")
        print(f"   Title  : {title}")
        print(f"   Region : {region_desc}")

        print(f"\n🔍 Verifying channel...")
        self._verify_channel()

        body = {
            "snippet": {
                "title"               : title,
                "description"         : desc,
                "tags"                : [
                    "sleep music",
                    "relaxing music",
                    "deep sleep",
                    "meditation",
                    "study music",
                    "rain sounds",
                    "white noise",
                    "stress relief",
                    "calm music",
                    "sleep aid",
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

        part = "snippet,status"
        if restriction:
            body["contentDetails"] = restriction
            part = "snippet,status,contentDetails"

        media = MediaFileUpload(
            video_file,
            mimetype  = "video/mp4",
            resumable = True
        )

        try:
            response = self.youtube.videos().insert(
                part       = part,
                body       = body,
                media_body = media
            ).execute()

            uploaded_id = response.get("id")
            print(f"\n✅ Uploaded! ID: {uploaded_id}")
            print(f"🔗 https://youtu.be/{uploaded_id}")

            # Set thumbnail
            thumb = video_info.get("thumbnail_file")
            if thumb and os.path.exists(thumb):
                try:
                    self.youtube.thumbnails().set(
                        videoId    = uploaded_id,
                        media_body = MediaFileUpload(
                            thumb,
                            mimetype = "image/jpeg"
                        )
                    ).execute()
                    print("🖼️ Thumbnail set!")
                except Exception as e:
                    print(f"⚠️ Thumbnail error: {e}")

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
