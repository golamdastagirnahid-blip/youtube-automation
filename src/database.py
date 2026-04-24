"""
Channel Monitor
Checks all source channels for new videos
Triggers ONE upload at a time to prevent overload
Uses same database structure as src/database.py
"""

import os
import json
import time
import requests
import feedparser
from datetime import datetime


# ─────────────────────────────────────────────
# Database Functions (matches src/database.py)
# ─────────────────────────────────────────────
DB_FILE = "database.json"

def load_db():
    """Load database - same structure as src/database.py"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "uploaded_videos": [],
        "daily_counts"   : {},
        "statistics"     : {"total_uploads": 0},
        "queued"         : [],
    }


def save_db(db):
    """Save database"""
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)


def is_processed(db, video_id):
    """Check if video already uploaded or queued"""
    # Check uploaded list
    if video_id in db.get("uploaded_videos", []):
        return True
    # Check queue
    for q in db.get("queued", []):
        if q.get("video_id") == video_id:
            return True
    return False


def add_to_queue(db, video):
    """Add video to queue"""
    if "queued" not in db:
        db["queued"] = []
    db["queued"].append({
        "video_id" : video["video_id"],
        "title"    : video["title"],
        "url"      : video["url"],
        "queued_at": datetime.now().isoformat(),
    })


def get_next_from_queue(db):
    """Get next video from queue"""
    queued = db.get("queued", [])
    if queued:
        return queued[0]
    return None


def remove_from_queue(db, video_id):
    """Remove video from queue"""
    db["queued"] = [
        q for q in db.get("queued", [])
        if q.get("video_id") != video_id
    ]


def mark_triggered(db, video_id, title):
    """Mark video as triggered in uploaded_videos"""
    if video_id not in db.get("uploaded_videos", []):
        db["uploaded_videos"].append(video_id)


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

    url     = (
        f"https://api.github.com"
        f"/repos/{repo}/dispatches"
    )
    headers = {
        "Authorization": f"token {token}",
        "Accept"       : "application/vnd.github.v3+json",
        "Content-Type" : "application/json",
    }
    payload = {
        "event_type"    : "new_video_detected",
        "client_payload": {
            "video_id"     : video_id,
            "video_url"    : video_url,
            "video_title"  : video_title,
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
            print(
                f"   ✅ Triggered: "
                f"{video_title[:50]}"
            )
            return True
        else:
            print(
                f"   ❌ Trigger failed: "
                f"{r.status_code} - {r.text}"
            )
            return False
    except Exception as e:
        print(f"   ❌ Trigger error: {e}")
        return False


# ─────────────────────────────────────────────
# Check If Upload Job Is Already Running
# ─────────────────────────────────────────────
def is_upload_running():
    """Check if automation.yml is currently running"""

    token = os.environ.get("GH_TOKEN")
    repo  = os.environ.get("GH_REPO")

    if not token or not repo:
        return False

    url = (
        f"https://api.github.com"
        f"/repos/{repo}/actions/runs"
        f"?status=in_progress"
    )
    headers = {
        "Authorization": f"token {token}",
        "Accept"       : "application/vnd.github.v3+json",
    }

    try:
        r    = requests.get(
            url,
            headers = headers,
            timeout = 10
        )
        data = r.json()
        runs = data.get("workflow_runs", [])

        for run in runs:
            name = run.get("name", "").lower()
            if "video upload" in name or \
               "automation"   in name:
                print(
                    f"   ⚠️ Upload running: "
                    f"{run.get('name')}"
                )
                return True

        return False

    except Exception as e:
        print(f"   ⚠️ Could not check jobs: {e}")
        return False


# ─────────────────────────────────────────────
# Check Single Channel RSS
# ─────────────────────────────────────────────
def check_channel(channel_id, db):
    """Check RSS feed for new videos"""
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
                    vid_id = (
                        link.split("v=")[1]
                            .split("&")[0]
                    )

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
    """Load channel IDs from channels.txt"""
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
    print(f"🔍 Channel Monitor: {now}")
    print("=" * 50)

    # Load channels
    channels = load_channels()
    if not channels:
        print("❌ No channels in channels.txt!")
        return

    # Load database
    db         = load_db()
    queue_size = len(db.get("queued", []))

    print(f"📋 Channels  : {len(channels)}")
    print(f"📦 Queue     : {queue_size} videos waiting")
    print(
        f"✅ Uploaded  : "
        f"{len(db.get('uploaded_videos', []))} videos"
    )

    # ── Check if upload already running ───────
    print(f"\n🔍 Checking upload status...")
    upload_running = is_upload_running()

    if upload_running:
        print(f"   ⏳ Upload job is running")
        should_trigger = False
    else:
        print(f"   ✅ No upload running")
        should_trigger = True

    # ── Scan all channels ──────────────────────
    print(f"\n🔍 Scanning {len(channels)} channels...")
    all_new = []

    for i, channel_id in enumerate(channels, 1):
        print(f"   [{i}/{len(channels)}] {channel_id}")
        new_videos = check_channel(channel_id, db)

        if new_videos:
            for video in new_videos:
                add_to_queue(db, video)
                all_new.append(video)
                print(
                    f"      🆕 {video['title'][:45]}"
                )
        else:
            print(f"      ✅ No new videos")

        time.sleep(1)

    # Save after scanning
    save_db(db)

    # ── Trigger ONE video from queue ───────────
    print(f"\n{'='*50}")
    queue_size = len(db.get("queued", []))
    print(f"📦 Queue size: {queue_size} videos")

    if should_trigger and queue_size > 0:
        next_video = get_next_from_queue(db)

        if next_video:
            print(f"\n🚀 Triggering next video:")
            print(
                f"   Title: "
                f"{next_video['title'][:50]}"
            )
            print(f"   ID   : {next_video['video_id']}")

            success = trigger_upload(
                video_id    = next_video["video_id"],
                video_url   = next_video["url"],
                video_title = next_video["title"],
            )

            if success:
                remove_from_queue(
                    db,
                    next_video["video_id"]
                )
                mark_triggered(
                    db,
                    next_video["video_id"],
                    next_video["title"]
                )
                save_db(db)
                print(f"   ✅ Done!")

    elif not should_trigger:
        print(
            f"\n⏳ Waiting — "
            f"{queue_size} videos in queue"
        )
    else:
        print(f"\n✅ Queue empty — nothing to trigger")

    # ── Summary ────────────────────────────────
    print(f"\n{'='*50}")
    print(f"📊 Summary:")
    print(f"   Channels scanned : {len(channels)}")
    print(f"   New videos found : {len(all_new)}")
    print(
        f"   Queue remaining  : "
        f"{len(db.get('queued', []))}"
    )
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
