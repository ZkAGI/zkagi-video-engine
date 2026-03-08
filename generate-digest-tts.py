#!/usr/bin/env python3
"""Generate TTS audio for all 7 scenes of the daily AI digest using pad voice."""
import os, sys, time, wave, subprocess

TTS_URL = "https://avatar.zkagi.ai/v1/clone-tts"
REF_AUDIO = "voices/pad.wav"
REF_TEXT = "Today, software handles our money, our health, our work."
OUTPUT_DIR = "public/audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FILENAME_PREFIX = "digest"

# TTS speaks at ~2.2 words/sec. Target: ~75s total.
SCENES = [
    # Scene 0: Hook (~5s, ~11 words)
    "Four stories. Seventy-five seconds. No filler. Let's go.",

    # Scene 1: Local LLMs (~12s)
    "Some dude ran AI on his laptop for a month. Says he learned more than two years paying for cloud. Local models are thriving. Your laptop is the new lab coat.",

    # Scene 2: Academic anxiety (~10s, ~20 words)
    "You finish your paper. Click submit. The portal just doesn't update. Three days. Welcome to MICCAI portal pain.",

    # Scene 3: PhDs becoming founders (~10s)
    "PhD job market is rough. People are just building startups instead. Thesis defense? Now it's a pitch deck. Honestly? Better career move.",

    # Scene 4: AI + Physics (~10s, ~20 words)
    "AI plus physics now makes real objects. Not pictures. Things you can pick up and hold. The future got physical.",

    # Scene 5: Watchlist rapid-fire (~15s)
    "Quick hits. Minimax disappointing. Qwen hyped. Open source winning big. OpenClaw, Supabase, ClickHouse. All cooking. Go explore.",

    # Scene 6: Outro (~8s, ~15 words)
    "That's your daily AI hit. Follow ZkAGI for tomorrow's. Stay curious out there.",
]


def generate_tts(text, output_path):
    """Use curl to call TTS endpoint (more reliable multipart handling)."""
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "-F", f"ref_audio=@{REF_AUDIO}",
        "-F", f"ref_text={REF_TEXT}",
        "-F", f"text={text}",
        "-F", "cfg_value=2.0",
        "-F", "steps=15",
        "-o", output_path,
        "-w", "%{http_code}",
        TTS_URL,
    ], capture_output=True, text=True, timeout=120)

    http_code = result.stdout.strip()
    if http_code != "200":
        raise Exception(f"HTTP {http_code}: {result.stderr}")

    return os.path.getsize(output_path)


def get_wav_duration(path):
    """Get duration of a WAV file in seconds."""
    try:
        with wave.open(path, 'r') as w:
            frames = w.getnframes()
            rate = w.getframerate()
            return frames / rate
    except Exception:
        # Fallback: estimate from file size (PCM 16-bit mono 44100Hz)
        size = os.path.getsize(path)
        return (size - 44) / (44100 * 2)


def main():
    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(SCENES)

    print(f"Generating TTS for scenes {start_idx} to {end_idx - 1}")
    durations = {}

    for i in range(start_idx, end_idx):
        output_path = os.path.join(OUTPUT_DIR, f"{FILENAME_PREFIX}-{i}.wav")

        # Skip if already exists and is reasonable size
        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            dur = get_wav_duration(output_path)
            durations[i] = dur
            print(f"  [scene-{i}] SKIP (exists, {dur:.2f}s)")
            continue

        print(f"  [scene-{i}] Generating: {SCENES[i][:60]}...")
        try:
            size = generate_tts(SCENES[i], output_path)
            dur = get_wav_duration(output_path)
            durations[i] = dur
            print(f"  [scene-{i}] DONE: {size} bytes, {dur:.2f}s")
        except Exception as e:
            print(f"  [scene-{i}] ERROR: {e}")

    print("\n=== DURATIONS ===")
    total = 0
    for i in sorted(durations.keys()):
        print(f"  Scene {i}: {durations[i]:.2f}s")
        total += durations[i]
    print(f"  TOTAL SPEECH: {total:.2f}s")

    # Print frame calculation helper
    print("\n=== FRAME CALCULATION (30fps) ===")
    for i in sorted(durations.keys()):
        audio_frames = int(durations[i] * 30)
        padded = audio_frames + 20  # add small pad
        print(f"  Scene {i}: {durations[i]:.2f}s → {audio_frames} audio frames → {padded} with pad")
    total_frames = sum(int(d * 30) + 20 for d in durations.values())
    print(f"  TOTAL FRAMES: {total_frames}")


if __name__ == "__main__":
    main()
