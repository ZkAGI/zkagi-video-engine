#!/usr/bin/env python3
"""Generate LTX-2 video clips for Zero-Employee Enterprise video via ComfyUI."""

import json
import time
import random
import requests
import subprocess
import sys
import os

COMFY_URL = "http://172.18.64.1:8001"
PROJECT_DIR = "/home/aten/zkagi-video-engine"

# Motion prompts per scene (novel-like, 40-80 words each)
MOTION_PROMPTS = {
    0: (
        "Camera slowly dollies forward toward the desk. The person leans back confidently, "
        "fingers tapping on the desk. Multiple monitor screens flicker with changing dashboard "
        "data, charts updating and numbers scrolling. Warm desk lamp light casts gentle shadows "
        "that shift slightly. Tiny dust particles float lazily in the lamplight. "
        "The person turns to face camera with a knowing smile."
    ),
    1: (
        "Camera holds steady with slight handheld wobble. The robot's multiple mechanical arms "
        "move busily, stamping papers, filing documents, and typing simultaneously. Papers flutter "
        "and stack themselves neatly. A filing cabinet drawer slides open and closed. The robot's "
        "head swivels to check different tasks, LED eyes blinking. Office plant leaves sway gently "
        "from the motion of the arms."
    ),
    2: (
        "Camera slowly trucks right across the split scene. On the left, the person casually lifts "
        "a spoon of cereal to their mouth, chewing contentedly. On the right, screens rapidly cycle "
        "through colorful marketing images being auto-generated, social media posts appearing and "
        "stacking, progress bars filling. Digital particles flow between the screens."
    ),
    3: (
        "Camera slowly orbits the isometric scene. The tiny robot trader's arms move frantically "
        "across keyboards, slamming buttons. Green arrows and numbers scroll upward on the trading "
        "screens. A chat bubble near the water cooler inflates and pops with a new message. "
        "Coins and data particles float upward from the desk. The screens pulse with green light."
    ),
    4: (
        "Camera slowly pushes in with dramatic energy. The person leans back triumphantly as "
        "holographic API icons pulse and orbit around them like satellites. Robot assistants in the "
        "background move purposefully, carrying glowing data packets. Neon purple and teal light "
        "rays sweep across the scene. Energy particles rise from below like embers. "
        "The synthwave grid on the floor pulses with light waves radiating outward."
    ),
}


def build_workflow(image_name: str, motion_prompt: str, seed: int, prefix: str):
    """Build ComfyUI workflow for image-to-video with distilled LoRA."""
    return {
        # 1: CheckpointLoaderSimple → MODEL(0), CLIP(1, unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"}
        },
        # 2: LTXAVTextEncoderLoader → CLIP(0) ONLY
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors"
            }
        },
        # 3: LoRA (distilled, model only)
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 1.0
            }
        },
        # 4: Load reference image
        "4": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name}
        },
        # 5: Preprocess image
        "5": {
            "class_type": "LTXVPreprocess",
            "inputs": {"image": ["4", 0], "img_compression": 35}
        },
        # 6: Positive prompt — CLIP from node 2 (text encoder), not checkpoint
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": motion_prompt, "clip": ["2", 0]}
        },
        # 7: Negative prompt
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed",
                "clip": ["2", 0]
            }
        },
        # 8: LTXVConditioning
        "8": {
            "class_type": "LTXVConditioning",
            "inputs": {"positive": ["6", 0], "negative": ["7", 0], "frame_rate": 25}
        },
        # 9: LTXVImgToVideo → positive(0), negative(1), latent(2)
        "9": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["8", 0], "negative": ["8", 1],
                "vae": ["1", 2], "image": ["5", 0],
                "width": 768, "height": 512, "length": 97,
                "batch_size": 1, "strength": 1.0
            }
        },
        # 10: LTXVScheduler (distilled: 8 steps)
        "10": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 8, "max_shift": 2.05, "base_shift": 0.95,
                "stretch": True, "terminal": 0.1, "latent": ["9", 2]
            }
        },
        # 11: Random noise
        "11": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed}
        },
        # 12: CFG Guider (cfg=1.0 for distilled) — MODEL from LoRA output
        "12": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0], "positive": ["9", 0],
                "negative": ["9", 1], "cfg": 1.0
            }
        },
        # 13: Sampler
        "13": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
        # 14: Sample
        "14": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["11", 0], "guider": ["12", 0],
                "sampler": ["13", 0], "sigmas": ["10", 0],
                "latent_image": ["9", 2]
            }
        },
        # 15: VAE Decode
        "15": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["14", 0], "vae": ["1", 2]}
        },
        # 16: Create Video
        "16": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["15", 0], "fps": 25.0}
        },
        # 17: Save Video
        "17": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["16", 0], "filename_prefix": prefix,
                "format": "mp4", "codec": "h264"
            }
        }
    }


def upload_image(filepath: str) -> str:
    """Upload an image to ComfyUI and return its name."""
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        resp = requests.post(
            f"{COMFY_URL}/upload/image",
            files={"image": (filename, f, "image/png")},
            data={"overwrite": "true"}
        )
    result = resp.json()
    print(f"  Uploaded {filename}: {result}")
    return result.get("name", filename)


def submit_workflow(workflow: dict) -> str:
    """Submit a workflow to ComfyUI and return prompt_id."""
    resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    result = resp.json()
    if "error" in result:
        print(f"  ERROR: {result['error']}")
        if "node_errors" in result:
            for nid, err in result["node_errors"].items():
                print(f"    Node {nid}: {err}")
        return None
    prompt_id = result["prompt_id"]
    print(f"  Submitted: {prompt_id}")
    return prompt_id


def poll_completion(prompt_id: str, timeout: int = 300) -> dict:
    """Poll until workflow completes."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            data = resp.json()
            if prompt_id in data:
                status = data[prompt_id].get("status", {}).get("status_str", "")
                outputs = data[prompt_id].get("outputs", {})
                if status == "error":
                    print(f"  ERROR in workflow")
                    msgs = data[prompt_id].get("status", {}).get("messages", [])
                    for msg in msgs:
                        print(f"    {msg}")
                    return None
                if outputs:
                    return outputs
        except Exception as e:
            print(f"  Poll error: {e}")
        time.sleep(5)
    print(f"  TIMEOUT after {timeout}s")
    return None


def download_video(outputs: dict, dest_path: str) -> bool:
    """Download the output video."""
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
                        resp = requests.get(url)
                        with open(dest_path, "wb") as f:
                            f.write(resp.content)
                        result = subprocess.run(
                            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "csv=p=0", dest_path],
                            capture_output=True, text=True
                        )
                        dur = result.stdout.strip()
                        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
                        print(f"  Downloaded: {dest_path} ({dur}s, {size_mb:.1f}MB)")
                        return True
    print(f"  No video found in outputs")
    return False


def main():
    scenes_to_gen = list(range(5))
    if len(sys.argv) > 1:
        scenes_to_gen = [int(x) for x in sys.argv[1:]]

    print("=" * 60)
    print("LTX-2 Video Generation: Zero-Employee Enterprise")
    print(f"Scenes: {scenes_to_gen}")
    print("=" * 60)

    for scene_idx in scenes_to_gen:
        img_path = f"{PROJECT_DIR}/public/scenes/scene-{scene_idx}-a.png"
        out_path = f"{PROJECT_DIR}/public/scenes/scene-{scene_idx}-a.mp4"

        if not os.path.exists(img_path):
            print(f"\n[Scene {scene_idx}] SKIP — {img_path} not found")
            continue
        if os.path.getsize(img_path) < 1024:
            print(f"\n[Scene {scene_idx}] SKIP — image too small ({os.path.getsize(img_path)} bytes)")
            continue

        print(f"\n[Scene {scene_idx}] Uploading reference image...")
        try:
            server_name = upload_image(img_path)
        except Exception as e:
            print(f"  Upload failed: {e}")
            continue

        seed = random.randint(1, 2**31)
        prefix = f"scene_{scene_idx}_a"
        workflow = build_workflow(server_name, MOTION_PROMPTS[scene_idx], seed, prefix)

        print(f"[Scene {scene_idx}] Submitting workflow (seed={seed})...")
        prompt_id = submit_workflow(workflow)
        if not prompt_id:
            continue

        print(f"[Scene {scene_idx}] Generating (~60s)...")
        outputs = poll_completion(prompt_id, timeout=300)
        if outputs:
            download_video(outputs, out_path)
        else:
            print(f"[Scene {scene_idx}] FAILED")

    print("\n" + "=" * 60)
    print("Results:")
    for i in scenes_to_gen:
        p = f"{PROJECT_DIR}/public/scenes/scene-{i}-a.mp4"
        if os.path.exists(p):
            s = os.path.getsize(p) / (1024*1024)
            print(f"  scene-{i}-a.mp4  {s:.1f}MB")
        else:
            print(f"  scene-{i}-a.mp4  MISSING")


if __name__ == "__main__":
    main()
