#!/usr/bin/env python3
"""
AGENT 2 — THE VOICE
Generates narration using ElevenLabs API.
Voice: Rudra
Triggered after Agent 1 completes and scripts are approved.
"""

import json
import os
import urllib.request
import urllib.error
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
QUEUE_FILE = BASE_DIR / "config" / "queue.json"

# ── ElevenLabs Config ─────────────────────────────────────────────────────────
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
VOICE_NAME = "Rudra"
VOICE_ID = None  # Auto-fetched from API using voice name

# Voice settings — calm, soothing, documentary style
VOICE_SETTINGS = {
    "stability": 0.55,           # Consistent, not robotic
    "similarity_boost": 0.75,    # Clear and natural
    "style": 0.35,               # Slight expressiveness
    "use_speaker_boost": True    # Richer, warmer sound
}

# Model — best quality for long-form narration
MODEL_ID = "eleven_multilingual_v2"


def load_queue():
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE) as f:
            return json.load(f)
    return []


def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


def get_voice_id(api_key, voice_name):
    """Fetch Rudra's voice ID from ElevenLabs."""
    url = "https://api.elevenlabs.io/v1/voices"
    req = urllib.request.Request(
        url,
        headers={"xi-api-key": api_key, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            voices = data.get("voices", [])
            for v in voices:
                if v["name"].lower() == voice_name.lower():
                    print(f"  ✅  Found voice: {v['name']} (ID: {v['voice_id']})")
                    return v["voice_id"]
            # If exact match not found, show available voices
            print(f"  ⚠️  Voice '{voice_name}' not found. Available voices:")
            for v in voices[:10]:
                print(f"      - {v['name']}")
            return None
    except Exception as e:
        print(f"  ❌  Could not fetch voices: {e}")
        return None


def generate_voice(script_text, output_path, voice_id, api_key):
    """Generate voice narration using ElevenLabs API."""

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    payload = json.dumps({
        "text": script_text,
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            audio_data = resp.read()
            with open(output_path, "wb") as f:
                f.write(audio_data)
            size_kb = len(audio_data) / 1024
            print(f"  ✅  Voice generated: {output_path.name} ({size_kb:.0f} KB)")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if "quota_exceeded" in error_body or "free" in error_body.lower():
            print("  ⚠️  Free plan limit reached — upgrade to Starter ($5/month) for commercial use")
        else:
            print(f"  ❌  ElevenLabs error {e.code}: {error_body[:200]}")
        return False
    except Exception as e:
        print(f"  ❌  Voice generation failed: {e}")
        return False


def check_quota(api_key):
    """Check remaining character quota."""
    url = "https://api.elevenlabs.io/v1/user/subscription"
    req = urllib.request.Request(
        url,
        headers={"xi-api-key": api_key}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 10000)
            remaining = limit - used
            plan = data.get("tier", "free")
            print(f"  📊  ElevenLabs quota: {remaining:,} chars remaining ({used:,}/{limit:,}) — Plan: {plan}")
            return remaining
    except Exception as e:
        print(f"  ⚠️  Could not check quota: {e}")
        return 999999


def run_voice_agent():
    print("\n" + "="*60)
    print("  CONTENTPILOT — AGENT 2: THE VOICE")
    print(f"  Voice: {VOICE_NAME} (ElevenLabs)")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)

    if not ELEVENLABS_API_KEY:
        print("\n  ❌  ELEVENLABS_API_KEY not set.")
        print("  Add it to GitHub Secrets as: ELEVENLABS_API_KEY")
        print("  Get your key at: elevenlabs.io/settings/api-keys")
        return

    # Check quota
    remaining = check_quota(ELEVENLABS_API_KEY)
    if remaining < 500:
        print("  ⚠️  Very low quota — skipping voice generation")
        print("  Upgrade to Starter plan at elevenlabs.io for 30,000 chars/month")
        return

    # Get Rudra's voice ID
    voice_id = get_voice_id(ELEVENLABS_API_KEY, VOICE_NAME)
    if not voice_id:
        print(f"\n  ❌  Could not find voice '{VOICE_NAME}'")
        print("  Make sure you've added Rudra to your ElevenLabs voice library")
        print("  Go to: elevenlabs.io/voice-library → search 'Rudra' → Add")
        return

    # Load queue — find approved scripts
    queue = load_queue()
    pending = [item for item in queue if item["status"] == "approved_for_voice"]

    if not pending:
        pending_review = [item for item in queue if item["status"] == "pending_review"]
        print(f"\n  ℹ️  No scripts approved for voice yet.")
        print(f"  📬  {len(pending_review)} script(s) waiting for your review in the dashboard.")
        return

    print(f"\n  🎙️  Processing {len(pending)} approved script(s)...\n")

    for item in pending:
        print(f"  📺  {item['channel_emoji']} {item['channel_name']}")
        print(f"       {item.get('title', item['topic'])[:55]}")

        script_file = Path(item["file"])
        if not script_file.exists():
            print(f"  ❌  Script file not found")
            continue

        with open(script_file) as f:
            video_data = json.load(f)

        script_text = video_data["script"]
        char_count = len(script_text)
        print(f"       Characters: {char_count:,}")

        if char_count > remaining:
            print(f"  ⚠️  Not enough quota ({remaining:,} remaining) — skipping")
            continue

        output_path = OUTPUT_DIR / item["channel"] / f"{item['id']}_voice.mp3"

        success = generate_voice(script_text, output_path, voice_id, ELEVENLABS_API_KEY)
        remaining -= char_count

        if success:
            video_data["voice_file"] = str(output_path)
            video_data["status"] = "voice_ready"
            video_data["voice_settings"] = {
                "provider": "elevenlabs",
                "voice": VOICE_NAME,
                "voice_id": voice_id,
                "model": MODEL_ID,
                "settings": VOICE_SETTINGS
            }
            with open(script_file, "w") as f:
                json.dump(video_data, f, indent=2)

            for q in queue:
                if q["id"] == item["id"]:
                    q["status"] = "voice_ready"
                    q["voice_file"] = str(output_path)
                    break

            print(f"  ✅  Voice ready → passing to Agent 3 (Video Maker)\n")

    save_queue(queue)

    print(f"{'='*60}")
    print(f"  ✅  VOICE AGENT COMPLETE")
    print(f"  📊  Remaining quota: {remaining:,} characters")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_voice_agent()
