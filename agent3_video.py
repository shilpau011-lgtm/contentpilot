#!/usr/bin/env python3
"""
AGENT 3 — THE VIDEO MAKER
Assembles final video: stock footage + voice + captions + music.
Uses MoviePy (free), Pexels API (free), Pixabay music (free).
Zero watermarks. Commercial use OK.
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import datetime
import subprocess
import random
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
QUEUE_FILE = BASE_DIR / "config" / "queue.json"
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# Visual style per channel
CHANNEL_STYLES = {
    "dark_psychology": {
        "color_overlay": (20, 10, 40, 160),   # deep purple tint
        "text_color": "white",
        "accent_color": "#7c6aff",
        "search_terms": ["brain", "shadow", "mind", "psychology", "darkness", "human silhouette"],
        "music_mood": "dark ambient"
    },
    "space_universe": {
        "color_overlay": (0, 10, 30, 140),    # deep space blue
        "text_color": "white",
        "accent_color": "#00c6ff",
        "search_terms": ["galaxy", "space", "stars", "universe", "nebula", "cosmos"],
        "music_mood": "cinematic space"
    },
    "dark_history": {
        "color_overlay": (30, 20, 10, 150),   # sepia/brown tint
        "text_color": "white",
        "accent_color": "#c8a96e",
        "search_terms": ["ancient ruins", "history", "medieval", "old documents", "dark castle", "ancient"],
        "music_mood": "dark orchestral"
    },
    "true_crime": {
        "color_overlay": (30, 0, 0, 160),     # dark red tint
        "text_color": "white",
        "accent_color": "#ff5e5e",
        "search_terms": ["detective", "mystery", "dark city", "rain night", "investigation", "shadows"],
        "music_mood": "thriller suspense"
    }
}


def install_dependencies():
    packages = ["moviepy", "pillow", "requests"]
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"  📦  Installing {pkg}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--break-system-packages", "-q"],
                capture_output=True
            )


def fetch_pexels_video(query, output_path, duration_needed=30):
    """Fetch a free stock video from Pexels API."""
    if not PEXELS_API_KEY:
        print("  ⚠️  No PEXELS_API_KEY — using placeholder footage")
        return create_placeholder_video(output_path, duration_needed)

    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page=10&orientation=landscape"
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_API_KEY})

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            videos = data.get("videos", [])
            if not videos:
                return create_placeholder_video(output_path, duration_needed)

            # Pick a random video from results
            video = random.choice(videos[:5])
            # Get the HD file
            video_files = video.get("video_files", [])
            hd_files = [f for f in video_files if f.get("quality") in ["hd", "sd"]]
            if not hd_files:
                return create_placeholder_video(output_path, duration_needed)

            video_url = hd_files[0]["link"]

            # Download it
            print(f"  🎬  Downloading footage: {query}")
            urllib.request.urlretrieve(video_url, output_path)
            return str(output_path)

    except Exception as e:
        print(f"  ⚠️  Pexels fetch error: {e}")
        return create_placeholder_video(output_path, duration_needed)


def create_placeholder_video(output_path, duration=30):
    """Create a dark gradient placeholder when no footage available."""
    try:
        from moviepy import ColorClip
        clip = ColorClip(size=(1280, 720), color=(10, 5, 20), duration=duration)
        clip.write_videofile(str(output_path), fps=24, logger=None)
        clip.close()
        return str(output_path)
    except Exception as e:
        print(f"  ❌  Placeholder creation failed: {e}")
        return None


def create_text_card(text, duration, style, output_path, font_size=48):
    """Create an animated text overlay card."""
    try:
        from moviepy import TextClip, ColorClip, CompositeVideoClip
        from moviepy.video.fx import FadeIn, FadeOut

        bg = ColorClip(size=(1280, 720), color=(10, 5, 20), duration=duration)

        txt = TextClip(
            text=text,
            font_size=font_size,
            color=style["text_color"],
            font="Arial",
            method="caption",
            size=(1100, None),
            text_align="center"
        ).with_duration(duration).with_position("center")

        composite = CompositeVideoClip([bg, txt])
        composite.write_videofile(str(output_path), fps=24, logger=None)
        composite.close()
        return str(output_path)
    except Exception as e:
        print(f"  ⚠️  Text card error: {e}")
        return None


def split_script_into_segments(script, num_segments=6):
    """Split script into timed visual segments."""
    paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
    if len(paragraphs) <= num_segments:
        return paragraphs
    # Group into roughly equal segments
    chunk_size = max(1, len(paragraphs) // num_segments)
    segments = []
    for i in range(0, len(paragraphs), chunk_size):
        segment = ' '.join(paragraphs[i:i+chunk_size])
        segments.append(segment[:200] + "..." if len(segment) > 200 else segment)
    return segments[:num_segments]


def assemble_video(video_data, output_path):
    """Main video assembly function."""
    install_dependencies()

    try:
        from moviepy import (
            VideoFileClip, AudioFileClip, TextClip,
            ColorClip, CompositeVideoClip, concatenate_videoclips
        )
        from moviepy.audio.fx import MultiplyVolume
    except ImportError as e:
        print(f"  ❌  MoviePy import error: {e}")
        return False

    channel_id = video_data["channel"]
    style = CHANNEL_STYLES.get(channel_id, CHANNEL_STYLES["dark_psychology"])
    script = video_data["script"]
    voice_file = video_data.get("voice_file")
    title = video_data["metadata"].get("title", video_data["topic"])

    temp_dir = OUTPUT_DIR / channel_id / f"temp_{video_data['id']}"
    temp_dir.mkdir(exist_ok=True)

    print(f"  🎬  Assembling video: {title[:50]}")

    # Get audio duration to match video length
    audio_duration = 300  # default 5 min
    if voice_file and Path(voice_file).exists():
        try:
            audio = AudioFileClip(voice_file)
            audio_duration = audio.duration
            audio.close()
            print(f"  ⏱️  Audio duration: {audio_duration:.0f}s")
        except Exception as e:
            print(f"  ⚠️  Could not read audio duration: {e}")

    # Build video segments
    search_terms = style["search_terms"]
    segments = []
    segment_duration = audio_duration / len(search_terms)

    for i, term in enumerate(search_terms):
        footage_path = temp_dir / f"footage_{i}.mp4"

        if not footage_path.exists():
            fetched = fetch_pexels_video(term, footage_path, segment_duration)
            time.sleep(0.5)  # rate limit respect
        else:
            fetched = str(footage_path)

        if fetched and Path(fetched).exists():
            try:
                clip = VideoFileClip(fetched)

                # Resize to 1280x720
                clip = clip.resized((1280, 720))

                # Loop or trim to segment duration
                if clip.duration < segment_duration:
                    loops = int(segment_duration / clip.duration) + 1
                    from moviepy import concatenate_videoclips
                    clip = concatenate_videoclips([clip] * loops)

                clip = clip.subclipped(0, segment_duration)

                # Apply dark color overlay
                r, g, b, alpha = style["color_overlay"]
                overlay = ColorClip(
                    size=(1280, 720),
                    color=(r, g, b),
                    duration=segment_duration
                ).with_opacity(alpha / 255.0)

                segment = CompositeVideoClip([clip, overlay])
                segments.append(segment)

            except Exception as e:
                print(f"  ⚠️  Segment {i} error: {e}")
                fallback = ColorClip(
                    size=(1280, 720),
                    color=(10, 5, 20),
                    duration=segment_duration
                )
                segments.append(fallback)
        else:
            fallback = ColorClip(
                size=(1280, 720),
                color=(10, 5, 20),
                duration=segment_duration
            )
            segments.append(fallback)

    if not segments:
        print("  ❌  No video segments created")
        return False

    # Concatenate all segments
    print("  🔗  Joining segments...")
    try:
        final_video = concatenate_videoclips(segments)

        # Trim/extend to match audio
        if final_video.duration > audio_duration:
            final_video = final_video.subclipped(0, audio_duration)
    except Exception as e:
        print(f"  ❌  Concatenation error: {e}")
        return False

    # Add title card at start
    try:
        title_card = ColorClip(
            size=(1280, 720),
            color=(10, 5, 20),
            duration=3
        )
        title_text = TextClip(
            text=title,
            font_size=52,
            color="white",
            font="Arial",
            method="caption",
            size=(1100, None),
            text_align="center"
        ).with_duration(3).with_position("center")

        channel_text = TextClip(
            text=f"{video_data['channel_emoji']}  {video_data['channel_name'].upper()}",
            font_size=24,
            color=style["accent_color"],
            font="Arial",
            method="label"
        ).with_duration(3).with_position(("center", 580))

        title_composite = CompositeVideoClip([title_card, title_text, channel_text])
        final_video = concatenate_videoclips([title_composite, final_video])
    except Exception as e:
        print(f"  ⚠️  Title card skipped: {e}")

    # Add captions (key phrases)
    try:
        script_segments = split_script_into_segments(script, 8)
        caption_clips = [final_video]

        offset = 3  # start after title card
        for seg_text in script_segments:
            words = seg_text.split()[:12]
            caption = " ".join(words) + ("..." if len(seg_text.split()) > 12 else "")
            seg_duration = audio_duration / len(script_segments)

            caption_clip = TextClip(
                text=caption,
                font_size=32,
                color="white",
                font="Arial",
                method="caption",
                size=(1100, None),
                text_align="center",
                stroke_color="black",
                stroke_width=2
            ).with_duration(seg_duration).with_start(offset).with_position(("center", 620))

            caption_clips.append(caption_clip)
            offset += seg_duration

        final_with_captions = CompositeVideoClip(caption_clips)
    except Exception as e:
        print(f"  ⚠️  Captions skipped: {e}")
        final_with_captions = final_video

    # Add voice audio
    if voice_file and Path(voice_file).exists():
        try:
            voice_audio = AudioFileClip(voice_file)
            final_with_captions = final_with_captions.with_audio(voice_audio)
            print("  🎙️  Voice audio attached")
        except Exception as e:
            print(f"  ⚠️  Audio attachment error: {e}")

    # Render final video
    print(f"  🎞️  Rendering final video...")
    try:
        final_with_captions.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            bitrate="2000k",
            logger=None
        )
        print(f"  ✅  Video rendered: {output_path.name}")
        return True
    except Exception as e:
        print(f"  ❌  Render error: {e}")
        return False
    finally:
        # Cleanup temp files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass


def run_video_agent():
    print("\n" + "="*60)
    print("  CONTENTPILOT — AGENT 3: THE VIDEO MAKER")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)

    queue = load_queue() if True else []

    def load_queue():
        if QUEUE_FILE.exists():
            with open(QUEUE_FILE) as f:
                return json.load(f)
        return []

    def save_queue(q):
        with open(QUEUE_FILE, "w") as f:
            json.dump(q, f, indent=2)

    queue = load_queue()
    pending = [item for item in queue if item["status"] == "voice_ready"]

    if not pending:
        print("\n  ℹ️  No videos ready for assembly yet.")
        print("  (Scripts need to be approved → voiced first)")
        return

    print(f"\n  🎬  Assembling {len(pending)} video(s)...")

    for item in pending:
        print(f"\n  📺  {item['channel_emoji']} {item['channel_name']}: {item['topic'][:50]}")

        script_file = Path(item["file"])
        if not script_file.exists():
            continue

        with open(script_file) as f:
            video_data = json.load(f)

        output_path = OUTPUT_DIR / item["channel"] / f"{item['id']}_final.mp4"
        success = assemble_video(video_data, output_path)

        if success:
            video_data["video_file"] = str(output_path)
            video_data["status"] = "ready_to_publish"
            with open(script_file, "w") as f:
                json.dump(video_data, f, indent=2)

            for q in queue:
                if q["id"] == item["id"]:
                    q["status"] = "ready_to_publish"
                    q["video_file"] = str(output_path)
                    break

    save_queue(queue)
    print(f"\n{'='*60}")
    print("  ✅  VIDEO MAKER COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_video_agent()
