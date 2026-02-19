# 🎬 ZkAGI Video Engine

**One template → infinite videos.** Parametrized video generation with consistent tiger characters and VoxCPM voice cloning, built entirely on [Remotion](https://github.com/remotion-dev/remotion).

---

## How Remotion is Used

Remotion turns React components into real MP4 videos. Here's how every piece fits:

| Remotion Feature | Where We Use It |
|---|---|
| **Compositions** | `src/compositions/ZkAGIVideo.tsx` — 3 registered: 16:9, 9:16, 1:1 |
| **Sequences** | Each scene is a `<Sequence>` with timed audio + character animation |
| **Input Props** | Video config JSON is passed as `inputProps` — parametrizes everything |
| **`<Audio>`** | Per-scene TTS audio + optional background music via `<Audio>` |
| **`<Img>`** | Character pose PNGs rendered with `<Img>` (transparent bg) |
| **`spring()` / `interpolate()`** | Character entrance bounce, idle breathing, subtitle word-reveal |
| **`staticFile()`** | All audio + character assets served from `public/` |
| **Remotion Studio** | `npm run dev` — live preview with hot reload while designing |
| **CLI Render** | `npx remotion render` — headless MP4 export |
| **Zod Schemas** | Type-safe `defaultProps` validation on compositions |

---

## Step-by-Step Setup

### Prerequisites
- Node.js ≥ 18
- ffmpeg installed (`brew install ffmpeg` / `apt install ffmpeg`)

### Step 1: Clone & Install

```bash
git clone <this-repo> zkagi-video-engine
cd zkagi-video-engine
npm install
```

### Step 2: Add Voice Samples

Record or obtain a **3-10 second clean WAV** for each character. This is what VoxCPM clones.

```bash
# Place your voice samples here:
voices/
├── paw.wav    # Voice for "Paw" (host tiger)
└── pad.wav    # Voice for "Pad" (explainer tiger)
```

**Tips:** Quiet room, natural pace, WAV format, 3-10 seconds.

### Step 3: Add Character Pose Images

Tiger PNGs are already included! To add more emotions, drop transparent PNGs into:

```bash
public/characters/
├── paw/
│   ├── neutral.png    ✅ included (tiger with headset)
│   └── excited.png    ✅ included
└── pad/
    ├── neutral.png    ✅ included (tiger with crystal ball)
    └── thinking.png   ✅ included
```

### Step 4: Test TTS Connection

```bash
npm run test-tts
```

This pings `https://avatar.zkagi.ai/v1/clone_tts` and generates a test audio file.

### Step 5: Preview in Remotion Studio

```bash
npm run dev
```

Opens the visual editor at `http://localhost:3000`. You can:
- See all 3 format compositions (16:9, 9:16, 1:1)
- Edit props live in the sidebar
- Scrub through the timeline
- Preview animations frame-by-frame

### Step 6: Create Your First Video

```bash
# Copy the template
cp configs/template.json configs/my-video.json

# Edit configs/my-video.json — change title, scenes, dialogue

# Generate everything (TTS + render)
npm run generate -- --config configs/my-video.json
```

### Step 7: Output

```bash
output/
├── my-video-landscape-2026-02-18.mp4   # 1920×1080
├── my-video-vertical-2026-02-18.mp4    # 1080×1920
└── my-video-square-2026-02-18.mp4      # 1080×1080
```

---

## Creating Videos (the workflow)

Every video is just a **JSON config**. The only thing you edit:

```json
{
  "title": "What is FROST MPC?",
  "scenes": [
    {
      "characterId": "paw",
      "dialogue": "What you want the character to say",
      "emotion": "excited",
      "visualType": "talking-head"
    }
  ]
}
```

Then run: `npm run generate -- --config configs/my-video.json`

### Emotions
`neutral` `excited` `thinking` `serious` `explaining` `celebrating` `waving`

### Visual Types
| Type | Description |
|---|---|
| `talking-head` | Character left, subtitles bottom |
| `split-screen` | Character left, highlight text right |
| `text-overlay` | Big text center, small character |
| `character-only` | Character big, centered |

### Themes
`zkagi-brand` `pawpad` `dark` `light`

---

## VoxCPM TTS API

Your endpoint at `https://avatar.zkagi.ai/v1/clone_tts`:

```
POST /v1/clone_tts  (multipart/form-data)

Required:
  ref_audio  — binary WAV (3-10s voice sample to clone)
  ref_text   — transcript of the reference audio
  text       — text to generate speech for

Optional:
  cfg_value  — CFG scale (default "2.0", lower = more relaxed)
  steps      — inference steps (default "15", higher = better quality)
  normalize  — normalize output audio
  denoise    — denoise output audio

Returns: audio/wav
```

---

## Project Structure

```
zkagi-video-engine/
├── .claude/instructions.md       ← Claude Code context file
├── configs/
│   ├── default.json              ← Full PawPad explainer (5 scenes)
│   └── template.json             ← Blank template for new videos
├── public/
│   ├── characters/paw/           ← Host tiger pose PNGs
│   ├── characters/pad/           ← Explainer tiger pose PNGs
│   ├── audio/                    ← Generated TTS (auto-created)
│   └── music/                    ← Background music tracks
├── voices/
│   ├── paw.wav                   ← Host voice sample (YOU ADD THIS)
│   └── pad.wav                   ← Explainer voice sample (YOU ADD THIS)
├── src/
│   ├── index.ts                  ← Remotion entry (registerRoot)
│   ├── Root.tsx                  ← Composition registration (3 formats)
│   ├── types.ts                  ← Zod schemas for config validation
│   ├── compositions/
│   │   └── ZkAGIVideo.tsx        ← Main Remotion composition
│   ├── components/
│   │   ├── CharacterDisplay.tsx  ← Animated character with poses
│   │   ├── Subtitle.tsx          ← Word-by-word subtitle reveal
│   │   └── Watermark.tsx         ← Brand watermark overlay
│   ├── lib/
│   │   ├── tts-client.ts        ← VoxCPM API client
│   │   └── themes.ts            ← Color theme system
│   └── scripts/
│       ├── generate-audio.ts     ← TTS generation for all scenes
│       ├── full-pipeline.ts      ← Audio + render in one command
│       └── test-tts.ts           ← Verify TTS endpoint works
└── output/                       ← Rendered MP4s
```

---

## For Claude Code Users

This project includes `.claude/instructions.md` which gives Claude Code full context about the architecture, TTS API, and file structure. Just open the project and ask Claude Code to:

- "Create a new video about X" → It'll write the config JSON
- "Add a new character" → It'll create poses + voice config
- "Change the theme" → It knows the theme system
- "Generate the video" → It'll run the pipeline

---

## Commands Reference

| Command | What it does |
|---|---|
| `npm run dev` | Open Remotion Studio (visual preview + editing) |
| `npm run test-tts` | Verify VoxCPM TTS endpoint works |
| `npm run generate-audio -- --config configs/x.json` | Generate TTS only |
| `npm run generate -- --config configs/x.json` | Full pipeline (TTS + render all formats) |
| `npm run generate -- --config configs/x.json --format 9:16` | Render one format only |
| `npm run build` | Render 16:9 with default props |
| `npm run build:vertical` | Render 9:16 with default props |
| `npm run build:square` | Render 1:1 with default props |
