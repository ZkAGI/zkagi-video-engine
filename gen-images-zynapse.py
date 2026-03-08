#!/usr/bin/env python3
"""Generate scene images via Zynapse API (fallback when primary is down)."""
import requests, os, time, random

FALLBACK_URL = "https://zynapse.zkagi.ai/v1/generate/image"
API_KEY = "758b5e2a-f9f5-4531-a062-6de90371ab9f"
SCENE_DIR = "/home/aten/zkagi-video-engine/public/scenes"
os.makedirs(SCENE_DIR, exist_ok=True)

IMAGE_PROMPTS = [
    # Scene 0 (2 images)
    ("scene-0-b", "Close-up of a glowing laptop screen showing an AI-powered company dashboard with zero employees listed and revenue charts climbing upward, holographic interface elements floating above the keyboard, cool blue monitor glow reflecting on nearby surfaces, Pixar 3D render style, extreme close-up shot, sharp focus, highly detailed, cinematic composition"),

    # Scene 1 (3 images)
    ("scene-1-a", "A cartoon robot in a tiny business suit sitting at an HR desk, reviewing holographic resumes floating in the air, a nameplate reading AI HR on the desk, modern minimalist office, flat vector illustration style, clean geometric shapes, bright even lighting, wide shot, highly detailed, vibrant colors, professional illustration"),
    ("scene-1-b", "A sleek robot arm painting on holographic canvases, generating colorful marketing posters and advertisements that float in mid-air, creative studio setting with paint splatters, isometric 3D perspective, soft pastel lighting, low-poly style, highly detailed, cinematic composition"),
    ("scene-1-c", "A robot in a tiny Wall Street suit frantically working multiple glowing trading screens showing green candlestick charts, crypto symbols floating around, dark trading floor with neon monitor glow, synthwave aesthetic, neon grid reflections, dramatic rim lighting, medium shot, highly detailed, vibrant saturated colors"),

    # Scene 2 (2 images)
    ("scene-2-a", "A lone man standing by an office water cooler talking to a floating holographic chatbot interface with speech bubbles, empty office cubicles stretching into the distance behind him, comic book art style, bold black outlines, halftone dots, warm fluorescent office lighting, wide establishing shot, highly detailed, vibrant colors"),
    ("scene-2-b", "A confident man nodding approvingly at a chatbot hologram while three ghost outlines of former employees fade away in the background looking confused, comic book art style, dramatic split lighting, halftone dots, dynamic composition, bold outlines, highly detailed, vibrant colors"),

    # Scene 3 (3 images)
    ("scene-3-a", "Split scene left side shows a futuristic server room with glowing API nodes connected by light beams running autonomously right side shows a relaxed person on a tropical beach with a cocktail, synthwave aesthetic, neon purple and orange sunset gradient, cinematic split composition, highly detailed, vibrant saturated colors"),
    ("scene-3-b", "A massive holographic control panel floating in space showing AI processes running autonomously with image generation video rendering and trading bots all connected by flowing data streams of light, concept art style, digital matte painting, epic scale, deep blue and purple tones, volumetric light rays, cinematic scope, highly detailed"),
    ("scene-3-c", "A happy person relaxing in a beach hammock, phone screen showing all-green dashboards and money symbols, tropical sunset behind, palm trees swaying, Studio Ghibli inspired, hand-painted watercolor style, warm golden hour sunlight, lush detail, whimsical atmosphere, medium shot, highly detailed"),

    # Scene 4 (2 images)
    ("scene-4-a", "A glowing holographic API endpoint personified as the perfect employee, a translucent figure in a crisp business suit with streaming code flowing through its body, holding a gold Employee of the Year trophy, Art Deco style, gold and black geometric patterns, dramatic uplighting from below, ornate symmetric frame, luxury illustration, hero shot, highly detailed"),
    ("scene-4-b", "Bold glowing text ZKAGI floating in 3D space surrounded by orbiting API icons and golden light bursts radiating outward, energy explosion effect, synthwave aesthetic, neon grid floor, chrome reflections, dramatic purple and gold color scheme, epic reveal shot from below, highly detailed, cinematic composition"),
]

def gen_image(name, prompt, attempt=1):
    out = os.path.join(SCENE_DIR, f"{name}.png")
    print(f"[{name}] Generating (attempt {attempt})...", flush=True)
    try:
        resp = requests.post(FALLBACK_URL,
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"prompt": prompt, "width": 768, "height": 512,
                  "num_steps": 24, "guidance": 3.5,
                  "seed": random.randint(0, 999999), "strength": 1},
            timeout=120)
        if resp.status_code == 200 and len(resp.content) > 5000:
            ct = resp.headers.get("content-type", "")
            if "image" in ct:
                # Convert JPEG to PNG using PIL if available, else save raw
                try:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(resp.content))
                    img.save(out, "PNG")
                    print(f"  -> OK ({os.path.getsize(out)} bytes, converted to PNG)", flush=True)
                except ImportError:
                    # Save raw (JPEG data with .png ext — browsers handle it)
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    print(f"  -> OK ({len(resp.content)} bytes, saved as-is)", flush=True)
                return True
            else:
                print(f"  Unexpected content-type: {ct}", flush=True)
        else:
            print(f"  HTTP {resp.status_code}, {len(resp.content)} bytes", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)
    return False

success = 0
total = len(IMAGE_PROMPTS)

for name, prompt in IMAGE_PROMPTS:
    out = os.path.join(SCENE_DIR, f"{name}.png")
    if os.path.exists(out) and os.path.getsize(out) > 5000:
        print(f"[{name}] Already exists, skipping", flush=True)
        success += 1
        continue

    ok = False
    for attempt in range(1, 4):  # up to 3 retries
        if gen_image(name, prompt, attempt):
            ok = True
            success += 1
            break
        time.sleep(3)  # backoff between retries

    if not ok:
        print(f"[{name}] FAILED after 3 attempts", flush=True)

    time.sleep(1)  # rate limiting between images

print(f"\n=== Results: {success}/{total} images generated ===", flush=True)
