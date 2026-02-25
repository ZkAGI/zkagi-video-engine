#!/usr/bin/env python3
"""LTX-2 Video Generation — 12 clips for PawPad wallet creation demo (60s)
TEXT-TO-VIDEO mode (image gen server down) — uses LTX-2 text-to-video directly."""

import json
import time
import random
import sys
import os
import subprocess
import urllib.request
import urllib.parse
import urllib.error

COMFY_URL = "http://" + subprocess.check_output(
    "ip route show default | awk '{print $3}'", shell=True
).decode().strip() + ":8001"

SCENES_DIR = "/home/aten/zkagi-video-engine/public/scenes"

print(f"ComfyUI URL: {COMFY_URL}")

# Motion/scene prompts for text-to-video generation
CLIPS = {
    # Scene 0: Hook — roast seed phrases
    "0-a": "A close-up shot slowly pushing into a messy kitchen drawer overflowing with crumpled papers and napkins. A hand frantically rummages through the contents, tossing wrinkled notes aside. Warm lamplight casts dramatic shadows as loose papers flutter upward. The atmosphere is chaotic and desperate. Rustling paper sounds with a frustrated sigh.",
    "0-b": "Close-up of a wrinkled coffee-stained napkin resting on a dark wooden table. The camera slowly orbits around it as the coffee stain appears to spread and darken across the paper surface. A dramatic spotlight from above creates long moody shadows. Purple and blue accent light from the side. Paper crinkling softly with a low dramatic hum.",
    "0-c": "A slow-motion cinematic shot of a crumpled napkin tumbling through dark empty space, illuminated by a single purple spotlight from behind. The napkin rotates gently and unfurls slightly as it falls through the void. Camera tracks the descent smoothly. Particles of dust float in the beam of light. A deep ominous bass tone reverberates.",

    # Scene 1: TEE Explain — hardware vault
    "1-a": "A sweeping dolly shot pushing through layers of translucent holographic security shields inside a futuristic digital vault. Electric teal energy crackles along the edges of each transparent layer. The camera moves deeper into the vault interior revealing glowing circuitry. Particles of light float upward like digital fireflies. A low electronic hum builds with crystalline undertones.",
    "1-b": "A slow cinematic orbit around a transparent sealed cube containing floating golden digital keys. Bright teal energy barriers pulse rhythmically around the cube in waves. The camera circles smoothly showing different angles of the protected keys inside. Particles drift outward from the barriers. A deep synthesizer tone pulses in rhythm with the energy waves.",
    "1-c": "A dramatic wide shot of a luminous teal energy shield blocking dark shadowy forms that press against it from outside. The shield ripples with bright energy on each impact creating outward waves of light. Camera slowly pushes forward toward the glowing protected core behind the shield. Energy impact sounds echo with a protective crystalline chime.",

    # Scene 2: Wallet creation flow
    "2-a": "A close-up shot of a sleek smartphone floating in dark space. The screen illuminates with a bright teal glow as a futuristic holographic interface appears above it. The camera slowly pushes in toward the phone as digital elements animate to life around the screen. Particles of light stream from the edges. A soft digital activation sound plays.",
    "2-b": "A medium shot of a holographic QR code floating and rotating between two glowing devices. Green verification particles spiral outward from the QR code as scanning beams of light connect the two devices. The camera pulls back smoothly to reveal both devices linked by streams of light. A satisfying digital chime rings. Teal light pulses rhythmically.",
    "2-c": "A close-up of a glowing digital file icon slowly descending into a secure futuristic vault opening below. A progress bar fills with bright teal light along the vault entrance. Lock mechanisms materialize and click shut with mechanical precision around the sealed file. Camera tracks downward following the file. Satisfying mechanical clicking with ambient electronic hum.",

    # Scene 3: CTA
    "3-a": "A dramatic cinematic composition with a crumpled napkin on the left side disintegrating into glowing embers and ash. On the right side a brilliant teal hardware vault shimmers with protective energy shields. Camera pushes forward as the left dissolves into darkness and the right fills the frame with triumphant teal light. An orchestral swell builds.",
    "3-b": "A slow dramatic zoom into a glowing shield emblem as it materializes from thousands of scattered energy particles converging from all directions. Teal and purple energy lines merge into the shape. The emblem pulses with brilliant radiant light once fully formed. Camera pushes forward as particles orbit the shape. A rising electronic tone resolves harmonically.",
    "3-c": "A futuristic glowing portal made of teal and purple spiraling energy opens dramatically in dark space. The camera slowly pulls back to reveal the full majestic portal shape as it stabilizes and glows warmly. Particles of light stream toward the portal center invitingly. The atmosphere shifts from mysterious to welcoming. Uplifting ambient electronic music plays.",
}

CLIP_ORDER = ["0-a", "0-b", "0-c", "1-a", "1-b", "1-c", "2-a", "2-b", "2-c", "3-a", "3-b", "3-c"]


def build_t2v_workflow(prompt, seed, output_prefix):
    """Build LTX-2 TEXT-TO-VIDEO workflow with distilled LoRA (8 steps, CFG 1.0)."""
    negative = "static, frozen, no motion, blurry, low quality, distorted, text, words, letters, watermark, jittery, flickering, ugly, deformed, amateur"
    return {
        # Load model + VAE
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"}},
        # Load text encoder (CLIP)
        "2": {"class_type": "LTXAVTextEncoderLoader", "inputs": {"text_encoder": "gemma_3_12B_it.safetensors", "ckpt_name": "ltx-2-19b-dev-fp8.safetensors", "device": "cpu"}},
        # Apply distilled LoRA for 8-step fast generation
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "ltx-2-19b-distilled-lora-384.safetensors", "strength_model": 1.0}},
        # Positive prompt
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        # Negative prompt
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
        # LTX conditioning with frame rate
        "6": {"class_type": "LTXVConditioning", "inputs": {"positive": ["4", 0], "negative": ["5", 0], "frame_rate": 25}},
        # Empty video latent (768x512, 97 frames = 3.88s at 25fps)
        "7": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": 768, "height": 512, "length": 97, "batch_size": 1}},
        # LTX Scheduler (8 steps for distilled)
        "8": {"class_type": "LTXVScheduler", "inputs": {"steps": 8, "max_shift": 2.05, "base_shift": 0.95, "stretch": True, "terminal": 0.1, "latent": ["7", 0]}},
        # Random noise
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        # CFG Guider (CFG 1.0 for distilled)
        "10": {"class_type": "CFGGuider", "inputs": {"model": ["3", 0], "positive": ["6", 0], "negative": ["6", 1], "cfg": 1.0}},
        # Sampler
        "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        # Sample
        "12": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["9", 0], "guider": ["10", 0], "sampler": ["11", 0], "sigmas": ["8", 0], "latent_image": ["7", 0]}},
        # VAE Decode (skip SeparateAVLatent for video-only)
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["1", 2]}},
        # Create video from frames
        "14": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "fps": 25.0}},
        # Save video
        "15": {"class_type": "SaveVideo", "inputs": {"video": ["14", 0], "filename_prefix": output_prefix, "format": "mp4", "codec": "h264"}},
    }


def submit_and_wait(workflow, clip_id):
    """Submit workflow and poll until completion."""
    payload = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=payload, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  SUBMIT FAILED ({e.code}): {error_body[:500]}")
        return None

    prompt_id = result.get("prompt_id")
    if not prompt_id:
        print(f"  SUBMIT FAILED: {result}")
        return None

    print(f"  Submitted: {prompt_id}")

    start = time.time()
    while True:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            history = json.loads(resp.read())
        except Exception as e:
            print(f"  Poll error: {e}")
            time.sleep(5)
            continue

        if prompt_id in history:
            entry = history[prompt_id]
            status_str = entry.get("status", {}).get("status_str", "")
            outputs = entry.get("outputs", {})

            if status_str == "error":
                msgs = entry.get("status", {}).get("messages", [])
                if msgs:
                    last = msgs[-1]
                    if isinstance(last, (list, tuple)) and len(last) > 1:
                        err_info = last[1] if isinstance(last[1], dict) else str(last[1])
                        print(f"  ERROR: {err_info.get('exception_message','?')[:300] if isinstance(err_info,dict) else str(err_info)[:300]}")
                    else:
                        print(f"  ERROR: {str(last)[:300]}")
                else:
                    print("  ERROR: unknown")
                return None

            if outputs:
                elapsed = time.time() - start
                print(f"  Done in {elapsed:.0f}s")
                for nid, out in outputs.items():
                    for key in ["gifs", "videos", "images"]:
                        if key in out:
                            for item in out[key]:
                                fn = item.get("filename", "")
                                if fn.endswith(".mp4") or fn.endswith(".webm"):
                                    return fn
                print("  No video file in output!")
                return None

        elapsed = time.time() - start
        if elapsed > 300:
            print(f"  TIMEOUT after {elapsed:.0f}s")
            return None
        time.sleep(5)


def download_video(filename, output_path):
    """Download generated video from ComfyUI."""
    for subfolder in ["pawpad", ""]:
        try:
            params = f"filename={urllib.parse.quote(os.path.basename(filename))}&type=output"
            if subfolder:
                params += f"&subfolder={subfolder}"
            url = f"{COMFY_URL}/view?{params}"
            urllib.request.urlretrieve(url, output_path)
            size = os.path.getsize(output_path)
            if size > 10000:
                dur = subprocess.check_output(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", output_path]
                ).decode().strip()
                print(f"  Saved: {output_path} ({size}B, {dur}s)")
                return True
        except Exception:
            continue

    try:
        url = f"{COMFY_URL}/view?filename={urllib.parse.quote(filename)}&type=output"
        urllib.request.urlretrieve(url, output_path)
        size = os.path.getsize(output_path)
        if size > 10000:
            dur = subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", output_path]
            ).decode().strip()
            print(f"  Saved: {output_path} ({size}B, {dur}s)")
            return True
    except Exception as e:
        print(f"  Download failed: {e}")
    return False


# Main
skip_existing = "--skip-existing" in sys.argv
only_clip = None
for arg in sys.argv[1:]:
    if arg != "--skip-existing" and not arg.startswith("-"):
        only_clip = arg

clip_list = [only_clip] if only_clip else CLIP_ORDER
total = len(clip_list)
failed = 0

for i, clip_id in enumerate(clip_list):
    output_path = f"{SCENES_DIR}/scene-{clip_id}.mp4"

    if skip_existing and os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        print(f"\n[{i+1}/{total}] SKIP {clip_id} (already exists)")
        continue

    print(f"\n{'='*60}")
    print(f"[{i+1}/{total}] Generating clip: scene-{clip_id}")
    print(f"{'='*60}")

    prompt = CLIPS[clip_id]
    seed = random.randint(1, 2**31)
    prefix = f"pawpad/scene_{clip_id.replace('-', '_')}"
    workflow = build_t2v_workflow(prompt, seed, prefix)

    print(f"  Submitting text-to-video workflow...")
    video_filename = submit_and_wait(workflow, clip_id)

    if video_filename:
        ok = download_video(video_filename, output_path)
        if ok:
            print(f"  [OK] scene-{clip_id}")
        else:
            print(f"  [FAIL] Download failed for scene-{clip_id}")
            failed += 1
    else:
        print(f"  [FAIL] scene-{clip_id}")
        failed += 1

print(f"\n{'='*60}")
print(f"SUMMARY: {total - failed}/{total} clips generated successfully")
print(f"{'='*60}")
if failed:
    print(f"Failed: {failed} clips. Re-run with: python3 generate_clips.py <clip-id>")
