#!/usr/bin/env python3
"""Generate LTX-2 video clips from reference images via ComfyUI."""

import requests, json, time, random, sys, os

COMFY_URL = "http://172.18.64.1:8001"
SCENE_DIR = "/home/aten/zkagi-video-engine/public/scenes"

CHECKPOINT = "ltx-2-19b-dev-fp8.safetensors"
TEXT_ENCODER = "gemma_3_12B_it.safetensors"
LORA = "ltx-2-19b-distilled-lora-384.safetensors"
STEPS = 8
CFG = 1.0
FRAMES = 97  # 3.88s at 25fps
WIDTH = 768
HEIGHT = 512
NEG_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, bad anatomy, extra limbs"

# Each clip: (filename, image_file, motion_prompt)
CLIPS = [
    # Scene 0 (7.84s → need 2 clips ~3.88s each)
    ("scene-0-a", "scene-0-a.png",
     "Camera slowly pushes forward toward the confident entrepreneur on his couch. He shifts his laptop, leaning forward with a knowing smile. The AI dashboard on screen animates with live metrics scrolling upward. Warm golden light from a nearby lamp flickers subtly. Tiny dust particles drift in the ambient glow."),
    ("scene-0-b", "scene-0-b.png",
     "Camera slowly dollies in on the glowing laptop screen as charts animate with climbing revenue lines. Holographic interface elements pulse and expand outward. Numbers tick upward rapidly. The zero employee count blinks with a playful green glow. Cool blue light reflects and shimmers off the surrounding desk surface."),

    # Scene 1 (6.88s → need 2 clips)
    ("scene-1-a", "scene-1-a.png",
     "Camera smoothly tracks right across the HR desk as the cartoon robot shuffles through holographic resumes, picking one up and examining it closely. Digital documents float and spin gently in the air around the robot. Soft office lighting flickers as the robot stamps APPROVED on a resume with a mechanical arm."),
    ("scene-1-b", "scene-1-b.png",
     "Camera slowly orbits around the robotic arm as it paints with sweeping strokes across holographic canvases. Colorful marketing posters materialize from brushstrokes floating outward. Paint particles drift through the air like confetti. The creative studio glows with warm pastel light shifting colors."),

    # Scene 2 (8.64s → need 3 clips)
    ("scene-2-a", "scene-2-a.png",
     "Camera slowly dollies forward through the empty office as a man stands by the water cooler, gesturing animatedly at the floating chatbot hologram. Speech bubbles pop in and out. The chatbot interface glows and pulses with each response. Empty cubicles stretch into shadow behind them."),
    ("scene-2-b", "scene-2-b.png",
     "Camera steadily pushes in on the glowing chatbot screen as text messages appear one by one with playful emoji reactions bouncing in. The chatbot avatar tips its tiny graduation cap with a mechanical nod. A thought bubble expands with a lightbulb icon. Screen glow pulses warmly."),
    ("scene-2-c", "scene-2-c.png",
     "Camera holds steady as the man nods confidently at the chatbot while three ghost-like figures of former employees slowly dissolve into glowing particles behind him. The chatbot interface brightens triumphantly. Holographic confetti drifts downward. Light shifts from cold blue to warm amber."),

    # Scene 3 (14.88s → need 4 clips)
    ("scene-3-a", "scene-3-a.png",
     "Camera slowly trucks right across the split scene. On the left, glowing API nodes pulse and connect with streaming light beams in the server room. On the right, a relaxed figure sips a cocktail on a tropical beach. Waves gently lap at the shore. Data streams flow left to right."),
    ("scene-3-b", "scene-3-b.png",
     "Camera slowly pulls back from the massive holographic control panel as AI processes animate across its surface. Image thumbnails generate in real-time, video frames render in sequence, trading graphs update with green arrows shooting upward. Deep blue volumetric light rays sweep across the scene."),
    ("scene-3-c", "scene-3-c.png",
     "Camera gently floats toward the person relaxing in the hammock as palm trees sway in a warm tropical breeze. Their phone screen glows with green dashboard updates. The sunset paints the sky in golden and orange hues. Leaves and flower petals drift lazily through the warm air."),
    ("scene-3-d", "scene-3-b.png",
     "Camera slowly orbits the holographic control panel from a different angle as autonomous trading bots execute orders on glowing screens. Green profit numbers cascade upward. Connected data streams pulse with energy. The vast space hums with ambient blue light shifting to warm gold."),

    # Scene 4 (7.36s → need 2 clips)
    ("scene-4-a", "scene-4-a.png",
     "Camera slowly orbits the holographic API employee figure as streaming code flows through its translucent body like digital blood. It holds the gold trophy aloft which gleams and catches the light with rotating sparkles. Golden Art Deco patterns pulse on the walls. Light particles rise upward like champagne bubbles."),
    ("scene-4-b", "scene-4-b.png",
     "Camera rapidly zooms out as the ZKAGI text explodes into view with golden light bursts radiating outward in all directions. Orbiting API icons spin faster leaving light trails. The neon grid floor pulses with energy waves expanding outward. A dramatic lens flare sweeps across the frame."),
]

def upload_image(image_path):
    """Upload image to ComfyUI and return its name."""
    with open(image_path, "rb") as f:
        resp = requests.post(f"{COMFY_URL}/upload/image",
            files={"image": (os.path.basename(image_path), f, "image/png")},
            data={"type": "input", "overwrite": "true"},
            timeout=30)
    if resp.status_code == 200:
        return resp.json().get("name", os.path.basename(image_path))
    raise Exception(f"Upload failed: {resp.status_code} {resp.text[:200]}")

def build_workflow(uploaded_image_name, motion_prompt, filename_prefix, seed=None):
    """Build LTX-2 image-to-video workflow."""
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    return {
        # 1: Load checkpoint → MODEL(0), CLIP(1, unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": CHECKPOINT}
        },
        # 2: Load text encoder → CLIP(0)
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": TEXT_ENCODER,
                "ckpt_name": CHECKPOINT,
                "device": "cpu"
            }
        },
        # 3: Apply distilled LoRA → MODEL(0)
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": LORA,
                "strength_model": 1.0
            }
        },
        # 4: Load reference image → IMAGE(0)
        "4": {
            "class_type": "LoadImage",
            "inputs": {"image": uploaded_image_name}
        },
        # 5: Preprocess image → IMAGE(0)
        "5": {
            "class_type": "LTXVPreprocess",
            "inputs": {
                "image": ["4", 0],
                "img_compression": 35
            }
        },
        # 6: Positive prompt → CONDITIONING(0)
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": motion_prompt,
                "clip": ["2", 0]
            }
        },
        # 7: Negative prompt → CONDITIONING(0)
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": NEG_PROMPT,
                "clip": ["2", 0]
            }
        },
        # 8: LTX conditioning → positive(0), negative(1)
        "8": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "frame_rate": 25
            }
        },
        # 9: Image-to-video → positive(0), negative(1), latent(2)
        "9": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["8", 0],
                "negative": ["8", 1],
                "vae": ["1", 2],
                "image": ["5", 0],
                "width": WIDTH,
                "height": HEIGHT,
                "length": FRAMES,
                "batch_size": 1,
                "strength": 1.0
            }
        },
        # 10: Scheduler → SIGMAS(0)
        "10": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": STEPS,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["9", 2]
            }
        },
        # 11: Random noise → NOISE(0)
        "11": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed}
        },
        # 12: CFG Guider → GUIDER(0)
        "12": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["9", 0],
                "negative": ["9", 1],
                "cfg": CFG
            }
        },
        # 13: Sampler select → SAMPLER(0)
        "13": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
        # 14: Sample → LATENT(0), LATENT(1)
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
        # 15: VAE Decode → IMAGE(0) [skip SeparateAVLatent for video-only]
        "15": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["14", 0],
                "vae": ["1", 2]
            }
        },
        # 16: Create video → VIDEO(0)
        "16": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["15", 0],
                "fps": 25.0
            }
        },
        # 17: Save video
        "17": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["16", 0],
                "filename_prefix": filename_prefix,
                "format": "mp4",
                "codec": "h264"
            }
        }
    }

def submit_workflow(workflow):
    """Submit workflow and return prompt_id."""
    resp = requests.post(f"{COMFY_URL}/prompt",
        json={"prompt": workflow}, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        if "error" in data:
            raise Exception(f"Workflow error: {json.dumps(data['error'])[:500]}")
        return data["prompt_id"]
    raise Exception(f"Submit failed: {resp.status_code} {resp.text[:500]}")

def poll_completion(prompt_id, timeout=300):
    """Poll until completion. Returns output dict or raises."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if prompt_id in data:
                entry = data[prompt_id]
                status = entry.get("status", {}).get("status_str", "")
                if status == "error":
                    msgs = entry.get("status", {}).get("messages", [])
                    raise Exception(f"Generation error: {msgs}")
                outputs = entry.get("outputs", {})
                if outputs:
                    return outputs
        time.sleep(5)
    raise Exception(f"Timeout after {timeout}s")

def download_video(prompt_id, outputs, dest_path):
    """Download the generated video file."""
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
                        resp = requests.get(url, timeout=60)
                        if resp.status_code == 200 and len(resp.content) > 1000:
                            with open(dest_path, "wb") as f:
                                f.write(resp.content)
                            return True
    return False

def process_clip(clip_name, image_file, motion_prompt):
    """Upload image, generate video clip, download result."""
    image_path = os.path.join(SCENE_DIR, image_file)
    dest_path = os.path.join(SCENE_DIR, f"{clip_name}.mp4")

    print(f"\n{'='*60}")
    print(f"Processing: {clip_name}")
    print(f"  Image: {image_file}")
    print(f"  Prompt: {motion_prompt[:80]}...")

    # Upload image
    print(f"  Uploading image...")
    uploaded_name = upload_image(image_path)
    print(f"  Uploaded as: {uploaded_name}")

    # Build and submit workflow
    print(f"  Building workflow...")
    workflow = build_workflow(uploaded_name, motion_prompt, f"ltx_{clip_name}")

    print(f"  Submitting to ComfyUI...")
    prompt_id = submit_workflow(workflow)
    print(f"  Prompt ID: {prompt_id}")

    # Poll for completion
    print(f"  Generating (8 steps, ~60s)...")
    t0 = time.time()
    outputs = poll_completion(prompt_id, timeout=300)
    elapsed = time.time() - t0
    print(f"  Generated in {elapsed:.1f}s")

    # Download
    print(f"  Downloading video...")
    if download_video(prompt_id, outputs, dest_path):
        size = os.path.getsize(dest_path)
        print(f"  Saved: {dest_path} ({size} bytes)")
        return True
    else:
        print(f"  WARNING: Could not download video for {clip_name}")
        return False

# Main
print(f"Generating {len(CLIPS)} video clips via LTX-2 ComfyUI")
print(f"Settings: {FRAMES} frames, {STEPS} steps, CFG {CFG}, {WIDTH}x{HEIGHT}")
print(f"LoRA: {LORA}")

results = {}
for clip_name, image_file, motion_prompt in CLIPS:
    try:
        ok = process_clip(clip_name, image_file, motion_prompt)
        results[clip_name] = ok
    except Exception as e:
        print(f"  ERROR: {e}")
        results[clip_name] = False

print(f"\n{'='*60}")
print(f"=== Video Generation Results ===")
ok_count = sum(1 for v in results.values() if v)
print(f"{ok_count}/{len(CLIPS)} clips generated successfully")
for name, ok in results.items():
    print(f"  {name}: {'OK' if ok else 'FAILED'}")
