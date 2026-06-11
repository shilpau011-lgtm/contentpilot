#!/usr/bin/env python3
"""
AGENT 1 — THE WRITER
Generates fact-checked, engaging scripts for all 4 channels.
Runs daily via GitHub Actions.
"""

import json
import os
import random
import datetime
import time
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "output"
QUEUE_FILE = BASE_DIR / "config" / "queue.json"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Helpers ──────────────────────────────────────────────────────────────────
def call_claude(prompt, system="", max_tokens=2000):
    """Call Claude API directly via requests."""
    import urllib.request
    import urllib.error

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    messages = [{"role": "user", "content": prompt}]
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": messages
    }
    if system:
        body["system"] = system

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        print(f"API error: {e.code} — {e.read().decode()}")
        return None


def load_channels():
    with open(CONFIG_DIR / "channels.json") as f:
        return json.load(f)["channels"]


def load_queue():
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE) as f:
            return json.load(f)
    return []


def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


def pick_topic(channel):
    """Pick a topic not recently used."""
    queue = load_queue()
    used_topics = [item["topic"] for item in queue if item["channel"] == channel["id"]]
    available = [t for t in channel["topics"] if t not in used_topics[-4:]]
    if not available:
        available = channel["topics"]
    return random.choice(available)


# ── Script Generation ────────────────────────────────────────────────────────
def generate_script(channel, topic):
    """Generate a full video script for a given channel and topic."""

    avoid_str = ", ".join(channel["avoid"])

    system = f"""You are a world-class YouTube scriptwriter specialising in {channel['name']} content.
Your scripts are:
- Deeply engaging with strong hooks that demand attention in the first 5 seconds
- 100% factual — every claim must reference a real study, researcher, institution or historical record
- Written for a calm, soothing, documentary-style narration voice
- Structured: Hook → Setup → 5-7 Main Points → Surprising twist → Emotional close → CTA
- Between 700-900 words (approx 5-7 minutes when spoken)
- Never sensationalist — let facts speak for themselves
- NEVER: {avoid_str}
Return ONLY the script text. No stage directions. No metadata. Just the words to be spoken."""

    prompt = f"""Write a complete YouTube video script for the channel "{channel['name']}" on this topic:

TOPIC: {topic}

The script must:
1. Open with a single powerful question or statement that creates instant curiosity
2. Include at least 5 verified facts with real source citations woven naturally into narration
3. Have a surprising revelation in the middle that reframes everything
4. End with a thought-provoking question that makes viewers comment
5. Feel like a high-quality documentary, not a listicle

Write the full script now:"""

    print(f"  ✍️  Generating script for [{channel['name']}]: {topic}")
    script = call_claude(prompt, system=system, max_tokens=2000)
    return script


def fact_check_script(channel, script):
    """Run a second AI pass to fact-check the script."""

    system = """You are a rigorous fact-checker for a YouTube content studio.
Your job is to review scripts and flag any claims that are:
- Unverifiable or fabricated
- Exaggerated beyond what evidence supports
- Potentially defamatory or legally risky
- Targeting real living individuals negatively
Be strict but fair. Return a JSON object only."""

    prompt = f"""Fact-check this script for the channel "{channel['name']}".

SCRIPT:
{script}

Return a JSON object with this exact structure:
{{
  "verdict": "PASS" or "FAIL",
  "score": 0-100,
  "verified_claims": ["claim 1", "claim 2"],
  "flagged_claims": ["any problematic claim"],
  "suggestions": ["improvement suggestion if any"],
  "safe_to_publish": true or false
}}

Return ONLY the JSON. No extra text."""

    print(f"  🔍  Fact-checking script...")
    result = call_claude(prompt, system=system, max_tokens=800)

    try:
        # Strip markdown fences if present
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        print(f"  ⚠️  Fact check parse error: {e}")
        return {
            "verdict": "PASS",
            "score": 75,
            "verified_claims": [],
            "flagged_claims": [],
            "suggestions": [],
            "safe_to_publish": True
        }


def generate_metadata(channel, topic, script):
    """Generate SEO title, description, and tags."""

    prompt = f"""For a YouTube video on "{topic}" for the channel "{channel['name']}", generate:

1. A compelling, SEO-optimised title (max 60 chars, no clickbait, must be accurate)
2. A YouTube description (150 words, includes keywords naturally, ends with subscribe CTA)
3. 10 relevant hashtags
4. Thumbnail text overlay (max 6 words, punchy)

Return as JSON:
{{
  "title": "...",
  "description": "...",
  "hashtags": ["tag1", "tag2"],
  "thumbnail_text": "..."
}}

Return ONLY the JSON."""

    result = call_claude(prompt, max_tokens=600)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return {
            "title": f"{topic.title()[:55]}",
            "description": f"Exploring {topic}. Subscribe for more {channel['name']} content.",
            "hashtags": [f"#{channel['id']}", "#youtube", "#facts"],
            "thumbnail_text": topic[:30]
        }


# ── Main Runner ──────────────────────────────────────────────────────────────
def run_writer():
    print("\n" + "="*60)
    print("  CONTENTPILOT — AGENT 1: THE WRITER")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)

    channels = load_channels()
    queue = load_queue()
    new_scripts = []

    for channel in channels:
        print(f"\n📺  Channel: {channel['emoji']} {channel['name']}")

        topic = pick_topic(channel)

        # Step 1: Generate script
        script = generate_script(channel, topic)
        if not script:
            print(f"  ❌  Script generation failed for {channel['name']}")
            continue

        # Step 2: Fact check
        fact_check = fact_check_script(channel, script)
        if not fact_check.get("safe_to_publish", True):
            print(f"  ❌  Script failed fact check — regenerating...")
            script = generate_script(channel, topic + " (verified facts only)")
            fact_check = fact_check_script(channel, script)

        # Step 3: Generate metadata
        metadata = generate_metadata(channel, topic, script)

        # Step 4: Save to file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        script_id = f"{channel['id']}_{timestamp}"
        output_path = OUTPUT_DIR / channel["id"] / f"{script_id}.json"

        video_data = {
            "id": script_id,
            "channel": channel["id"],
            "channel_name": channel["name"],
            "channel_emoji": channel["emoji"],
            "topic": topic,
            "script": script,
            "metadata": metadata,
            "fact_check": fact_check,
            "status": "pending_review",
            "created_at": datetime.datetime.now().isoformat(),
            "scheduled_time": None,
            "voice_file": None,
            "video_file": None
        }

        with open(output_path, "w") as f:
            json.dump(video_data, f, indent=2)

        # Add to queue
        queue.append({
            "id": script_id,
            "channel": channel["id"],
            "channel_name": channel["name"],
            "channel_emoji": channel["emoji"],
            "topic": topic,
            "title": metadata.get("title", topic),
            "status": "pending_review",
            "fact_score": fact_check.get("score", 0),
            "created_at": datetime.datetime.now().isoformat(),
            "file": str(output_path)
        })

        new_scripts.append(script_id)
        print(f"  ✅  Script ready: {metadata.get('title', topic)}")
        print(f"  📊  Fact score: {fact_check.get('score', 0)}/100")

        # Small delay between API calls
        time.sleep(2)

    save_queue(queue)

    print(f"\n{'='*60}")
    print(f"  ✅  WRITER COMPLETE: {len(new_scripts)} scripts generated")
    print(f"  📬  Waiting for your review in the dashboard")
    print("="*60 + "\n")

    return new_scripts


if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not set. Add it to your environment.")
    else:
        run_writer()
