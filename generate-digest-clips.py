#!/usr/bin/env python3
"""Generate all LTX-2 text-to-video clips for Daily AI Digest video.

Uses Pixar/cartoon style with relatable characters — NO generic sci-fi or abstract visuals.
"""
import json, time, random, sys, os

COMFY_URL = "http://172.18.64.1:8001"
OUTPUT_DIR = "/home/aten/zkagi-video-engine/public/scenes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All clips: (filename, prompt) — 2 clips per scene, 7 scenes = 14 clips
# Style: Pixar 3D, warm colors, CHARACTER-DRIVEN, relatable scenarios
CLIPS = [
    # ═══ SCENE 0: HOOK — Energetic intro ═══
    ("digest-0-a.mp4",
     "Camera pushes in toward a cheerful cartoon tiger character sitting behind a colorful curved news desk. The tiger adjusts a tiny microphone on the desk and grins at camera. Behind the tiger, a warm glowing screen displays a playful calendar flipping to today's date. Soft studio spotlights sweep across the set casting warm golden beams. Confetti particles drift gently in the air. Pixar 3D render style, vibrant teal and purple color palette, warm studio lighting, clean smooth surfaces. The tiger's eyes sparkle with excitement."),

    ("digest-0-b.mp4",
     "Camera cranes upward as the cartoon tiger character behind the news desk dramatically slams a big red GO button on the desk. A burst of teal and purple sparkles erupts upward from the button. The desk monitors behind light up one by one showing colorful headline cards. The tiger leans forward eagerly. Everything feels warm, playful, and inviting like a Saturday morning cartoon. Pixar 3D style, vibrant saturated colors, volumetric warm light, smooth rounded shapes."),

    # ═══ SCENE 1: LOCAL LLMs — Cozy laptop hacker ═══
    ("digest-1-a.mp4",
     "Camera slowly orbits around a cartoon person sitting at a cozy bedroom desk late at night. Their laptop screen glows warm orange illuminating their excited face. Messy cables snake across the desk between energy drink cans and sticky notes. A small tower of hard drives blinks with green lights next to the laptop. The character pumps their fist in celebration as code scrolls on screen. A cat sleeps on a stack of books nearby. Pixar 3D render style, warm amber desk lamp lighting, soft shadows, cozy cluttered room atmosphere."),

    ("digest-1-b.mp4",
     "Camera trucks right across a split scene. Left side shows a cartoon character standing sadly under a grey rain cloud. They hold a wilting credit card and look at a giant CLOUD API BILL floating above them. Puddles form at their feet. Right side shows the same character now glowing and confident sitting at home with a laptop. Warm golden light radiates from the screen. Tiny GPU cards orbit around them like trophies. Pixar 3D style, dramatic contrast between cold grey left and warm golden right, bold clean outlines."),

    ("digest-1-c.mp4",
     "Close-up camera shot of cartoon hands typing enthusiastically on a glowing keyboard. The laptop screen shows a friendly AI chat interface with messages flowing. Behind the laptop a cozy room is visible with warm string lights on the wall and posters. A coffee mug with a heart sends up steam curls. The screen reflects warmly on the character's reading glasses. Pixar 3D style, shallow depth of field, warm interior lighting, intimate close-up feel."),

    # ═══ SCENE 2: ACADEMIA — Refreshing the portal ═══
    ("digest-2-a.mp4",
     "Camera handheld with subtle wobble. A stressed cartoon character sits at a desk surrounded by towers of coffee cups. Their hair sticks up in all directions. They stare wide-eyed at a laptop screen showing a massive loading spinner that just keeps spinning. One hand hovers over the keyboard ready to hit refresh again. Papers are scattered everywhere. Dark room lit only by the cold blue screen glow. Pixar 3D style, dramatic blue screen lighting on face, exaggerated comedic stress expression, messy cluttered desk."),

    ("digest-2-b.mp4",
     "Camera slowly pushes in on a giant computer monitor filling the frame. The screen shows a submission portal stuck displaying INTENTION TO SUBMIT in big bold red letters. A progress bar is frozen at ninety-nine percent. A tiny cursor arrow clicks the refresh button over and over. Each click produces a sad little bounce but nothing changes. A crack appears in the screen from frustration. Pixar 3D style, cold fluorescent colors, glitch effects on the screen edges, comedic tragic mood."),

    # ═══ SCENE 3: PHD → FOUNDER — Career pivot ═══
    ("digest-3-a.mp4",
     "Camera cranes upward as a cartoon character in a graduation cap and gown throws their cap high into the air. Mid-flight the graduation cap transforms into a tiny rocket ship with a sparkle trail. Below the character stands between a grey university building on the left and a warm glowing garage with a neon STARTUP sign on the right. Sunset light paints everything golden orange. Pixar 3D style, dramatic golden hour lighting, wide cinematic angle, warm hopeful atmosphere."),

    ("digest-3-b.mp4",
     "Camera pushes forward as a cartoon character in a hoodie presents enthusiastically at a whiteboard covered in colorful diagrams and arrows. They hold a marker in one hand and point at a growth chart shooting upward. Behind them a folding table holds a laptop and energy drinks. The garage setting has exposed brick walls and warm overhead bulb lighting. Expression is passionate and determined. Pixar 3D style, warm tungsten bulb lighting, startup garage aesthetic, energetic pose."),

    # ═══ SCENE 4: AI + PHYSICS — Real objects from AI ═══
    ("digest-4-a.mp4",
     "Camera steadily dollies forward as a cartoon scientist in a white coat holds up a glowing object that just appeared from a futuristic 3D printer. The object transitions from transparent holographic wireframe to solid and colorful. The scientist's face shows pure wonder and amazement. Lab setting with warm golden light emanating from the object. Floating equation symbols dissolve gently in the background. Pixar 3D style, warm golden object glow, subsurface scattering, clean lab environment."),

    ("digest-4-b.mp4",
     "Camera close-up on cartoon hands carefully picking up a freshly printed object from a lab table. The object still shimmers with fading holographic residue transitioning to solid matte. One hand turns it over inspecting it with child-like curiosity. Warm golden light reflects off the object surface. The lab background is soft and blurred. Other printed objects sit on the table nearby. Pixar 3D style, shallow depth of field, warm amber lighting, tactile satisfying feeling."),

    # ═══ SCENE 5: WATCHLIST — Rapid fire open source ═══
    ("digest-5-a.mp4",
     "Camera whip-pans between colorful floating cards arranged in a circle around a cartoon character. Each card displays a different app icon with a GitHub star counter rapidly climbing. The character spins trying to grab them all with an overwhelmed but excited expression. Some cards flash green upward arrows while one flashes a red downward arrow. Stars and sparkles fly off the cards. Pixar 3D style, vibrant rainbow color palette, energetic dynamic angle, playful motion."),

    ("digest-5-b.mp4",
     "Camera tracks forward as a cartoon character sits at a desk rapidly clicking through browser tabs. Each tab shows a different colorful open-source project page. Golden GitHub stars fly out of the screen toward camera like coins. The character has a huge grin and types furiously. Behind them a wall covered in sticky notes with project names glows warmly. Pixar 3D style, warm desk lamp and screen glow, energetic feel, stars as golden particles."),

    # ═══ SCENE 6: OUTRO — Warm goodbye ═══
    ("digest-6-a.mp4",
     "Camera slowly pushes in as a cartoon tiger character waves warmly at camera from behind the news desk. Sunset colors pour through a large window behind the desk painting everything golden orange and soft purple. The ZkAGI logo glows softly on the desk nameplate. Tiny floating lantern orbs rise gently in the background. The tiger's expression is warm and friendly. Pixar 3D style, warm sunset lighting through window, soft volumetric light rays, inviting cozy mood."),

    ("digest-6-b.mp4",
     "Camera slowly cranes upward as hundreds of tiny warm glowing orbs rise like lanterns into a purple and gold gradient sky. The scene is serene and uplifting. The orbs trail soft light behind them. At center frame the text STAY CURIOUS fades in softly glowing in teal. Everything feels warm conclusive and hopeful like the end of a Pixar film. Pixar 3D style, warm volumetric light, atmospheric golden haze, gentle floating particles."),
]

NEG_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, extra limbs, bad anatomy, words, letters, numbers, realistic photo, live action"


def build_workflow(prompt, seed, length=97):
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                "type": "ltx"
            }
        },
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2.3-distilled-lora-384.safetensors",
                "strength_model": 1.0
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["2", 0]
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": NEG_PROMPT,
                "clip": ["2", 0]
            }
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
                "width": 768,
                "height": 512,
                "length": length,
                "batch_size": 1
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
            "inputs": {
                "samples": ["12", 0],
                "vae": ["1", 2]
            }
        },
        "14": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["13", 0],
                "fps": 25.0
            }
        },
        "15": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["14", 0],
                "filename_prefix": "digest_clip",
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
