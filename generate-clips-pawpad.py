#!/usr/bin/env python3
"""Generate LTX-2 video clips for PawPad DeFi Horror Stories via ComfyUI."""

import json, time, random, sys, os, urllib.request, urllib.parse

COMFY_URL = "http://172.18.64.1:8001"
SCENES_DIR = "/home/aten/zkagi-video-engine/public/scenes"

MOTION_PROMPTS = [
    # Scene 0: Rick approves unlimited
    "Camera slowly pushes in on a cartoon man as he taps his glowing phone screen confidently. His grin widens as tiny red flags wave frantically behind him. The phone screen flashes green then abruptly turns blood red. The man's expression freezes mid-grin. Shadows creep in from the edges of the frame. The approve button pulses ominously.",
    # Scene 1: Karen's napkin seed phrase
    "Camera tracks right across a warm kitchen as a claymation man raises a napkin to his face. The woman beside him freezes in horror, hand reaching out too late. Tiny fragments scatter from the napkin. The warm kitchen light flickers. The man blows his nose completely unaware while the woman's jaw drops in slow motion.",
    # Scene 2: Knowledge drop — wallets that think
    "Camera slowly pulls back from a split scene. On the left, rain falls on a dejected figure staring at an empty phone. On the right, a woman presses helplessly against a locked vault. A crack of warm golden light breaks through the center, expanding outward, turning raindrops into golden particles. Both figures look up toward the growing light.",
    # Scene 3: PawPad solution
    "Camera dollies forward through a protective force field as a sleek vault materializes in bright warm light. Shadowy hands reach toward it but deflect off rippling energy shields. An AI eye scans a suspicious document and marks it red. Three holographic tap indicators light up in sequence. Warm light particles spiral upward around the vault.",
    # Scene 4: CTA mic drop
    "Camera starts close on a glowing wallet card floating in neon space. Energy arcs radiate outward as the card rotates slowly. The synthwave grid below pulses with purple and teal light. Camera pulls back to reveal the full energy burst. Chrome reflections shimmer on every surface as particles stream toward the camera.",
]

NEGATIVE_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, extra limbs, bad anatomy"


def upload_image(filepath):
    """Upload image to ComfyUI, return the server-side filename."""
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        data = f.read()

    boundary = "----WebKitFormBoundary" + str(random.randint(10**15, 10**16))
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result.get("name", filename)


def build_workflow(image_name, motion_prompt, seed, scene_idx=0):
    """Build ComfyUI workflow for LTX-2 image-to-video."""
    return {
        # 1: Load checkpoint → MODEL(0), CLIP(1, unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"},
        },
        # 2: Load text encoder → CLIP(0)
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                "type": "ltx",
            },
        },
        # 3: Apply distilled LoRA (model only, not clip)
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2.3-distilled-lora-384.safetensors",
                "strength_model": 1.0,
            },
        },
        # 4: Load reference image
        "4": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name},
        },
        # 5: Preprocess image
        "5": {
            "class_type": "LTXVPreprocess",
            "inputs": {"image": ["4", 0], "img_compression": 35},
        },
        # 6: Positive prompt (clip from text encoder directly, not through LoRA)
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": motion_prompt, "clip": ["2", 0]},
        },
        # 7: Negative prompt
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE_PROMPT, "clip": ["2", 0]},
        },
        # 8: LTX conditioning
        "8": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "frame_rate": 25.0,
            },
        },
        # 9: Image to Video
        "9": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["8", 0],
                "negative": ["8", 1],
                "vae": ["1", 2],
                "image": ["5", 0],
                "width": 768,
                "height": 512,
                "length": 97,
                "batch_size": 1,
                "strength": 1.0,
            },
        },
        # 10: Scheduler (distilled: 8 steps)
        "10": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 8,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["9", 2],
            },
        },
        # 11: Random noise
        "11": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed},
        },
        # 12: CFG Guider (cfg=1.0 for distilled)
        "12": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["9", 0],
                "negative": ["9", 1],
                "cfg": 1.0,
            },
        },
        # 13: Sampler select
        "13": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"},
        },
        # 14: Sample
        "14": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["11", 0],
                "guider": ["12", 0],
                "sampler": ["13", 0],
                "sigmas": ["10", 0],
                "latent_image": ["9", 2],
            },
        },
        # 15: VAE Decode
        "15": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["14", 0], "vae": ["1", 2]},
        },
        # 16: Create Video
        "16": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["15", 0], "fps": 25.0},
        },
        # 17: Save Video
        "17": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["16", 0],
                "filename_prefix": f"scene_{scene_idx}_a",
                "format": "mp4",
                "codec": "h264",
            },
        },
    }


def submit_workflow(workflow):
    """Submit workflow to ComfyUI and return prompt_id."""
    payload = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    if "error" in result:
        print(f"  ERROR: {result['error']}")
        if "node_errors" in result:
            for nid, err in result["node_errors"].items():
                print(f"    Node {nid}: {err}")
        return None
    return result["prompt_id"]


def poll_completion(prompt_id, timeout=300):
    """Poll until workflow completes or errors."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            history = json.loads(resp.read())
            if prompt_id in history:
                status = history[prompt_id].get("status", {}).get("status_str", "")
                outputs = history[prompt_id].get("outputs", {})
                if status == "error":
                    print(f"  ERROR in workflow")
                    msgs = history[prompt_id].get("status", {}).get("messages", [])
                    for m in msgs:
                        print(f"    {m}")
                    return None
                if outputs:
                    return history[prompt_id]
        except Exception as e:
            print(f"  Poll error: {e}")
        time.sleep(5)
    print(f"  TIMEOUT after {timeout}s")
    return None


def download_video(history_entry, output_path):
    """Download the generated video from ComfyUI."""
    outputs = history_entry.get("outputs", {})
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    subfolder = item.get("subfolder", "")
                    if fn.endswith(".mp4"):
                        url = f"{COMFY_URL}/view?filename={urllib.parse.quote(fn)}&type=output"
                        if subfolder:
                            url += f"&subfolder={urllib.parse.quote(subfolder)}"
                        urllib.request.urlretrieve(url, output_path)
                        return True
    return False


def main():
    for i in range(2, 5):  # scenes 2,3,4 (0,1 already done)
        print(f"\n{'='*60}")
        print(f"SCENE {i}: Generating video clip...")
        print(f"{'='*60}")

        image_path = f"{SCENES_DIR}/scene-{i}-a.png"
        output_path = f"{SCENES_DIR}/scene-{i}-a.mp4"

        # Upload image
        print(f"  Uploading {image_path}...")
        image_name = upload_image(image_path)
        print(f"  Uploaded as: {image_name}")

        # Build workflow
        seed = random.randint(1, 2**32)
        workflow = build_workflow(image_name, MOTION_PROMPTS[i], seed, i)

        # Submit
        print(f"  Submitting workflow (seed={seed})...")
        prompt_id = submit_workflow(workflow)
        if not prompt_id:
            print(f"  FAILED to submit scene {i}")
            continue
        print(f"  Submitted: {prompt_id}")

        # Poll
        print(f"  Waiting for completion...")
        result = poll_completion(prompt_id, timeout=300)
        if not result:
            print(f"  FAILED scene {i}")
            continue

        # Download
        print(f"  Downloading video...")
        if download_video(result, output_path):
            size = os.path.getsize(output_path)
            print(f"  DONE: {output_path} ({size} bytes)")
        else:
            print(f"  FAILED to download scene {i}")

    print(f"\n{'='*60}")
    print("All scenes processed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
