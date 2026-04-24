"""
Database Manager
Handles all video tracking and statistics
"""

import json
import os
from datetime import datetime
from src.config import DATABASE_FILE


class Database:

    def __init__(self):
        self.db_file = DATABASE_FILE
        self.data    = self._load()

    # ─────────────────────────────────────────
    # Load Database
    # ─────────────────────────────────────────
    def _load(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r") as f:
                    data = json.load(f)
                    # ── Ensure all keys exist ──
                    if "uploaded_videos" not in data:
                        data["uploaded_videos"] = []
                    if "daily_counts" not in data:
                        data["daily_counts"] = {}
                    if "statistics" not in data:
                        data["statistics"] = {
                            "total_uploads": 0
                        }
                    if "queued" not in data:
                        data["queued"] = []
                    return data
            except Exception:
                pass

        return {
            "uploaded_videos": [],
            "daily_counts"   : {},
            "statistics"     : {
                "total_uploads": 0
            },
            "queued"         : [],
        }

    # ─────────────────────────────────────────
    # Save Database
    # ─────────────────────────────────────────
    def save(self):
        with open(self.db_file, "w") as f:
            json.dump(self.data, f, indent=4)

    # ─────────────────────────────────────────
    # Check If Video Already Uploaded
    # ─────────────────────────────────────────
    def is_video_uploaded(self, video_id):
        return video_id in self.data.get(
            "uploaded_videos", []
        )

    # ─────────────────────────────────────────
    # Mark Video As Uploaded
    # ─────────────────────────────────────────
    def mark_video_uploaded(self, video_id, info={}):
        if video_id not in self.data["uploaded_videos"]:
            self.data["uploaded_videos"].append(video_id)
            self.data["statistics"]["total_uploads"] += 1

            today = datetime.now().strftime("%Y-%m-%d")
            self.data["daily_counts"][today] = (
                self.data["daily_counts"].get(today, 0) + 1
            )
            self.save()

    # ─────────────────────────────────────────
    # Get Daily Upload Count
    # ─────────────────────────────────────────
    def get_daily_upload_count(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.data["daily_counts"].get(today, 0)

    # ─────────────────────────────────────────
    # Get Statistics
    # ─────────────────────────────────────────
    def get_statistics(self):
        return self.data.get("statistics", {
            "total_uploads": 0
        })

    # ─────────────────────────────────────────
    # Queue Management
    # ─────────────────────────────────────────
    def add_to_queue(self, video):
        if "queued" not in self.data:
            self.data["queued"] = []
        self.data["queued"].append({
            "video_id" : video["video_id"],
            "title"    : video["title"],
            "url"      : video["url"],
            "queued_at": datetime.now().isoformat(),
        })
        self.save()

    def get_queue(self):
        return self.data.get("queued", [])

    def remove_from_queue(self, video_id):
        self.data["queued"] = [
            q for q in self.data.get("queued", [])
            if q.get("video_id") != video_id
        ]
        self.save()

    def is_queued(self, video_id):
        for q in self.data.get("queued", []):
            if q.get("video_id") == video_id:
                return True
        return False
