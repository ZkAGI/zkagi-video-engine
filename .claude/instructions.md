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

#### AI Video Clips (Optional — fal.ai + Kling, if FAL_KEY is set)
```bash
curl -X POST "https://fal.run/fal-ai/kling-video/v1.5/pro/image-to-video" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "SCENE MOTION DESCRIPTION, smooth camera movement",
    "image_url": "URL_OF_GENERATED_IMAGE",
    "duration": "5",
    "aspect_ratio": "16:9"
  }'
# Download video → public/scenes/scene-{i}.mp4
```

**Default behavior:** Always generate images via the self-hosted GPU API (free, fast). Only use fal.ai video gen if user explicitly requests video clips AND FAL_KEY is set.

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
export FAL_KEY=your-fal-ai-key                    # Optional: for AI video clip generation
```

No API keys needed for image gen or TTS — both are self-hosted!

---

## EXAMPLE BRIEFS

**Simple:**
> "Make a 60s video about PawPad wallet. Use paw for intro/outro and pad for technical parts."

**With voice selection:**
> "Make a video about ZkAGI token launch. Use paw (energetic host) for the announcement scenes and pad (calm explainer) for the tokenomics breakdown."

**With format:**
> "Make a 30s TikTok (9:16) about why privacy matters in crypto. Fast-paced, use paw only."
