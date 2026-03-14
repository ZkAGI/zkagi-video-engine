#!/usr/bin/env python3
"""Generate remaining LTX-2 video clips with 97 frames to avoid OOM."""

import json
import time
import random
import requests
import subprocess
import sys
import os

COMFY_URL = "http://172.18.64.1:8001"
PROJECT_DIR = "/home/aten/zkagi-video-engine"

# Remaining clips to generate (all 97 frames to avoid OOM)
CLIPS = [
    # Scene 1: still need b, c (use 97 frames instead of 121)
    (1, "b", "Camera pushes in on a creative robot painting station. The robot's digital canvas erupts with colorful images that fly outward in all directions. Splashes of neon digital paint arc through the air creating rainbow trails. Colors shift and morph on floating canvases spinning slowly."),
    (1, "c", "Camera zooms into a busy trading desk. A robot in a business suit frantically slams buttons as bright green arrows shoot upward on multiple screens. Trading charts pulse with cascading numbers. Red and green candles grow rapidly. The robot pumps its tiny fist triumphantly as profit numbers flash."),

    # Scene 2: all 3 clips needed
    (2, "a", "Camera gently pushes in on a cozy break room scene. A person takes a sip of water and chuckles. A holographic AI face floats above the counter, animating with nodding and hand gestures. Speech bubbles with chart icons float upward and pop with sparkle effects. Warm ambient light fills the room."),
    (2, "b", "Camera orbits slowly around the break room. The holographic chatbot projects rotating 3D charts and graphs in mid-air. Potted plants in the background sway gently. Steam curls upward from a coffee mug on the counter. Light shifts through venetian blinds creating moving stripe patterns on the wall."),
    (2, "c", "Camera slowly pulls back revealing the empty office beyond the break room. The holographic AI assistant waves its hand as speech bubbles fade into particles. The person walks away smiling toward their desk. Overhead lights glow softly in the vacant workspace."),

    # Scene 3: all 3 clips needed (97 frames instead of 121)
    (3, "a", "Camera slowly trucks from left to right starting on a tropical beach. A hammock sways gently in the ocean breeze. Palm tree fronds wave slowly casting dappled shadows. Turquoise ocean waves roll in and recede on white sand. A cocktail umbrella spins lazily in a drink resting on the sand."),
    (3, "b", "Camera continues trucking right into a massive glowing server room. Holographic screens flicker rapidly displaying AI-generated images and videos rendering frame by frame. Rivers of light data stream between tall server racks. Robotic arms sort and stack glowing translucent files on shelves."),
    (3, "c", "Camera pulls back to reveal the full split scene from beach to server room. Warm golden beach light contrasts dramatically with cool blue server glow. The person in the hammock stretches contentedly. All server screens simultaneously flash green with completed task icons."),

    # Scene 4: all 2 clips needed
    (4, "a", "Camera pushes in dramatically on a person in an executive chair. They kick back and do confident finger guns toward the camera. Confetti explodes from both sides of the frame showering down. An Employee of the Month holographic frame pulses and glows brighter with API text inside."),
    (4, "b", "Camera slowly orbits the desk in a hero arc. A golden trophy gleams with starburst light effects on the desk surface. Floating holographic screens display glowing API text that pulsates rhythmically. Confetti drifts downward catching neon light."),
]


def build_workflow(image_name, motion_prompt, seed, prefix):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}},
        "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "gemma_3_12B_it.safetensors", "clip_name2": "ltx-2.3_text_projection_bf16.safetensors", "type": "ltx"}},
        "3": {"class_type": "LoraLoader", "inputs": {"model": ["1", 0], "clip": ["2", 0], "lora_name": "ltx-2.3-distilled-lora-384.safetensors", "strength_model": 1.0, "strength_clip": 1.0}},
        "4": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "5": {"class_type": "LTXVPreprocess", "inputs": {"image": ["4", 0], "img_compression": 35}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": motion_prompt, "clip": ["3", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, extra limbs, bad anatomy", "clip": ["3", 1]}},
        "8": {"class_type": "LTXVConditioning", "inputs": {"positive": ["6", 0], "negative": ["7", 0], "frame_rate": 25}},
        "9": {"class_type": "LTXVImgToVideo", "inputs": {"positive": ["8", 0], "negative": ["8", 1], "vae": ["1", 2], "image": ["5", 0], "width": 768, "height": 512, "length": 97, "batch_size": 1, "strength": 1.0}},
        "10": {"class_type": "LTXVScheduler", "inputs": {"steps": 8, "max_shift": 2.05, "base_shift": 0.95, "stretch": True, "terminal": 0.1, "latent": ["9", 2]}},
        "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "12": {"class_type": "CFGGuider", "inputs": {"model": ["3", 0], "positive": ["9", 0], "negative": ["9", 1], "cfg": 1.0}},
        "13": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["11", 0], "guider": ["12", 0], "sampler": ["13", 0], "sigmas": ["10", 0], "latent_image": ["9", 2]}},
        "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}},
        "16": {"class_type": "CreateVideo", "inputs": {"images": ["15", 0], "fps": 25.0}},
        "17": {"class_type": "SaveVideo", "inputs": {"video": ["16", 0], "filename_prefix": prefix, "format": "mp4", "codec": "h264"}},
    }


def main():
    print("Uploading images...", flush=True)
    image_names = {}
    for scene_idx in range(5):
        img_path = f"{PROJECT_DIR}/public/scenes/scene-{scene_idx}-a.png"
        fn = os.path.basename(img_path)
        with open(img_path, 'rb') as f:
            resp = requests.post(f"{COMFY_URL}/upload/image", files={"image": (fn, f, "image/png")}, data={"overwrite": "true"})
        image_names[scene_idx] = resp.json().get("name", fn)
        print(f"  Uploaded scene-{scene_idx}: {image_names[scene_idx]}", flush=True)

    print(f"\nSubmitting {len(CLIPS)} workflows...", flush=True)
    jobs = []
    for scene_idx, sub, motion in CLIPS:
        prefix = f"scene_{scene_idx}_{sub}"
        seed = random.randint(1, 2**31)
        workflow = build_workflow(image_names[scene_idx], motion, seed, prefix)
        resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
        result = resp.json()
        if "error" in result:
            print(f"  ERROR submitting {prefix}: {result.get('error','?')}", flush=True)
            if "node_errors" in result:
                for nid, err in result["node_errors"].items():
                    print(f"    Node {nid}: {err}", flush=True)
            continue
        pid = result["prompt_id"]
        dest = f"{PROJECT_DIR}/public/scenes/scene-{scene_idx}-{sub}.mp4"
        jobs.append((pid, dest, f"scene-{scene_idx}-{sub}"))
        print(f"  Queued: {prefix} → {pid[:12]}...", flush=True)

    print(f"\nWaiting for {len(jobs)} clips...", flush=True)
    completed = 0
    for pid, dest, label in jobs:
        print(f"\n  Generating {label}...", flush=True)
        start = time.time()
        while time.time() - start < 600:
            resp = requests.get(f"{COMFY_URL}/history/{pid}")
            data = resp.json()
            if pid in data:
                status = data[pid].get("status", {}).get("status_str", "")
                outputs = data[pid].get("outputs", {})
                if status == "error":
                    msgs = data[pid].get("status", {}).get("messages", [])
                    print(f"  ERROR: {label}", flush=True)
                    for m in msgs[-2:]:
                        if isinstance(m, list) and len(m) > 1:
                            err_msg = str(m[1])[:300]
                            print(f"    {m[0]}: {err_msg}", flush=True)
                    break
                if outputs:
                    # Download the video
                    for nid, out in outputs.items():
                        for key in ["images", "animated", "videos", "gifs"]:
                            if key in out and isinstance(out[key], list):
                                for item in out[key]:
                                    if isinstance(item, dict):
                                        fn = item.get("filename", "")
                                        if fn.endswith(".mp4"):
                                            sf = item.get("subfolder", "")
                                            url = f"{COMFY_URL}/view?filename={fn}&type=output"
                                            if sf:
                                                url += f"&subfolder={sf}"
                                            r = requests.get(url)
                                            with open(dest, "wb") as f:
                                                f.write(r.content)
                                            dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dest], capture_output=True, text=True).stdout.strip()
                                            sz = os.path.getsize(dest) / (1024*1024)
                                            print(f"  DONE: {label} ({dur}s, {sz:.1f}MB)", flush=True)
                                            completed += 1
                    break
            elapsed = int(time.time() - start)
            if elapsed % 30 == 0 and elapsed > 0:
                print(f"    ...{elapsed}s elapsed", flush=True)
            time.sleep(5)

    print(f"\n{'='*50}", flush=True)
    print(f"Completed: {completed}/{len(jobs)} clips", flush=True)


if __name__ == "__main__":
    main()
