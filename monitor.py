"""
Channel Monitor
Checks all source channels for new videos
Triggers upload workflow when new video found
"""

import os
import json
import time
import requests
import feedparser
from datetime import datetime


# ─────────────────────────────────────────────
# GitHub API Trigger
# ─────────────────────────────────────────────
def trigger_upload(video_id, video_url, video_title):
    """Trigger the upload workflow via GitHub API"""

    token = os.environ.get("GH_TOKEN")
    repo  = os.environ.get("GH_REPO")

    if not token or not repo:
        print("❌ GH_TOKEN or GH_REPO not set!")
        return False

    url     = f"https://api.github.com/repos/{repo}/dispatches"
    headers = {
        "Authorization": f"token {token}",
        "Accept"       : "application/vnd.github.v3+json",
        "Content-Type" : "application/json",
    }
    payload = {
        "event_type"    : "new_video_detected",
        "client_payload": {
            "video_id"    : video_id,
            "video_url"   : video_url,
            "video_title" : video_title,
            "video_privacy": "public",
        }
    }

    try:
        r = requests.post(
            url,
            headers = headers,
            data    = json.dumps(payload),
            timeout = 15
        )
        if r.status_code == 204:
            print(f"   ✅ Upload triggered for: {video_title}")
            return True
        else:
            print(f"   ❌ Trigger failed: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"   ❌ Trigger error: {e}")
        return False


# ─────────────────────────────────────────────
# Load Database
# ─────────────────────────────────────────────
def load_db():
    if os.path.exists("database.json"):
        try:
            with open("database.json") as f:
                return json.load(f)
        except Exception:
            pass
    return {"uploaded": {}}


# ─────────────────────────────────────────────
# Save Database
# ─────────────────────────────────────────────
def save_db(db):
    with open("database.json", "w") as f:
        json.dump(db, f, indent=2)


# ─────────────────────────────────────────────
# Is Video Already Processed
# ─────────────────────────────────────────────
def is_processed(db, video_id):
    return video_id in db.get("uploaded", {})


# ─────────────────────────────────────────────
# Mark Video As Queued
# ─────────────────────────────────────────────
def mark_queued(db, video_id, title):
    if "uploaded" not in db:
        db["uploaded"] = {}
    db["uploaded"][video_id] = {
        "title"  : title,
        "queued" : datetime.now().isoformat(),
        "status" : "queued"
    }


# ─────────────────────────────────────────────
# Check Single Channel RSS
# ─────────────────────────────────────────────
def check_channel(channel_id, db):
    url = (
        f"https://www.youtube.com/feeds/videos.xml"
        f"?channel_id={channel_id}"
    )
    try:
        feed      = feedparser.parse(url)
        new_found = []

        for entry in feed.entries[:3]:
            vid_id = entry.get("yt_videoid", "")
            if not vid_id:
                link = entry.get("link", "")
                if "v=" in link:
                    vid_id = link.split("v=")[1].split("&")[0]

            if not vid_id:
                continue

            title = entry.get("title", "Unknown")

            if is_processed(db, vid_id):
                continue

            new_found.append({
                "video_id": vid_id,
                "title"   : title,
                "url"     : (
                    f"https://www.youtube.com"
                    f"/watch?v={vid_id}"
                ),
            })

        return new_found

    except Exception as e:
        print(f"   ⚠️ RSS error {channel_id}: {e}")
        return []


# ─────────────────────────────────────────────
# Load Channels
# ─────────────────────────────────────────────
def load_channels():
    channels = []
    if os.path.exists("channels.txt"):
        with open("channels.txt") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    channels.append(line)
    return channels


# ─────────────────────────────────────────────
# Main Monitor Function
# ─────────────────────────────────────────────
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🔍 Channel Monitor Started: {now}")
    print("=" * 50)

    # Load channels
    channels = load_channels()
    if not channels:
        print("❌ No channels in channels.txt!")
        return

    print(f"📋 Monitoring {len(channels)} channels")

    # Load database
    db = load_db()

    # Check all channels
    all_new    = []
    triggered  = 0

    for i, channel_id in enumerate(channels, 1):
        print(f"\n[{i}/{len(channels)}] Checking: {channel_id}")

        new_videos = check_channel(channel_id, db)

        if new_videos:
            print(f"   🆕 Found {len(new_videos)} new video(s)!")
            all_new.extend(new_videos)
        else:
            print(f"   ✅ No new videos")

        # Small delay between channels
        time.sleep(1)

    # Trigger uploads for new videos
    if all_new:
        print(f"\n{'='*50}")
        print(f"🚀 Triggering uploads for {len(all_new)} videos...")

        for video in all_new:
            print(f"\n📹 {video['title']}")
            print(f"   ID: {video['video_id']}")

            # Trigger upload workflow
            success = trigger_upload(
                video_id    = video["video_id"],
                video_url   = video["url"],
                video_title = video["title"],
            )

            if success:
                # Mark as queued in database
                mark_queued(db, video["video_id"], video["title"])
                triggered += 1

            # Wait between triggers
            time.sleep(5)

        # Save updated database
        save_db(db)

    else:
        print(f"\n✅ No new videos found across all channels")

    print(f"\n{'='*50}")
    print(f"📊 Summary:")
    print(f"   Channels checked : {len(channels)}")
    print(f"   New videos found : {len(all_new)}")
    print(f"   Uploads triggered: {triggered}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
