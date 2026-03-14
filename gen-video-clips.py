#!/usr/bin/env python3
"""Generate LTX-2 text-to-video clips via ComfyUI (no reference images needed)."""

import json, time, random, subprocess, sys, os, urllib.request, urllib.parse

COMFY_URL = "http://172.18.64.1:8001"
SCENES_DIR = "public/scenes"

# Only video scenes (skip motion-graphic scenes 1 and 5)
VIDEO_SCENES = {
    0: {
        "output": "scene-0-a.mp4",
        "prompt": "Camera slowly pushes forward through a dark hazy server room toward a massive golden GPU chip sitting on a velvet pedestal under a single dramatic spotlight. A glowing neon price tag sways gently in the air. Silhouette figures shuffle forward in a long queue, mechanically tossing glowing money bags toward the pedestal. Dust particles drift lazily through beams of warm light. The golden chip begins developing cracks down the center, with bright light leaking through the fractures. Comic book style with bold outlines. Audio: low electronic hum, distant cash register sounds, a slow metallic groan."
    },
    2: {
        "output": "scene-2-a.mp4",
        "prompt": "Camera tracks rapidly across a chaotic scene with handheld energy. A massive glowing blue supercomputer hums with pulsing energy, panels vibrating and blinking rapidly. An avalanche of official documents with red stamps cascades and tumbles through the air, papers swirling in a vortex. A shiny humanoid robot stumbles forward awkwardly, arms flailing wildly, sparking and twitching before toppling sideways. Papers fly everywhere carried by gusts. Fluorescent lights flicker overhead creating a strobe effect. Anime style with speed lines and vibrant colors. Audio: electronic buzzing, papers rustling intensely, metallic clanking."
    },
    3: {
        "output": "scene-3-a.mp4",
        "prompt": "Camera slowly cranes upward from ground level revealing a massive floating circuit board city dramatically splitting apart into separate islands. Glowing bridges between neon-colored islands crumble and fall into a dark void below, trailing sparks and digital debris. The islands drift apart in different directions with lightning arcing between the separating chunks in bright flashes. Storm clouds swirl overhead in purple and blue tones. The camera continues rising to show the full epic scale of fragmentation. Concept art matte painting style with atmospheric perspective. Audio: deep rumbling, cracking metal, distant thunder, electrical crackling."
    },
    4: {
        "output": "scene-4-a.mp4",
        "prompt": "Camera smoothly orbits around three glowing holographic product cards arranged in a fan formation in a bright clean futuristic workspace. Each card pulses with its own color — teal, amber, and purple — casting colored light on nearby surfaces. Warm golden sunlight streams through tall floor-to-ceiling windows, with slowly moving light patches across the scene. The cards gently rotate on their axes and begin converging toward a central glowing white orb. Particles of warm light spiral upward like fireflies. Pixar 3D render style with soft ambient occlusion. Audio: soft ambient electronic tones, gentle chimes, a warm harmonic swell."
    },
}

NEGATIVE_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed"


def build_t2v_workflow(motion_prompt: str, output_prefix: str, seed: int) -> dict:
    """Build text-to-video workflow (no reference image needed)."""
    return {
        # 1. CheckpointLoaderSimple -> MODEL(0), CLIP(1,unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}
        },
        # 2. DualCLIPLoader -> CLIP(0)
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                "type": "ltx"
            }
        },
        # 3. LoraLoader -> MODEL(0), CLIP(1)
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
        # 4. CLIPTextEncode (positive)
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": motion_prompt, "clip": ["3", 1]}
        },
        # 5. CLIPTextEncode (negative)
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE_PROMPT, "clip": ["3", 1]}
        },
        # 6. LTXVConditioning
        "6": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["4", 0],
                "negative": ["5", 0],
                "frame_rate": 25
            }
        },
        # 7. EmptyLTXVLatentVideo
        "7": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {
                "width": 768,
                "height": 512,
                "length": 97,
                "batch_size": 1
            }
        },
        # 8. LTXVScheduler
        "8": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 8,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["7", 0]
            }
        },
        # 9. RandomNoise
        "9": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed}
        },
        # 10. CFGGuider
        "10": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["6", 0],
                "negative": ["6", 1],
                "cfg": 1.0
            }
        },
        # 11. KSamplerSelect
        "11": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
        # 12. SamplerCustomAdvanced
        "12": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["9", 0],
                "guider": ["10", 0],
                "sampler": ["11", 0],
                "sigmas": ["8", 0],
                "latent_image": ["7", 0]
            }
        },
        # 13. VAEDecode
        "13": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["12", 0], "vae": ["1", 2]}
        },
        # 14. CreateVideo
        "14": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["13", 0], "fps": 25.0}
        },
        # 15. SaveVideo
        "15": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["14", 0],
                "filename_prefix": output_prefix,
                "format": "mp4",
                "codec": "h264"
            }
        },
    }


def submit_workflow(workflow: dict) -> str:
    """Submit workflow and return prompt_id."""
    payload = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["prompt_id"]


def poll_completion(prompt_id: str, timeout: int = 300) -> dict:
    """Poll until workflow completes or times out."""
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as resp:
            history = json.loads(resp.read())
        if prompt_id in history:
            status = history[prompt_id].get("status", {}).get("status_str", "")
            outputs = history[prompt_id].get("outputs", {})
            if status == "error":
                print(f"  ERROR: {json.dumps(history[prompt_id].get('status', {}), indent=2)}")
                return None
            if outputs:
                return outputs
        time.sleep(3)
    print(f"  TIMEOUT after {timeout}s")
    return None


def download_video(outputs: dict, dest: str):
    """Find and download the video file from outputs."""
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    if fn.endswith(".mp4") or fn.endswith(".webm"):
                        url = f"{COMFY_URL}/view?filename={urllib.parse.quote(fn)}&type=output"
                        urllib.request.urlretrieve(url, dest)
                        size = os.path.getsize(dest)
                        print(f"  Downloaded: {dest} ({size} bytes)")
                        return True
    print(f"  No video found in outputs")
    return False


def extract_frames(video_path: str, scene_idx: int, num_frames: int):
    """Extract frames from video for Ken Burns overflow images."""
    duration = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video_path],
        capture_output=True, text=True
    ).stdout.strip())

    for i in range(num_frames):
        # Spread frames evenly across the video
        t = duration * (i + 1) / (num_frames + 1)
        suffix = chr(ord('b') + i)  # b, c, d
        out = os.path.join(SCENES_DIR, f"scene-{scene_idx}-{suffix}.png")
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(t), "-i", video_path,
            "-frames:v", "1", "-q:v", "2", out
        ], capture_output=True)
        size = os.path.getsize(out) if os.path.exists(out) else 0
        print(f"  Extracted frame at {t:.1f}s → {out} ({size} bytes)")


def main():
    os.makedirs(SCENES_DIR, exist_ok=True)
    # Remove any stale png files
    for f in os.listdir(SCENES_DIR):
        if f.endswith('.png'):
            os.remove(os.path.join(SCENES_DIR, f))

    # Overflow image counts per scene (audio duration based)
    # S0: 12.16s > 12s → 3 overflow (b,c,d)
    # S2: 10.08s 8-12s → 2 overflow (b,c)
    # S3: 10.88s 8-12s → 2 overflow (b,c)
    # S4: 12.16s > 12s → 3 overflow (b,c,d)
    overflow_counts = {0: 3, 2: 2, 3: 2, 4: 3}

    for scene_idx, scene in VIDEO_SCENES.items():
        out_path = os.path.join(SCENES_DIR, scene["output"])
        print(f"\n=== Scene {scene_idx} (text-to-video) ===")

        seed = random.randint(1, 2**32)
        prefix = f"scene_{scene_idx}"
        workflow = build_t2v_workflow(scene["prompt"], prefix, seed)

        print(f"  Submitting workflow (seed={seed})...")
        prompt_id = submit_workflow(workflow)
        print(f"  Prompt ID: {prompt_id}")

        print(f"  Polling for completion...")
        outputs = poll_completion(prompt_id, timeout=300)
        if outputs:
            download_video(outputs, out_path)
            dur = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", out_path],
                capture_output=True, text=True
            ).stdout.strip()
            print(f"  Duration: {dur}s")

            # Extract overflow frames
            n_overflow = overflow_counts.get(scene_idx, 0)
            if n_overflow > 0:
                print(f"  Extracting {n_overflow} overflow frames...")
                extract_frames(out_path, scene_idx, n_overflow)
        else:
            print(f"  FAILED for scene {scene_idx}")

    print("\n=== Summary ===")
    for f in sorted(os.listdir(SCENES_DIR)):
        fp = os.path.join(SCENES_DIR, f)
        print(f"  {f}: {os.path.getsize(fp)} bytes")


if __name__ == "__main__":
    main()
