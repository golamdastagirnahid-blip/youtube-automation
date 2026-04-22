import os
import random
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from src.config import DEFAULT_PRIVACY, DEFAULT_CATEGORY, DEFAULT_LANGUAGE
from src.database import Database
from src.title_generator import TitleGenerator
from src.thumbnail_editor import ThumbnailEditor

class VideoUploader:
    def __init__(self, youtube, target_channel_id=None):
        self.youtube          = youtube
        self.target_channel_id = target_channel_id
        self.db               = Database()
        self.title_gen        = TitleGenerator()
        self.thumb_editor     = ThumbnailEditor()

    def upload_video(self, video_info):
        video_file = video_info.get("video_file")
        if not video_file or not os.path.exists(video_file):
            print("❌ Video file not found")
            return None

        video_id    = video_info.get("video_id")
        new_title   = self.title_gen.generate_title(video_info.get("title", "Video"))
        new_desc    = self.title_gen.generate_description(video_info.get("description", ""))

        print(f"📤 Uploading to @TekoGopal-o6f5f")
        print(f"   Title: {new_title}")

        body = {
            "snippet": {
                "title"               : new_title,
                "description"         : new_desc,
                "tags"                : ["viral", "trending", "entertainment"],
                "categoryId"          : DEFAULT_CATEGORY,
                "defaultLanguage"     : DEFAULT_LANGUAGE,
                "defaultAudioLanguage": DEFAULT_LANGUAGE,
            },
            "status": {
                "privacyStatus"          : DEFAULT_PRIVACY,
                "selfDeclaredMadeForKids": False,
            }
        }

        media = MediaFileUpload(
            video_file,
            mimetype  = "video/mp4",
            resumable = True
        )

        try:
            # ✅ Insert video to specific channel
            insert_request = self.youtube.videos().insert(
                part       = "snippet,status",
                body       = body,
                media_body = media
            )
            response    = insert_request.execute()
            uploaded_id = response.get("id")

            print(f"✅ Uploaded! ID: {uploaded_id}")
            print(f"🔗 https://youtu.be/{uploaded_id}")

            # Set thumbnail
            thumb = video_info.get("thumbnail_file")
            if thumb and os.path.exists(thumb):
                modified = self.thumb_editor.modify_thumbnail(thumb)
                if modified:
                    try:
                        media_thumb = MediaFileUpload(
                            modified, mimetype="image/jpeg"
                        )
                        self.youtube.thumbnails().set(
                            videoId    = uploaded_id,
                            media_body = media_thumb
                        ).execute()
                        print("🖼️ Thumbnail set!")
                    except HttpError as e:
                        print(f"⚠️ Thumbnail error: {e}")

            self.db.mark_video_uploaded(video_id, {"title": new_title})

            return {
                "success" : True,
                "video_id": uploaded_id,
                "url"     : f"https://youtu.be/{uploaded_id}"
            }

        except HttpError as e:
            print(f"❌ Upload failed: {e}")
            return None