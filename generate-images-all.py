import requests, os, sys, concurrent.futures, json, base64, time

SCENE_DIR = "/home/aten/zkagi-video-engine/public/scenes"
os.makedirs(SCENE_DIR, exist_ok=True)

PRIMARY_URL = "http://45.251.34.28:8010/generate"
FALLBACK_URL = "https://zynapse.zkagi.ai/v1/generate/image"
FALLBACK_KEY = "758b5e2a-f9f5-4531-a062-6de90371ab9f"

IMAGE_PROMPTS = [
    # Scene 0 (2 images - 4s hook)
    ("scene-0-a", "A confident young South Asian tech entrepreneur sitting casually on a modern couch, laptop open showing colorful AI dashboards, empty ergonomic office chairs arranged behind him, cozy modern loft office, Pixar 3D render style, warm ambient lighting with soft golden tones, medium shot, highly detailed, vibrant saturated colors, cinematic composition"),
    ("scene-0-b", "Close-up of a glowing laptop screen showing an AI-powered company dashboard with zero employees listed and revenue charts climbing upward, holographic interface elements floating above the keyboard, Pixar 3D render style, cool blue monitor glow reflecting on nearby surfaces, extreme close-up shot, sharp focus, highly detailed, cinematic composition"),

    # Scene 1 (3 images - 11.52s AI workforce)
    ("scene-1-a", "A cartoon robot in a tiny business suit sitting at an HR desk, reviewing holographic resumes floating in the air, a nameplate reading AI HR on the desk, modern minimalist office, flat vector illustration style, clean geometric shapes, bright even lighting, wide shot, highly detailed, vibrant colors, professional illustration"),
    ("scene-1-b", "A sleek robot arm painting on holographic canvases, generating colorful marketing posters and advertisements that float in mid-air, creative studio setting with paint splatters, isometric 3D perspective, soft pastel lighting, low-poly style, highly detailed, artstation quality, cinematic composition"),
    ("scene-1-c", "A robot in a tiny Wall Street suit frantically working multiple glowing trading screens showing green candlestick charts, crypto symbols floating around, dark trading floor with neon monitor glow, synthwave aesthetic, neon grid reflections, dramatic rim lighting, medium shot, highly detailed, vibrant saturated colors"),

    # Scene 2 (3 images - 10.40s water cooler)
    ("scene-2-a", "A lone man standing by an office water cooler talking to a floating holographic chatbot interface with speech bubbles, empty office cubicles stretching into the distance behind him, comic book art style, bold black outlines, halftone dots, warm fluorescent office lighting, wide establishing shot, highly detailed, vibrant colors, pop art influence"),
    ("scene-2-b", "Close-up of a glowing chatbot screen showing a witty conversation with emoji reactions, the chatbot avatar wearing a tiny counselor graduation cap, comic book art style, bold outlines, bright saturated colors, pop art influence, extreme close-up, sharp focus, cinematic composition"),
    ("scene-2-c", "A confident man nodding approvingly at a chatbot hologram while three ghost outlines of former employees fade away in the background looking confused, comic book art style, dramatic split lighting, halftone dots, dynamic composition, bold outlines, highly detailed, vibrant colors"),

    # Scene 3 (3 images - 12.32s API everything)
    ("scene-3-a", "Split scene left side shows a futuristic server room with glowing API nodes connected by light beams running autonomously right side shows a relaxed person on a tropical beach with a cocktail, synthwave aesthetic, neon purple and orange sunset gradient, cinematic split composition, highly detailed, vibrant saturated colors, dramatic lighting"),
    ("scene-3-b", "A massive holographic control panel floating in space showing AI processes running autonomously with image generation video rendering and trading bots all connected by flowing data streams of light, concept art style, digital matte painting, epic scale, deep blue and purple tones, volumetric light rays, cinematic scope, highly detailed"),
    ("scene-3-c", "A happy person relaxing in a beach hammock, phone screen showing all-green dashboards and money symbols, tropical sunset behind, palm trees swaying, Studio Ghibli inspired, hand-painted watercolor style, warm golden hour sunlight, lush detail, whimsical atmosphere, medium shot, highly detailed"),

    # Scene 4 (2 images - 6.72s mic drop)
    ("scene-4-a", "A glowing holographic API endpoint personified as the perfect employee, a translucent figure in a crisp business suit with streaming code flowing through its body, holding a gold Employee of the Year trophy, Art Deco style, gold and black geometric patterns, dramatic uplighting from below, ornate symmetric frame, luxury illustration, hero shot, highly detailed"),
    ("scene-4-b", "Bold glowing text ZKAGI floating in 3D space surrounded by orbiting API icons and golden light bursts radiating outward, energy explosion effect, synthwave aesthetic, neon grid floor, chrome reflections, dramatic purple and gold color scheme, epic reveal shot from below, highly detailed, cinematic composition"),
]

def generate_image_primary(prompt, filename):
    """Try primary server first"""
    try:
        resp = requests.post(PRIMARY_URL, 
            json={"prompt": prompt, "width": 768, "height": 512},
            timeout=60)
        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "")
            if "image" in content_type:
                return resp.content
            else:
                # Might be JSON with base64
                try:
                    data = resp.json()
                    if "image" in data:
                        return base64.b64decode(data["image"])
                    elif "images" in data and len(data["images"]) > 0:
                        return base64.b64decode(data["images"][0])
                except:
                    pass
    except Exception as e:
        print(f"  Primary failed for {filename}: {e}")
    return None

def generate_image_fallback(prompt, filename):
    """Use Zynapse fallback"""
    try:
        resp = requests.post(FALLBACK_URL,
            headers={"X-API-Key": FALLBACK_KEY, "Content-Type": "application/json"},
            json={"prompt": prompt, "width": 768, "height": 512, "num_steps": 24, "guidance": 3.5, "strength": 1},
            timeout=120)
        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "")
            if "image" in content_type:
                return resp.content
            else:
                try:
                    data = resp.json()
                    if "image" in data:
                        return base64.b64decode(data["image"])
                    elif "images" in data and len(data["images"]) > 0:
                        img_data = data["images"][0]
                        if isinstance(img_data, dict) and "url" in img_data:
                            img_resp = requests.get(img_data["url"], timeout=30)
                            return img_resp.content
                        return base64.b64decode(img_data)
                    elif "url" in data:
                        img_resp = requests.get(data["url"], timeout=30)
                        return img_resp.content
                except Exception as e2:
                    print(f"  Fallback parse failed for {filename}: {e2}, resp text: {resp.text[:200]}")
        else:
            print(f"  Fallback HTTP {resp.status_code} for {filename}: {resp.text[:200]}")
    except Exception as e:
        print(f"  Fallback failed for {filename}: {e}")
    return None

def generate_image(item):
    filename, prompt = item
    out_path = os.path.join(SCENE_DIR, f"{filename}.png")
    
    # Try primary first
    img_data = generate_image_primary(prompt, filename)
    if img_data and len(img_data) > 1000:
        with open(out_path, "wb") as f:
            f.write(img_data)
        print(f"  {filename}: OK (primary, {len(img_data)} bytes)")
        return filename, True
    
    # Fallback to Zynapse
    print(f"  {filename}: trying fallback...")
    img_data = generate_image_fallback(prompt, filename)
    if img_data and len(img_data) > 1000:
        with open(out_path, "wb") as f:
            f.write(img_data)
        print(f"  {filename}: OK (fallback, {len(img_data)} bytes)")
        return filename, True
    
    print(f"  {filename}: FAILED both servers")
    return filename, False

print(f"Generating {len(IMAGE_PROMPTS)} images...")
# Use 4 workers to not overwhelm servers
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(generate_image, item): item for item in IMAGE_PROMPTS}
    results = {}
    for future in concurrent.futures.as_completed(futures):
        filename, success = future.result()
        results[filename] = success

print("\n=== Image Results ===")
ok = sum(1 for v in results.values() if v)
print(f"{ok}/{len(IMAGE_PROMPTS)} images generated successfully")
for name in sorted(results.keys()):
    status = "OK" if results[name] else "FAILED"
    print(f"  {name}: {status}")
