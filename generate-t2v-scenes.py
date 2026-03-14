#!/usr/bin/env python3
"""Generate LTX-2 text-to-video clips for all scenes via ComfyUI (video-only, no audio)."""
import json, time, random, subprocess, sys, os

COMFY_URL = "http://172.18.64.1:8001"
OUTPUT_DIR = "/home/aten/zkagi-video-engine/public/scenes"

SCENES = [
    {
        "name": "scene_0",
        "output": "scene-0-a.mp4",
        "prompt": (
            "Camera slowly dollies forward through a dark empty modern office space. "
            "A lone figure sits at a minimal desk, the only laptop screen glowing blue in the darkness. "
            "Empty chairs and desks stretch into the background, slightly swaying. "
            "Dust particles drift through a single overhead spotlight beam. "
            "The figure leans forward typing confidently, screen light casting shadows on their determined face. "
            "Atmospheric and moody, cool blue and amber tones shift across the scene."
        ),
    },
    {
        "name": "scene_1",
        "output": "scene-1-a.mp4",
        "prompt": (
            "Camera trucks right along a wall of multiple glowing screens displaying blog graphics, "
            "video editing timelines, podcast waveforms, and social media analytics. "
            "Data visualizations pulse and animate across each monitor. "
            "Holographic charts float between the screens, numbers ticking upward. "
            "A single person works rapidly at the center, neon purple and cyan reflections dancing on surfaces. "
            "Synthwave atmosphere with VHS scan line effects."
        ),
    },
    {
        "name": "scene_2",
        "output": "scene-2-a.mp4",
        "prompt": (
            "Camera pushes forward toward a futuristic glowing terminal interface. "
            "Green command text scrolls rapidly on screen. "
            "Holographic images and video frames materialize from the screen, floating outward into the room. "
            "Particles of golden light spiral around each generated piece of content. "
            "A product image assembles pixel by pixel, then a video timeline unfolds beside it. "
            "Warm amber mixed with cool teal lighting shifts across the workspace."
        ),
    },
    {
        "name": "scene_3",
        "output": "scene-3-a.mp4",
        "prompt": (
            "Camera slowly orbits around a floating crystal ball made of streaming data and glowing code. "
            "Cryptocurrency symbols like Bitcoin and Ethereum orbit it like tiny planets, each pulsing with color. "
            "Green prediction arrows shoot upward from the crystal ball surface. "
            "Holographic charts and trend lines materialize in the surrounding air. "
            "Soft mystical particle effects drift upward. "
            "The atmosphere is technological yet magical, deep blue and green tones."
        ),
    },
    {
        "name": "scene_4",
        "output": "scene-4-a.mp4",
        "prompt": (
            "Camera cranes upward as a golden crown slowly descends onto a glowing laptop sitting on a throne. "
            "Confetti particles burst outward in vibrant colors from the moment of crowning. "
            "Golden light radiates from the laptop screen in triumphant pulsing waves. "
            "Energy arcs crackle around the crowned laptop as it rises slightly. "
            "The background transforms from darkness to vibrant synthwave colors with cascading light beams. "
            "Triumphant and celebratory atmosphere."
        ),
    },
]

def build_workflow(prompt, filename_prefix, seed, length=161):
    """Video-only workflow (no audio latents). Distilled LoRA, 8 steps, CFG 1.0."""
    return {
        # Load checkpoint: MODEL(0), CLIP(1, unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"},
        },
        # Load text encoder: CLIP(0) only
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                "type": "ltx",
            },
        },
        # Apply distilled LoRA to model
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2.3-distilled-lora-384.safetensors",
                "strength_model": 1.0,
            },
        },
        # Positive prompt
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 0]},
        },
        # Negative prompt
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed",
                "clip": ["2", 0],
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
        # Empty video latent (no audio)
        "7": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {
                "width": 768,
                "height": 512,
                "length": length,
                "batch_size": 1,
            },
        },
        # Scheduler — latent is optional, feed it the empty video latent
        "10": {
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
        # Random noise
        "11": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed},
        },
        # CFG Guider with distilled settings (cfg=1.0)
        "12": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["6", 0],
                "negative": ["6", 1],
                "cfg": 1.0,
            },
        },
        # Sampler
        "13": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"},
        },
        # Advanced sampling — pass video-only latent directly
        "14": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["11", 0],
                "guider": ["12", 0],
                "sampler": ["13", 0],
                "sigmas": ["10", 0],
                "latent_image": ["7", 0],
            },
        },
        # VAE decode — pass sampler output directly (video-only, skip SeparateAVLatent)
        "16": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["14", 0], "vae": ["1", 2]},
        },
        # Convert IMAGE → VIDEO
        "17": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["16", 0], "fps": 25},
        },
        # Save
        "18": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["17", 0],
                "filename_prefix": filename_prefix,
                "format": "mp4",
                "codec": "h264",
            },
        },
    }

def submit_workflow(workflow):
    import urllib.request
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        return result["prompt_id"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code}: {body}", file=sys.stderr)
        return None

def poll_completion(prompt_id, timeout=600):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
        data = json.loads(resp.read())
        if prompt_id in data:
            status = data[prompt_id].get("status", {}).get("status_str", "")
            if status == "error":
                msgs = data[prompt_id].get("status", {}).get("messages", [])
                print(f"  ERROR: {msgs}", file=sys.stderr)
                return None
            outputs = data[prompt_id].get("outputs", {})
            if outputs:
                return outputs
        time.sleep(5)
    print(f"  TIMEOUT after {timeout}s", file=sys.stderr)
    return None

def download_video(outputs, dest_path):
    import urllib.request
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    if fn.endswith(".mp4") or fn.endswith(".webm"):
                        subfolder = item.get("subfolder", "")
                        url = f"{COMFY_URL}/view?filename={fn}&type=output"
                        if subfolder:
                            url += f"&subfolder={subfolder}"
                        urllib.request.urlretrieve(url, dest_path)
                        return True
    return False

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i, scene in enumerate(SCENES):
        seed = random.randint(1, 2**31)
        print(f"\n=== Generating {scene['name']} (seed={seed}) ===")
        workflow = build_workflow(scene["prompt"], scene["name"], seed, length=161)
        prompt_id = submit_workflow(workflow)
        if not prompt_id:
            print(f"  FAILED to submit {scene['name']}")
            continue
        print(f"  Submitted: {prompt_id}")
        outputs = poll_completion(prompt_id, timeout=600)
        if outputs:
            dest = os.path.join(OUTPUT_DIR, scene["output"])
            if download_video(outputs, dest):
                dur = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", dest],
                    capture_output=True, text=True,
                ).stdout.strip()
                print(f"  Saved: {dest} ({dur}s)")
            else:
                print(f"  ERROR: No video in outputs")
        else:
            print(f"  FAILED to generate {scene['name']}")

if __name__ == "__main__":
    main()
