# 🎬 ZkAGI Video Engine — User Guide

## ONE-TIME SETUP (do this once)

### 1. Install
```bash
cd zkagi-video-engine
npm install
```

### 2. Set Up Characters (images)
Drop transparent PNG images into `public/characters/{name}/`:
```
public/characters/
├── paw/               ← your host character
│   ├── neutral.png    ← REQUIRED: default pose
│   ├── excited.png    ← optional: happy/energetic
│   ├── thinking.png   ← optional: contemplative
│   ├── serious.png    ← optional: focused
│   ├── waving.png     ← optional: greeting
│   └── celebrating.png← optional: victory
└── pad/               ← your explainer character
    ├── neutral.png    ← REQUIRED
    └── thinking.png   ← optional
```
Missing emotions fall back to neutral.png automatically.

### 3. Set Up Voices (audio)
For each character, add TWO files to `voices/`:
```
voices/
├── paw.wav   ← 3-10 second clean voice sample (WAV)
├── paw.txt   ← exact transcript of what's said in paw.wav
├── pad.wav   ← different voice for variety
└── pad.txt   ← exact transcript of pad.wav
```

To get the transcript if you don't know it:
```bash
pip install openai-whisper
whisper voices/paw.wav --model base --output_format txt
```

### 4. Set Claude API Key
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```
Add to your `~/.zshrc` or `~/.bashrc` to persist.

### 5. Test Everything
```bash
npm run test-tts    # verify VoxCPM TTS works
npm run dev         # preview in Remotion Studio
```

---

## MAKING VIDEOS (do this every time)

### The One Command
```bash
npm run create -- "Your topic or prompt here"
```

That's it. This will:
1. 🤖 Claude writes the script (picks characters, emotions, layouts)
2. 🎙️ VoxCPM generates voice audio for each scene
3. 🎬 Remotion renders MP4 videos (16:9 + 9:16 + 1:1)

### Examples
```bash
# Explainer video
npm run create -- "Explain what PawPad wallet is in 60 seconds"

# Crypto update
npm run create -- "Weekly crypto update: BTC at 120k, ETH ETFs surging, Solana DeFi growing"

# Technical deep dive
npm run create -- "How FROST MPC threshold signing works and why it matters for wallet security"

# Product launch
npm run create -- "Announcing ZkTerminal v2 with AI-powered ZK proof verification"

# Only vertical format (TikTok/Reels)
npm run create -- "3 reasons privacy matters in AI" --format 9:16
```

### Output
Videos appear in `output/` folder:
```
output/
├── explain-pawpad-wallet-landscape-2026-02-18.mp4   ← YouTube
├── explain-pawpad-wallet-vertical-2026-02-18.mp4    ← TikTok/Reels
└── explain-pawpad-wallet-square-2026-02-18.mp4      ← Instagram
```

---

## STEP-BY-STEP COMMANDS (if you want more control)

### Generate script only (review before rendering)
```bash
npm run generate-script -- "Your topic here"
# Creates configs/your-topic.json — edit it if needed
```

### Generate audio only
```bash
npm run generate-audio -- --config configs/your-topic.json
```

### Render video only
```bash
npm run generate -- --config configs/your-topic.json
```

### Preview in Remotion Studio
```bash
npm run dev
# Opens http://localhost:3000 with visual editor
```

---

## ADDING NEW CHARACTERS

### Step 1: Create image folder
```bash
mkdir public/characters/newchar
cp your-character-neutral.png public/characters/newchar/neutral.png
cp your-character-excited.png public/characters/newchar/excited.png
# add as many emotion PNGs as you have
```

### Step 2: Add voice
```bash
cp your-voice-sample.wav voices/newchar.wav
# Transcribe it:
whisper voices/newchar.wav --model base --output_format txt
mv newchar.txt voices/newchar.txt
```

### Step 3: Use it
The script generator auto-discovers characters from the folders.
Just run `npm run create -- "your prompt"` and it will use all available characters.

---

## ALL COMMANDS

| Command | What it does |
|---|---|
| `npm run create -- "prompt"` | **FULL AUTO: prompt → script → audio → video** |
| `npm run create -- "prompt" --format 9:16` | Full auto, one format only |
| `npm run generate-script -- "prompt"` | Script only (JSON config) |
| `npm run generate-audio -- --config x.json` | TTS audio only |
| `npm run generate -- --config x.json` | Audio + render |
| `npm run dev` | Remotion Studio preview |
| `npm run test-tts` | Test VoxCPM connection |
