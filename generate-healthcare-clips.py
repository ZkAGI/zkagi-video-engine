#!/usr/bin/env python3
"""Generate all LTX-2 text-to-video clips for Healthcare Privacy ZK Proofs video."""
import json, time, random, sys, os, subprocess

COMFY_URL = "http://172.18.64.1:8001"
OUTPUT_DIR = "/home/aten/zkagi-video-engine/public/scenes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All clips: (filename, prompt)
CLIPS = [
    # ═══ SCENE 0: HOOK — Meet Sarah (29.12s → 3 clips, cycled) ═══
    ("scene-0-a.mp4",
     "Camera slowly pushes into a dim hospital office where a stressed woman in a white coat sits behind mountains of compliance paperwork. Overhead fluorescent lights flicker casting sharp shadows across her face. She grabs a medical folder marked confidential and clutches it protectively. Venetian blind shadows stripe across the walls shifting slowly. Film noir atmosphere, high contrast, dramatic chiaroscuro lighting. Audio: fluorescent lights buzzing, papers rustling, a low anxious drone building in intensity."),

    ("scene-0-b.mp4",
     "Camera handheld with slight tension wobble. An auditor's hand reaches across a hospital conference table toward a blood test document. Another hand pulls the document back protectively. The fluorescent lights above flicker and cast shifting shadows on the polished table surface. Papers on the desk flutter from an unseen draft. The tension builds as both hands hover. Comic book style bold outlines halftone dots dynamic angles. Audio: tense silence punctuated by clock ticking and paper sliding across desk surface."),

    ("scene-0-c.mp4",
     "Camera slowly dollies backward from a woman standing at a crossroads in a dark hospital corridor. One path glows ominous red with filing cabinets bursting open spilling papers and data streams. The other path shows a locked vault surrounded by penalty warning signs in yellow. Dust particles float in crossing beams of colored light from both directions. Concept art style atmospheric perspective cinematic scope. Audio: echoing footsteps in empty corridor, a distant alarm wailing, wind gusting through the hallway."),

    # ═══ SCENE 1: AGITATE — Data Dilemma (29.44s → 3 clips, cycled) ═══
    ("scene-1-a.mp4",
     "Camera slowly tilts down to reveal a massive golden scale of justice in a dark courtroom setting with dramatic spotlight from above. One side overflows with glowing patient files that cascade down like a waterfall of paper. The other side is weighed down by stacks of red fine notices stamped with dollar signs. The scale tips dangerously, chains creaking and swaying. Art Deco style gold and black geometric patterns ornate frames. Audio: heavy chains creaking, metal groaning under weight, papers fluttering down."),

    ("scene-1-b.mp4",
     "Camera slowly pushes in on a split scene divided by a cracking glass wall. Left side hospital records pass through the fractures with data leaking out as red glowing streams dripping downward like liquid fire. Right side a document so heavily redacted with thick black bars it is completely unreadable and useless. The glass cracks widen spreading like a spiderweb. Glitch art style RGB channel splitting chromatic aberration scan line artifacts. Audio: glass cracking sharply, digital distortion warping, a warning klaxon fading away."),

    ("scene-1-c.mp4",
     "Camera pans left to right across generic AI company headquarters behind frosted glass walls with glowing red holographic signs reading CANNOT HELP in bold letters. A desperate hospital administrator in blue scrubs reaches toward them in a rain-slicked corridor. Neon reflections shimmer on the wet floor. Volumetric fog drifts through the scene from overhead vents. Cyberpunk atmosphere dense urban layers Blade Runner mood. Audio: rain pattering steadily, distant thunder rumbling, electronic interference buzzing and crackling."),

    # ═══ SCENE 2: ZK PROOF REVEAL (21.44s → 3 clips, cycled) ═══
    ("scene-2-a.mp4",
     "Camera smoothly dollies forward toward a massive crystalline chamber glowing with warm teal light in a dark void. A medical document enters from the left dissolving into streams of glowing mathematical symbols as it passes through the crystal wall. On the far side a single clean verified answer emerges floating gently outward surrounded by soft light. The chamber pulses rhythmically like breathing. Pixar 3D render style warm lighting subsurface scattering soft ambient occlusion. Audio: soft crystalline humming building, a gentle chime as the answer materializes."),

    ("scene-2-b.mp4",
     "Camera slowly orbits around a blood test document suspended in mid-air that transforms into abstract geometric proof shapes. The paper dissolves into streams of glowing teal particles that spiral and reassemble into a shimmering diamond-like crystalline structure. Patient names and personal data vanish into dark wisps while only medical numbers remain visible and bright. Watercolor painting style flowing color bleeds ink outline details paper texture. Audio: paper dissolving softly, crystalline formation tinkling, a warm harmonic chord resolving."),

    ("scene-2-c.mp4",
     "Camera pulls back to reveal a transparent vault containing a medical record surrounded by orbiting rings of mathematical equations glowing in teal. Outside the protective barrier a clean holographic display shows VERIFIED with a pulsing green checkmark. No patient names or personal information visible anywhere. The vault rotates slowly catching light. Warm teal accent lighting throughout. Isometric 3D perspective clean geometric shapes soft shadows pastel accents. Audio: a gentle protective hum, a satisfying verification chime ringing out, ambient electronic warmth."),

    # ═══ SCENE 3: TWO API CALLS (18.24s → 3 clips, cycled) ═══
    ("scene-3-a.mp4",
     "Camera steadily pushes in on a sleek dark terminal screen in a modern server room. The text POST generate_proof types itself across the screen in glowing green monospace characters. A medical document icon feeds into an animated pipeline visualization on screen from the left side. Glowing particles flow through the pipeline processing stages. A shimmering proof artifact emerges from the right end. Flat vector illustration style dark background teal and green accents clean lines. Audio: rapid keyboard typing clicking, a processing hum rising, a satisfying completion ping."),

    ("scene-3-b.mp4",
     "Camera smoothly trucks right to reveal a second terminal screen showing POST ask in glowing teal characters. A question mark icon and the proof artifact from before plug into input slots on screen. The system processes with flowing particle animations between stages. A verified answer materializes with a bright green checkmark expanding outward in a pulse of light. Clean flat vector style dark background green and white accents modern graphic design. Audio: data processing whooshing sounds, a scanning beam hum, a bright verification chime ringing."),

    ("scene-3-c.mp4",
     "Camera pulls back dramatically revealing a before and after split composition. Left side shows a tangled nightmare of medical records red tape compliance forms and flashing warning signs piled in chaotic darkness. Right side shows a clean organized dashboard with rows of verified green checkmarks neat answer cards and a calm teal glow radiating order. The contrast between chaos and clarity is stark and immediate. Comic book art style bold outlines high energy dynamic composition vibrant colors. Audio: chaotic noise rapidly fading to clean silence then a satisfying click of everything falling into place."),

    # ═══ SCENE 4: PAYOFF — Sarah Wins (11.52s → 3 clips) ═══
    ("scene-4-a.mp4",
     "Camera smoothly pushes in on a woman at her desk now smiling confidently in a bright office. A holographic dashboard floating in front of her glows green showing AUDIT PASSED in large triumphant letters. Her office is bright warm and organized with sunlight streaming through windows compared to the earlier dark chaos. Plants and clean surfaces reflect the warm light. Studio Ghibli inspired style hand-painted backgrounds soft warm lighting whimsical atmosphere. Audio: a triumphant warm chord swelling, birds singing outside the window, a gentle completion chime."),

    ("scene-4-b.mp4",
     "Camera slowly pulls back as two people in a modern hospital conference room exchange a relieved handshake. A tablet on the table shows verified medical answers with green checkmarks lined up neatly. Both figures have relaxed shoulders and warm expressions. Warm golden light fills the room through large windows. Papers are neatly stacked. Storybook children's illustration style gentle rounded shapes warm cozy lighting textured paper background. Audio: a relieved exhale, papers settling quietly, a warm harmonic tone resolving gently."),

    ("scene-4-c.mp4",
     "Camera cranes upward revealing a hospital building from outside bathed in a protective dome of golden shimmering light. The building glows warmly from within through every window. Above the sky transitions from stormy dark clouds to clear blue with golden sunlight breaking through. Tiny particles of light rise from the building upward like fireflies ascending. Concept art style digital matte painting epic scale dramatic sky atmospheric perspective cinematic scope. Audio: a rising orchestral swell building, wind calming to stillness, a final triumphant sustained note."),

    # ═══ SCENE 5: CTA — Zynapse API (8.32s → 3 clips) ═══
    ("scene-5-a.mp4",
     "Camera holds wide as glowing text materializes letter by letter in bright teal and purple neon colors floating in a vast dark digital space. Proof artifacts shaped like glowing diamonds and green checkmarks orbit the text like satellites in smooth elliptical paths. Energy ripples pulse outward from the center in concentric waves. A neon grid extends to infinity below reflecting the glow. Synthwave aesthetic neon grid landscape purple and teal gradient sky VHS scan lines subtle chrome reflections. Audio: each letter chiming digitally on appearance, energy building steadily, a deep bass pulse on completion."),

    ("scene-5-b.mp4",
     "Camera pushes forward dynamically as a confident hand reaches toward a glowing button floating in dark space. The hand presses the button and a massive shockwave of golden light erupts outward in all directions rushing past camera. The wave creates a brilliant lens flare as it passes through. Everything behind the wave bathes in warm triumphant golden light. Particles scatter outward in the wake. Dramatic bold composition synthwave with clean modern accents. Audio: building electrical charge crackling, a deeply satisfying button click, a massive bass impact with rushing shockwave whoosh."),

    ("scene-5-c.mp4",
     "Camera slowly pulls back revealing a central glowing emblem surrounded by the text TWO ENDPOINTS ZERO DATA EXPOSED in clean white letters. Concentric circles of teal and gold energy radiate outward from the emblem in gentle pulses. Glowing proof artifacts orbit gracefully at different distances and speeds. The entire scene pulses with confident warm energy and feels triumphant and final. Synthwave aesthetic with clean modern design vibrant saturated colors chrome reflections. Audio: a final triumphant chord swelling, energy humming softly, a warm harmonic tone resolving to completion."),
]

NEG_PROMPT = "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed, extra limbs, bad anatomy, words, letters, numbers"

def build_workflow(prompt, seed, length=97):
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "ltx-2-19b-dev-fp8.safetensors"}
        },
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it.safetensors",
                "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
                "device": "cpu"
            }
        },
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
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
                "filename_prefix": "healthcare_clip",
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
                dur = "?"
                try:
                    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", output_path], capture_output=True, text=True)
                    dur = r.stdout.strip()
                except:
                    pass
                print(f"  DONE: {filename} ({size} bytes, {dur}s)")
            else:
                print(f"  ERROR: Could not find video in outputs")
        elif status == "ERROR":
            print(f"  ERROR: {err}")
        else:
            print(f"  TIMEOUT after 300s")

    print("\nAll done!")


if __name__ == "__main__":
    main()
