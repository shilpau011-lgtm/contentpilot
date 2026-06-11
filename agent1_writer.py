#!/usr/bin/env python3
"""
AGENT 1 — THE WRITER
Works whether files are in root or subfolders.
"""

import json, os, random, datetime, time, urllib.request, urllib.error
from pathlib import Path

# ── Auto-detect base directory ───────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
# Works from root OR agents/ subfolder
if SCRIPT_DIR.name == "agents":
    BASE_DIR = SCRIPT_DIR.parent
else:
    BASE_DIR = SCRIPT_DIR

CONFIG_DIR = BASE_DIR
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
QUEUE_FILE = BASE_DIR / "queue.json"

# Create output folders
for ch in ["dark_psychology","space_universe","dark_history","true_crime"]:
    (OUTPUT_DIR / ch).mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def call_claude(prompt, system="", max_tokens=2000):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    body = {"model": "claude-sonnet-4-20250514", "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    if system:
        body["system"] = system
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                  data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["content"][0]["text"]
    except urllib.error.HTTPError as e:
        print(f"API error: {e.code} — {e.read().decode()}")
        return None

def load_channels():
    path = BASE_DIR / "channels.json"
    if not path.exists():
        path = BASE_DIR / "config" / "channels.json"
    with open(path) as f:
        return json.load(f)["channels"]

def load_queue():
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE) as f:
            try: return json.load(f)
            except: return []
    return []

def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)

def pick_topic(channel):
    queue = load_queue()
    used = [i["topic"] for i in queue if i["channel"] == channel["id"]][-4:]
    available = [t for t in channel["topics"] if t not in used]
    return random.choice(available if available else channel["topics"])

def generate_script(channel, topic):
    avoid = ", ".join(channel["avoid"])
    system = f"""You are a world-class YouTube scriptwriter for {channel['name']}.
Scripts are 100% factual with real citations, calm documentary narration style.
Structure: Hook → Setup → 5-7 verified points → twist → emotional close → CTA
Length: 750-900 words. NEVER: {avoid}
Return ONLY the script text."""
    prompt = f"""Write a YouTube script for "{channel['name']}" on: "{topic}"
1. Open with a powerful question creating instant curiosity
2. Include 5+ verified facts with real source citations
3. Include a surprising mid-video revelation
4. End with a thought-provoking question
5. Calm, soothing documentary tone

After script write:
TITLE: [SEO title under 60 chars]
SCORE: [factual accuracy confidence 0-100]"""
    print(f"  ✍️  [{channel['name']}] {topic}")
    return call_claude(prompt, system, 2000)

def run_writer():
    print("\n" + "="*55)
    print("  CONTENTPILOT — AGENT 1: THE WRITER")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)

    channels = load_channels()
    queue = load_queue()
    new_scripts = []

    for channel in channels:
        print(f"\n📺 {channel['emoji']} {channel['name']}")
        topic = pick_topic(channel)
        response = generate_script(channel, topic)
        if not response:
            print(f"  ❌ Failed")
            continue

        lines = response.split('\n')
        title, score, script_lines = topic, 80, []
        for line in lines:
            if line.startswith('TITLE:'): title = line.replace('TITLE:','').strip()
            elif line.startswith('SCORE:'):
                try: score = int(line.replace('SCORE:','').strip())
                except: pass
            else: script_lines.append(line)

        script = '\n'.join(script_lines).strip()
        preview = ' '.join(script.split()[:50]) + '...'
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        script_id = f"{channel['id']}_{timestamp}"
        output_path = OUTPUT_DIR / channel["id"] / f"{script_id}.json"

        video_data = {
            "id": script_id, "channel": channel["id"],
            "channel_name": channel["name"], "channel_emoji": channel["emoji"],
            "topic": topic, "title": title, "script": script,
            "script_preview": preview, "fact_score": score,
            "status": "pending_review",
            "created_at": datetime.datetime.now().isoformat(),
            "scheduled_time": None, "voice_file": None, "video_file": None
        }

        with open(output_path, "w") as f:
            json.dump(video_data, f, indent=2)

        queue.append({
            "id": script_id, "channel": channel["id"],
            "channel_name": channel["name"], "channel_emoji": channel["emoji"],
            "topic": topic, "title": title, "script_preview": preview,
            "fact_score": score, "status": "pending_review",
            "created_at": datetime.datetime.now().isoformat(),
            "file": str(output_path)
        })

        new_scripts.append(script_id)
        print(f"  ✅ {title[:50]}")
        print(f"  📊 Score: {score}/100")
        time.sleep(2)

    save_queue(queue)
    print(f"\n{'='*55}")
    print(f"  ✅ DONE: {len(new_scripts)} scripts generated")
    print("="*55 + "\n")
    return new_scripts

if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not set")
    else:
        run_writer()
