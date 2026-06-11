#!/usr/bin/env python3
"""
AGENT 4 — THE PUBLISHER
Handles YouTube scheduling and posting after your approval.
Triggered when you approve a video in the dashboard.
"""

import json
import os
import datetime
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
QUEUE_FILE = BASE_DIR / "config" / "queue.json"

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# Optimal posting times per channel (Dubai time, UTC+4)
POSTING_SCHEDULE = {
    "dark_psychology": {"days": [0,1,2,3,4], "hour": 19, "minute": 0},   # Mon-Fri 7pm
    "space_universe":  {"days": [0,1,2,3,4], "hour": 20, "minute": 0},   # Mon-Fri 8pm
    "dark_history":    {"days": [0,1,2,3,4], "hour": 19, "minute": 30},  # Mon-Fri 7:30pm
    "true_crime":      {"days": [0,1,2,3,4], "hour": 20, "minute": 30},  # Mon-Fri 8:30pm
}


def load_queue():
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE) as f:
            return json.load(f)
    return []


def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


def calculate_next_post_time(channel_id):
    """Calculate the next optimal posting time for a channel."""
    schedule = POSTING_SCHEDULE.get(channel_id, {"days": [0,1,2,3,4], "hour": 19, "minute": 0})
    now = datetime.datetime.now()

    for days_ahead in range(8):
        candidate = now + datetime.timedelta(days=days_ahead)
        if candidate.weekday() in schedule["days"]:
            post_time = candidate.replace(
                hour=schedule["hour"],
                minute=schedule["minute"],
                second=0, microsecond=0
            )
            if post_time > now + datetime.timedelta(minutes=30):
                return post_time.isoformat()

    # Fallback: tomorrow same time
    tomorrow = now + datetime.timedelta(days=1)
    return tomorrow.replace(hour=19, minute=0, second=0).isoformat()


def schedule_video(video_id):
    """Schedule an approved video for posting."""
    queue = load_queue()
    item = next((q for q in queue if q["id"] == video_id), None)

    if not item:
        return {"success": False, "error": "Video not found"}

    script_file = Path(item["file"])
    if not script_file.exists():
        return {"success": False, "error": "Script file not found"}

    with open(script_file) as f:
        video_data = json.load(f)

    # Calculate posting time
    post_time = calculate_next_post_time(item["channel"])

    # Update records
    video_data["status"] = "scheduled"
    video_data["scheduled_time"] = post_time
    with open(script_file, "w") as f:
        json.dump(video_data, f, indent=2)

    for q in queue:
        if q["id"] == video_id:
            q["status"] = "scheduled"
            q["scheduled_time"] = post_time
            break

    save_queue(queue)

    print(f"  📅  Scheduled: {item['title']}")
    print(f"  🕐  Post time: {post_time}")

    return {
        "success": True,
        "scheduled_time": post_time,
        "channel": item["channel_name"],
        "title": item.get("title", "")
    }


def reject_video(video_id, reason=""):
    """Mark a video as rejected."""
    queue = load_queue()

    script_file = None
    for item in queue:
        if item["id"] == video_id:
            script_file = Path(item["file"])
            item["status"] = "rejected"
            item["rejected_at"] = datetime.datetime.now().isoformat()
            item["rejection_reason"] = reason
            break

    if script_file and script_file.exists():
        with open(script_file) as f:
            video_data = json.load(f)
        video_data["status"] = "rejected"
        video_data["rejection_reason"] = reason
        with open(script_file, "w") as f:
            json.dump(video_data, f, indent=2)

    save_queue(queue)
    return {"success": True, "message": "Video rejected — new script will be generated"}


def approve_for_voice(video_id):
    """Move approved script to voice generation queue."""
    queue = load_queue()

    for item in queue:
        if item["id"] == video_id:
            item["status"] = "approved_for_voice"
            item["approved_at"] = datetime.datetime.now().isoformat()
            break

    script_file = None
    for item in queue:
        if item["id"] == video_id:
            script_file = Path(item["file"])
            break

    if script_file and script_file.exists():
        with open(script_file) as f:
            video_data = json.load(f)
        video_data["status"] = "approved_for_voice"
        with open(script_file, "w") as f:
            json.dump(video_data, f, indent=2)

    save_queue(queue)
    return {"success": True, "message": "Approved! Voice generation queued."}


def get_publishing_stats():
    """Get overview stats for the dashboard."""
    queue = load_queue()

    stats = {
        "total": len(queue),
        "pending_review": len([q for q in queue if q["status"] == "pending_review"]),
        "approved": len([q for q in queue if q["status"] == "approved_for_voice"]),
        "voice_ready": len([q for q in queue if q["status"] == "voice_ready"]),
        "ready_to_publish": len([q for q in queue if q["status"] == "ready_to_publish"]),
        "scheduled": len([q for q in queue if q["status"] == "scheduled"]),
        "published": len([q for q in queue if q["status"] == "published"]),
        "rejected": len([q for q in queue if q["status"] == "rejected"]),
        "by_channel": {}
    }

    for channel_id in ["dark_psychology", "space_universe", "dark_history", "true_crime"]:
        channel_items = [q for q in queue if q["channel"] == channel_id]
        stats["by_channel"][channel_id] = {
            "total": len(channel_items),
            "scheduled": len([q for q in channel_items if q["status"] == "scheduled"]),
            "published": len([q for q in channel_items if q["status"] == "published"])
        }

    return stats


if __name__ == "__main__":
    print("Agent 4 — Publisher")
    print("This agent is called by the dashboard when you approve/reject videos.")
    stats = get_publishing_stats()
    print(json.dumps(stats, indent=2))
