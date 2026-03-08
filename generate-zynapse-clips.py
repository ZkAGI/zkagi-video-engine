#!/usr/bin/env python3
"""Generate LTX-2 text-to-video clips for Zynapse story via ComfyUI."""

import json
import time
import subprocess
import random
import sys

COMFY_URL = "http://172.18.64.1:8001"

# Motion prompts for each scene (novel-like, 40-80 words, with movement)
SCENES = [
    {
        "index": 0,
        "prefix": "scene_0_a",
        "prompt": (
            "Camera slowly pushes into a dimly lit office desk cluttered with multiple glowing laptop screens. "
            "A stressed developer slumps in his chair, rubbing his temples. Credit card bills and receipts flutter "
            "and scatter across the desk from an unseen breeze. Each screen flashes different API dashboards with "
            "red warning indicators. The overhead fluorescent light flickers ominously. Shadows deepen around the edges. "
            "Comic book style, dramatic harsh lighting, halftone dots pattern."
        ),
    },
    {
        "index": 1,
        "prefix": "scene_1_a",
        "prompt": (
            "Camera tracks laterally across a chaotic office as monitors explode with bright red ERROR messages one by one. "
            "A developer pulls at his hair in exaggerated frustration, spinning in his office chair. Sparks fly from a keyboard. "
            "Papers erupt upward like confetti. Each screen flashes RATE LIMITED in bold red letters. "
            "The room lighting shifts from cool blue to angry red. Smoke wisps rise from overheating hardware. "
            "Comic book art style with bold outlines, dynamic energy, dramatic red and orange lighting."
        ),
    },
    {
        "index": 2,
        "prefix": "scene_2_a",
        "prompt": (
            "Camera slowly dollies forward through a dark void toward a magnificent golden API key floating in the center. "
            "The key rotates gently, casting warm light rays in all directions. Holographic icons orbit around it — "
            "an image frame, a film strip, a sound wave, and a glowing shield — all connected by golden threads of light. "
            "Tiny luminous particles drift upward like fireflies. The darkness gradually transforms to warm amber. "
            "Studio Ghibli inspired, magical atmosphere, soft golden glow, cinematic."
        ),
    },
    {
        "index": 3,
        "prefix": "scene_3_a",
        "prompt": (
            "Camera gently pulls back to reveal a happy developer leaning back in a bright modern office chair, "
            "feet on a clean desk, holding a large coffee mug. A single laptop screen shows a simple clean dashboard. "
            "Warm golden sunlight streams through large windows, dust motes floating lazily in the light beams. "
            "A small plant on the desk sways gently. The developer takes a satisfied sip of coffee. "
            "Pixar 3D render style, warm golden hour lighting, cheerful cozy atmosphere, highly detailed."
        ),
    },
    {
        "index": 4,
        "prefix": "scene_4_a",
        "prompt": (
            "Camera holds on a dramatic wide shot as a golden ring of light materializes in a dark cosmic void. "
            "Energy tendrils crackle and radiate outward from the ring in all directions. A silhouetted figure stands below, "
            "reaching upward as golden particles rise from the ground like lanterns. "
            "The ring pulses with power, each pulse sending shockwaves of light rippling through space. "
            "Synthwave aesthetic, purple and gold gradient, neon grid below, epic scale, volumetric light rays, cinematic."
        ),
    },
]


def build_txt2vid_workflow(prompt: str, prefix: str, seed: int) -> dict:
    """Build a text-to-video workflow (no reference image)."""
    return {
        # Load model checkpoint (for MODEL and VAE)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"},
        },
        # Load text encoder (for CLIP)
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
            },
        },
        # Apply distilled LoRA (8 steps, CFG 1.0)
        "3": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],  # MODEL from checkpoint
                "clip": ["2", 0],  # CLIP from text encoder
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
            },
        },
        # Positive prompt
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["3", 1]},  # CLIP after LoRA
        },
        # Negative prompt
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed",
                "clip": ["3", 1],
            },
        },
        # LTX conditioning
        "6": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["4", 0],
                "negative": ["5", 0],
                "frame_rate": 25,
            },
        },
        # Empty video latent (97 frames at 25fps = 3.88s)
        "7": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {"width": 768, "height": 512, "length": 97, "batch_size": 1},
        },
        # LTX scheduler (distilled: 8 steps)
        "8": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 8,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["7", 0],
            },
        },
        # Noise
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        # Guider (CFG 1.0 for distilled)
        "10": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],  # MODEL after LoRA
                "positive": ["6", 0],
                "negative": ["6", 1],
                "cfg": 1.0,
            },
        },
        # Sampler
        "11": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"},
        },
        # Sample
        "12": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["9", 0],
                "guider": ["10", 0],
                "sampler": ["11", 0],
                "sigmas": ["8", 0],
                "latent_image": ["7", 0],
            },
        },
        # Decode video
        "13": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["12", 0],
                "vae": ["1", 2],  # VAE from checkpoint
            },
        },
        # Create video from frames
        "14": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["13", 0], "fps": 25},
        },
        # Save video
        "15": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["14", 0],
                "filename_prefix": prefix,
                "format": "mp4",
                "codec": "h264",
            },
        },
    }


def submit_workflow(workflow: dict) -> str:
    """Submit workflow to ComfyUI and return prompt_id."""
    payload = json.dumps({"prompt": workflow})
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{COMFY_URL}/prompt",
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True, timeout=30
    )
    resp = json.loads(result.stdout)
    if "prompt_id" not in resp:
        print(f"ERROR submitting: {resp}")
        sys.exit(1)
    return resp["prompt_id"]


def poll_completion(prompt_id: str, timeout_s: int = 300) -> dict:
    """Poll for workflow completion."""
    start = time.time()
    while time.time() - start < timeout_s:
        result = subprocess.run(
            ["curl", "-s", f"{COMFY_URL}/history/{prompt_id}"],
            capture_output=True, text=True, timeout=15
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            time.sleep(3)
            continue

        if prompt_id in data:
            status = data[prompt_id].get("status", {}).get("status_str", "")
            outputs = data[prompt_id].get("outputs", {})
            if status == "error":
                print(f"ERROR: Workflow failed")
                print(json.dumps(data[prompt_id].get("status", {}), indent=2))
                sys.exit(1)
            if outputs:
                return data[prompt_id]
        time.sleep(5)
    print(f"TIMEOUT waiting for {prompt_id}")
    sys.exit(1)


def download_video(history: dict, output_path: str):
    """Download the output video file."""
    outputs = history.get("outputs", {})
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    subfolder = item.get("subfolder", "")
                    if fn.endswith(".mp4") or fn.endswith(".webm"):
                        url = f"{COMFY_URL}/view?filename={fn}&type=output"
                        if subfolder:
                            url += f"&subfolder={subfolder}"
                        subprocess.run(
                            ["curl", "-s", url, "--output", output_path],
                            timeout=30
                        )
                        print(f"  Downloaded: {output_path}")
                        return
    print(f"  WARNING: No video found in outputs")


def main():
    for scene in SCENES:
        idx = scene["index"]
        prefix = scene["prefix"]
        prompt = scene["prompt"]
        seed = 10000 + idx * 1000 + random.randint(0, 999)
        output_path = f"public/scenes/scene-{idx}-a.mp4"

        print(f"\n{'='*60}")
        print(f"Scene {idx}: Generating text-to-video clip...")
        print(f"  Seed: {seed}")
        print(f"  Prompt: {prompt[:80]}...")

        workflow = build_txt2vid_workflow(prompt, prefix, seed)
        prompt_id = submit_workflow(workflow)
        print(f"  Submitted: {prompt_id}")

        history = poll_completion(prompt_id)
        download_video(history, output_path)

        # Verify the file
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", output_path],
            capture_output=True, text=True
        )
        print(f"  Duration: {result.stdout.strip()}s")

    print(f"\n{'='*60}")
    print("All video clips generated!")

    # Extract frames for overflow images
    print("\nExtracting overflow frames from video clips...")
    overflow_config = {
        0: {"count": 2, "suffixes": ["b", "c"]},      # 11.20s → 2 overflow
        1: {"count": 2, "suffixes": ["b", "c"]},      # 12.00s → 2 overflow
        2: {"count": 3, "suffixes": ["b", "c", "d"]}, # 13.44s → 3 overflow
        3: {"count": 2, "suffixes": ["b", "c"]},      # 8.64s → 2 overflow
        4: {"count": 1, "suffixes": ["b"]},            # 7.20s → 1 overflow
    }

    for idx, cfg in overflow_config.items():
        video_path = f"public/scenes/scene-{idx}-a.mp4"
        for i, suffix in enumerate(cfg["suffixes"]):
            # Extract frames at different timestamps (spread evenly)
            t = (i + 1) * 3.0 / (cfg["count"] + 1)
            output = f"public/scenes/scene-{idx}-{suffix}.png"
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(t), "-i", video_path,
                 "-frames:v", "1", "-q:v", "2", output],
                capture_output=True, timeout=15
            )
            print(f"  Extracted: {output} (t={t:.1f}s)")

    print("\nDone! All clips and overflow images ready.")


if __name__ == "__main__":
    main()
