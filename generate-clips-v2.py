#!/usr/bin/env python3
"""Generate LTX-2 video clips for Zero-Employee Enterprise video.
Uses image-to-video for scene 0 (has reference image), text-to-video for rest."""

import json
import time
import random
import requests
import subprocess
import os

COMFY_URL = "http://172.18.64.1:8001"
PROJECT_DIR = "/home/aten/zkagi-video-engine"

# Scene clips: (scene_idx, sub_clip_letter, num_frames, mode, prompt)
# mode: "i2v" = image-to-video, "t2v" = text-to-video
CLIPS = [
    # Scene 0: Hook — Meet Raj (4.48s audio → 2 clips at 97 frames)
    (0, "a", 97, "i2v",
     "Camera slowly dollies toward the confident entrepreneur sitting at the desk. Golden sunlight shifts through the windows casting moving shadows across empty chairs. The laptop screen glows brighter with pulsing AI dashboards. Dust motes drift lazily through warm light beams. The man's expression shifts to a confident smirk."),
    (0, "b", 97, "t2v",
     "Camera slowly orbits around a modern empty office revealing rows of vacant desks and ergonomic chairs stretching into the distance, Pixar 3D animated style with soft ambient occlusion. A single person sits confidently at the center desk typing on a glowing laptop. City skyline visible through tall windows. Warm golden light shifts with the camera movement creating moving shadows across the polished floor."),

    # Scene 1: AI Workforce (16.64s audio → 4 clips at 121 frames)
    (1, "a", 121, "t2v",
     "A cartoon robot in a crisp tiny business suit sits at an HR desk stamping holographic floating resumes in a bright modern office, Pixar 3D animated style. Each rejected resume dissolves into sparkles and flies upward. Filing cabinets open and close autonomously behind the robot. Warm overhead lighting mixes with cool holographic screen glow. Camera pushes in slowly toward the busy robot."),
    (1, "b", 121, "t2v",
     "A sleek robot arm paints on floating holographic canvases in a colorful creative studio, flat vector illustration style with clean lines. Marketing images fly outward in all directions as they are generated automatically. Digital paint splashes arc through the air creating rainbow trails. Floating screens rotate showing auto-generated advertisements. Camera trucks slowly to the right through the studio."),
    (1, "c", 121, "t2v",
     "A small robot in a tiny Wall Street suit frantically works multiple glowing crypto trading monitors in a dark trading floor, synthwave neon aesthetic with chrome reflections. Green candlestick charts shoot upward rapidly on the screens. Numbers cascade across displays. The robot pumps its tiny fist triumphantly as profit indicators flash bright green. Camera zooms in slowly on the action."),
    (1, "d", 121, "t2v",
     "Camera pulls back revealing three AI robot workstations in a panoramic modern office, Pixar 3D style. An HR robot stamps resumes on the left, a creative robot generates colorful images in the center, and a trading robot monitors green charts on the right. Each workstation glows with different colored accent light. Thin data streams connect them like rivers of light flowing through the air above."),

    # Scene 2: Water Cooler (8.00s audio → 2 clips at 121 frames)
    (2, "a", 121, "t2v",
     "A lone cartoon office worker in business casual stands at a water cooler in a completely empty modern break room, comic book art style with bold black outlines and halftone dots. A friendly glowing blue holographic chatbot hovers nearby showing an expressive animated face. Speech bubbles with chart icons float upward and pop with sparkle effects. Warm fluorescent lighting fills the cozy scene. Camera gently pushes in toward the pair."),
    (2, "b", 121, "t2v",
     "Camera orbits slowly around a cozy office break room, Studio Ghibli hand-painted style with soft warm lighting. A holographic AI chatbot projects rotating 3D charts and graphs in mid-air next to a water cooler. Steam curls upward from a coffee mug on the counter. A person standing nearby chuckles and nods approvingly. Light shifts through venetian blinds creating moving stripe patterns on the wall. Empty cubicles visible through a doorway behind."),

    # Scene 3: APIs Run Everything (14.88s audio → 3 clips at 137 frames)
    (3, "a", 137, "t2v",
     "A relaxed cartoon person in sunglasses and a hawaiian shirt lies in a beach hammock under swaying palm trees, warm synthwave sunset gradient colors. Palm fronds wave gently in the ocean breeze casting dappled moving shadows. Turquoise ocean waves roll in and recede on white sand. A phone resting on their chest shows green dashboard checkmarks. Golden sunset light bathes the entire tropical scene. Camera slowly trucks right along the beach."),
    (3, "b", 137, "t2v",
     "A massive futuristic server room with glowing API nodes connected by flowing streams of light data, concept art digital matte painting style with epic scale. Holographic screens flicker rapidly displaying AI-generated images and videos rendering frame by frame. Data particles stream between tall server racks like luminous rivers. Cool blue and purple volumetric lighting fills the cavernous space. Camera pushes forward slowly through the server corridor."),
    (3, "c", 137, "t2v",
     "Camera pulls back slowly revealing a dramatic split scene composition. Left side shows a tropical beach with warm golden sunset light and a person relaxing in a hammock under palm trees. Right side shows a busy server room with cool blue glow and actively processing screens showing green checkmarks. Particles of golden light drift from the beach side across into the server room side. All server screens simultaneously flash green with completed task indicators."),

    # Scene 4: Mic Drop (4.96s audio → 2 clips at 97 frames)
    (4, "a", 97, "t2v",
     "A confident cartoon character on a spotlight comedy stage drops a microphone dramatically downward, comic book art style with bold outlines and halftone dots. Confetti explodes from both sides of the frame showering down in slow motion. A golden Employee of the Month frame glows brighter behind them showing clean API code text inside. Dramatic overhead spotlight creates lens flares. Camera at dramatic low angle looking up at the performer."),
    (4, "b", 97, "t2v",
     "Camera slowly orbits a polished desk with a golden trophy gleaming with starburst light effects, Art Deco style with gold and black geometric patterns. Floating holographic screens display glowing API endpoint code that pulsates rhythmically with a warm glow. Confetti particles drift slowly downward catching colorful neon light. A synthwave sunset gradient shifts from deep purple to warm orange across the background grid behind the desk. Camera rises slightly."),
]


def build_i2v_workflow(image_name, motion_prompt, num_frames, seed, prefix):
    """Image-to-video workflow with distilled LoRA."""
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}},
        "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "gemma_3_12B_it.safetensors", "clip_name2": "ltx-2.3_text_projection_bf16.safetensors", "type": "ltx"}},
        "3": {"class_type": "LoraLoader", "inputs": {"model": ["1", 0], "clip": ["2", 0], "lora_name": "ltx-2.3-distilled-lora-384.safetensors", "strength_model": 1.0, "strength_clip": 1.0}},
        "4": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "5": {"class_type": "LTXVPreprocess", "inputs": {"image": ["4", 0], "img_compression": 35}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": motion_prompt, "clip": ["3", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, extra limbs, bad anatomy", "clip": ["3", 1]}},
        "8": {"class_type": "LTXVConditioning", "inputs": {"positive": ["6", 0], "negative": ["7", 0], "frame_rate": 25}},
        "9": {"class_type": "LTXVImgToVideo", "inputs": {"positive": ["8", 0], "negative": ["8", 1], "vae": ["1", 2], "image": ["5", 0], "width": 768, "height": 512, "length": num_frames, "batch_size": 1, "strength": 1.0}},
        "10": {"class_type": "LTXVScheduler", "inputs": {"steps": 8, "max_shift": 2.05, "base_shift": 0.95, "stretch": True, "terminal": 0.1, "latent": ["9", 2]}},
        "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "12": {"class_type": "CFGGuider", "inputs": {"model": ["3", 0], "positive": ["9", 0], "negative": ["9", 1], "cfg": 1.0}},
        "13": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["11", 0], "guider": ["12", 0], "sampler": ["13", 0], "sigmas": ["10", 0], "latent_image": ["9", 2]}},
        "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}},
        "16": {"class_type": "CreateVideo", "inputs": {"images": ["15", 0], "fps": 25.0}},
        "17": {"class_type": "SaveVideo", "inputs": {"video": ["16", 0], "filename_prefix": prefix, "format": "mp4", "codec": "h264"}}
    }


def build_t2v_workflow(prompt, num_frames, seed, prefix):
    """Text-to-video workflow with distilled LoRA (no reference image)."""
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}},
        "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "gemma_3_12B_it.safetensors", "clip_name2": "ltx-2.3_text_projection_bf16.safetensors", "type": "ltx"}},
        "3": {"class_type": "LoraLoader", "inputs": {"model": ["1", 0], "clip": ["2", 0], "lora_name": "ltx-2.3-distilled-lora-384.safetensors", "strength_model": 1.0, "strength_clip": 1.0}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["3", 1]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, extra limbs, bad anatomy", "clip": ["3", 1]}},
        "6": {"class_type": "LTXVConditioning", "inputs": {"positive": ["4", 0], "negative": ["5", 0], "frame_rate": 25}},
        "7": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": 768, "height": 512, "length": num_frames, "batch_size": 1}},
        "8": {"class_type": "LTXVScheduler", "inputs": {"steps": 8, "max_shift": 2.05, "base_shift": 0.95, "stretch": True, "terminal": 0.1, "latent": ["7", 0]}},
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "10": {"class_type": "CFGGuider", "inputs": {"model": ["3", 0], "positive": ["6", 0], "negative": ["6", 1], "cfg": 1.0}},
        "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "12": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["9", 0], "guider": ["10", 0], "sampler": ["11", 0], "sigmas": ["8", 0], "latent_image": ["7", 0]}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["1", 2]}},
        "14": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "fps": 25.0}},
        "15": {"class_type": "SaveVideo", "inputs": {"video": ["14", 0], "filename_prefix": prefix, "format": "mp4", "codec": "h264"}}
    }


def upload_image(filepath):
    """Upload an image to ComfyUI and return its name."""
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        resp = requests.post(f"{COMFY_URL}/upload/image",
            files={"image": (filename, f, "image/png")},
            data={"overwrite": "true"})
    result = resp.json()
    print(f"  Uploaded {filename}: {result}", flush=True)
    return result.get("name", filename)


def submit_workflow(workflow):
    """Submit a workflow to ComfyUI and return prompt_id."""
    resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    result = resp.json()
    if "error" in result:
        print(f"  ERROR: {result['error']}", flush=True)
        if "node_errors" in result:
            for nid, err in result["node_errors"].items():
                print(f"    Node {nid}: {err}", flush=True)
        return None
    prompt_id = result["prompt_id"]
    print(f"  Submitted: {prompt_id}", flush=True)
    return prompt_id


def poll_completion(prompt_id, timeout=600):
    """Poll until workflow completes."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            data = resp.json()
            if prompt_id in data:
                status = data[prompt_id].get("status", {}).get("status_str", "")
                outputs = data[prompt_id].get("outputs", {})
                if status == "error":
                    print(f"  ERROR in workflow", flush=True)
                    msgs = data[prompt_id].get("status", {}).get("messages", [])
                    for msg in msgs:
                        print(f"    {msg}", flush=True)
                    return None
                if outputs:
                    return outputs
        except Exception as e:
            print(f"  Poll error: {e}", flush=True)
        time.sleep(5)
    print(f"  TIMEOUT", flush=True)
    return None


def download_video(outputs, dest_path):
    """Download the output video."""
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    subfolder = item.get("subfolder", "")
                    if fn.endswith(".mp4"):
                        url = f"{COMFY_URL}/view?filename={fn}&type=output"
                        if subfolder:
                            url += f"&subfolder={subfolder}"
                        resp = requests.get(url)
                        with open(dest_path, "wb") as f:
                            f.write(resp.content)
                        result = subprocess.run(
                            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "csv=p=0", dest_path],
                            capture_output=True, text=True)
                        duration = result.stdout.strip()
                        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
                        print(f"  Downloaded: {os.path.basename(dest_path)} ({duration}s, {size_mb:.1f}MB)", flush=True)
                        return True
    print(f"  No video found in outputs", flush=True)
    return False


def extract_first_frame(video_path, image_path):
    """Extract the first frame from a video as PNG."""
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-vframes", "1",
        "-q:v", "2", image_path
    ], capture_output=True)


def main():
    print("=" * 60, flush=True)
    print("LTX-2 Video Generation: Zero-Employee Enterprise", flush=True)
    print(f"Generating {len(CLIPS)} clips...", flush=True)
    print("=" * 60, flush=True)

    # Upload scene-0-a.png for i2v clips
    image_names = {}
    img_path = f"{PROJECT_DIR}/public/scenes/scene-0-a.png"
    if os.path.exists(img_path):
        print("\n[1] Uploading reference image for scene 0...", flush=True)
        image_names[0] = upload_image(img_path)
    else:
        print("\n[1] No reference image for scene 0, will use t2v", flush=True)

    # Generate all clips
    print(f"\n[2] Generating {len(CLIPS)} video clips...", flush=True)
    completed = 0

    for i, (scene_idx, sub, frames, mode, prompt) in enumerate(CLIPS):
        label = f"scene-{scene_idx}-{sub}"
        prefix = f"scene_{scene_idx}_{sub}"
        dest = f"{PROJECT_DIR}/public/scenes/{label}.mp4"

        print(f"\n--- Clip {i+1}/{len(CLIPS)}: {label} ({mode}, {frames}f) ---", flush=True)

        seed = random.randint(1, 2**31)

        if mode == "i2v" and scene_idx in image_names:
            workflow = build_i2v_workflow(image_names[scene_idx], prompt, frames, seed, prefix)
        else:
            if mode == "i2v":
                print(f"  No image available, falling back to t2v", flush=True)
            workflow = build_t2v_workflow(prompt, frames, seed, prefix)

        prompt_id = submit_workflow(workflow)
        if not prompt_id:
            print(f"  FAILED to submit {label}", flush=True)
            continue

        outputs = poll_completion(prompt_id, timeout=600)
        if outputs:
            if download_video(outputs, dest):
                completed += 1
                # Extract first frame as PNG for KenBurns fallback
                png_path = f"{PROJECT_DIR}/public/scenes/{label}.png"
                extract_first_frame(dest, png_path)
                if os.path.exists(png_path):
                    print(f"  Extracted first frame: {label}.png", flush=True)
        else:
            print(f"  FAILED to generate {label}", flush=True)

    print(f"\n{'=' * 60}", flush=True)
    print(f"Complete: {completed}/{len(CLIPS)} clips generated", flush=True)
    print(f"{'=' * 60}", flush=True)

    # List all generated files
    print("\nGenerated files:", flush=True)
    for scene_idx, sub, frames, mode, _ in CLIPS:
        mp4 = f"{PROJECT_DIR}/public/scenes/scene-{scene_idx}-{sub}.mp4"
        png = f"{PROJECT_DIR}/public/scenes/scene-{scene_idx}-{sub}.png"
        if os.path.exists(mp4):
            size = os.path.getsize(mp4) / (1024 * 1024)
            print(f"  {os.path.basename(mp4)} ({size:.1f}MB)", flush=True)
        else:
            print(f"  {os.path.basename(mp4)} MISSING", flush=True)


if __name__ == "__main__":
    main()
