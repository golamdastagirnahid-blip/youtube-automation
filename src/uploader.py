import os
import random
from googleapiclient.http import MediaFileUpload
from src.config import DEFAULT_PRIVACY, DEFAULT_CATEGORY, DEFAULT_LANGUAGE
from src.database import Database
from src.title_generator import TitleGenerator
from src.thumbnail_editor import ThumbnailEditor

class VideoUploader:
    def __init__(self, youtube):
        self.youtube = youtube
        self.db = Database()
        self.title_gen = TitleGenerator()
        self.thumb_editor = ThumbnailEditor()

    def upload_video(self, video_info):
        video_file = video_info.get("video_file")
        if not video_file or not os.path.exists(video_file):
            print("❌ Video file not found")
            return None

        video_id = video_info.get("video_id")
        new_title = self.title_gen.generate_title(video_info.get("title", "Video"))
        new_description = self.title_gen.generate_description(video_info.get("description", ""))

        print(f"📤 Uploading: {new_title}")

        body = {
            "snippet": {
                "title": new_title,
                "description": new_description,
                "tags": ["viral", "trending"],
                "categoryId": DEFAULT_CATEGORY,
                "defaultLanguage": DEFAULT_LANGUAGE,
            },
            "status": {
                "privacyStatus": DEFAULT_PRIVACY,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_file, mimetype="video/mp4", resumable=True)

        try:
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            response = request.execute()
            uploaded_id = response.get("id")

            print(f"✅ Successfully uploaded! Video ID: {uploaded_id}")
            print(f"🔗 https://youtu.be/{uploaded_id}")

            # Set thumbnail
            thumb = video_info.get("thumbnail_file")
            if thumb and os.path.exists(thumb):
                modified_thumb = self.thumb_editor.modify_thumbnail(thumb)
                if modified_thumb:
                    media_thumb = MediaFileUpload(modified_thumb, mimetype='image/jpeg')
                    self.youtube.thumbnails().set(videoId=uploaded_id, media_body=media_thumb).execute()

            self.db.mark_video_uploaded(video_id, {"title": new_title})
            return {"success": True, "video_id": uploaded_id}

        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None