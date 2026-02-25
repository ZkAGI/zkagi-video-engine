# ZkAGI Video Engine — Claude Code Instructions

## Overview
Full AI video production pipeline. Claude Code handles everything:
**Brief → Script → Visuals (image/video) → TTS audio → Remotion compositing → MP4**

---

## MANDATORY: READ SKILLS BEFORE ANY VIDEO TASK

Before doing ANYTHING for a video brief, Claude Code MUST read these files in order:

1. .claude/skills/screenplay/SKILL.md — for script writing
2. .claude/skills/image-prompt-craft/SKILL.md — for image generation prompts
3. .claude/skills/motion-prompt-craft/SKILL.md — for LTX-2 video prompts
4. .claude/LTX2-SKILL.md — for ComfyUI workflow reference
5. products/{product}/PRODUCT.md — if the video is about a specific product

Then check for demo clips:
6. ls products/*/demo-clips/*.mp4 — if any exist for the product, USE THEM

These skills contain the quality standards, prompt engineering techniques, and style guides that make videos professional and entertaining. SKIPPING these produces generic, boring, corporate-looking videos.

This is NOT optional. Read them EVERY time. Even if you think you remember them.

---

## PIPELINE

**BEFORE writing scripts, read .claude/skills/screenplay/SKILL.md. BEFORE writing image prompts, read .claude/skills/image-prompt-craft/SKILL.md. BEFORE writing LTX-2 prompts, read .claude/skills/motion-prompt-craft/SKILL.md.**

### Step 1: Write Script
Based on user's brief, write 3-7 scenes. For each scene define:
- `characterId` — which voice/character to use
- `dialogue` — what they say (15-25 words per scene)
- `visualPrompt` — description of what the background should show
- `sceneType` — one of:
  - `"video"` — AI-generated video clip via LTX-2 (hype, concept, abstract)
  - `"demo"` — real product screen recording with voiceover (product showcase)
  - `"image"` — fallback: AI image with Ken Burns zoom
- `demoClip` — (only for demo scenes) path to screen recording, e.g. `"products/pawpad/demo-clips/tee-wallet-creation.mp4"`
- `demoTimestamp` — (only for demo scenes) start/end time to trim, e.g. `[6, 18]` (seconds)

**Video structure with product demos (RECOMMENDED for product videos):**
```
Scene 1: [video]  AI hype scene — hook the viewer, roast the problem
Scene 2: [video]  AI explainer — "here's what PawPad does differently"
Scene 3: [demo]   REAL product footage — "let me show you"
Scene 4: [demo]   REAL product footage — "and look at this"
Scene 5: [video]  AI CTA scene — "try it yourself at..."
```

### Step 1b: Load Product Knowledge (for product videos)
If the video is about a specific product, read its knowledge base FIRST:
```bash
# Check available products
ls products/*/PRODUCT.md

# Read the product knowledge
cat products/pawpad/PRODUCT.md    # ← for PawPad videos
```
This gives you: features, user flows, USPs, analogies for scripts, and demo clip paths with timestamps.

**Available products:**
```
products/
├── pawpad/
│   ├── PRODUCT.md          ← Features, flows, USPs, script analogies
│   └── demo-clips/         ← Screen recordings (add .mp4 files here)
│       ├── tee-wallet-creation.mp4
│       ├── agent-dashboard.mp4
│       └── key-recovery.mp4
├── zkterminal/             ← (coming soon)
└── zynapse/                ← (coming soon)
```

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

**FIRST: Read `.claude/LTX2-SKILL.md` for complete LTX-2 reference.**

**For EVERY scene, use this 2-step pipeline:**

**Step A: Generate a reference image per sub-clip**
```bash
curl -X POST "http://45.251.34.28:8010/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "SCENE VISUAL DESCRIPTION, no text, cinematic lighting, vibrant colors",
    "negative_prompt": "text, words, letters, watermark, blurry, low quality, deformed",
    "width": 768, "height": 512, "steps": 30, "cfg_scale": 6,
    "num_images": 1, "backend": "diffusers"
  }' --output public/scenes/scene-{i}.png
```

**Step B: Animate EACH reference image with LTX-2 image-to-video**
1. Upload image to ComfyUI: `curl -s -X POST "$COMFY_URL/upload/image" -F "image=@public/scenes/scene-{i}.png" -F "type=input"`
2. Submit workflow from LTX2-SKILL.md (use image-to-video pipeline with motion prompt + audio)
3. Poll for completion, download video clip

**CRITICAL: Generate MULTIPLE video clips per scene to fill audio duration. NO static images as filler. NO looping.**

**Health check for image gen:** `curl http://45.251.34.28:8010/health`

#### ComfyUI LTX-2 Connection
```bash
COMFY_URL="http://$(ip route show default | awk '{print $3}'):8001"
# Verify: curl -s "$COMFY_URL/system_stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['system']['comfyui_version'])"
```
**All LTX-2 workflow details, prompting guide, and quality tips → `.claude/LTX2-SKILL.md`**

**VISUAL STYLE GUIDE (CRITICAL — READ THIS)**

The #1 problem with our videos: visuals are GENERIC. "Glowing vault", "neon city", "digital shield" — boring, seen it a million times. Our visuals must be as funny, artsy, and personality-driven as our scripts.

**IMAGE GEN PROMPT RULES:**

1. **Match the TONE of the dialogue, not just the topic.**
   - Dialogue: "Bro, your wallet has ONE key and you think that's safe?"
   - BAD image: "glowing digital key in cyberspace, neon blue" ← boring stock art
   - GOOD image: "cartoon character sweating nervously holding a giant golden key while shadowy figures reach for it from all sides, dramatic spotlight, comic book style, vibrant saturated colors, expressive faces"

2. **Use CHARACTERS and SCENARIOS, not abstract concepts.**
   - BAD: "blockchain security concept art" ← meaningless
   - GOOD: "a confused person standing at a crossroads, one path labeled 'write 24 words on napkin' with a dumpster fire at the end, other path is a sleek glowing door, stylized illustration, warm lighting"
   - BAD: "futuristic technology privacy" ← generic
   - GOOD: "a tiny person sitting comfortably inside a giant crystal ball that is completely opaque from outside, curious people pressing faces against it trying to see in, whimsical illustration style"

3. **Style keywords to ALWAYS include (pick 2-3 per prompt):**
   - For humor: "comic book style, exaggerated expressions, cartoon, whimsical, playful"
   - For quality: "highly detailed, professional illustration, artstation quality, cinematic composition"
   - For mood: "dramatic lighting, volumetric light, vibrant saturated colors, depth of field"
   - For crypto/tech: "cyberpunk aesthetic, holographic, iridescent, glitch art accents"
   - NEVER: "stock photo", "corporate", "clean minimal" ← these produce boring images

4. **Character-driven scenes beat abstract concepts:**
   - Instead of "security concept" → show a character IN a secure situation
   - Instead of "privacy technology" → show someone being protected
   - Instead of "decentralization" → show a group of characters each holding a piece
   - People connect with CHARACTERS and STORIES, not concepts

5. **Vary the art style across scenes for visual interest:**
   - Scene 1 (hook): Bold, high contrast, dramatic — grab attention
   - Scene 2 (problem): Dark, moody, slightly chaotic — feel the pain
   - Scene 3 (solution): Bright, clean, hopeful — relief
   - Scene 4 (CTA): Energetic, warm, inviting — take action

6. **EXPERIMENT with styles — try these:**
   - "3D rendered cartoon character, Pixar style"
   - "anime style illustration with dramatic lighting"
   - "retro 80s synthwave aesthetic"
   - "watercolor illustration with ink outlines"
   - "isometric 3D scene, low poly"
   - "claymation style, stop motion aesthetic"
   - "comic book panel, bold outlines, halftone dots"
   - "Studio Ghibli inspired, soft lighting, detailed backgrounds"

**LTX-2 MOTION PROMPT RULES:**

Motion prompts must describe WHAT MOVES, not what the scene looks like (the image already defines that).

- **BAD motion:** "a secure digital vault" ← static, produces frozen video
- **GOOD motion:** "character nervously looking around, then sighing with relief as a glowing shield wraps around them, camera slowly orbiting, particles of light drifting upward, warm light intensifying"

- **BAD motion:** "cryptocurrency technology concept"
- **GOOD motion:** "the giant key in the character's hands begins cracking and shattering into pieces, fragments floating away in slow motion, character's expression shifting from panic to calm, camera pulling back dramatically, dust particles catching light"

**Motion must MATCH the dialogue emotion:**
- Funny/roast dialogue → chaotic motion, things going wrong, exaggerated reactions
- Explainer dialogue → smooth camera, gentle movements, things assembling/connecting
- Hype/CTA dialogue → fast motion, energy bursts, things coming together triumphantly

- NEVER include text/words in images or video — Remotion adds all text
- Each sub-clip needs a DIFFERENT motion prompt even for same scene

**Fallback:** If ComfyUI is down, use static images with Ken Burns zoom. But PREFER video clips always.

Save all generated visuals to:
```
public/scenes/
├── scene-0-a.mp4 (first clip)
├── scene-0-b.mp4 (second clip)
├── scene-1-a.mp4
└── ...
```

### Step 3b: USE REAL DEMO CLIPS (MANDATORY for demo scenes)

**⚠️ THIS IS NOT OPTIONAL. If the brief mentions a product demo, screen recording, or "show the real app", you MUST use the actual demo clip file. Do NOT generate AI visuals for demo scenes. Do NOT skip this step.**

**BEFORE writing any code, verify the demo clip exists:**
```bash
# Check what demo clips are available
ls -la products/pawpad/demo-clips/
ffprobe -v error -show_entries format=duration -of csv=p=0 products/pawpad/demo-clips/tee-wallet-creation.mp4
```

**If the file exists, you MUST use it. No exceptions.**

**Step 1: Copy the demo clip to public/scenes/ (so Remotion can access it via staticFile):**
```bash
# Copy the FULL demo clip first
cp products/pawpad/demo-clips/tee-wallet-creation.mp4 public/scenes/scene-{i}-demo.mp4

# OR trim to a specific section if needed
ffmpeg -i products/pawpad/demo-clips/tee-wallet-creation.mp4 \
  -ss 0 -to 30 \
  -c:v libx264 -an \
  public/scenes/scene-{i}-demo.mp4
```

**Step 2: Get the demo clip duration (needed for Remotion frame math):**
```bash
DEMO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 public/scenes/scene-{i}-demo.mp4)
echo "Demo clip duration: $DEMO_DURATION seconds"
```

**Step 3: In the Remotion composition, the demo scene MUST use OffthreadVideo pointing to the demo file:**
```jsx
// ═══════════════════════════════════════════════════
// DEMO SCENE — REAL PRODUCT FOOTAGE (NOT AI GENERATED)
// ═══════════════════════════════════════════════════
<Sequence from={demoSceneStart} durationInFrames={demoSceneFrames}>
  {/* THE ACTUAL SCREEN RECORDING */}
  <OffthreadVideo
    src={staticFile("scenes/scene-{i}-demo.mp4")}
    style={{
      width: "100%",
      height: "100%",
      objectFit: "contain",
      backgroundColor: "#000"
    }}
    volume={0}
  />

  {/* Dark gradient at bottom so captions are readable over the app UI */}
  <div style={{
    position: "absolute",
    bottom: 0,
    width: "100%",
    height: "25%",
    background: "linear-gradient(transparent, rgba(0,0,0,0.75))",
    zIndex: 5
  }} />

  {/* Subtitles explaining what's happening on screen */}
  <Subtitles
    text={scenes[sceneIndex].dialogue}
    accentColor={accentColor}
    durationInFrames={demoSceneFrames}
  />

  {/* TTS voiceover narrating the demo */}
  <Audio src={staticFile("audio/scene-{i}.wav")} />
</Sequence>
```

**Demo clip rules:**
- Remove audio from demo clip (`-an`) — TTS voiceover replaces the original audio
- If demo clip is SHORTER than TTS audio: slow it down with `-filter:v "setpts=1.3*PTS"` during ffmpeg copy
- If demo clip is LONGER than TTS audio: speed it up with `-filter:v "setpts=0.8*PTS"` or trim tighter
- Use `objectFit: "contain"` so the app UI is fully visible (don't crop it)
- Use dark background (`#000`) so letterbox bars are black
- The dark gradient at bottom is essential — without it, captions are unreadable over bright app UI

**HOW TO VERIFY DEMO CLIP IS ACTUALLY IN THE VIDEO:**
After rendering, check manually:
```bash
# Extract a frame from the demo scene portion of the video
DEMO_START_SEC=20  # adjust based on scene timing
ffmpeg -ss $DEMO_START_SEC -i output/video.mp4 -frames:v 1 -q:v 2 /tmp/demo-frame.png
# Open and visually verify it shows the actual app UI, not AI art
```

**COMMON MISTAKES TO AVOID:**
- ❌ Generating an AI image of "a phone showing a wallet app" — this is NOT a demo, it's fake
- ❌ Using LTX-2 to generate "app interface animation" — this is NOT the real product
- ❌ Skipping the demo clip because "AI looks better" — NO, the real app IS the demo
- ❌ Forgetting to copy the file to public/scenes/ — Remotion can only access staticFile paths
- ✅ Using the ACTUAL .mp4 file from products/pawpad/demo-clips/ with OffthreadVideo

### Step 4: Generate TTS Audio
For each scene, call VoxCPM with the character's voice.

**CRITICAL: Use these EXACT commands. Do NOT modify the ref_text strings.**

**For paw voice scenes:**
```bash
curl -X POST "https://avatar.zkagi.ai/v1/clone-tts" \
  -F "ref_audio=@voices/paw.wav" \
  -F "ref_text=ZM folks, here is your July 24th 2025 crypto update. Bitcoin is trading around 118520 US dollars." \
  -F "text=SCENE DIALOGUE HERE" \
  -F "cfg_value=2.0" \
  -F "steps=15" \
  --output public/audio/scene-{i}.wav
```

**For pad voice scenes:**
```bash
curl -X POST "https://avatar.zkagi.ai/v1/clone-tts" \
  -F "ref_audio=@voices/pad.wav" \
  -F "ref_text=Today, software handles our money, our health, our work." \
  -F "text=SCENE DIALOGUE HERE" \
  -F "cfg_value=2.0" \
  -F "steps=15" \
  --output public/audio/scene-{i}.wav
```

**DO NOT use `$(cat voices/paw.txt)` or `$(cat voices/pad.txt)` — this causes encoding issues and non-English output.**
**DO NOT change cfg_value or steps — these exact values produce English output.**
**DO NOT use any other TTS endpoint — ONLY /v1/clone-tts.**

**AFTER generating each audio file, VERIFY it:**
```bash
# Check file size (must be >50KB for 5+ seconds of audio)
ls -la public/audio/scene-{i}.wav

# Check duration
ffprobe -v error -show_entries format=duration -of csv=p=0 public/audio/scene-{i}.wav

# MANDATORY: Play it to verify it's English (on Linux)
timeout 3 aplay public/audio/scene-{i}.wav 2>/dev/null || timeout 3 ffplay -nodisp -autoexit -t 3 public/audio/scene-{i}.wav 2>/dev/null
```

If any audio is NOT English or has glitches, regenerate it ONE time with the same exact command. If still broken after one retry, the dialogue text might be confusing the model — simplify the dialogue to use common English words and shorter sentences.

**IMPORTANT TTS RULES:**
- Each scene dialogue MUST be 15-30 words to produce 8-15 seconds of audio
- If audio comes out under 5 seconds, the dialogue is too short — rewrite it longer
- Do NOT regenerate more than once — write proper length dialogue the first time
- Keep dialogue in simple, clear English — no unusual words, no special characters
- Do NOT use emojis, symbols, or non-ASCII characters in dialogue text

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
- Do NOT force character overlay when the AI background already tells the story
- Do NOT make every transition a crossfade
- Do NOT make it look like a PowerPoint slideshow
- NEVER put giant heading text in the center of the screen (like "UNBREAKABLE" or "SECURITY") — this looks hideous and covers the video
- NEVER make captions/subtitles cover more than 15% of screen height

**STRICT CAPTION/SUBTITLE RULES:**
- Subtitles go at the BOTTOM of the screen, not center
- Maximum 2 lines of text at any time
- Font size: 20-28px max for 1080p. NEVER 40px+
- Use a subtle semi-transparent dark pill/bar behind text for readability
- Subtitles should cover max 10-15% of screen height
- No highlightText giant titles — if you want to emphasize a word, make it a different color within the subtitle, not a separate giant heading
- The video background is the star, captions are supporting — never let text dominate the visual

**TTS AUDIO QUALITY RULES:**
- After generating each audio file, VERIFY it is English by checking file size (should be >50KB for 5+ seconds)
- If any audio sounds wrong, regenerate ONCE with same parameters
- Use cfg_value=2.0 and steps=15 always — do not change these
- Hardcode ref_text strings, do not read from files with cat (can cause encoding issues)

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
products/                 ← Product knowledge base + demo clips
├── pawpad/
│   ├── PRODUCT.md        ← Features, flows, USPs, analogies
│   └── demo-clips/       ← Real screen recordings (.mp4)
│       ├── tee-wallet-creation.mp4
│       ├── agent-dashboard.mp4
│       └── key-recovery.mp4
├── zkterminal/           ← (add more products here)
└── zynapse/

public/
├── characters/           ← Tiger character overlays (PNG, transparent bg)
│   ├── paw/neutral.png, excited.png
│   └── pad/neutral.png, thinking.png
├── scenes/               ← AI-generated + trimmed demo clips per scene
│   ├── scene-0-a.mp4     ← LTX-2 video clip
│   ├── scene-0-b.mp4     ← second clip
│   ├── scene-2-demo.mp4  ← trimmed product demo
│   └── ...
├── audio/                ← TTS audio files (Step 4)
│   ├── scene-0.wav
│   └── ...
├── sfx/                  ← Sound effects (whoosh, pop, bass-drop, ping, scratch)
└── music/                ← Optional background music tracks

voices/                   ← Voice reference samples
├── paw.wav + paw.txt     ← Host tiger voice
├── pad.wav + pad.txt     ← Explainer tiger voice
└── {new}.wav + {new}.txt ← Add more voices here

src/
├── compositions/ZkAGIVideo.tsx  ← Main Remotion composition (rewritten per video)
├── components/                   ← Reusable components
└── lib/                          ← TTS client, themes

.claude/
├── instructions.md       ← This file (pipeline guide)
└── LTX2-SKILL.md         ← LTX-2 video generation reference

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
- Write like a FUNNY content creator, NOT a corporate explainer
- Be conversational, witty, slightly irreverent — like MrBeast meets a crypto bro
- Short punchy sentences. No jargon. No technical babble.
- Each scene: 15-25 words of dialogue (produces 8-12s of audio)
- Think "storytelling" not "presenting" — hook people in the first 3 seconds
- Add humor, personality, and "masala" — make people want to watch till the end
- Use analogies a 12-year-old would understand
- ROAST the problem before presenting the solution
- Use rhetorical questions, sarcasm, and surprise

**Structure:**
- Scene 1: HOOK — funny roast, shocking question, or "wait what?" moment (8-10 seconds)
- Scenes 2-3: STORY — explain through funny analogies and relatable examples (8-12 seconds each)
- Last scene: CTA — hype them up, give the link, end with energy (8-10 seconds)

**What NOT to do:**
- No long monologues. Ever.
- No "In this video we will explore..." — boring!
- No listing features like a product spec sheet
- No "Let me explain..." — just explain it
- No technical jargon unless absolutely needed
- No robotic corporate tone — be HUMAN
- No "Welcome to..." or "Today we're going to..." — snooze!

**Examples of GOOD vs BAD dialogue:**
- BAD: "PawPad utilizes Trusted Execution Environment cryptographic key management infrastructure"
- GOOD: "Bro, your wallet has ONE key and you think that's safe? That's like putting all your money under your mattress and hoping nobody checks."

- BAD: "We leverage Oasis ROFL Trusted Execution Environments for hardware-level isolation"
- GOOD: "Imagine a vault... inside another vault... inside a volcano. That's basically where your transactions happen. Good luck hacking THAT."

- BAD: "ZkAGI combines artificial intelligence with zero knowledge proofs for private computation"
- GOOD: "What if AI could help you without EVER seeing your data? Sounds impossible right? That's literally what we built."

- BAD: "Join us at zkagi.ai to learn more about our platform"
- GOOD: "Stop letting big tech spy on your breakfast searches. zkagi dot ai. You're welcome."

---

## SOUND EFFECTS & ATTENTION HOOKS (CRITICAL)
Claude Code MUST add sound effects to make videos engaging. These go in the Remotion composition.

**Download or generate these sound effects and save to public/sfx/:**
```bash
mkdir -p public/sfx
```

**Required sounds (use free sources or generate with ffmpeg):**
```bash
# Whoosh transition (between scenes)
ffmpeg -f lavfi -i "anoisesrc=d=0.3:c=pink:r=44100:a=0.4" -af "afade=t=in:st=0:d=0.05,afade=t=out:st=0.15:d=0.15,highpass=f=2000,lowpass=f=8000" public/sfx/whoosh.wav

# Pop/ding (for highlight words)  
ffmpeg -f lavfi -i "sine=frequency=880:duration=0.15" -af "afade=t=out:st=0.05:d=0.1" public/sfx/pop.wav

# Bass drop (for hook/reveal moments)
ffmpeg -f lavfi -i "sine=frequency=60:duration=0.4" -af "afade=t=in:st=0:d=0.05,afade=t=out:st=0.2:d=0.2" public/sfx/bass-drop.wav

# Notification ping (for CTA/link moments)
ffmpeg -f lavfi -i "sine=frequency=1200:duration=0.2" -af "afade=t=out:st=0.1:d=0.1" public/sfx/ping.wav

# Record scratch (for "wait what" moments)
ffmpeg -f lavfi -i "anoisesrc=d=0.5:c=white:r=44100:a=0.3" -af "highpass=f=1000,tremolo=f=20:d=0.7,afade=t=in:st=0:d=0.05,afade=t=out:st=0.2:d=0.3" public/sfx/scratch.wav
```

**When to use sounds in Remotion:**
```jsx
// Scene transition — add whoosh
<Sequence from={sceneTransitionFrame - 5} durationInFrames={15}>
  <Audio src={staticFile("sfx/whoosh.wav")} volume={0.4} />
</Sequence>

// Hook moment — bass drop
<Sequence from={hookRevealFrame} durationInFrames={15}>
  <Audio src={staticFile("sfx/bass-drop.wav")} volume={0.5} />
</Sequence>

// CTA link shown — ping
<Sequence from={ctaLinkFrame} durationInFrames={10}>
  <Audio src={staticFile("sfx/ping.wav")} volume={0.3} />
</Sequence>
```

**Rules:**
- EVERY scene transition gets a whoosh or bass drop
- Highlight/keyword moments get a pop sound
- CTA/link reveal gets a ping
- "Wait what?" or surprise moments get a record scratch
- Keep SFX volume at 0.3-0.5 (not louder than voice)
- SFX make the video feel ALIVE and PROFESSIONAL

---

## EXAMPLE BRIEFS

**Simple AI-only:**
> "Make a 45s video about why privacy matters in crypto. Use paw voice. Make it funny."

**Product demo (PawPad wallet creation):**
> "Make a 60s video showing how PawPad wallet creation works. Use pad voice. Include the real screen recording of TEE wallet creation flow. Read products/pawpad/PRODUCT.md first. AI scenes for hook and CTA, demo clip for the actual product walkthrough."

**Product demo (PawPad agent):**
> "Make a 45s video about PawPad's AI trading agent. Show the real agent dashboard demo clip. Explain how the agent trades autonomously while your keys stay safe in TEE. Use paw voice for hype, pad for the demo walkthrough."

**Product demo (PawPad recovery):**
> "Make a 30s video showing how easy PawPad wallet recovery is. Include the real key recovery demo clip. Hook: 'Lost your phone? No problem.' Use pad voice."

**Use case / scenario video:**
> "Make a 60s video: scenario where someone loses their phone with crypto on it. Show the panic, then show how PawPad recovery saves them. Mix AI scenes for the story with real product demo of recovery flow."

**Multi-product:**
> "Make a 90s video about ZkAGI's product ecosystem. Cover PawPad wallet, ZkTerminal, and Zynapse. Use demo clips from each product. Read all PRODUCT.md files first."
