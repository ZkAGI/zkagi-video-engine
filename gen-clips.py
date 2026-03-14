#!/usr/bin/env python3
"""Generate LTX-2 video clips for scenes 0-3 via ComfyUI."""
import json, time, random, sys, urllib.request, urllib.error, shutil

COMFY_URL = "http://172.18.64.1:8001"

SCENES = [
    {
        "image": "scene-0-a.png",
        "prompt": "Camera slowly pushes in on a woman sitting up in bed in the dark, her face lit by the harsh blue glow of a phone screen. Her eyes dart nervously across crypto charts. She shifts anxiously, pulling blankets tighter. The phone screen flickers between different falling charts. Shadows dance on the walls from the screen light. A cat stirs at the foot of the bed.",
        "prefix": "scene_0",
    },
    {
        "image": "scene-1-a.png",
        "prompt": "Camera slowly trucks right across three panels. Left panel: a hand slides a notebook under a mattress, the mattress bouncing. Center: a massive vault door swings open revealing a tiny paper fluttering inside. Right: a phone screen lights up with shocked emoji reactions cascading down a group chat. Each panel animates in sequence. Dramatic lighting shifts between warm, cold, and bright.",
        "prefix": "scene_1",
    },
    {
        "image": "scene-2-a.png",
        "prompt": "Camera slowly dollies forward as a crystalline vault materializes from particles of light, golden keys float upward inside the forming structure. Energy ripples pulse across the translucent surface. Shadowy hands reach toward the vault but are repelled by flashes of light on contact. Blue and purple volumetric rays sweep across the scene. The vault glows brighter as it solidifies.",
        "prefix": "scene_2",
    },
    {
        "image": "scene-3-a.png",
        "prompt": "Camera slowly trucks right across a split scene. Left side: a person sleeps peacefully, blanket gently rising and falling with breath, warm amber nightlight glowing. Right side: a tiny robot in a suit frantically works holographic screens, arms blur across controls, green profit arrows shoot upward on charts. Coffee cup rattles on the desk. The contrast between calm and chaos.",
        "prefix": "scene_3",
    },
]

def build_workflow(image_name, motion_prompt, prefix):
    seed = random.randint(1, 2**31)
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}},
        "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "gemma_3_12B_it.safetensors", "clip_name2": "ltx-2.3_text_projection_bf16.safetensors", "type": "ltx"}},
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "ltx-2.3-distilled-lora-384.safetensors", "strength_model": 1.0}},
        "4": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "5": {"class_type": "LTXVPreprocess", "inputs": {"image": ["4", 0], "img_compression": 35}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": motion_prompt, "clip": ["2", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed", "clip": ["2", 0]}},
        "8": {"class_type": "LTXVConditioning", "inputs": {"positive": ["6", 0], "negative": ["7", 0], "frame_rate": 25}},
        "9": {"class_type": "LTXVImgToVideo", "inputs": {"positive": ["8", 0], "negative": ["8", 1], "vae": ["1", 2], "image": ["5", 0], "width": 768, "height": 512, "length": 97, "batch_size": 1, "strength": 1.0}},
        "10": {"class_type": "LTXVScheduler", "inputs": {"steps": 8, "max_shift": 2.05, "base_shift": 0.95, "stretch": True, "terminal": 0.1, "latent": ["9", 2]}},
        "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "12": {"class_type": "CFGGuider", "inputs": {"model": ["3", 0], "positive": ["8", 0], "negative": ["8", 1], "cfg": 1.0}},
        "13": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["11", 0], "guider": ["12", 0], "sampler": ["13", 0], "sigmas": ["10", 0], "latent_image": ["9", 2]}},
        "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}},
        "16": {"class_type": "CreateVideo", "inputs": {"images": ["15", 0], "fps": 25.0}},
        "17": {"class_type": "SaveVideo", "inputs": {"video": ["16", 0], "filename_prefix": prefix, "format": "mp4", "codec": "h264"}}
    }

def submit_and_wait(workflow, scene_idx):
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    prompt_id = result["prompt_id"]
    print(f"Scene {scene_idx}: submitted prompt_id={prompt_id}")

    while True:
        time.sleep(5)
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            hist = json.loads(resp.read())
        except:
            print(f"Scene {scene_idx}: polling error, retrying...")
            continue

        if prompt_id not in hist:
            print(f"Scene {scene_idx}: waiting...")
            continue

        entry = hist[prompt_id]
        status = entry.get("status", {}).get("status_str", "")
        if status == "error":
            print(f"Scene {scene_idx}: ERROR!")
            print(json.dumps(entry.get("status", {}), indent=2))
            return None

        outputs = entry.get("outputs", {})
        if outputs:
            for nid, out in outputs.items():
                for key in ["gifs", "videos", "images"]:
                    if key in out:
                        for item in out[key]:
                            fn = item.get("filename", "")
                            if fn.endswith(".mp4") or fn.endswith(".webm"):
                                print(f"Scene {scene_idx}: DONE -> {fn}")
                                return fn
            print(f"Scene {scene_idx}: outputs found but no video file")
            print(json.dumps(outputs, indent=2))
            return None

        print(f"Scene {scene_idx}: running...")

def download_video(filename, output_path):
    url = f"{COMFY_URL}/view?filename={filename}&type=output"
    with urllib.request.urlopen(url) as resp, open(output_path, "wb") as f:
        shutil.copyfileobj(resp, f)
    print(f"Downloaded: {output_path}")

if __name__ == "__main__":
    # Scene 0 was already submitted, let's check if it's done first
    # Then submit remaining scenes
    for i, scene in enumerate(SCENES):
        if i == 0:
            # Scene 0 already submitted with prompt_id ff916bc6-d4c9-473b-b1e3-3eab4811e2c0
            prompt_id = "ff916bc6-d4c9-473b-b1e3-3eab4811e2c0"
            print(f"\n{'='*60}")
            print(f"Waiting for scene 0 (already submitted: {prompt_id})")
            print(f"{'='*60}")
            while True:
                time.sleep(5)
                try:
                    resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
                    hist = json.loads(resp.read())
                except:
                    print("Polling error, retrying...")
                    continue
                if prompt_id not in hist:
                    print("Scene 0: waiting...")
                    continue
                entry = hist[prompt_id]
                status = entry.get("status", {}).get("status_str", "")
                if status == "error":
                    print("Scene 0: ERROR, resubmitting...")
                    wf = build_workflow(scene["image"], scene["prompt"], scene["prefix"])
                    filename = submit_and_wait(wf, 0)
                    break
                outputs = entry.get("outputs", {})
                if outputs:
                    filename = None
                    for nid, out in outputs.items():
                        for key in ["gifs", "videos", "images"]:
                            if key in out:
                                for item in out[key]:
                                    fn = item.get("filename", "")
                                    if fn.endswith(".mp4") or fn.endswith(".webm"):
                                        filename = fn
                                        print(f"Scene 0: DONE -> {fn}")
                    break
                print("Scene 0: running...")
        else:
            print(f"\n{'='*60}")
            print(f"Generating video clip for scene {i}")
            print(f"{'='*60}")
            wf = build_workflow(scene["image"], scene["prompt"], scene["prefix"])
            filename = submit_and_wait(wf, i)

        if filename:
            output_path = f"/home/aten/zkagi-video-engine/public/scenes/scene-{i}-a.mp4"
            download_video(filename, output_path)
        else:
            print(f"Scene {i}: FAILED to generate video")
            sys.exit(1)

    print("\n\nAll video clips generated successfully!")
