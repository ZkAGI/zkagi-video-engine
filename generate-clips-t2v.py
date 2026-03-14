#!/usr/bin/env python3
"""Generate LTX-2 text-to-video clips for Zynapse Content Factory demo."""

import json, time, random, subprocess, sys, os, urllib.request, urllib.error

COMFY_URL = "http://172.18.64.1:8001"
OUTPUT_DIR = "public/scenes"

SCENES = [
    {
        "index": 0,
        "prompt": "Camera slowly dollies forward into a corporate glass office. A stressed executive stands before a massive whiteboard covered in red marker showing rising costs and salary figures. Papers flutter off the desk as if caught in a gust. The fluorescent lights overhead flicker ominously. Shadows deepen across the room as the camera pushes closer, revealing the executive's worried expression. Dust particles drift through harsh cold light beams. The mood is tense and oppressive, cold blue corporate lighting.",
    },
    {
        "index": 1,
        "prompt": "Camera slowly pans across a chaotic open-plan office. Designers wave color swatches in the air while copywriters frantically type on keyboards. Notification bubbles float upward like soap bubbles from multiple screens. A person in the center holds up a single social media post card looking overwhelmed as colleagues crowd around pointing and arguing. Papers swirl through the air. Warm overhead lights cast busy cluttered shadows. The atmosphere is frantic and exhausting.",
    },
    {
        "index": 2,
        "prompt": "Camera pushes forward into a sleek dark command center with three floating holographic terminal windows glowing bright teal. Each terminal displays a different API endpoint pulsing with energy. Data streams flow between the terminals like luminous rivers. The first terminal materializes a product image, the second morphs it into motion, the third generates waveform audio. Particles of light drift upward. The atmosphere is futuristic and powerful, deep blue and teal lighting with volumetric light rays.",
    },
    {
        "index": 3,
        "prompt": "Camera starts wide and slowly pushes into a developer's clean minimal workstation. Three terminal windows are open side by side, green text scrolling as curl commands execute. Output results appear one after another - an image materializes, then transforms into a video thumbnail, then an audio waveform appears. The screen glow illuminates the developer's satisfied expression. Ambient particles float in the cool blue monitor light. The mood is efficient and triumphant.",
    },
    {
        "index": 4,
        "prompt": "Camera holds on a medium shot as a glowing teal shield emblem materializes in the center of a dark space, surrounded by orbiting data fragments. The shield pulses with energy, sending out radial waves of light. Privacy lock symbols float around it like satellites. The camera slowly pulls back revealing the full emblem with a URL text below it glowing bright. Energy crackles around the edges. Warm golden and teal volumetric light fills the scene. The atmosphere is triumphant and secure.",
    },
]

NEGATIVE = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, words, letters, numbers"


def build_workflow(prompt, seed, prefix):
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"},
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                "type": "ltx",
            },
        },
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2.3-distilled-lora-384.safetensors",
                "strength_model": 1.0,
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 0]},
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE, "clip": ["2", 0]},
        },
        "6": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["4", 0],
                "negative": ["5", 0],
                "frame_rate": 25,
            },
        },
        "7": {
            "class_type": "EmptyLTXVLatentVideo",
            "inputs": {
                "width": 768,
                "height": 512,
                "length": 97,
                "batch_size": 1,
            },
        },
        "8": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 8,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["7", 0],
            },
        },
        "9": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed},
        },
        "10": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["6", 0],
                "negative": ["6", 1],
                "cfg": 1.0,
            },
        },
        "11": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"},
        },
        "12": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["9", 0],
                "guider": ["10", 0],
                "sampler": ["11", 0],
                "sigmas": ["8", 0],
                "latent_image": ["7", 0],
            },
        },
        "13": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["12", 0], "vae": ["1", 2]},
        },
        "14": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["13", 0], "fps": 25.0},
        },
        "15": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["14", 0],
                "filename_prefix": prefix,
                "format": "mp4",
                "codec": "h264",
            },
        },
    }


def submit_workflow(workflow):
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["prompt_id"]


def poll_completion(prompt_id, timeout=300):
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
                    print(f"  ERROR: {msgs}")
                    return None
                if outputs:
                    return data[prompt_id]
        except Exception as e:
            print(f"  Poll error: {e}")
        time.sleep(5)
    print(f"  TIMEOUT after {timeout}s")
    return None


def download_video(result, output_path):
    outputs = result.get("outputs", {})
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
                        urllib.request.urlretrieve(url, output_path)
                        print(f"  Downloaded: {output_path}")
                        return True
    print("  No video file found in outputs")
    return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for scene in SCENES:
        idx = scene["index"]
        prefix = f"scene_{idx}"
        output_path = f"{OUTPUT_DIR}/scene-{idx}-a.mp4"
        seed = random.randint(1, 2**31)

        print(f"\n=== Scene {idx} ===")
        print(f"  Prompt: {scene['prompt'][:80]}...")

        workflow = build_workflow(scene["prompt"], seed, prefix)
        prompt_id = submit_workflow(workflow)
        print(f"  Submitted: {prompt_id}")

        result = poll_completion(prompt_id, timeout=300)
        if result:
            download_video(result, output_path)
            # Verify
            dur = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", output_path],
                capture_output=True, text=True
            )
            print(f"  Duration: {dur.stdout.strip()}s")
        else:
            print(f"  FAILED for scene {idx}")

    print("\n=== All clips generated ===")


if __name__ == "__main__":
    main()
