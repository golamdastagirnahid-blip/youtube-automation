"""
Channel Monitor
Checks all source channels for new videos
Triggers ONE upload at a time to prevent overload
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
            print(f"   ✅ Upload triggered: {video_title[:50]}")
            return True
        else:
            print(f"   ❌ Trigger failed: {r.status_code}")
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

    url     = (
        f"https://api.github.com/repos/{repo}"
        f"/actions/runs?status=in_progress"
    )
    headers = {
        "Authorization": f"token {token}",
        "Accept"       : "application/vnd.github.v3+json",
    }

    try:
        r    = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        runs = data.get("workflow_runs", [])

        for run in runs:
            name = run.get("name", "")
            if "Video Upload" in name or \
               "automation" in name.lower():
                print(
                    f"   ⚠️ Upload already running: {name}"
                )
                return True

        return False

    except Exception as e:
        print(f"   ⚠️ Could not check running jobs: {e}")
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
    return {"uploaded": {}, "queued": []}


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
    # Check uploaded
    if video_id in db.get("uploaded", {}):
        return True
    # Check queued
    queued = db.get("queued", [])
    for q in queued:
        if q.get("video_id") == video_id:
            return True
    return False


# ─────────────────────────────────────────────
# Add To Queue
# ─────────────────────────────────────────────
def add_to_queue(db, video):
    if "queued" not in db:
        db["queued"] = []
    db["queued"].append({
        "video_id"  : video["video_id"],
        "title"     : video["title"],
        "url"       : video["url"],
        "queued_at" : datetime.now().isoformat(),
    })


# ─────────────────────────────────────────────
# Get Next From Queue
# ─────────────────────────────────────────────
def get_next_from_queue(db):
    queued = db.get("queued", [])
    if queued:
        return queued[0]
    return None


# ─────────────────────────────────────────────
# Remove From Queue
# ─────────────────────────────────────────────
def remove_from_queue(db, video_id):
    queued = db.get("queued", [])
    db["queued"] = [
        q for q in queued
        if q.get("video_id") != video_id
    ]


# ─────────────────────────────────────────────
# Mark As Triggered
# ─────────────────────────────────────────────
def mark_triggered(db, video_id, title):
    if "uploaded" not in db:
        db["uploaded"] = {}
    db["uploaded"][video_id] = {
        "title"      : title,
        "triggered_at": datetime.now().isoformat(),
        "status"     : "triggered"
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
    print(f"🔍 Channel Monitor: {now}")
    print("=" * 50)

    # Load channels and database
    channels = load_channels()
    if not channels:
        print("❌ No channels in channels.txt!")
        return

    db = load_db()

    print(f"📋 Monitoring {len(channels)} channels")
    print(
        f"📦 Queue size: "
        f"{len(db.get('queued', []))} videos"
    )

    # ── Check if upload is already running ────
    print(f"\n🔍 Checking if upload is running...")
    if is_upload_running():
        print(
            f"⏳ Upload job is running — "
            f"will check queue next time"
        )
        # Still scan channels to add to queue
        # but don't trigger new upload
        should_trigger = False
    else:
        print(f"✅ No upload running — ready to trigger")
        should_trigger = True

    # ── Check all channels for new videos ─────
    print(f"\n🔍 Scanning all channels...")
    all_new = []

    for i, channel_id in enumerate(channels, 1):
        print(f"   [{i}/{len(channels)}] {channel_id}")
        new_videos = check_channel(channel_id, db)

        if new_videos:
            print(
                f"   🆕 Found {len(new_videos)} "
                f"new video(s)"
            )
            for video in new_videos:
                # Add to queue if not already there
                if not is_processed(db, video["video_id"]):
                    add_to_queue(db, video)
                    all_new.append(video)
                    print(f"   📥 Queued: {video['title'][:40]}")
        else:
            print(f"   ✅ No new videos")

        time.sleep(1)

    # ── Save queue to database ─────────────────
    save_db(db)

    # ── Trigger ONE video if ready ─────────────
    print(f"\n{'='*50}")
    queue_size = len(db.get("queued", []))
    print(f"📦 Total queue: {queue_size} videos")

    if should_trigger and queue_size > 0:
        # Get next video from queue
        next_video = get_next_from_queue(db)

        if next_video:
            print(f"\n🚀 Triggering next video:")
            print(f"   Title: {next_video['title'][:50]}")
            print(f"   ID   : {next_video['video_id']}")

            success = trigger_upload(
                video_id    = next_video["video_id"],
                video_url   = next_video["url"],
                video_title = next_video["title"],
            )

            if success:
                # Remove from queue
                remove_from_queue(db, next_video["video_id"])
                # Mark as triggered
                mark_triggered(
                    db,
                    next_video["video_id"],
                    next_video["title"]
                )
                # Save updated database
                save_db(db)
                print(f"   ✅ Triggered successfully!")
            else:
                print(f"   ❌ Trigger failed")

    elif not should_trigger:
        print(
            f"\n⏳ Upload running — "
            f"{queue_size} videos waiting in queue"
        )
    else:
        print(f"\n✅ Queue is empty — nothing to trigger")

    # ── Final Summary ──────────────────────────
    print(f"\n{'='*50}")
    print(f"📊 Summary:")
    print(f"   Channels scanned : {len(channels)}")
    print(f"   New videos found : {len(all_new)}")
    print(
        f"   Queue size       : "
        f"{len(db.get('queued', []))}"
    )
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
