#!/usr/bin/env python3
"""Generate LTX-2 video clips for each scene via ComfyUI."""

import json
import time
import random
import requests
import sys
import os

COMFY_URL = "http://172.18.64.1:8001"
SCENES_DIR = "/home/aten/zkagi-video-engine/public/scenes"

# Motion prompts per scene (novel-like, descriptive)
MOTION_PROMPTS = [
    # Scene 0: Robot hand typing (HOOK)
    "Camera slowly pushes in on chrome robot fingers rapidly typing on a glowing holographic keyboard. Green and cyan code cascades across multiple monitors, reflections dancing on the chrome surface. Sparks of digital particles rise from the keyboard with each keystroke. Rim lighting from monitors pulses rhythmically. Atmospheric haze drifts through the dark room.",

    # Scene 1: Factory assembly line (TWIST)
    "Camera trucks right across a futuristic factory floor. Multiple robotic arms swing into action simultaneously, one arm paints sweeping brushstrokes on a canvas, another cuts and splices film strips, a third scribes flowing text. Sparks fly from welding joints. Neon lights pulse along the ceiling. Conveyor belts carry finished creative works forward through the assembly line.",

    # Scene 2: Infinite recursion/meta (META MOMENT)
    "Camera slowly dollies forward into a tunnel of nested screens stretching to infinity. Each screen flickers with video content being assembled in real-time. Blue and purple light pulses ripple from the center outward through each layer. Glitch artifacts shimmer at the edges. Digital particles drift between the recursive screen layers. The depth creates a mesmerizing vortex.",

    # Scene 3: Boring vs creative comparison (ROAST)
    "Camera holds on a wide split scene. On the left, a presenter gestures weakly at a flat pie chart, the audience slumps in dim fluorescent light. On the right, a glowing AI robot directs beams of colorful light that transform into video scenes. Explosions of particles and energy burst from the robot side. The contrast between dim left and vibrant right intensifies dramatically.",

    # Scene 4: Text prompt explosion (MIC DROP)
    "Camera slowly pushes in on a glowing text prompt floating in dark space. Energy crackles and arcs around it, building intensity. Suddenly the prompt shatters outward, fragments transforming into video clips, images, and audio waveforms radiating in all directions. Golden light floods the scene. Particles spiral in a triumphant vortex overhead. Camera pulls back to reveal the full creative explosion.",
]

def build_workflow(image_filename: str, motion_prompt: str, scene_prefix: str, seed: int = None):
    """Build ComfyUI workflow for image-to-video generation."""
    if seed is None:
        seed = random.randint(0, 2**31)

    return {
        # 1. CheckpointLoaderSimple → MODEL(0), CLIP(1, unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"
            }
        },
        # 2. DualCLIPLoader → CLIP(0) only
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                "type": "ltx"
            }
        },
        # 3. LoRA loader (distilled, 8 steps)
        "3": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["2", 0],
                "lora_name": "ltx-2.3-distilled-lora-384.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0
            }
        },
        # 4. LoadImage
        "4": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_filename
            }
        },
        # 5. LTXVPreprocess
        "5": {
            "class_type": "LTXVPreprocess",
            "inputs": {
                "image": ["4", 0],
                "img_compression": 35
            }
        },
        # 6. Positive prompt (motion-focused)
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": motion_prompt,
                "clip": ["3", 1]
            }
        },
        # 7. Negative prompt
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed",
                "clip": ["3", 1]
            }
        },
        # 8. LTXVConditioning
        "8": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "frame_rate": 25
            }
        },
        # 9. LTXVImgToVideo → positive(0), negative(1), latent(2)
        "9": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["8", 0],
                "negative": ["8", 1],
                "vae": ["1", 2],
                "image": ["5", 0],
                "width": 768,
                "height": 512,
                "length": 97,
                "batch_size": 1,
                "strength": 1.0
            }
        },
        # 10. LTXVScheduler (8 steps for distilled)
        "10": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 8,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["9", 2]
            }
        },
        # 11. RandomNoise
        "11": {
            "class_type": "RandomNoise",
            "inputs": {
                "noise_seed": seed
            }
        },
        # 12. CFGGuider (cfg=1.0 for distilled)
        "12": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["9", 0],
                "negative": ["9", 1],
                "cfg": 1.0
            }
        },
        # 13. KSamplerSelect
        "13": {
            "class_type": "KSamplerSelect",
            "inputs": {
                "sampler_name": "euler"
            }
        },
        # 14. SamplerCustomAdvanced
        "14": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["11", 0],
                "guider": ["12", 0],
                "sampler": ["13", 0],
                "sigmas": ["10", 0],
                "latent_image": ["9", 2]
            }
        },
        # 15. VAEDecode (skip SeparateAVLatent for video-only)
        "15": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["14", 0],
                "vae": ["1", 2]
            }
        },
        # 16. CreateVideo (IMAGE → VIDEO)
        "16": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["15", 0],
                "fps": 25.0
            }
        },
        # 17. SaveVideo
        "17": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["16", 0],
                "filename_prefix": f"video/{scene_prefix}",
                "format": "mp4",
                "codec": "h264"
            }
        }
    }


def upload_image(filepath: str) -> str:
    """Upload image to ComfyUI and return the server filename."""
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        resp = requests.post(
            f"{COMFY_URL}/upload/image",
            files={"image": (filename, f, "image/png")},
            data={"overwrite": "true"}
        )
    result = resp.json()
    return result.get("name", filename)


def submit_workflow(workflow: dict) -> str:
    """Submit workflow and return prompt_id."""
    resp = requests.post(
        f"{COMFY_URL}/prompt",
        json={"prompt": workflow}
    )
    data = resp.json()
    if "error" in data:
        print(f"  ERROR submitting: {data['error']}")
        if "node_errors" in data:
            for nid, err in data["node_errors"].items():
                print(f"    Node {nid}: {err}")
        return None
    return data["prompt_id"]


def poll_completion(prompt_id: str, timeout: int = 300) -> dict:
    """Poll until workflow completes. Returns output dict or None."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            data = resp.json()
            if prompt_id in data:
                status = data[prompt_id].get("status", {}).get("status_str", "")
                if status == "error":
                    print(f"  Workflow ERROR")
                    return None
                outputs = data[prompt_id].get("outputs", {})
                if outputs:
                    return outputs
        except Exception as e:
            print(f"  Poll error: {e}")
        time.sleep(3)
    print(f"  TIMEOUT after {timeout}s")
    return None


def download_video(outputs: dict, dest_path: str) -> bool:
    """Download the output video from ComfyUI."""
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
                        print(f"  Downloaded: {dest_path} ({len(resp.content)} bytes)")
                        return True
    print(f"  No video found in outputs")
    return False


def generate_scene(scene_idx: int):
    """Generate video clip for a single scene."""
    image_path = f"{SCENES_DIR}/scene-{scene_idx}-a.png"
    output_path = f"{SCENES_DIR}/scene-{scene_idx}-a.mp4"
    motion_prompt = MOTION_PROMPTS[scene_idx]

    print(f"\n{'='*60}")
    print(f"SCENE {scene_idx}: Generating video clip")
    print(f"{'='*60}")

    # 1. Upload image
    print(f"  Uploading {image_path}...")
    if not os.path.exists(image_path):
        print(f"  ERROR: Image not found: {image_path}")
        return False
    server_filename = upload_image(image_path)
    print(f"  Uploaded as: {server_filename}")

    # 2. Build and submit workflow
    workflow = build_workflow(server_filename, motion_prompt, f"scene-{scene_idx}-a")
    print(f"  Submitting workflow...")
    prompt_id = submit_workflow(workflow)
    if not prompt_id:
        return False
    print(f"  Prompt ID: {prompt_id}")

    # 3. Poll for completion
    print(f"  Generating video (~60s)...")
    outputs = poll_completion(prompt_id, timeout=300)
    if not outputs:
        return False

    # 4. Download
    return download_video(outputs, output_path)


def main():
    # Generate specified scenes, or all 5
    if len(sys.argv) > 1:
        scenes = [int(x) for x in sys.argv[1:]]
    else:
        scenes = list(range(5))

    print(f"Generating videos for scenes: {scenes}")
    results = {}
    for idx in scenes:
        success = generate_scene(idx)
        results[idx] = success
        if not success:
            print(f"  FAILED scene {idx}")

    print(f"\n{'='*60}")
    print("RESULTS:")
    for idx, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  Scene {idx}: {status}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
