import os
from googleapiclient.http    import MediaFileUpload
from googleapiclient.errors  import HttpError
from src.config              import (
    DEFAULT_PRIVACY, DEFAULT_CATEGORY,
    DEFAULT_LANGUAGE
)
from src.database            import Database
from src.title_generator     import TitleGenerator
from src.thumbnail_editor    import ThumbnailEditor


class VideoUploader:

    def __init__(self, youtube, target_channel_id=None):
        self.youtube           = youtube
        self.target_channel_id = target_channel_id
        self.db                = Database()
        self.title_gen         = TitleGenerator()
        self.thumb_editor      = ThumbnailEditor()

    # ─────────────────────────────────────────────
    # Verify We Are On Correct Channel
    # ─────────────────────────────────────────────
    def _verify_channel(self):
        """Check which channel the token is linked to"""
        try:
            response = self.youtube.channels().list(
                part = "snippet",
                mine = True
            ).execute()

            items = response.get("items", [])
            if items:
                for item in items:
                    ch_id   = item.get("id", "")
                    ch_name = item.get("snippet", {}).get("title", "")
                    print(f"   📺 Token channel: {ch_name} ({ch_id})")

                    if ch_id == self.target_channel_id:
                        print(f"   ✅ Correct channel confirmed!")
                        return True

                print(f"   ⚠️ Token is linked to different channel!")
                print(f"   ⚠️ Target: {self.target_channel_id}")
                return False
            return False
        except Exception as e:
            print(f"   ⚠️ Channel verify error: {e}")
            return False

    # ─────────────────────────────────────────────
    # Main Upload Function
    # ─────────────────────────────────────────────
    def upload_video(self, video_info):
        video_file = video_info.get("video_file")
        if not video_file or not os.path.exists(video_file):
            print("❌ Video file not found")
            return None

        video_id  = video_info.get("video_id")
        new_title = self.title_gen.generate_title(
            video_info.get("title", "Video")
        )
        new_desc  = self.title_gen.generate_description(
            video_info.get("description", "")
        )

        blocked_countries = video_info.get("blocked_countries", [])

        print(f"\n📤 Uploading to YouTube")
        print(f"   Target  : {self.target_channel_id}")
        print(f"   Title   : {new_title}")

        if blocked_countries:
            print(f"   Blocking: {len(blocked_countries)} countries")
        else:
            print(f"   Blocking: None")

        # ── Verify correct channel ─────────────────
        print(f"\n🔍 Verifying channel...")
        self._verify_channel()

        # ── Build request body ─────────────────────
        body = {
            "snippet": {
                "title"               : new_title,
                "description"         : new_desc,
                "tags"                : [
                    "viral",
                    "trending",
                    "entertainment"
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

        # ── Add country restrictions ───────────────
        if blocked_countries:
            body["contentDetails"] = {
                "regionRestriction": {
                    "blocked": blocked_countries
                }
            }
            part = "snippet,status,contentDetails"

        # ── Upload video ───────────────────────────
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
            print(f"✅ Uploaded! ID: {uploaded_id}")
            print(f"🔗 https://youtu.be/{uploaded_id}")

            # ── Move to correct channel if needed ──
            if self.target_channel_id:
                try:
                    # Check if uploaded to correct channel
                    vid_response = self.youtube.videos().list(
                        part = "snippet",
                        id   = uploaded_id
                    ).execute()

                    vid_items = vid_response.get("items", [])
                    if vid_items:
                        actual_channel = vid_items[0].get(
                            "snippet", {}
                        ).get("channelId", "")

                        print(f"   📺 Uploaded to channel: {actual_channel}")

                        if actual_channel != self.target_channel_id:
                            print(f"   ⚠️ Wrong channel detected!")
                            print(f"   ⚠️ Expected : {self.target_channel_id}")
                            print(f"   ⚠️ Got      : {actual_channel}")
                        else:
                            print(f"   ✅ Correct channel confirmed!")

                except Exception as e:
                    print(f"   ⚠️ Channel check error: {e}")

            # ── Set thumbnail ──────────────────────
            thumb = video_info.get("thumbnail_file")
            if thumb and os.path.exists(thumb):
                modified = self.thumb_editor.modify_thumbnail(thumb)
                target   = modified if modified else thumb
                if os.path.exists(target):
                    try:
                        self.youtube.thumbnails().set(
                            videoId    = uploaded_id,
                            media_body = MediaFileUpload(
                                target,
                                mimetype = "image/jpeg"
                            )
                        ).execute()
                        print("🖼️ Thumbnail set!")
                    except Exception as e:
                        print(f"⚠️ Thumbnail error: {e}")

            # ── Save to database ───────────────────
            self.db.mark_video_uploaded(video_id, {
                "title"     : new_title,
                "channel_id": self.target_channel_id,
                "youtube_id": uploaded_id,
            })

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
