#!/usr/bin/env python3
"""Generate all LTX-2 text-to-video clips for PawPad seed-roast video."""
import json, time, random, sys, os, subprocess

COMFY_URL = "http://172.18.64.1:8001"
OUTPUT_DIR = "/home/aten/zkagi-video-engine/public/scenes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All clips: (filename, prompt)
CLIPS = [
    # ═══ SCENE 0: HOOK / ROAST (5.92s → 2 clips) ═══
    ("scene-0-a.mp4",
     "Camera handheld with nervous wobble. A panicked cartoon character in a dark alley clutches a coffee-stained napkin to their chest, eyes darting frantically. Shadowy hands emerge from cracks in brick walls, fingers stretching toward the napkin. Dramatic spotlight from above flickers. The character stumbles backward. Comic book style, bold outlines, halftone dots, high contrast, vibrant saturated colors. Audio: nervous breathing, creaking, a low ominous drone building."),

    ("scene-0-b.mp4",
     "Camera slowly pushes in as a crumpled napkin with scribbled words tears apart down the middle in slow motion. Paper fragments scatter and float upward, spinning and catching dramatic spotlight. The torn halves drift apart revealing pure darkness behind them. Deep shadows swallow everything from the edges inward. Comic book noir atmosphere with bold ink outlines. Audio: sharp paper tearing, fragments rustling in silence, a deep reverberating void sound."),

    # ═══ SCENE 1: TWIST THE KNIFE (10.08s → 3 clips) ═══
    ("scene-1-a.mp4",
     "Camera slowly dollies toward a kitchen fridge door covered in colorful sticky notes and paper scraps. One by one the sticky notes peel off and flutter to the floor. A dark shadow creeps across from the right, darkening everything it touches. The fluorescent kitchen light flickers above. Film noir style, high contrast, venetian blind shadows striping across the scene. Audio: sticky notes peeling, fluorescent buzz flickering, an ominous low hum."),

    ("scene-1-b.mp4",
     "Camera tracks downward following golden coins and paper money dissolving into black smoke and ash. A desperate hand reaches into frame trying to grab them but fingers pass through the dissolving money like grabbing air. Ash particles float upward against the dark background like glowing embers. Volumetric light from below casts eerie orange glow on the rising ash. Audio: coins clinking then fading, whooshing dissolution sound, crackling embers."),

    ("scene-1-c.mp4",
     "Camera pushes in as a glowing digital wallet interface on a screen begins corrupting, cracks spreading across the display. Red warning symbols flash rapidly. Data streams leak from the cracks like liquid light. RGB channels split and shift, pixel sorting cascades across the frame. The screen shudders violently then goes dark. Glitch art aesthetic with chromatic aberration and scan line artifacts. Audio: digital distortion, warning beeps, sharp electronic crackle then dead silence."),

    # ═══ SCENE 2: THE SOLUTION (8.64s → 3 clips) ═══
    ("scene-2-a.mp4",
     "Camera smoothly dollies forward toward a massive gleaming vault door that slowly swings open with heavy mechanical precision. Warm golden light pours out from inside, illuminating dust particles dancing in the air. The vault surface reflects shimmering light patterns. The interior reveals three floating keys orbiting each other inside a translucent protective force field. Pixar 3D render style, smooth shading, warm lighting, soft ambient occlusion. Audio: heavy mechanical locks clicking open, a low resonant hum, warm harmonic tone."),

    ("scene-2-b.mp4",
     "Camera slowly orbits around three glowing key fragments floating inside a translucent force field bubble. Each fragment pulses with soft warm light, rotating gently on different axes. The force field ripples when particles touch its surface, deflecting them outward with tiny flashes. Outside the barrier, shadowy figures reach toward the keys but their hands cannot penetrate. Pixar 3D style, subsurface scattering, expressive. Audio: gentle crystalline hum, soft pings as particles bounce off, a reassuring warm tone."),

    ("scene-2-c.mp4",
     "Camera pulls back dramatically revealing the vault from outside, surrounded by multiple layers of glowing protective barriers. Walls within walls within walls, each glowing gold, amber, and white. The outermost layer pulses gently like breathing. Tiny sparks of light orbit the entire structure like satellites. The scene exudes impenetrable security and warmth. Pixar 3D render, cinematic wide shot, atmospheric perspective. Audio: a deep satisfying resonance, layers humming at different harmonics, a triumphant swell."),

    # ═══ SCENE 3: WALKTHROUGH (14.24s → 4 clips) ═══
    ("scene-3-a.mp4",
     "Camera steadily pushes in on a clean isometric scene showing a stylized glowing smartphone floating in dark space. A finger taps the screen and a bright button activates with a satisfying ripple of light radiating outward from the tap point. The phone tilts slightly toward camera. Clean minimal isometric 3D design, teal and white palette, soft geometric shadows, pastel accents. Audio: a satisfying digital click, a soft chime, a whoosh as the interface activates."),

    ("scene-3-b.mp4",
     "Camera smoothly trucks right revealing a QR code materializing on the phone screen through a particle assembly animation. Glowing bits fly in from all directions to form the intricate pattern. A second device enters frame from the right, its camera emitting a scanning beam connecting to the QR code in a flash of light. Clean isometric 3D, teal and white color palette, soft shadows. Audio: particles assembling with rapid soft clicks, a scanning beam hum, a successful connection ping."),

    ("scene-3-c.mp4",
     "Camera tilts gently as a glowing file icon descends from above the floating phone, drifting down smoothly into a small safe below the device. The safe door swings shut with a satisfying mechanical click. A bright green checkmark bursts into existence above the phone with sparkle particles. Everything locks into place with a final warm pulse of teal light. Isometric 3D style, warm colors, clean geometric shapes. Audio: gentle descent tone, a heavy lock clicking shut, a bright cheerful confirmation chime."),

    ("scene-3-d.mp4",
     "Camera pulls back smoothly to reveal the complete setup: a phone at center surrounded by a protective dome of soft teal light, connected by glowing lines to a vault and an authenticator device. Everything pulses harmoniously in sync. Tiny celebration confetti particles drift downward catching the light. The scene radiates warmth, security, and completion. Isometric 3D, teal and gold palette, soft ambient lighting. Audio: a warm harmonic chord resolving, gentle confetti rustle, a triumphant completion jingle."),

    # ═══ SCENE 4: CTA (8.32s → 3 clips) ═══
    ("scene-4-a.mp4",
     "Camera slowly trucks right across a dramatic split scene. Left side shows a dumpster fire with napkins and sticky notes burning in chaos, smoke billowing, papers curling in flames. Right side shows a gleaming crystal vault radiating clean golden light, organized and serene with floating particles. Stark contrast between destruction and protection. Synthwave aesthetic, neon purple grid below, sunset gradient sky in orange and purple. Audio: crackling fire fading to a clean harmonic tone."),

    ("scene-4-b.mp4",
     "Camera holds medium shot as a confident character raises a glowing golden card above their head triumphantly. Energy arcs crackle around the card, lightning connecting to the ground. The character slams the card down and a massive radial shockwave of golden light erupts outward in all directions, rushing past camera. Everything bathes in warm triumphant light. Synthwave with neon accents, dramatic bold composition. Audio: building electrical charge, a massive satisfying bass impact, a rushing shockwave."),

    ("scene-4-c.mp4",
     "Camera rapidly cranes upward as hundreds of tiny glowing orbs rise from below like floating lanterns, filling a purple and orange gradient sky. A massive glowing portal opens at center frame, radiating warm inviting golden light outward. The orbs spiral toward the portal in flowing streams. Everything feels triumphant, epic, and final. Synthwave aesthetic with subtle VHS scanlines, chrome reflections. Audio: rushing upward wind, orchestral swell building to a peak, a final resonant triumphant chord."),
]

NEG_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, extra limbs, bad anatomy, words, letters, numbers"

def build_workflow(prompt, seed, length=97):
    return {
        # 1. Load checkpoint (MODEL + VAE)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"}
        },
        # 2. Load text encoder (CLIP)
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
                "device": "cpu"
            }
        },
        # 3. Apply distilled LoRA (8-step mode)
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
                "strength_model": 1.0
            }
        },
        # 4. Positive prompt
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["2", 0]
            }
        },
        # 5. Negative prompt
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": NEG_PROMPT,
                "clip": ["2", 0]
            }
        },
        # 6. LTX conditioning
        "6": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["4", 0],
                "negative": ["5", 0],
                "frame_rate": 25
            }
        },
        # 7. Empty video latent
        "7": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {
                "width": 768,
                "height": 512,
                "length": length,
                "batch_size": 1
            }
        },
        # 8. Scheduler (distilled: 8 steps)
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
        # 9. Random noise
        "9": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed}
        },
        # 10. CFG Guider (cfg=1.0 for distilled)
        "10": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["6", 0],
                "negative": ["6", 1],
                "cfg": 1.0
            }
        },
        # 11. Sampler select
        "11": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
        # 12. Sample
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
        # 13. VAE Decode (skip SeparateAVLatent for video-only)
        "13": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["12", 0],
                "vae": ["1", 2]
            }
        },
        # 14. Create video from images
        "14": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["13", 0],
                "fps": 25.0
            }
        },
        # 15. Save video
        "15": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["14", 0],
                "filename_prefix": "pawpad_clip",
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
        except Exception as e:
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


def main():
    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(CLIPS)

    total = end_idx - start_idx
    print(f"Generating clips {start_idx} to {end_idx-1} ({total} clips)")

    for i in range(start_idx, end_idx):
        filename, prompt = CLIPS[i]
        output_path = os.path.join(OUTPUT_DIR, filename)

        # Skip if already exists and is > 10KB
        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            print(f"[{i+1}/{len(CLIPS)}] SKIP {filename} (already exists)")
            continue

        seed = random.randint(1, 999999999)
        workflow = build_workflow(prompt, seed)

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
            else:
                print(f"  ERROR: Could not find video in outputs")
        elif status == "ERROR":
            print(f"  ERROR: {err}")
        else:
            print(f"  TIMEOUT after 300s")

    print("\nAll done!")


if __name__ == "__main__":
    main()
