# ZkAGI Video Engine — Claude Code Instructions

## Overview
Full AI video production pipeline. Claude Code handles everything:
**Brief → Script → Visuals (image/video) → TTS audio → Remotion compositing → MP4**

---

## PIPELINE

### Step 1: Write Script
Based on user's brief, write 3-7 scenes. For each scene define:
- `characterId` — which voice/character to use
- `dialogue` — what they say (15-30 words per scene)
- `visualPrompt` — description of what the background should show
- `sceneType` — "image" (AI image + Remotion animation) or "video" (AI video clip)
- `highlightText` — key phrase to display big on screen

### Step 2: Discover Available Voices
Check `voices/` folder for available characters:
```bash
ls voices/*.wav
# Each character has:
#   voices/{name}.wav  — reference audio (3-10s)
#   voices/{name}.txt  — transcript of the reference audio
```
Check `public/characters/` for available character images:
```bash
ls public/characters/
# Each character has:
#   public/characters/{name}/neutral.png  — default pose
#   public/characters/{name}/excited.png  — optional emotion poses
```

**Currently available:**
- `paw` — Host tiger. Energetic, friendly. Purple theme (#7C3AED)
- `pad` — Explainer tiger. Thoughtful, technical. Teal theme (#06B6D4)

**Users can add more voices anytime** by dropping wav+txt files in `voices/` and images in `public/characters/{name}/`.

### Step 3: Generate Scene Visuals

**For each scene, decide: image or video clip?**
- Use **video clips** for: intros, dramatic moments, abstract concepts, outros
- Use **images** for: technical explanations, data points, anything with text overlay

#### AI Image Generation (Self-Hosted GPU — SDXL/Diffusers)
**Endpoint:** `POST http://45.251.34.28:8010/generate`
**Content-Type:** `application/json`
**Returns:** Raw PNG bytes (save directly to file)
**Cost:** FREE (self-hosted)

```bash
curl -X POST "http://45.251.34.28:8010/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "SCENE VISUAL DESCRIPTION, no text, cinematic lighting, vibrant colors",
    "negative_prompt": "text, words, letters, watermark, blurry, low quality, deformed",
    "width": 1920,
    "height": 1080,
    "steps": 30,
    "cfg_scale": 6,
    "num_images": 1,
    "backend": "diffusers"
  }' \
  --output public/scenes/scene-{i}.png
```

**For 9:16 vertical videos**, use `"width": 1080, "height": 1920`
**For 1:1 square videos**, use `"width": 1080, "height": 1080`

**Health check:** `curl http://45.251.34.28:8010/health`

#### AI Video Clips (Self-Hosted LTX-2 via ComfyUI — FREE)
**ComfyUI URL:** Determined at runtime. Always discover it with:
```bash
COMFY_URL="http://$(ip route show default | awk '{print $3}'):8001"
# Verify: curl -s "$COMFY_URL/system_stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['system']['comfyui_version'])"
```

**How it works:** Send a workflow JSON to ComfyUI's `/prompt` endpoint. ComfyUI runs LTX-2 on the RTX 5090 and outputs a video file.

**Step-by-step for each scene video clip:**

**1. Submit the workflow:**
```bash
COMFY_URL="http://$(ip route show default | awk '{print $3}'):8001"

curl -s -X POST "$COMFY_URL/prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "1": {
        "class_type": "EmptyLTXVLatentVideo",
        "inputs": {
          "width": 768,
          "height": 512,
          "length": 97,
          "batch_size": 1
        }
      },
      "2": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
          "ckpt_name": "ltx-video-2b-v0.9.5.safetensors"
        }
      },
      "3": {
        "class_type": "CLIPTextEncode",
        "inputs": {
          "text": "SCENE_PROMPT_HERE, cinematic, smooth motion, vibrant colors, no text",
          "clip": ["2", 1]
        }
      },
      "4": {
        "class_type": "CLIPTextEncode",
        "inputs": {
          "text": "blurry, low quality, distorted, text, watermark, static, ugly",
          "clip": ["2", 1]
        }
      },
      "5": {
        "class_type": "KSampler",
        "inputs": {
          "seed": RANDOM_SEED,
          "steps": 30,
          "cfg": 3.5,
          "sampler_name": "euler_ancestral",
          "scheduler": "normal",
          "denoise": 1.0,
          "model": ["2", 0],
          "positive": ["3", 0],
          "negative": ["4", 0],
          "latent_image": ["1", 0]
        }
      },
      "6": {
        "class_type": "VAEDecode",
        "inputs": {
          "samples": ["5", 0],
          "vae": ["2", 2]
        }
      },
      "7": {
        "class_type": "SaveVideo",
        "inputs": {
          "filename_prefix": "scene_VIDEO_INDEX",
          "images": ["6", 0]
        }
      }
    }
  }'
```

**IMPORTANT:** The workflow above is a starting template. Claude Code MUST first check what LTX-2 model files are available:
```bash
curl -s "$COMFY_URL/object_info/CheckpointLoaderSimple" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0])"
```
Use whichever LTX model checkpoint is listed (e.g., `ltx-video-2b-v0.9.5.safetensors` or similar).

If the basic workflow above fails, Claude Code should inspect available nodes and build a working workflow:
```bash
# List all LTX-related nodes
curl -s "$COMFY_URL/object_info" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(k) for k in sorted(d.keys()) if 'ltx' in k.lower()]"

# Get node details (inputs/outputs)
curl -s "$COMFY_URL/object_info/LTXVConditioning" | python3 -m json.tool
curl -s "$COMFY_URL/object_info/LTXVImgToVideo" | python3 -m json.tool
curl -s "$COMFY_URL/object_info/LTXVScheduler" | python3 -m json.tool
```

Available LTX-2 nodes on this system:
- `EmptyLTXVLatentVideo` — create empty latent for text-to-video
- `LTXVConditioning` — LTX-specific conditioning
- `LTXVImgToVideo` — image-to-video (use a generated scene image as first frame)
- `LTXVImgToVideoInplace` — in-place image-to-video
- `LTXVScheduler` — LTX-specific scheduler
- `LTXVLoRALoader` / `LTXVLoRASelector` — for LoRA support
- `LTXVPreprocess` — preprocessing
- `LTXVAddGuide` — add guide frames
- `LTXVLatentUpsampler` — upscale latent
- `ModelSamplingLTXV` — model sampling config

**2. Poll for completion:**
```bash
# The /prompt response returns a prompt_id
PROMPT_ID=$(curl -s -X POST "$COMFY_URL/prompt" -H "Content-Type: application/json" -d "$WORKFLOW_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['prompt_id'])")

# Poll history until complete
while true; do
  STATUS=$(curl -s "$COMFY_URL/history/$PROMPT_ID" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if '$PROMPT_ID' in d:
  outputs = d['$PROMPT_ID'].get('outputs', {})
  if outputs:
    print('DONE')
  else:
    status = d['$PROMPT_ID'].get('status', {})
    if status.get('status_str') == 'error':
      print('ERROR')
    else:
      print('RUNNING')
else:
  print('WAITING')
")
  if [ "$STATUS" = "DONE" ]; then break; fi
  if [ "$STATUS" = "ERROR" ]; then echo "ComfyUI workflow failed"; break; fi
  sleep 2
done
```

**3. Download the output video:**
```bash
# Get the output filename from history
FILENAME=$(curl -s "$COMFY_URL/history/$PROMPT_ID" | python3 -c "
import sys,json
d=json.load(sys.stdin)['$PROMPT_ID']['outputs']
for node_id, output in d.items():
  if 'gifs' in output:
    print(output['gifs'][0]['filename'])
    break
  elif 'videos' in output:
    print(output['videos'][0]['filename'])
    break
")

# Download the video
curl -s "$COMFY_URL/view?filename=$FILENAME&type=output" --output public/scenes/scene-{i}.mp4
```

**Fallback:** If ComfyUI is not running or LTX-2 fails, fall back to static images from the image gen API at http://45.251.34.28:8010/generate with Ken Burns zoom in Remotion.

**Default behavior:** PREFER video clips via LTX-2 for ALL scenes (free, local, high quality). Fall back to static images only if ComfyUI is unavailable.

**Style guide for ALL visual prompts:**
- Include: "cute cartoon tiger mascot, tech/crypto theme, modern, vibrant gradient"
- Match scene mood: "glowing neon circuits" for tech, "warm sunrise" for intro, "confetti celebration" for outro
- NEVER include text in AI images (Remotion adds all text)
- Keep consistent style by reusing style keywords across all scenes

Save all generated visuals to:
```
public/scenes/
├── scene-0.png (or .mp4)
├── scene-1.png (or .mp4)
└── ...
```

### Step 4: Generate TTS Audio
For each scene, call VoxCPM with the character's voice:

```bash
# Read the character's reference text
REF_TEXT=$(cat voices/{characterId}.txt)

curl -X POST "https://avatar.zkagi.ai/v1/clone-tts" \
  -F "ref_audio=@voices/{characterId}.wav" \
  -F "ref_text=$REF_TEXT" \
  -F "text=SCENE DIALOGUE HERE" \
  -F "cfg_value=2.0" \
  -F "steps=15" \
  --output public/audio/scene-{i}.wav
```

After generating all audio, get durations:
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 public/audio/scene-{i}.wav
```

### Step 5: Write Remotion Composition
Write/update `src/compositions/ZkAGIVideo.tsx` to composite everything.

**CRITICAL REMOTION RULES:**
- Use `staticFile()` for ALL asset paths (images, video, audio)
- Use `<Img>` from remotion (not `<img>`) for images
- Use `<Video>` from remotion for video clips, with `startFrom={0}`
- Use `<Audio>` from remotion for TTS audio
- Use `<Sequence>` for each scene with correct `from` and `durationInFrames`
- Calculate durationInFrames = Math.ceil(audioDurationSeconds * 30) for 30fps
- Use `spring()` and `interpolate()` for all animations
- Register composition with total frames = sum of all scene frames

**Layer order per scene (bottom to top):**
1. **Background** — AI-generated image (with slow Ken Burns zoom via `interpolate`) OR video clip (via `<Video>`)
2. **Overlay gradient** — semi-transparent gradient for text readability
3. **Tiger character** — from `public/characters/{id}/neutral.png`, with:
   - Spring bounce entrance from below
   - Gentle idle floating (sin wave on Y)
   - Subtle scale pulse (simulates speaking energy)
   - Exit: fade out in last 15 frames
4. **Highlight text** — key phrase with spring scale-pop animation
5. **Subtitles** — word-by-word reveal synced to scene duration
6. **TTS Audio** — `<Audio src={staticFile('audio/scene-{i}.wav')}>`

**Scene transitions:** 10-15 frame crossfade overlap between scenes

**Global layers:**
- Animated background particles (subtle, matches theme)
- Watermark (top right)
- Background music if provided (public/music/, low volume)

### Step 6: Render
```bash
# 16:9 landscape (YouTube, Twitter)
npx remotion render ZkAGIVideo output/video-landscape.mp4 --bundle-cache=false --timeout=300000

# 9:16 vertical (TikTok, Reels) — if requested
npx remotion render ZkAGIVideoVertical output/video-vertical.mp4 --bundle-cache=false --timeout=300000
```

---

## FILE STRUCTURE
```
public/
├── characters/           ← Tiger character overlays (PNG, transparent bg)
│   ├── paw/neutral.png, excited.png
│   └── pad/neutral.png, thinking.png
├── scenes/               ← AI-generated backgrounds per scene (Step 3)
│   ├── scene-0.png (or .mp4)
│   └── ...
├── audio/                ← TTS audio files (Step 4)
│   ├── scene-0.wav
│   └── ...
└── music/                ← Optional background music tracks

voices/                   ← Voice reference samples
├── paw.wav + paw.txt     ← Host tiger voice
├── pad.wav + pad.txt     ← Explainer tiger voice
└── {new}.wav + {new}.txt ← Add more voices here

configs/                  ← Video config JSONs (optional, for manual mode)
src/
├── compositions/ZkAGIVideo.tsx  ← Main Remotion composition (rewritten per video)
├── components/                   ← Reusable components
└── lib/                          ← TTS client, themes

output/                   ← Rendered MP4s
```

---

## ADDING NEW VOICES
1. Record/obtain a 3-10 second clean WAV
2. Place at `voices/{name}.wav`
3. Transcribe: `whisper voices/{name}.wav --model base --output_format txt` → rename to `voices/{name}.txt`
4. Add character image: `public/characters/{name}/neutral.png`
5. Mention the character in video brief

---

## ENVIRONMENT VARIABLES
```bash
export IMAGE_GEN_URL=http://45.251.34.28:8010    # Self-hosted GPU image gen (default, free)
export TTS_URL=https://avatar.zkagi.ai            # VoxCPM TTS (default)
# ComfyUI URL is auto-discovered: http://$(ip route show default | awk '{print $3}'):8001
```

No API keys needed — image gen, video gen (LTX-2), and TTS are all self-hosted!

---

## SCRIPT WRITING RULES (CRITICAL)
Claude Code MUST follow these rules when writing video scripts:

**Tone & Style:**
- Write like a viral content creator, NOT a corporate explainer
- Short punchy sentences. No jargon. No technical babble.
- Each scene: max 15-20 words of dialogue
- Think "storytelling" not "presenting" — hook people in the first 3 seconds
- Add humor, personality, and "masala" — make people want to watch till the end
- Use analogies a 12-year-old would understand

**Structure:**
- Scene 1: HOOK — shocking stat, bold claim, or funny opener (3-5 seconds)
- Scenes 2-4: STORY — explain through examples and stories, not features (5-8 seconds each)
- Last scene: CTA — tell them what to do next (3-5 seconds)

**What NOT to do:**
- No long monologues. Ever.
- No "In this video we will explore..." — boring!
- No listing features like a product spec sheet
- No "Let me explain..." — just explain it
- No technical jargon unless absolutely needed

**Examples of GOOD vs BAD dialogue:**
- BAD: "PawPad utilizes FROST MPC threshold signature schemes for distributed key management"
- GOOD: "Your wallet key is split into pieces. No single device has the full thing. That means nobody can steal it."

- BAD: "We leverage Oasis ROFL Trusted Execution Environments for hardware-level isolation"
- GOOD: "Imagine a vault inside a vault. That is where your transactions happen. Not even we can peek inside."

---

## EXAMPLE BRIEFS

**Simple:**
> "Make a 60s video about PawPad wallet. Use paw for intro/outro and pad for technical parts."

**With voice selection:**
> "Make a video about ZkAGI token launch. Use paw (energetic host) for the announcement scenes and pad (calm explainer) for the tokenomics breakdown."

**With format:**
> "Make a 30s TikTok (9:16) about why privacy matters in crypto. Fast-paced, use paw only."
