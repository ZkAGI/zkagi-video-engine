#!/usr/bin/env python3
"""Generate remaining LTX-2 clips (scenes 1-4) with 97 frames for speed."""
import json, time, random, subprocess, sys, os, urllib.request

COMFY_URL = "http://172.18.64.1:8001"
OUTPUT_DIR = "/home/aten/zkagi-video-engine/public/scenes"

SCENES = [
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

def build_workflow(prompt, filename_prefix, seed, length=97):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}},
        "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "gemma_3_12B_it.safetensors", "clip_name2": "ltx-2.3_text_projection_bf16.safetensors", "type": "ltx"}},
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "ltx-2.3-distilled-lora-384.safetensors", "strength_model": 1.0}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed", "clip": ["2", 0]}},
        "6": {"class_type": "LTXVConditioning", "inputs": {"positive": ["4", 0], "negative": ["5", 0], "frame_rate": 25}},
        "7": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": 768, "height": 512, "length": length, "batch_size": 1}},
        "10": {"class_type": "LTXVScheduler", "inputs": {"steps": 8, "max_shift": 2.05, "base_shift": 0.95, "stretch": True, "terminal": 0.1, "latent": ["7", 0]}},
        "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "12": {"class_type": "CFGGuider", "inputs": {"model": ["3", 0], "positive": ["6", 0], "negative": ["6", 1], "cfg": 1.0}},
        "13": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["11", 0], "guider": ["12", 0], "sampler": ["13", 0], "sigmas": ["10", 0], "latent_image": ["7", 0]}},
        "16": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}},
        "17": {"class_type": "CreateVideo", "inputs": {"images": ["16", 0], "fps": 25}},
        "18": {"class_type": "SaveVideo", "inputs": {"video": ["17", 0], "filename_prefix": filename_prefix, "format": "mp4", "codec": "h264"}},
    }

def submit(workflow):
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())["prompt_id"]
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()}")
        return None

def poll(prompt_id, timeout=900):
    start = time.time()
    while time.time() - start < timeout:
        resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
        data = json.loads(resp.read())
        if prompt_id in data:
            status = data[prompt_id].get("status", {}).get("status_str", "")
            if status == "error":
                print(f"  ERROR: {data[prompt_id].get('status', {}).get('messages', [])}")
                return None
            outputs = data[prompt_id].get("outputs", {})
            if outputs:
                return outputs
        time.sleep(10)
    print(f"  TIMEOUT")
    return None

def download(outputs, dest):
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    if fn.endswith(".mp4"):
                        sf = item.get("subfolder", "")
                        url = f"{COMFY_URL}/view?filename={fn}&type=output"
                        if sf: url += f"&subfolder={sf}"
                        urllib.request.urlretrieve(url, dest)
                        return True
    return False

# Submit ALL jobs to queue at once
prompt_ids = []
for scene in SCENES:
    seed = random.randint(1, 2**31)
    wf = build_workflow(scene["prompt"], scene["name"], seed)
    pid = submit(wf)
    if pid:
        prompt_ids.append((scene, pid))
        print(f"Submitted {scene['name']}: {pid}")
    else:
        print(f"FAILED to submit {scene['name']}")

# Wait for each in order
for scene, pid in prompt_ids:
    print(f"\nWaiting for {scene['name']}...")
    outputs = poll(pid, timeout=900)
    if outputs:
        dest = os.path.join(OUTPUT_DIR, scene["output"])
        if download(outputs, dest):
            dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dest], capture_output=True, text=True).stdout.strip()
            print(f"  Saved {dest} ({dur}s)")
        else:
            print(f"  No video found in outputs")
    else:
        print(f"  FAILED")

print("\nAll done!")
