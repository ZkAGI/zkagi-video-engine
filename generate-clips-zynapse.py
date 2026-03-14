#!/usr/bin/env python3
"""Generate LTX-2 text-to-video clips for Zynapse Content Factory demo."""

import json
import time
import random
import urllib.request
import urllib.error
import subprocess
import os

COMFY_URL = "http://172.18.64.1:8001"
OUTPUT_DIR = "/home/aten/zkagi-video-engine/public/scenes"

SCENES = [
    {
        "index": 0,
        "prompt": "Camera slowly dollies forward through a vast abandoned corporate office at night. Rows of empty ergonomic chairs sit before dark dual monitors, papers flutter gently on the floor from an unseen draft. A single fluorescent light flickers overhead, casting harsh shadows that stretch and shift across the desks. Dust particles drift lazily in the cold blue light. The atmosphere is desolate and eerie, suggesting a workspace suddenly abandoned.",
    },
    {
        "index": 1,
        "prompt": "Camera handheld with slight nervous wobble. An overwhelmed office worker sits surrounded by a storm of floating notification bubbles and message alerts, hands gripping their head in frustration. Multiple screens around them flash with red overdue warnings and revision counters ticking up. Sticky notes peel off walls and swirl through the air. The fluorescent lights pulse with increasing intensity. Papers cascade off the desk in slow motion.",
    },
    {
        "index": 2,
        "prompt": "Camera slowly pushes in on a sleek dark terminal window floating in a futuristic void. Three lines of glowing cyan code appear one by one, each followed by a green success indicator that pulses with light. Holographic data streams flow outward from the terminal like ribbons of light. A neon grid stretches below into infinity. Particles of light scatter and reform around the terminal. The atmosphere shifts from dark to warm as each API call completes successfully.",
    },
    {
        "index": 3,
        "prompt": "Camera trucks right across a dramatic triptych display. Left panel materializes showing a polished product photograph forming from particles of light. Center panel reveals a video playing in slow motion with a timeline scrubber advancing. Right panel shows an audio waveform pulsing with life. Glowing cyan data lines connect all three panels, energy flowing between them. The whole scene bathes in professional blue and cyan lighting. Clean geometric frames surround each panel.",
    },
    {
        "index": 4,
        "prompt": "Camera starts close on glowing text spelling out a URL, then dramatically pulls back to reveal a massive translucent privacy shield made of hexagonal geometric patterns surrounding it. Small proof symbols orbit like electrons around the shield. Energy ripples across the hexagonal surface. A burst of cyan and purple light radiates outward from the center. The atmosphere is triumphant and energetic, with particles rising upward like floating lanterns.",
    },
]

NEG_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, letters, words, numbers"


def build_workflow(scene_index: int, prompt: str, seed: int) -> dict:
    return {
        # 1: CheckpointLoaderSimple → MODEL(0), CLIP(1,unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"},
        },
        # 2: DualCLIPLoader → CLIP(0)
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                "type": "ltx",
            },
        },
        # 3: LoraLoader (model from #1[0], clip from #2[0]) → MODEL(0), CLIP(1)
        "3": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["2", 0],
                "lora_name": "ltx-2.3-distilled-lora-384.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
            },
        },
        # 4: Positive prompt
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["3", 1]},
        },
        # 5: Negative prompt
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEG_PROMPT, "clip": ["3", 1]},
        },
        # 6: LTXVConditioning
        "6": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["4", 0],
                "negative": ["5", 0],
                "frame_rate": 25.0,
            },
        },
        # 7: EmptyLTXVLatentVideo (text-to-video, no reference image)
        "7": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {
                "width": 768,
                "height": 512,
                "length": 97,
                "batch_size": 1,
            },
        },
        # 8: LTXVScheduler (distilled: 8 steps)
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
        # 9: RandomNoise
        "9": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed},
        },
        # 10: CFGGuider (distilled: cfg=1.0)
        "10": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["6", 0],
                "negative": ["6", 1],
                "cfg": 1.0,
            },
        },
        # 11: KSamplerSelect
        "11": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"},
        },
        # 12: SamplerCustomAdvanced
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
        # 13: VAEDecode
        "13": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["12", 0],
                "vae": ["1", 2],
            },
        },
        # 14: CreateVideo
        "14": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["13", 0],
                "fps": 25.0,
            },
        },
        # 15: SaveVideo
        "15": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["14", 0],
                "filename_prefix": f"scene-{scene_index}-a",
                "format": "mp4",
                "codec": "h264",
            },
        },
    }


def submit_workflow(workflow: dict) -> str:
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result["prompt_id"]


def poll_completion(prompt_id: str, timeout: int = 300) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            data = json.loads(resp.read())
            if prompt_id in data:
                status = data[prompt_id].get("status", {}).get("status_str", "")
                outputs = data[prompt_id].get("outputs", {})
                if status == "error":
                    print(f"  ERROR: {json.dumps(data[prompt_id].get('status', {}))}")
                    return None
                if outputs:
                    return data[prompt_id]
        except Exception as e:
            print(f"  Poll error: {e}")
        time.sleep(3)
    print(f"  TIMEOUT after {timeout}s")
    return None


def download_video(result: dict, output_path: str) -> bool:
    outputs = result.get("outputs", {})
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    subfolder = item.get("subfolder", "")
                    if fn.endswith(".mp4"):
                        url = f"{COMFY_URL}/view?filename={fn}&type=output"
                        if subfolder:
                            url += f"&subfolder={subfolder}"
                        urllib.request.urlretrieve(url, output_path)
                        print(f"  Downloaded: {output_path}")
                        return True
    print("  No MP4 found in outputs")
    return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for scene in SCENES:
        idx = scene["index"]
        prompt = scene["prompt"]
        seed = random.randint(1, 2**31)
        output_path = os.path.join(OUTPUT_DIR, f"scene-{idx}-a.mp4")

        print(f"\n{'='*60}")
        print(f"Scene {idx}: Generating text-to-video clip...")
        print(f"  Prompt: {prompt[:80]}...")
        print(f"  Seed: {seed}")

        workflow = build_workflow(idx, prompt, seed)
        prompt_id = submit_workflow(workflow)
        print(f"  Submitted: {prompt_id}")

        result = poll_completion(prompt_id, timeout=300)
        if result:
            download_video(result, output_path)
            # Verify
            dur = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", output_path],
                capture_output=True, text=True
            )
            print(f"  Duration: {dur.stdout.strip()}s")
        else:
            print(f"  FAILED for scene {idx}")

    # Extract Ken Burns overflow frames from each video
    print(f"\n{'='*60}")
    print("Extracting overflow frames for Ken Burns...")
    overflow_map = {
        0: ["b"],              # 6.40s → 1 extra
        1: ["b", "c"],         # 11.04s → 2 extra
        2: ["b", "c", "d"],    # 15.20s → 3 extra
        3: ["b", "c"],         # 11.20s → 2 extra
        4: ["b", "c"],         # 8.96s → 2 extra
    }

    for idx, suffixes in overflow_map.items():
        video_path = os.path.join(OUTPUT_DIR, f"scene-{idx}-a.mp4")
        if not os.path.exists(video_path):
            print(f"  Skipping scene {idx} - no video")
            continue

        for i, suffix in enumerate(suffixes):
            # Extract frame at different timestamps for variety
            # Spread frames across the video: 1s, 2s, 3s
            timestamp = (i + 1) * 1.0
            out_img = os.path.join(OUTPUT_DIR, f"scene-{idx}-{suffix}.png")
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path,
                 "-vframes", "1", "-q:v", "2", out_img],
                capture_output=True
            )
            if os.path.exists(out_img):
                print(f"  Extracted: scene-{idx}-{suffix}.png (t={timestamp}s)")
            else:
                print(f"  FAILED: scene-{idx}-{suffix}.png")

    print(f"\n{'='*60}")
    print("All clips generated!")


if __name__ == "__main__":
    main()
