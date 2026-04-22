import json
import os
from datetime import datetime
from src.config import DATABASE_FILE

class Database:
    def __init__(self):
        self.db_file = DATABASE_FILE
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, "r") as f: return json.load(f)
        return {"uploaded_videos": [], "daily_counts": {}, "statistics": {"total_uploads": 0}}

    def save(self):
        with open(self.db_file, "w") as f: json.dump(self.data, f, indent=4)

    def is_video_uploaded(self, video_id):
        return video_id in self.data["uploaded_videos"]

    def mark_video_uploaded(self, video_id, info):
        if video_id not in self.data["uploaded_videos"]:
            self.data["uploaded_videos"].append(video_id)
            self.data["statistics"]["total_uploads"] += 1
            today = datetime.now().strftime("%Y-%m-%d")
            self.data["daily_counts"][today] = self.data["daily_counts"].get(today, 0) + 1
            self.save()

    def get_daily_upload_count(self):
        return self.data["daily_counts"].get(datetime.now().strftime("%Y-%m-%d"), 0)

    def get_statistics(self):
        return self.data["statistics"]