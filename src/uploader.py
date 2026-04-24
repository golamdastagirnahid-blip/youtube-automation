import os
from googleapiclient.http    import MediaFileUpload
from googleapiclient.errors  import HttpError
from src.config              import (
    DEFAULT_PRIVACY, DEFAULT_CATEGORY,
    DEFAULT_LANGUAGE
)
from src.database            import Database
from src.title_generator     import TitleGenerator
from src.thumbnail_generator import ThumbnailGenerator as ThumbnailEditor


class VideoUploader:

    def __init__(self, youtube, target_channel_id=None):
        self.youtube           = youtube
        self.target_channel_id = target_channel_id
        self.db                = Database()
        self.title_gen         = TitleGenerator()
        self.thumb_editor      = ThumbnailEditor()

    # ─────────────────────────────────────────────
    # Verify Correct Channel
    # ─────────────────────────────────────────────
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
                    ch_name = item.get("snippet", {}).get("title", "")
                    print(f"   📺 Uploading to: {ch_name} ({ch_id})")
                    if ch_id == self.target_channel_id:
                        print(f"   ✅ Correct channel confirmed!")
                        return True
                print(f"   ⚠️ Channel mismatch!")
                return False
        except Exception as e:
            print(f"   ⚠️ Channel verify error: {e}")
            return False

    # ─────────────────────────────────────────────
    # Get Full Region Restriction from Source
    # ─────────────────────────────────────────────
    def _get_region_restriction(self, video_info):
        """
        Copy exact same region restriction as source video.
        Returns (restriction_dict, description_string)
        """
        blocked_countries = video_info.get("blocked_countries", [])
        allowed_countries = video_info.get("allowed_countries", [])

        restriction  = {}
        description  = "None"

        if blocked_countries and len(blocked_countries) > 0:
            # Source has BLOCKED countries list
            # → Block same countries in our upload
            restriction = {
                "regionRestriction": {
                    "blocked": blocked_countries
                }
            }
            description = (
                f"{len(blocked_countries)} countries blocked "
                f"(same as source)"
            )

        elif allowed_countries and len(allowed_countries) > 0:
            # Source has ALLOWED countries list
            # → Allow only same countries in our upload
            restriction = {
                "regionRestriction": {
                    "allowed": allowed_countries
                }
            }
            description = (
                f"Only {len(allowed_countries)} countries allowed "
                f"(same as source)"
            )

        else:
            # No restriction on source
            # → No restriction on our upload
            restriction  = {}
            description  = "No restriction (available worldwide)"

        return restriction, description

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

        # ── Get exact region restriction ───────────
        region_restriction, region_desc = self._get_region_restriction(
            video_info
        )

        print(f"\n📤 Uploading to YouTube")
        print(f"   Target  : {self.target_channel_id}")
        print(f"   Title   : {new_title}")
        print(f"   Region  : {region_desc}")

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

        # ── Add region restriction if exists ───────
        part = "snippet,status"
        if region_restriction:
            body["contentDetails"] = region_restriction
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
            print(f"\n✅ Uploaded! ID: {uploaded_id}")
            print(f"🔗 https://youtu.be/{uploaded_id}")

            # ── Verify upload channel ──────────────
            try:
                vid_response = self.youtube.videos().list(
                    part = "snippet",
                    id   = uploaded_id
                ).execute()
                vid_items = vid_response.get("items", [])
                if vid_items:
                    actual_channel = vid_items[0].get(
                        "snippet", {}
                    ).get("channelId", "")
                    if actual_channel == self.target_channel_id:
                        print(f"✅ Uploaded to correct channel!")
                    else:
                        print(f"⚠️ Wrong channel!")
                        print(f"   Expected : {self.target_channel_id}")
                        print(f"   Got      : {actual_channel}")
            except Exception:
                pass

            # ── Set thumbnail ──────────────────────
            thumb = video_info.get("thumbnail_file")
            if thumb and os.path.exists(thumb):
                modified = self.thumb_editor.modify_thumbnail(thumb)
                target   = modified if modified else thumb
                if target and os.path.exists(target):
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
                "title"             : new_title,
                "channel_id"        : self.target_channel_id,
                "youtube_id"        : uploaded_id,
                "region_restriction": region_desc,
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
