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

### Step 3: Generate Scene Visuals (2-Step Pipeline)

**For EVERY scene, use this 2-step pipeline for best quality:**

**Step A: Generate a scene image** (gives LTX-2 a high-quality starting frame)
```bash
curl -X POST "http://45.251.34.28:8010/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "SCENE VISUAL DESCRIPTION, no text, cinematic lighting, vibrant colors",
    "negative_prompt": "text, words, letters, watermark, blurry, low quality, deformed",
    "width": 768,
    "height": 512,
    "steps": 30,
    "cfg_scale": 6,
    "num_images": 1,
    "backend": "diffusers"
  }' \
  --output public/scenes/scene-{i}.png
```

**Step B: Animate it with LTX-2 image-to-video** (turns the static image into a video clip)
Upload the generated image to ComfyUI, then use `LTXVImgToVideo` node to animate it.
```bash
# First upload the image to ComfyUI
COMFY_URL="http://$(ip route show default | awk '{print $3}'):8001"
curl -s -X POST "$COMFY_URL/upload/image" \
  -F "image=@public/scenes/scene-{i}.png" \
  -F "type=input"

# Then submit a workflow using LTXVImgToVideo
# Claude Code: check the node details first:
# curl -s "$COMFY_URL/object_info/LTXVImgToVideo" | python3 -m json.tool
# Build a workflow that loads the uploaded image → LTXVImgToVideo → SaveVideo
```

This 2-step approach gives much higher quality than text-to-video alone because LTX-2 has a reference frame to animate from.

**Health check for image gen:** `curl http://45.251.34.28:8010/health`

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
# Get ALL outputs from history - look for videos/gifs/images
OUTPUT_JSON=$(curl -s "$COMFY_URL/history/$PROMPT_ID" | python3 -c "
import sys,json
d=json.load(sys.stdin)['$PROMPT_ID']['outputs']
for node_id, output in d.items():
  for key in ['gifs', 'videos', 'images']:
    if key in output:
      for item in output[key]:
        if item.get('filename','').endswith('.mp4') or item.get('filename','').endswith('.webm'):
          print(item['filename'])
          break
")

# Download using the EXACT filename from the output
curl -s "$COMFY_URL/view?filename=$OUTPUT_JSON&type=output" --output public/scenes/scene-{i}.mp4

# Verify the file is valid
ffprobe -v error -show_entries format=duration -of csv=p=0 public/scenes/scene-{i}.mp4
ls -la public/scenes/scene-{i}.mp4
```

**IMPORTANT:** ComfyUI SaveVideo node uses the prefix you set + `_00001_`. So if prefix is `scene_0`, the filename is `scene_0_00001_.mp4`. Always check history output for the exact filename.

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

**IMPORTANT TTS RULES:**
- Each scene dialogue MUST be 15-30 words to produce 8-15 seconds of audio
- If audio comes out under 5 seconds, the dialogue is too short — rewrite it longer
- Do NOT regenerate more than once — write proper length dialogue the first time
- Test audio plays correctly before moving on: `ffplay -nodisp -autoexit public/audio/scene-{i}.wav`

After generating all audio, get durations:
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 public/audio/scene-{i}.wav
```

**CRITICAL — VIDEO vs AUDIO DURATION MISMATCH:**
LTX-2 video clips are typically 3-5 seconds. TTS audio is 8-15 seconds per scene. Claude Code MUST fill the entire scene duration intelligently:

**Strategy: Generate MULTIPLE assets per scene to fill the audio duration.**

For a scene with 12 seconds of audio, Claude Code should:
1. Generate 2-3 LTX-2 video clips (3-5s each) with slightly different prompts/angles
2. Generate 1-2 still images (from image gen API) as transition frames
3. Remotion stitches them together: clip1 → image (with Ken Burns) → clip2 → clip3

**Example for a 12-second scene about "wallet security":**
```
Sub-clip A (0-4s):    LTX-2 video - "glowing digital vault opening, neon blue"
Sub-clip B (4-7s):    Still image with zoom - "shield protecting crypto keys, vibrant"  
Sub-clip C (7-12s):   LTX-2 video - "keys splitting into fragments, secure encryption visual"
```

**Rules:**
- NEVER loop a single clip — it looks cheap and repetitive
- NEVER leave black gaps — every frame must have a visual
- Each sub-clip should show a different angle/moment of the scene topic
- Use crossfade transitions (10-15 frames) between sub-clips
- Still images get Ken Burns zoom effect (slow zoom in or pan) to feel alive
- Total sub-clip durations must add up to >= audio duration

**In Remotion, use nested Sequences within each scene:**
```jsx
<Sequence from={sceneStart} durationInFrames={totalSceneFrames}>
  <Audio src={staticFile('audio/scene-0.wav')} />
  
  {/* Sub-clip A: video */}
  <Sequence from={0} durationInFrames={120}>
    <Video src={staticFile('scenes/scene-0-a.mp4')} volume={0} />
  </Sequence>
  
  {/* Sub-clip B: image with zoom */}
  <Sequence from={105} durationInFrames={100}>
    <Img src={staticFile('scenes/scene-0-b.png')} style={{transform: `scale(${zoom})`}} />
  </Sequence>
  
  {/* Sub-clip C: video */}
  <Sequence from={195} durationInFrames={165}>
    <Video src={staticFile('scenes/scene-0-c.mp4')} volume={0} />
  </Sequence>
  
  {/* Subtitles and highlight text on top */}
</Sequence>
```

**File naming for sub-clips:**
```
public/scenes/
├── scene-0-a.mp4     ← first video clip
├── scene-0-b.png     ← transition image  
├── scene-0-c.mp4     ← second video clip
├── scene-1-a.mp4
├── scene-1-b.mp4
└── ...
```

### Step 5: Write Remotion Composition (CREATIVE — VIBE-BASED)
Write/update `src/compositions/ZkAGIVideo.tsx` to composite everything.

**CRITICAL: Every video should look DIFFERENT. Do NOT copy-paste the same template every time.**
Claude Code must make creative decisions based on the video's vibe, topic, and tone.

**Technical rules (always follow):**
- Use `staticFile()` for ALL asset paths (images, video, audio)
- Use `<Img>` from remotion (not `<img>`) for images
- Use `<Video>` from remotion for video clips, with `startFrom={0}`
- Use `<Audio>` from remotion for TTS audio
- Use `<Sequence>` for each scene with correct `from` and `durationInFrames`
- Calculate durationInFrames = Math.ceil(audioDurationSeconds * 30) for 30fps
- Use `spring()` and `interpolate()` for all animations
- Register composition with total frames = sum of all scene frames

**Creative rules (Claude Code DECIDES per video):**

Claude Code must pick the visual style based on the vibe. DO NOT use the same look every time. Options include:

**Caption/Subtitle Style — pick one per video:**
- Big bold center text (hype/announcement videos)
- Small lower-third subtitle bar (news/update style)
- Word-by-word pop-in with spring physics (educational)
- Karaoke-style highlight (fun/casual)
- Minimal — no captions, just key phrases (cinematic)
- Caption size, font weight, color, position should ALL vary per video vibe

**Scene Transition Style — pick one per video:**
- Hard cut (fast-paced, TikTok style)
- Crossfade (smooth, educational)
- Zoom-through (dramatic, announcement)
- Wipe/slide (news style)
- Glitch/flash (tech/crypto vibe)
- Mix transitions within a video for variety

**Background Treatment — pick per scene:**
- Full-bleed video clip from LTX-2 (default for most scenes)
- Video clip with color overlay tint (for text-heavy scenes)
- Split screen — video on one side, key stats on other
- Blurred/dimmed video background with sharp text foreground
- NO background character overlay if the AI video already shows a character — avoid redundant layering

**Motion & Animation — vary per scene:**
- Character overlay: sometimes show it, sometimes don't (if AI background already has a character)
- Text entrance: spring, typewriter, fade, slide, bounce — pick what fits
- Pacing: vary speed per scene (fast cuts for hype, slow for emotional)
- Scale effects: zoom in on important moments, zoom out for establishing shots
- Shake/vibrate for impact moments

**Color & Mood — match the topic:**
- Crypto/tech: dark backgrounds, neon accents, purple/blue/green
- Product launch: bright, celebratory, golden highlights
- Educational: clean, light backgrounds, clear contrast
- News update: professional, muted with accent colors
- Fun/casual: saturated colors, playful animations

**What NOT to do:**
- Do NOT use the exact same layout for every scene
- Do NOT always put character in bottom-left with subtitle in bottom-right
- Do NOT use the same font size for every caption
- Do NOT force character overlay when the AI background already tells the story
- Do NOT make every transition a crossfade
- Do NOT make it look like a PowerPoint slideshow

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
