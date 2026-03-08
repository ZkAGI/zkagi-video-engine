#!/usr/bin/env python3
"""Generate LTX-2 video clips for 'Don't Be Dave' video."""
import json, time, random, subprocess, sys, os

COMFY_URL = "http://172.18.64.1:8001"
SCENES_DIR = "public/scenes"

CLIPS = [
    # (image_file, output_file, motion_prompt, frames)
    ("scene-0-a.png", "scene-0-a.mp4",
     "Camera holds on a medium shot. The confident cartoon man grins wider, puffing out his chest, phone screen glowing brighter in his hand. He casually pats his jeans pocket with his free hand, completely unaware. A laundry basket in the corner shifts slightly in the shadows. Warm spotlight intensifies on the character. Audio: upbeat jazzy tune, a confident chuckle, fabric rustling.", 97),

    ("scene-0-b.png", "scene-0-b.mp4",
     "Camera slowly pushes in on the man's worried face. His hand frantically searches his pockets, pulling out lint and loose threads. The giant floating jeans behind him sway ominously, their glowing pockets pulsing with an eerie light. The washing machine in the corner rumbles and its door creaks open slightly. Shadows deepen. Audio: frantic pocket-searching sounds, ominous low rumble, fabric rustling.", 97),

    ("scene-1-a.png", "scene-1-a.mp4",
     "Camera slowly dollies toward the open washing machine mouth. Water inside swirls violently in a vortex, pulling the napkin fragments inward. Soap bubbles burst around the edges. The overhead light flickers rhythmically. Pieces of paper dissolve into foam and disappear. Camera continues pushing into the dark churning water. Audio: aggressive water churning, paper tearing, machine rumbling, menacing mechanical rhythm.", 97),

    ("scene-1-b.png", "scene-1-b.mp4",
     "Camera on a slow dolly in toward the frozen man. His jaw trembles slightly, a single sweat drop rolls down his temple. The ghostly dollar signs behind him drift upward and dissolve into smoke particles. Wet paper pieces on the floor slowly uncurl. The fluorescent light above flickers twice. His expression shifts from shock to pure devastation. Camera tightens to close-up. Audio: silence, then a distant cash register sound in reverse, a hollow wind.", 97),

    ("scene-1-c.png", "scene-1-c.mp4",
     "Camera looking straight down at the sewer grate. Water flows faster below, carrying golden coin fragments and paper scraps. Raindrops hit the wet concrete around the grate creating ripples. The coins catch light as they tumble and spin deeper into the dark water. Camera slowly rotates clockwise. Water level rises slightly. Audio: rain pattering, water rushing through pipes, coins clinking and fading, a distant echo.", 97),

    ("scene-2-a.png", "scene-2-a.mp4",
     "Camera starts medium shot then slowly pushes forward. The crystalline vault brightens from within, golden light intensifying and pulsing like a heartbeat. The force field shimmers with rippling energy waves. Key fragments drift closer from all directions, rotating gently as they approach the vault center. Warm light particles rise upward like fireflies. Atmosphere shifts from cool blue to warm gold. Audio: a rising harmonic tone, crystalline chimes tinkling, energy humming warmly.", 97),

    ("scene-2-b.png", "scene-2-b.mp4",
     "Camera slowly orbits around the cross-section vault. Each protective layer pulses sequentially from outer to inner, like a heartbeat traveling inward. The tiny keys in the center bob gently, catching golden light. Holographic shields between layers shimmer and ripple. The inner golden chamber glows brighter. Light particles spiral upward from the center. Camera continues its orbit smoothly. Audio: soft mechanical humming, shield energy crackling gently, a warm resonant tone.", 97),

    ("scene-2-c.png", "scene-2-c.mp4",
     "Camera slowly pulls back to reveal the full vault. The golden seams pulse with energy. A shadowy figure lunges toward the vault but bounces off the force field in a flash of sparks, tumbling backward. The shield ripples from the impact point outward. Golden light pushes back the surrounding darkness further. The vault stands unmoved and triumphant. Audio: a thud of impact, electric crackling, sparks sizzling, a deep protective hum.", 97),

    ("scene-3-a.png", "scene-3-a.mp4",
     "Camera slowly dollies in toward the floating smartphone. The screen illuminates brighter, showing the Create Wallet button pulsing invitingly. The three floating checkmark steps beside it light up one by one in sequence with satisfying flashes. Soft particles drift around the phone. The clean bright space gradually fills with warm purple ambient light. Audio: soft digital interface sounds, three ascending chimes for each step, gentle ambient hum.", 97),

    ("scene-3-b.png", "scene-3-b.mp4",
     "Camera slowly trucks right across the split scene. On the left, the happy person taps their phone and purple checkmarks float up with each tap, sparkles erupting. On the right, sad Dave slumps further, wet laundry pile growing taller beside him, a question mark above him wobbles. The contrast between warm left lighting and cold right lighting intensifies. Audio: happy tap sounds and chimes on left, sad trombone notes on right, a comedic contrast.", 97),

    ("scene-3-c.png", "scene-3-c.mp4",
     "Camera holds centered then slowly zooms in. The giant purple checkmark pulses once brightly, then confetti and sparkle particles explode outward in all directions. Golden sparkles rain down from above. The vault icon below gleams and its lock clicks shut with a satisfying motion. The phone shield icon glows triumphantly. Everything bathes in warm celebratory light. Audio: a triumphant fanfare sting, confetti popping, a satisfying lock click, sparkle sounds.", 97),

    ("scene-4-a.png", "scene-4-a.mp4",
     "Camera slowly pushes toward the glowing neon portal. Purple and gold energy crackles and swirls around the portal edges. In the far background, tiny Dave waves sadly as he recedes further away. The golden shield logo drifts forward through the portal, growing larger and brighter. Neon grid lines on the ground pulse with energy traveling toward the viewer. Laser beams sweep across the scene. Audio: synthwave bass pulse, energy crackling, a warm triumphant pad sound building.", 97),

    ("scene-4-b.png", "scene-4-b.mp4",
     "Camera cranes upward dramatically. The golden shockwave expands outward in a ring from the center emblem. Hundreds of golden orbs rise from below like floating lanterns, filling the purple sky. The neon grid landscape below reflects golden light in shimmering ripples. Chrome reflections catch the light. Energy radiates in waves. Everything builds to a crescendo of golden triumphant light. Audio: deep bass impact, rushing wind of shockwave, warm harmonic swell building to climax, golden chimes.", 97),
]

def upload_image(image_name):
    """Upload image to ComfyUI, return the uploaded filename."""
    filepath = os.path.join(SCENES_DIR, image_name)
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{COMFY_URL}/upload/image",
         "-F", f"image=@{filepath}", "-F", "type=input"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data.get("name", image_name)

def build_workflow(uploaded_name, motion_prompt, frames=97):
    """Build the LTX-2 img2vid workflow with distilled LoRA."""
    seed = random.randint(1, 2**31)
    return {
        # Node 1: CheckpointLoaderSimple → MODEL(0), CLIP(1 unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"}
        },
        # Node 2: LTXAVTextEncoderLoader → CLIP(0) only
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
                "device": "default"
            }
        },
        # Node 3: LoRA (distilled, 8 steps)
        "3": {
            "class_type": "LoraLoader",
            "inputs": {
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
                "model": ["1", 0],
                "clip": ["2", 0]
            }
        },
        # Node 4: Load reference image
        "4": {
            "class_type": "LoadImage",
            "inputs": {"image": uploaded_name}
        },
        # Node 5: Preprocess image
        "5": {
            "class_type": "LTXVPreprocess",
            "inputs": {
                "image": ["4", 0],
                "img_compression": 35
            }
        },
        # Node 6: Positive prompt (motion)
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": motion_prompt,
                "clip": ["3", 1]
            }
        },
        # Node 7: Negative prompt
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, worst quality",
                "clip": ["3", 1]
            }
        },
        # Node 8: LTXVConditioning
        "8": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "frame_rate": 25
            }
        },
        # Node 9: LTXVImgToVideo → positive(0), negative(1), latent(2)
        "9": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["8", 0],
                "negative": ["8", 1],
                "vae": ["1", 2],
                "image": ["5", 0],
                "width": 768,
                "height": 512,
                "length": frames,
                "batch_size": 1,
                "strength": 1.0
            }
        },
        # Node 10: LTXVScheduler
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
        # Node 11: Random noise
        "11": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed}
        },
        # Node 12: CFG Guider (cfg=1.0 for distilled)
        "12": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["9", 0],
                "negative": ["9", 1],
                "cfg": 1.0
            }
        },
        # Node 13: Sampler select
        "13": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
        # Node 14: Sample
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
        # Node 15: VAEDecode (skip SeparateAVLatent for video-only)
        "15": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["14", 0],
                "vae": ["1", 2]
            }
        },
        # Node 16: CreateVideo (IMAGE → VIDEO)
        "16": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["15", 0],
                "frame_rate": 25,
                "audio": None
            }
        },
        # Node 17: SaveVideo
        "17": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["16", 0],
                "filename_prefix": "dave_clip"
            }
        }
    }

def submit_workflow(workflow):
    """Submit workflow to ComfyUI, return prompt_id."""
    payload = json.dumps({"prompt": workflow})
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{COMFY_URL}/prompt",
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    if "prompt_id" not in data:
        print(f"  ERROR: {data}")
        return None
    return data["prompt_id"]

def poll_completion(prompt_id, timeout=300):
    """Poll until workflow completes. Return output filename."""
    start = time.time()
    while time.time() - start < timeout:
        result = subprocess.run(
            ["curl", "-s", f"{COMFY_URL}/history/{prompt_id}"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        if prompt_id in data:
            status = data[prompt_id].get("status", {}).get("status_str", "")
            if status == "error":
                msgs = data[prompt_id].get("status", {}).get("messages", [])
                print(f"  ERROR: {msgs}")
                return None
            outputs = data[prompt_id].get("outputs", {})
            if outputs:
                # Find the video file
                for nid, out in outputs.items():
                    for key in ["gifs", "videos", "images"]:
                        if key in out:
                            for item in out[key]:
                                fn = item.get("filename", "")
                                if fn.endswith(".mp4") or fn.endswith(".webm"):
                                    return fn
                print(f"  WARNING: No video in outputs: {outputs.keys()}")
                return None
        time.sleep(3)
    print("  TIMEOUT")
    return None

def download_output(filename, output_path):
    """Download the output file from ComfyUI."""
    subprocess.run(
        ["curl", "-s", f"{COMFY_URL}/view?filename={filename}&type=output",
         "--output", output_path],
        capture_output=True
    )

def main():
    total = len(CLIPS)
    for i, (img, out, prompt, frames) in enumerate(CLIPS):
        print(f"\n[{i+1}/{total}] Processing {img} → {out}")
        out_path = os.path.join(SCENES_DIR, out)

        # Skip if already exists
        if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
            print(f"  SKIP (already exists: {os.path.getsize(out_path)} bytes)")
            continue

        # Upload
        print(f"  Uploading {img}...")
        uploaded = upload_image(img)
        print(f"  Uploaded as: {uploaded}")

        # Build & submit workflow
        print(f"  Submitting workflow ({frames} frames)...")
        wf = build_workflow(uploaded, prompt, frames)
        pid = submit_workflow(wf)
        if not pid:
            print("  FAILED to submit")
            continue
        print(f"  Prompt ID: {pid}")

        # Poll
        print(f"  Waiting for completion...")
        start_t = time.time()
        output_fn = poll_completion(pid)
        elapsed = time.time() - start_t
        if not output_fn:
            print(f"  FAILED after {elapsed:.0f}s")
            continue
        print(f"  Done in {elapsed:.0f}s → {output_fn}")

        # Download
        download_output(output_fn, out_path)
        size = os.path.getsize(out_path)
        print(f"  Saved: {out_path} ({size/1024:.0f}KB)")

    print("\n=== ALL CLIPS DONE ===")

if __name__ == "__main__":
    main()
