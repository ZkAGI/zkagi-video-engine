#!/usr/bin/env python3
"""Generate LTX-2.3 text-to-video clips for Day 9 video (AI chaos digest)."""
import json, time, random, sys, os, subprocess

COMFY_URL = "http://172.18.64.1:8001"
OUTPUT_DIR = "/home/aten/zkagi-video-engine/public/scenes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Text-to-video clips for each video scene
CLIPS = [
    # Scene 0: Robot face-plant (comic book style)
    ("scene-0-a.mp4",
     "Camera handheld with nervous wobble. A shiny humanoid robot in a warehouse confidently steps forward out of a glowing blue portal. Its foot catches on a cable and it stumbles, arms windmilling wildly. Sparks fly from its joints. Comic book impact lines radiate outward. Tools clatter off shelves. Dramatic spotlight from the portal flickers. Bold outlines, vibrant saturated colors. Audio: confident footstep, cable snap, comical metallic crash with clanging."),

    # Scene 2: EU bureaucracy homework (Pixar style)
    ("scene-2-a.mp4",
     "Camera slowly pushes in on a cartoon robot sitting at a small school desk in a classroom, surrounded by enormous stacks of paperwork and forms that wobble and sway. The robot frantically scribbles with four mechanical arms, ink splattering everywhere. Papers fly off the desk. A large clock ticks on the wall. Warm classroom lighting, soft shadows. The paper stacks grow taller, threatening to topple. Audio: frantic scribbling, paper rustling, clock ticking louder."),

    # Scene 3: Engineers on plane in thunderstorm
    ("scene-3-a.mp4",
     "Camera tracking shot across the wing of a passenger jet flying through a violent thunderstorm. Two small figures in hardhats cling to the wing while trying to work on an exposed engine panel with wrenches and laptops. Lightning cracks across the dark sky illuminating everything in white flashes. Rain streaks horizontally. Papers and tools blow away into the void. Dark dramatic concept art style, epic scale. Audio: howling wind, thunder cracks, metallic creaking, rain pelting."),

    # Scene 4: ZkAGI calm command center vs chaos outside
    ("scene-4-a.mp4",
     "Camera slowly dollies forward into a sleek futuristic command center with three glowing holographic dashboards pulsing with data in purple, teal, and amber light. The interior is calm, organized, with dark brushed metal surfaces reflecting the holographic glow. Through panoramic windows, a chaotic cityscape flickers with distant explosions and lightning. Particles of light drift upward from the dashboards. Concept art style with synthwave accents. Audio: soft electronic ambient hum, distant muffled chaos, clean interface chimes."),
]

NEG_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, extra limbs, bad anatomy, words, letters, numbers"


def build_t2v_workflow(prompt, seed, length=97):
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"}
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "gemma_3_12B_it.safetensors",
                "type": "ltxv"
            }
        },
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 1.0
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 0]}
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEG_PROMPT, "clip": ["2", 0]}
        },
        "6": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["4", 0],
                "negative": ["5", 0],
                "frame_rate": 25
            }
        },
        "7": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {
                "width": 768, "height": 512,
                "length": length, "batch_size": 1
            }
        },
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
        "9": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed}
        },
        "10": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["6", 0],
                "negative": ["6", 1],
                "cfg": 1.0
            }
        },
        "11": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
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
        "13": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["12", 0], "vae": ["1", 2]}
        },
        "14": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["13", 0], "fps": 25.0}
        },
        "15": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["14", 0],
                "filename_prefix": "day9_clip",
                "format": "mp4",
                "codec": "h264"
            }
        }
    }


def submit_workflow(workflow):
    import urllib.request
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["prompt_id"]


def poll_until_done(prompt_id, timeout=300):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            data = json.loads(resp.read())
            if prompt_id in data:
                status = data[prompt_id].get("status", {}).get("status_str", "")
                outputs = data[prompt_id].get("outputs", {})
                if status == "error":
                    msgs = data[prompt_id].get("status", {}).get("messages", [])
                    return "ERROR", None, str(msgs)
                if outputs:
                    return "DONE", data[prompt_id], None
        except Exception:
            pass
        time.sleep(3)
    return "TIMEOUT", None, None


def download_output(history_data, output_path):
    import urllib.request
    outputs = history_data.get("outputs", {})
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    if fn.endswith(".mp4") or fn.endswith(".webm"):
                        url = f"{COMFY_URL}/view?filename={fn}&type=output"
                        urllib.request.urlretrieve(url, output_path)
                        return True
    return False


def extract_stills(video_path, scene_idx, num_stills):
    """Extract evenly-spaced stills from a video clip for Ken Burns overflow."""
    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ]).decode().strip())

    for i in range(num_stills):
        t = duration * (i + 1) / (num_stills + 1)
        suffix = chr(ord('b') + i)  # b, c, d
        out_path = os.path.join(OUTPUT_DIR, f"scene-{scene_idx}-{suffix}.png")
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(t), "-i", video_path,
            "-frames:v", "1", "-q:v", "2", out_path
        ], capture_output=True)
        if os.path.exists(out_path):
            print(f"  Extracted still: scene-{scene_idx}-{suffix}.png ({os.path.getsize(out_path)} bytes)")


def main():
    # Scene index mapping: clip index -> (scene_num, num_overflow_stills)
    scene_info = {
        0: (0, 2),   # S0: 8.48s → 2 overflow stills (b, c)
        1: (2, 3),   # S2: 12.16s → 3 overflow stills (b, c, d)
        2: (3, 2),   # S3: 9.12s → 2 overflow stills (b, c)
        3: (4, 3),   # S4: 13.28s → 3 overflow stills (b, c, d)
    }

    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(CLIPS)

    for i in range(start_idx, end_idx):
        filename, prompt = CLIPS[i]
        output_path = os.path.join(OUTPUT_DIR, filename)
        scene_num, num_stills = scene_info[i]

        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            print(f"[{i+1}/{len(CLIPS)}] SKIP {filename} (already exists)")
            extract_stills(output_path, scene_num, num_stills)
            continue

        seed = random.randint(1, 999999999)
        workflow = build_t2v_workflow(prompt, seed)

        print(f"[{i+1}/{len(CLIPS)}] Submitting {filename}...")
        try:
            prompt_id = submit_workflow(workflow)
            print(f"  Prompt ID: {prompt_id}")
        except Exception as e:
            print(f"  ERROR submitting: {e}")
            continue

        print(f"  Polling for completion...")
        status, data, err = poll_until_done(prompt_id, timeout=300)

        if status == "DONE":
            if download_output(data, output_path):
                size = os.path.getsize(output_path)
                print(f"  DONE: {filename} ({size} bytes)")
                # Extract stills for Ken Burns overflow
                extract_stills(output_path, scene_num, num_stills)
            else:
                print(f"  ERROR: Could not find video in outputs")
        elif status == "ERROR":
            print(f"  ERROR: {err}")
        else:
            print(f"  TIMEOUT after 300s")

    print("\nAll clips done!")


if __name__ == "__main__":
    main()
