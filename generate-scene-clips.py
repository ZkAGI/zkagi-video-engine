#!/usr/bin/env python3
"""Generate LTX-2 video clips for all scenes via ComfyUI."""

import json
import time
import random
import requests
import subprocess
import sys
import os

COMFY_URL = "http://172.18.64.1:8001"
PROJECT = "/home/aten/zkagi-video-engine"

# Motion prompts for each scene (motion-focused, ~50-70 words)
SCENE_PROMPTS = {
    0: "Camera slowly pushes in with slight handheld wobble. A trader hunched over glowing monitors, eyes scanning frantically left and right across charts. Candlestick bars pulse and flicker on screens. Blue monitor light casts shifting shadows across his tense face. Dust particles drift in the glow. Screen reflections shimmer on the desk surface. The atmosphere feels restless and urgent.",
    1: "Camera steadily dollies forward toward a futuristic dashboard. Green signal indicators pulse rhythmically like heartbeats. Holographic trend arrows glow brighter and extend upward. Data streams flow across the interface like rivers of light. A Bitcoin symbol rotates slowly in the center, casting green light outward. Particles of data drift upward. The atmosphere shifts from dark to illuminated green.",
    2: "Camera slowly pulls back to reveal the full scene. A confident trader leans back in his chair, hands behind his head, a satisfied grin spreading across his face. Monitor screens behind him glow with green confirmed positions. Green checkmark notifications cascade gently across screens. Warm amber light from a desk lamp contrasts cool blue monitors. The mood is calm and victorious.",
    3: "Camera trucks right across a split scene composition. On the left, a massive green candlestick shoots upward on a chart, energy lines radiating from its peak. On the right, green profit numbers reflect in a trader's glasses as he smirks. Chart values tick upward rapidly. Golden particles rise from the green candle. The atmosphere crackles with triumphant energy.",
    4: "Camera holds steady then slowly cranes upward. A burst of radiant green energy explodes from the center of frame, forming a logo shape. Holographic interface elements materialize around it, floating and rotating. Volumetric light rays stream outward in all directions. Particles swirl in a vortex overhead. The entire scene bathes in dramatic green and purple neon glow, pulsing with power.",
}

def upload_image(filepath):
    """Upload an image to ComfyUI and return the filename."""
    name = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        resp = requests.post(
            f"{COMFY_URL}/upload/image",
            files={"image": (name, f, "image/png")},
            data={"overwrite": "true"}
        )
    resp.raise_for_status()
    result = resp.json()
    return result.get("name", name)

def build_workflow(uploaded_image_name, motion_prompt, scene_idx):
    """Build the img-to-video workflow with distilled LoRA."""
    seed = random.randint(1, 2**31)

    workflow = {
        # 1. Load checkpoint (MODEL + VAE)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors"
            }
        },
        # 2. Load text encoder (CLIP only)
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
                "device": "cpu"
            }
        },
        # 3. Apply distilled LoRA to model
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 1.0
            }
        },
        # 4. Load reference image
        "4": {
            "class_type": "LoadImage",
            "inputs": {
                "image": uploaded_image_name
            }
        },
        # 5. Preprocess image
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
                "clip": ["2", 0]
            }
        },
        # 7. Negative prompt
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed",
                "clip": ["2", 0]
            }
        },
        # 8. LTX conditioning with frame rate
        "8": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "frame_rate": 25
            }
        },
        # 9. LTXVImgToVideo — inserts reference image, creates latent
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
        # 10. Scheduler
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
        # 11. Random noise
        "11": {
            "class_type": "RandomNoise",
            "inputs": {
                "noise_seed": seed
            }
        },
        # 12. CFG Guider
        "12": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["9", 0],
                "negative": ["9", 1],
                "cfg": 1.0
            }
        },
        # 13. Sampler select
        "13": {
            "class_type": "KSamplerSelect",
            "inputs": {
                "sampler_name": "euler"
            }
        },
        # 14. Sample
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
        # 15. VAE Decode (skip SeparateAVLatent for video-only)
        "15": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["14", 0],
                "vae": ["1", 2]
            }
        },
        # 16. Create VIDEO from IMAGE sequence
        "16": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["15", 0],
                "fps": 25.0
            }
        },
        # 17. Save video
        "17": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["16", 0],
                "filename_prefix": f"scene_{scene_idx}_a",
                "format": "mp4",
                "codec": "h264"
            }
        }
    }
    return workflow

def submit_workflow(workflow):
    """Submit workflow to ComfyUI and return prompt_id."""
    resp = requests.post(
        f"{COMFY_URL}/prompt",
        json={"prompt": workflow}
    )
    resp.raise_for_status()
    return resp.json()["prompt_id"]

def poll_completion(prompt_id, timeout=300):
    """Poll for workflow completion."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{COMFY_URL}/history/{prompt_id}")
        data = resp.json()
        if prompt_id in data:
            status = data[prompt_id].get("status", {}).get("status_str", "")
            outputs = data[prompt_id].get("outputs", {})
            if status == "error":
                print(f"  ERROR: {json.dumps(data[prompt_id].get('status', {}), indent=2)}")
                return None
            if outputs:
                return data[prompt_id]
        time.sleep(3)
    print(f"  TIMEOUT after {timeout}s")
    return None

def download_video(prompt_id, result, output_path):
    """Download the generated video."""
    outputs = result.get("outputs", {})
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
                        resp = requests.get(url)
                        resp.raise_for_status()
                        with open(output_path, "wb") as f:
                            f.write(resp.content)
                        print(f"  Downloaded: {output_path} ({len(resp.content)} bytes)")
                        return True
    print(f"  No video found in outputs")
    return False

def main():
    scenes = [0, 1, 2, 3, 4]
    if len(sys.argv) > 1:
        scenes = [int(x) for x in sys.argv[1:]]

    for scene_idx in scenes:
        print(f"\n{'='*60}")
        print(f"Scene {scene_idx}")
        print(f"{'='*60}")

        # Upload reference image
        img_path = f"{PROJECT}/public/scenes/scene-{scene_idx}-a.png"
        print(f"  Uploading {img_path}...")
        uploaded_name = upload_image(img_path)
        print(f"  Uploaded as: {uploaded_name}")

        # Build and submit workflow
        prompt = SCENE_PROMPTS[scene_idx]
        print(f"  Motion prompt: {prompt[:80]}...")
        workflow = build_workflow(uploaded_name, prompt, scene_idx)

        prompt_id = submit_workflow(workflow)
        print(f"  Submitted: {prompt_id}")

        # Poll for completion
        print(f"  Waiting for completion...")
        result = poll_completion(prompt_id, timeout=300)

        if result:
            output_path = f"{PROJECT}/public/scenes/scene-{scene_idx}-a.mp4"
            download_video(prompt_id, result, output_path)

            # Check duration
            dur = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", output_path],
                capture_output=True, text=True
            )
            print(f"  Duration: {dur.stdout.strip()}s")
        else:
            print(f"  FAILED for scene {scene_idx}")

    print(f"\nAll done!")

if __name__ == "__main__":
    main()
