#!/usr/bin/env python3
"""Generate LTX-2 video clips for Zero-Employee Enterprise video via ComfyUI."""

import json
import random
import time
import subprocess
import sys
import urllib.request
import urllib.parse
import os

COMFY_URL = "http://172.18.64.1:8001"
SCENES_DIR = "public/scenes"

# Motion prompts per scene (novel-like, descriptive, 40-80 words)
MOTION_PROMPTS = [
    # Scene 0: Founder at desk
    "Camera slowly dollies forward toward a confident man sitting alone at a sleek modern desk. He leans back casually in his chair, fingers tapping the laptop keyboard. Empty office chairs around him shift slightly as if ghost employees just left. Warm golden sunlight streams through windows, casting long shadows across empty desks. Dust particles drift lazily in the light beams. The laptop screen glows brighter as charts animate upward.",

    # Scene 1: Robot with AI screens
    "Camera slowly orbits around a small robot in a business suit surrounded by floating holographic screens. The robot's arms blur as it rapidly works across multiple displays. On one screen HR documents shuffle and sort themselves. On another, colorful marketing images materialize from brushstrokes of light. Trading charts pulse with green arrows shooting upward. Neon particles spiral around the robot. The screens glow brighter with each completed task.",

    # Scene 2: Water cooler chatbot
    "Camera holds on a medium shot as a man stands next to a water cooler, gesturing and talking to a floating holographic chatbot face. The chatbot's expression shifts from listening to nodding wisely, its glow pulsing warmly. A speech bubble materializes with glowing text. The man reacts with surprised delight, pointing at the chatbot. Warm claymation-style lighting shifts subtly. Empty office chairs in background remain perfectly still, emphasizing the loneliness.",

    # Scene 3: Beach with AI working
    "Camera slowly pulls back from a man relaxing in a hammock on a tropical beach, coconut drink in hand. Behind him, holographic screens float above the turquoise water, each showing different AI tasks in progress. Images generate in real-time on one screen, video renders on another, trading charts pulse green on a third. Palm trees sway gently in the breeze. Golden sunset light bathes everything in warm amber. Waves lap the shore softly.",

    # Scene 4: API Employee of the Month
    "Camera pushes in dramatically toward a glowing golden API code symbol floating center frame, framed by an ornate Employee of the Month picture frame. Energy crackles around the symbol, arcs of golden light connecting outward. Confetti particles explode from behind and cascade downward in slow motion. A radial shockwave of purple and gold light erupts outward. The frame pulses triumphantly. Camera continues pushing closer as the glow intensifies.",
]

NEGATIVE_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed"


def upload_image(filepath):
    """Upload an image to ComfyUI and return the server filename."""
    import mimetypes
    filename = os.path.basename(filepath)

    boundary = f"----PythonBoundary{random.randint(100000,999999)}"

    with open(filepath, 'rb') as f:
        file_data = f.read()

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f'Content-Type: image/png\r\n\r\n'
    ).encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()

    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )

    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result.get("name", filename)


def build_workflow(image_name, motion_prompt, scene_idx):
    """Build LTX-2 img-to-video workflow."""
    seed = random.randint(1, 2**32 - 1)

    workflow = {
        # 1. CheckpointLoaderSimple → MODEL(0), CLIP(1), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors"
            }
        },
        # 2. LTXAVTextEncoderLoader → CLIP(0) only
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors"
            }
        },
        # 3. LoraLoader → MODEL(0), CLIP(1)
        "3": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["2", 0],
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0
            }
        },
        # 4. LoadImage
        "4": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_name
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
        # 6. CLIPTextEncode (positive)
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": motion_prompt,
                "clip": ["3", 1]
            }
        },
        # 7. CLIPTextEncode (negative)
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": NEGATIVE_PROMPT,
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
        # 10. LTXVScheduler
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
        # 12. CFGGuider
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
        # 16. CreateVideo (convert IMAGE → VIDEO)
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
                "filename_prefix": f"scene_{scene_idx}",
                "format": "mp4",
                "codec": "h264"
            }
        }
    }

    return workflow


def submit_workflow(workflow):
    """Submit workflow to ComfyUI and return prompt_id."""
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    if "error" in result:
        print(f"  ERROR submitting: {result['error']}")
        if "node_errors" in result:
            for nid, err in result["node_errors"].items():
                print(f"    Node {nid}: {err}")
        return None
    return result["prompt_id"]


def poll_completion(prompt_id, timeout=300):
    """Poll until workflow completes or errors."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            data = json.loads(resp.read())
            if prompt_id in data:
                status = data[prompt_id].get("status", {}).get("status_str", "")
                outputs = data[prompt_id].get("outputs", {})
                if status == "error":
                    print(f"  ERROR in workflow")
                    # Try to get error details
                    msgs = data[prompt_id].get("status", {}).get("messages", [])
                    for msg in msgs:
                        print(f"    {msg}")
                    return None
                if outputs:
                    return outputs
        except Exception as e:
            pass
        time.sleep(5)
    print(f"  TIMEOUT after {timeout}s")
    return None


def download_video(outputs, output_path):
    """Download the generated video from ComfyUI output."""
    for nid, out in outputs.items():
        for key in ['gifs', 'videos', 'images']:
            if key in out:
                for item in out[key]:
                    fn = item.get('filename', '')
                    subfolder = item.get('subfolder', '')
                    if fn.endswith('.mp4') or fn.endswith('.webm'):
                        url = f"{COMFY_URL}/view?filename={urllib.parse.quote(fn)}&type=output"
                        if subfolder:
                            url += f"&subfolder={urllib.parse.quote(subfolder)}"
                        urllib.request.urlretrieve(url, output_path)
                        print(f"  Downloaded: {output_path}")
                        return True
    print(f"  No video found in outputs")
    return False


def main():
    scenes = list(range(5))
    if len(sys.argv) > 1:
        scenes = [int(x) for x in sys.argv[1:]]

    for i in scenes:
        print(f"\n{'='*60}")
        print(f"SCENE {i}: Generating video clip")
        print(f"{'='*60}")

        img_path = f"{SCENES_DIR}/scene-{i}-a.png"
        output_path = f"{SCENES_DIR}/scene-{i}-a.mp4"

        if not os.path.exists(img_path):
            print(f"  SKIP: {img_path} not found")
            continue

        # Upload image
        print(f"  Uploading {img_path}...")
        uploaded_name = upload_image(img_path)
        print(f"  Uploaded as: {uploaded_name}")

        # Build and submit workflow
        print(f"  Building workflow...")
        workflow = build_workflow(uploaded_name, MOTION_PROMPTS[i], i)

        print(f"  Submitting to ComfyUI...")
        prompt_id = submit_workflow(workflow)
        if not prompt_id:
            print(f"  FAILED to submit scene {i}")
            continue
        print(f"  Prompt ID: {prompt_id}")

        # Poll for completion
        print(f"  Generating (~1 min)...")
        outputs = poll_completion(prompt_id, timeout=300)
        if not outputs:
            print(f"  FAILED scene {i}")
            continue

        # Download
        download_video(outputs, output_path)

        # Verify
        if os.path.exists(output_path):
            size = os.path.getsize(output_path) / 1024
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", output_path],
                capture_output=True, text=True
            )
            dur = result.stdout.strip()
            print(f"  Size: {size:.0f}KB, Duration: {dur}s")

    print(f"\n{'='*60}")
    print("ALL DONE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
