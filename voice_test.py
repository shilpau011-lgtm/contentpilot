#!/usr/bin/env python3
"""
ContentPilot — Voice Clone Tester
===================================
Step 1: Record your voice (see instructions below)
Step 2: Run this script
Step 3: Listen to the output — adjust settings if needed
Step 4: When happy, this becomes Agent 2 in your pipeline

ACCENT REDUCTION SETTINGS:
- cfg_weight = 0.0  →  Strips accent most aggressively
- exaggeration = 0.3 → Keeps speech calm and steady
- These are the key settings that will smooth your Indian accent
"""

import sys
import os
import subprocess
from pathlib import Path

# ── Install dependencies ──────────────────────────────────────────────────────
def install():
    pkgs = ["chatterbox-tts", "torchaudio", "torch"]
    for pkg in pkgs:
        print(f"Installing {pkg}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            capture_output=True
        )
    print("✅ All packages installed\n")

# ── Test texts — short to medium ─────────────────────────────────────────────
TEST_SHORT = "Have you ever walked away from a conversation feeling confused, exhausted, or somehow guilty — even though you did nothing wrong?"

TEST_MEDIUM = """Have you ever walked away from a conversation feeling confused,
exhausted, or somehow guilty — even though you did nothing wrong?
That feeling isn't accidental. Someone engineered it.
The most dangerous form of manipulation is invisible —
woven into everyday conversations, disguised as kindness."""

TEST_FULL = """Some of the most profound discoveries in human history
didn't come from laboratories or universities.
They came from ordinary people asking questions
that nobody else thought to ask.
The world is full of patterns — hidden beneath the surface of everyday life —
waiting to be noticed by anyone curious enough to look.
Today, we explore one of those patterns.
And by the end, you may never see things quite the same way again."""

# ── Settings to try ───────────────────────────────────────────────────────────
# cfg_weight:   0.0 = ignore accent completely, 1.0 = copy accent exactly
# exaggeration: 0.3 = calm/flat, 1.0 = very expressive

PRESETS = {
    "accent_reduced": {
        "cfg_weight": 0.0,      # KEY: this removes accent most effectively
        "exaggeration": 0.3,    # calm, soothing documentary tone
        "description": "Accent reduced, calm narration — RECOMMENDED"
    },
    "slight_accent": {
        "cfg_weight": 0.3,
        "exaggeration": 0.35,
        "description": "Slight accent kept, still calm"
    },
    "natural_voice": {
        "cfg_weight": 0.5,
        "exaggeration": 0.4,
        "description": "Your natural voice and accent, documentary pace"
    },
    "expressive": {
        "cfg_weight": 0.0,
        "exaggeration": 0.6,
        "description": "Accent reduced + more expressive delivery"
    }
}


def generate_sample(text, voice_ref_path, output_path, cfg_weight=0.0, exaggeration=0.3):
    """Generate a voice sample with given settings."""
    try:
        from chatterbox.tts import ChatterboxTTS
        import torchaudio

        print(f"  🧠 Loading model (first time takes ~30 seconds)...")
        model = ChatterboxTTS.from_pretrained(device="cpu")

        print(f"  🎙️ Generating speech...")
        wav = model.generate(
            text,
            audio_prompt_path=str(voice_ref_path),
            exaggeration=exaggeration,
            cfg_weight=cfg_weight
        )

        torchaudio.save(str(output_path), wav, model.sr)
        print(f"  ✅ Saved: {output_path.name}")
        return True

    except ImportError:
        print("  ❌ Chatterbox not installed. Run: pip install chatterbox-tts")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def run_voice_test(voice_file_path):
    """
    Run all preset tests on your voice recording.
    Generates 4 audio samples so you can pick the best one.
    """
    voice_path = Path(voice_file_path)
    if not voice_path.exists():
        print(f"\n❌ Voice file not found: {voice_file_path}")
        print("\n📋 HOW TO RECORD YOUR VOICE:")
        print("=" * 50)
        print()
        print("1. Find a quiet room (bedroom works great)")
        print("2. Open your phone's Voice Memos app")
        print("3. Read this script SLOWLY and CLEARLY:")
        print()
        print("─" * 50)
        print("""
  \"Some of the most profound discoveries in human
  history didn't come from laboratories or universities.
  They came from ordinary people asking questions that
  nobody else thought to ask. The world is full of
  patterns — hidden beneath the surface of everyday
  life — waiting to be noticed by anyone curious enough
  to look. Today, we explore one of those patterns.
  And by the end, you may never see things quite the
  same way again. Stay with me.\"
        """)
        print("─" * 50)
        print()
        print("4. Record 2-3 takes, pick the clearest")
        print("5. Export/save as: my_voice.wav or my_voice.m4a")
        print("6. Run this script again:")
        print("   python voice_test.py my_voice.wav")
        print()
        return

    output_dir = voice_path.parent / "voice_samples"
    output_dir.mkdir(exist_ok=True)

    print("\n" + "="*60)
    print("  CONTENTPILOT — VOICE CLONE TESTER")
    print("="*60)
    print(f"\n  📁 Voice reference: {voice_path.name}")
    print(f"  🎯 Testing {len(PRESETS)} accent/tone presets\n")

    results = []

    for preset_name, preset in PRESETS.items():
        print(f"\n  🎛️  Preset: {preset['description']}")
        print(f"     cfg_weight={preset['cfg_weight']}, exaggeration={preset['exaggeration']}")

        output_file = output_dir / f"sample_{preset_name}.wav"

        success = generate_sample(
            text=TEST_FULL,
            voice_ref_path=voice_path,
            output_path=output_file,
            cfg_weight=preset["cfg_weight"],
            exaggeration=preset["exaggeration"]
        )

        if success:
            results.append({
                "preset": preset_name,
                "description": preset["description"],
                "file": str(output_file)
            })

    print("\n" + "="*60)
    print("  ✅ ALL SAMPLES GENERATED")
    print("="*60)
    print(f"\n  📂 Your samples are in: {output_dir}")
    print()
    print("  LISTEN TO EACH FILE AND PICK YOUR FAVOURITE:")
    print()
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['file'].split('/')[-1]}")
        print(f"     → {r['description']}")
        print()

    print("  💡 RECOMMENDATION:")
    print("  Start with: sample_accent_reduced.wav")
    print("  (cfg_weight=0.0 is the strongest accent reducer)")
    print()
    print("  Once you pick your favourite preset, tell me which one")
    print("  and I'll lock those settings into Agent 2 permanently.")
    print()
    print("  🎯 The preset you choose becomes your channel's voice — forever.")
    print("="*60 + "\n")


def quick_test_without_voice():
    """Generate a sample with default Chatterbox voice (no reference needed)."""
    print("\n" + "="*60)
    print("  QUICK TEST — No voice reference")
    print("  (Tests if Chatterbox is working correctly)")
    print("="*60)

    output_file = Path("chatterbox_default_test.wav")

    try:
        from chatterbox.tts import ChatterboxTTS
        import torchaudio

        print("\n  Loading model...")
        model = ChatterboxTTS.from_pretrained(device="cpu")

        print("  Generating test audio...")
        wav = model.generate(
            TEST_SHORT,
            exaggeration=0.3,
            cfg_weight=0.5
        )
        torchaudio.save(str(output_file), wav, model.sr)

        print(f"\n  ✅ Test successful! Listen to: {output_file}")
        print("  If it sounds good, you're ready to record your voice.")

    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        print("  Try: pip install chatterbox-tts torchaudio torch")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n  Usage:")
        print("  python voice_test.py my_voice.wav        ← test YOUR voice")
        print("  python voice_test.py --quick             ← test default voice")
        print("  python voice_test.py --install           ← install packages")
        print()

        # Auto-detect if a voice file exists nearby
        common_names = ["my_voice.wav", "voice.wav", "recording.wav",
                       "my_voice.m4a", "voice.m4a", "voice_reference.wav"]
        found = None
        for name in common_names:
            if Path(name).exists():
                found = name
                break

        if found:
            print(f"  🔍 Found voice file: {found}")
            print(f"  Running test automatically...\n")
            run_voice_test(found)
        else:
            run_voice_test("my_voice.wav")  # Will show instructions

    elif sys.argv[1] == "--install":
        install()
    elif sys.argv[1] == "--quick":
        quick_test_without_voice()
    else:
        run_voice_test(sys.argv[1])
