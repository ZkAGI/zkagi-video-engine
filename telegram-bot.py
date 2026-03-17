#!/usr/bin/env python3
"""
ZkAGI Video Engine — Telegram Bot

Send /video <topic> to generate a complete video via Claude Code.
Send /video_today to auto-generate today's planned video from the content calendar.
Send /carousel to generate a LinkedIn carousel from daily news.
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, date
from functools import wraps
from pathlib import Path

import httpx

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ── Config ──────────────────────────────────────────────────────────────────

load_dotenv()

PROJECT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_IDS = [
    int(x)
    for x in os.environ.get("ALLOWED_TELEGRAM_USERS", "").split(",")
    if x.strip()
]
MAX_TIMEOUT = 2400  # 40 minutes hard timeout
TELEGRAM_FILE_LIMIT_MB = 50
DIGEST_API_BASE = "http://34.67.134.209:8030"
DIGEST_INGEST_URL = f"{DIGEST_API_BASE}/ingest/run"
DIGEST_GENERATE_URL = f"{DIGEST_API_BASE}/digest/daily/generate"
DIGEST_LATEST_URL = f"{DIGEST_API_BASE}/digest/daily/latest"
CALENDAR_PATH = PROJECT_DIR / "content-calendar.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("zkagi-bot")

# ── Job state ───────────────────────────────────────────────────────────────

job_queue: asyncio.Queue = asyncio.Queue()
current_job: dict | None = None
current_proc: asyncio.subprocess.Process | None = None


# ── Auth decorator ──────────────────────────────────────────────────────────

def authorized(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if ALLOWED_USER_IDS and uid not in ALLOWED_USER_IDS:
            await update.message.reply_text("Not authorized.")
            log.warning("Unauthorized access attempt from user %s", uid)
            return
        return await func(update, context)
    return wrapper


# ── Digest API ─────────────────────────────────────────────────────────────

async def fetch_daily_digest() -> str:
    """Fetch today's daily digest. Runs full pipeline: ingest → generate → return.

    Pipeline:
      1. Check /latest — if created today, use it (fast, ~1s)
      2. Otherwise run /ingest/run to pull fresh news (~10-30s)
      3. Then /digest/daily/generate to create today's digest (~10-30s)
    Returns empty string on failure — caller handles fallback.
    """
    from datetime import datetime, timezone
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        # 1. Try cached latest — only accept if created today
        try:
            resp = await client.get(DIGEST_LATEST_URL, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", "")
            created = data.get("created_at", "")
            if content and created.startswith(today_str):
                log.info("Fetched today's cached digest (%d chars, created %s)", len(content), created[:19])
                return content
            elif content:
                log.info("Cached digest is stale (created %s, today is %s) — refreshing", created[:10], today_str)
            else:
                log.info("Cached digest empty — refreshing")
        except Exception as e:
            log.warning("Failed to fetch cached digest: %s", e)

        # 2. Run ingestion to pull fresh news items
        try:
            log.info("Running news ingestion pipeline...")
            resp = await client.post(DIGEST_INGEST_URL, timeout=60.0)
            resp.raise_for_status()
            ingest_data = resp.json()
            new_items = ingest_data.get("new_items_ingested", 0)
            log.info("Ingestion complete: %d new items", new_items)
        except Exception as e:
            log.warning("Ingestion failed (will try generate anyway): %s", e)

        # 3. Generate fresh digest from ingested items
        try:
            log.info("Generating fresh daily digest...")
            resp = await client.post(DIGEST_GENERATE_URL, timeout=90.0)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", "")
            if content and len(content) > 200:
                log.info("Generated fresh daily digest (%d chars)", len(content))
                return content
            else:
                log.warning("Generated digest too short (%d chars) — may lack news items", len(content))
        except Exception as e:
            log.warning("Failed to generate fresh digest: %s", e)

        # 4. Last resort — return whatever /latest has, even if stale
        try:
            resp = await client.get(DIGEST_LATEST_URL, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", "")
            if content:
                log.info("Falling back to stale digest (%d chars)", len(content))
                return content
        except Exception as e:
            log.warning("All digest attempts failed: %s", e)

    return ""


# ── Claude prompt ───────────────────────────────────────────────────────────

def build_digest_prompt(digest_content: str, output_filename: str, mode: str = "story") -> str:
    """Build a prompt where the daily digest is the PRIMARY content source (days 6-10)."""
    return f"""You are generating a complete video for the ZkAGI Video Engine.

TONE: Make this FUNNY and LIVELY. Not dry. Not corporate. Not a lecture. Think stand-up comedian
reacting to the news — punchy one-liners, absurd analogies, roasting the problem hard before
dropping the solution. The viewer should laugh at least twice and share it with a friend.
If the script reads like a press release, rewrite it. If it reads like something a bored narrator
would mumble through, rewrite it. Energy. Personality. Punchlines. Every scene.

PRIMARY CONTENT SOURCE — today's trending news digest:
{digest_content}

PRODUCT SELECTION — pick the BEST-FIT product based on the news above:
  - PawPad → wallet, security, custody, DeFi, trading agents, yield, seed phrase, keys
  - Zynapse → developer API, privacy, ZK proofs, DePIN, image/video/audio generation, content creation
  - ZkTerminal → AI playground, content creation, trading signals, prediction markets, crypto analysis
  - ZkAGI → parent brand, zero-employee enterprise, multi-product, general AI/crypto news
Pick the product whose keywords best match the trending topics. Use "auto" logic:
  if the digest mentions wallet/DeFi/security → PawPad
  if the digest mentions APIs/privacy/generation → Zynapse
  if the digest mentions predictions/trading/signals → ZkTerminal
  if multiple products fit or general crypto/AI news → ZkAGI (reference all products)

INSTRUCTIONS:
1. Read the digest above and identify the most compelling trending story
2. Pick the best-fit product using the keyword map
3. Create a {mode}-mode screenplay that LEADS with the trending news, then naturally weaves in the product
4. The video should feel timely and topical — like a hot take, not a product ad
5. Use humor: absurd comparisons, roasts, callbacks, rule-of-three jokes, specific details over vague stats
6. Product URLs: pawpad = paw.zkagi.ai | zynapse = docs.zkagi.ai/docs/getting-started/zynapse | zkterminal = zkterminal.zkagi.ai

MANDATORY PIPELINE — follow these steps IN THIS EXACT ORDER:

0. CLEANUP: Remove stale assets from previous runs:
   - Delete all files in public/scenes/ (rm public/scenes/*)
   - Delete all files in public/audio/ (rm public/audio/*)

1. READ SKILLS (do this FIRST, before anything else):
   - .claude/skills/screenplay/SKILL.md
   - .claude/skills/image-prompt-craft/SKILL.md
   - .claude/skills/motion-prompt-craft/SKILL.md
   - .claude/skills/motion-graphics/SKILL.md
   - .claude/LTX2-SKILL.md

2. SCREENPLAY: Write 4-6 scenes, 15-25 words per scene. Mode: {mode}.
   - VOICE: ALWAYS use "pad" character for ALL scenes. Never use "paw". pad is the ONLY voice.
   - LANGUAGE: ALL dialogue MUST be in English. ONLY English. No exceptions.
   - For each scene, write a VISUAL DESCRIPTION and mark it as "video" or "motion-graphic" type.
   - Use 1-2 motion-graphic scenes MAX for data-heavy moments (stats, prices, comparisons).
   - HUMOR/ENERGY CHECK — before moving to step 3, re-read your screenplay and ask:
     * Does Scene 1 hook in 3 seconds? Would someone stop scrolling?
     * Is there at least ONE punchline or moment that made you smile?
     * Did you name a character or use a specific, vivid detail?
     * Does the CTA have swagger, or does it sound like a robot reading a URL?
     If any answer is "no", rewrite. The news is the hook — make it a HOT TAKE, not a summary.
   - CONVERSION FOCUS: Every video must drive action. Include:
     * TARGET AUDIENCE: Identify who this video is for
     * CTA: The FINAL scene MUST end with a clear CTA — product URL
     * Build toward the CTA: trending hook → context → product solution → proof → action

3. TTS AUDIO (generate BEFORE images/video — you need durations first):
   - Generate for EVERY scene via VoxCPM at https://avatar.zkagi.ai/v1/clone-tts
   - ALWAYS use pad voice: ref_audio="./voices/pad.wav", ref_text="Today, software handles our money, our health, our work."
   - Save to public/audio/scene-N.wav
   - After generating ALL audio, measure EACH audio duration with ffprobe and record them.

4. REFERENCE IMAGES: Generate ONE image per scene as the LTX-2 source frame:
   - SKIP for motion-graphic scenes — they don't need reference images.
   - Primary: curl -X POST http://45.251.34.28:8010/generate (params: prompt, width=768, height=512)
   - Fallback: curl -X POST https://zynapse.zkagi.ai/v1/generate/image with header X-API-Key: 758b5e2a-f9f5-4531-a062-6de90371ab9f (params: prompt, width=768, height=512, num_steps=24, guidance=3.5)
   - Save to public/scenes/scene-N-a.png
   - ALSO generate overflow images for scenes where TTS audio > 4.5s:
     * If audio 4.5-8s: 1 extra → scene-N-b.png
     * If audio 8-12s: 2 extra → scene-N-b.png, scene-N-c.png
     * If audio > 12s: 3 extra → scene-N-b.png, scene-N-c.png, scene-N-d.png

5. VIDEO CLIPS: Generate ONE LTX-2 video clip per scene via LOCAL ComfyUI at http://172.18.64.1:8001
   - SKIP for motion-graphic scenes — they don't need video clips.
   - CRITICAL: Read .claude/LTX2-SKILL.md and use ONLY the local LTX-2 nodes listed there
   - NEVER use BFL, Flux, or any cloud/API nodes
   - Save to public/scenes/scene-N-a.mp4

6. COMPOSITION: Update src/Root.tsx and src/compositions/ZkAGIVideo.tsx
   - Import reusable components from "../components" (KenBurnsImage, GlitchFlash, ScreenShake, WordPopSubtitles, BottomGradient, SubClipFade, TopicBadge, CtaUrl)
   - Import motion graphics from "../components/motion-graphics" as needed
   - For VIDEO scenes: video clip first, then Ken Burns overflow images
   - For MOTION-GRAPHIC scenes: use the component directly (no video/images), with standard overlays
   - MANDATORY ENDING: append ending.mp4 (300 frames) after all scenes
   - URL ACCURACY: zkterminal = "zkterminal.zkagi.ai" | pawpad = "paw.zkagi.ai" | zynapse = "docs.zkagi.ai/docs/getting-started/zynapse"

7. RENDER: npx remotion render ZkAGIVideo output/{output_filename} --bundle-cache=false --timeout=300000

8. SOCIAL MEDIA CAPTIONS: Save to output/{output_filename}.captions.json:
   {{
     "twitter": "<max 280 chars, punchy, 2-3 hashtags, product URL>",
     "linkedin": "<max 3000 chars, professional, hook first line, CTA>",
     "youtube_title": "<max 100 chars, SEO-friendly>",
     "youtube_description": "<max 5000 chars, SEO-rich, product URLs>"
   }}

After rendering, verify the file exists and print its size.
"""


def build_prompt(topic: str, output_filename: str, digest_context: str = "") -> str:
    digest_section = ""
    if digest_context:
        digest_section = f"""
DAILY TRENDING CONTEXT (use to add timely references to your screenplay):
{digest_context}

Use 1-2 relevant trending topics as hooks or references in your screenplay to make
it timely and engaging. Don't force it — only reference trends that naturally connect
to the video's product/topic.

"""

    return f"""You are generating a complete video for the ZkAGI Video Engine.

TONE: Make this ENTERTAINING. Not boring. Not corporate. Not a lecture nobody asked for.
Write like a sharp comedian who actually knows crypto — punchy, specific, full of personality.
Use absurd analogies, roast the problem hard, drop punchlines, use named characters ("Meet Dave"),
and end with energy. If a line sounds like it belongs in a pitch deck, delete it. If the viewer
wouldn't send this to a friend, rewrite it. Every scene needs personality. Every. Single. One.

BRIEF: {topic}
{digest_section}
MANDATORY PIPELINE — follow these steps IN THIS EXACT ORDER:

0. CLEANUP: Remove stale assets from previous runs:
   - Delete all files in public/scenes/ (rm public/scenes/*)
   - Delete all files in public/audio/ (rm public/audio/*)

1. READ SKILLS (do this FIRST, before anything else):
   - .claude/skills/screenplay/SKILL.md
   - .claude/skills/image-prompt-craft/SKILL.md
   - .claude/skills/motion-prompt-craft/SKILL.md
   - .claude/skills/motion-graphics/SKILL.md
   - .claude/LTX2-SKILL.md

2. SCREENPLAY: Write 4-6 scenes, 15-25 words per scene. Pick story or standard mode based on the brief.
   - VOICE: ALWAYS use "pad" character for ALL scenes. Never use "paw". pad is the ONLY voice.
   - LANGUAGE: ALL dialogue MUST be in English. ONLY English. No exceptions. No non-English words.
     If the TTS receives non-English text it produces garbage audio. Write ONLY plain English.
   - For each scene, write a VISUAL DESCRIPTION and mark it as "video" or "motion-graphic" type.
   - Use 1-2 motion-graphic scenes MAX for data-heavy moments (stats, prices, product reveals).
   - HUMOR/ENERGY CHECK — before moving to step 3, re-read your screenplay and ask:
     * Does Scene 1 hook in 3 seconds? Would someone stop scrolling?
     * Is there at least ONE line that made you smile while writing it?
     * Are there named characters, specific details, or absurd comparisons?
     * Does the CTA have personality, or does it sound like a Terms of Service?
     * Would YOU watch this, or would you click away after 4 seconds?
     If any answer is "no", rewrite that scene with more personality.
   - CONVERSION FOCUS: Every video must drive action. Include in your screenplay:
     * TARGET AUDIENCE: Identify who this video is for (e.g. crypto traders, developers, solo founders)
     * CTA (Call To Action): The FINAL scene MUST end with a clear CTA — a URL, "try it now", "download today"
     * Product URLs: pawpad = paw.zkagi.ai | zynapse = docs.zkagi.ai/docs/getting-started/zynapse | zkterminal = zkterminal.zkagi.ai
     * Make the CTA natural, not salesy. Example: "paw dot zkagi dot ai. Thirty seconds. No seed phrase. No excuses."
     * Build toward the CTA: problem → pain → solution → proof → action

3. TTS AUDIO (generate BEFORE images/video — you need durations first):
   - Generate for EVERY scene via VoxCPM at https://avatar.zkagi.ai/v1/clone-tts
   - ALWAYS use pad voice: ref_audio="./voices/pad.wav", ref_text="Today, software handles our money, our health, our work."
   - NEVER use paw voice. pad is the only voice for all scenes.
   - Save to public/audio/scene-N.wav
   - After generating ALL audio, measure EACH audio duration with ffprobe and record them.
     You MUST know exact durations before proceeding to step 4.

4. REFERENCE IMAGES: Generate ONE image per scene as the LTX-2 source frame:
   - SKIP for motion-graphic scenes — they don't need reference images.
   - Primary: curl -X POST http://45.251.34.28:8010/generate (params: prompt, width=768, height=512)
   - Fallback: curl -X POST https://zynapse.zkagi.ai/v1/generate/image with header X-API-Key: 758b5e2a-f9f5-4531-a062-6de90371ab9f (params: prompt, width=768, height=512, num_steps=24, guidance=3.5)
   - Save to public/scenes/scene-N-a.png
   - Use the scene's VISUAL DESCRIPTION as the image prompt
   - ALSO generate overflow images ONLY for scenes where TTS audio > 4.5s:
     * If audio 4.5-8s: generate 1 extra image → scene-N-b.png
     * If audio 8-12s: generate 2 extra images → scene-N-b.png, scene-N-c.png
     * If audio > 12s: generate 3 extra images → scene-N-b.png, scene-N-c.png, scene-N-d.png
     * Each extra image shows a DIFFERENT angle/moment of the scene

5. VIDEO CLIPS: Generate ONE LTX-2 video clip per scene via LOCAL ComfyUI at http://172.18.64.1:8001
   - SKIP for motion-graphic scenes — they don't need video clips.
   - CRITICAL: Read .claude/LTX2-SKILL.md and use ONLY the local LTX-2 nodes listed there
   - NEVER use BFL, Flux, or any cloud/API nodes — they require login and WILL fail
   - Use ONLY these local node types: DualCLIPLoader, EmptyLTXVLatentVideo, LTXVImgToVideo, LTXVConditioning, LTXVScheduler, LTXVPreprocess, LTXVConcatAVLatent, LTXVSeparateAVLatent, LTXVEmptyLatentAudio, CFGGuider, KSamplerSelect, SamplerCustomAdvanced, RandomNoise, CLIPTextEncode, LoadImage, VAEDecode, SaveVideo
   - Available models: ckpt_name="ltx-2.3-22b-dev-fp8.safetensors", DualCLIPLoader with clip_name1 and clip_name2
   - Input: scene-N-a.png as reference image
   - TEXT PROMPT: Use the scene's VISUAL DESCRIPTION as the CLIPTextEncode prompt for LTX-2.
     This drives the motion/animation of the video. Describe movement and action.
   - Save to public/scenes/scene-N-a.mp4
   - Each video clip is ~3.88s (97 frames at 25fps)

6. COMPOSITION: Update src/Root.tsx and src/compositions/ZkAGIVideo.tsx
   - Import reusable components from "../components" (KenBurnsImage, GlitchFlash, ScreenShake, WordPopSubtitles, BottomGradient, SubClipFade, TopicBadge, CtaUrl)
   - Import motion graphics from "../components/motion-graphics" as needed (PriceTicker, DataMetric, NewsHeadline, ProductShowcase, StatGrid, AnimatedComparison)

   VIDEO scenes — video clips are the PRIMARY visual:
   - ALWAYS start each scene with the LTX-2 video clip (scene-N-a.mp4)
   - If TTS audio <= 4.5s: use ONLY the video clip. No images needed.
   - If TTS audio > 4.5s: play the video clip FIRST (~3.88s), THEN fill remaining
     time with Ken Burns images (scene-N-b.png, scene-N-c.png etc.)
   - Ken Burns images are OVERFLOW ONLY — they pad the remaining duration after the video ends.
   - Use 8-frame crossfade (SubClipFade) between video→image and image→image transitions.
   - Ken Burns directions: alternate zoom-in, pan-left, pan-right, zoom-out for variety.
   - Calculate precisely: scene_frames = audio_duration * 30 (fps), video_frames = 97

   MOTION-GRAPHIC scenes — use Remotion components instead of video/images:
   - Use the appropriate component (PriceTicker, DataMetric, etc.) — it fills the entire scene
   - No video clip or Ken Burns images needed for these scenes
   - Standard overlays (BottomGradient, TopicBadge, WordPopSubtitles, Audio) still apply on top

   MANDATORY ENDING — EVERY video MUST end with ending clip:
   - After ALL scenes, append ONE final Sequence before global layers:
     <Sequence from={{ENDING_START}} durationInFrames={{ENDING_CLIP_FRAMES}}><AbsoluteFill><Video src={{staticFile("video/ending.mp4")}} style={{{{ width: "100%", height: "100%", objectFit: "cover" }}}} volume={{1}} startFrom={{0}} /></AbsoluteFill></Sequence>
   - ENDING_START = sum of all scene frame durations
   - ENDING_CLIP_FRAMES = 300 (ending.mp4, ~10s)
   - TOTAL_FRAMES in Root.tsx MUST include: scenes_total + 300
   - Do NOT add a BrandOutro component — it has been removed.

   URL ACCURACY — when displaying product URLs (e.g. in CtaUrl components):
   - zkterminal URL is "zkterminal.zkagi.ai" — NEVER drop the "zk" prefix
   - pawpad URL is "paw.zkagi.ai"
   - zynapse URL is "docs.zkagi.ai/docs/getting-started/zynapse"

7. RENDER: npx remotion render ZkAGIVideo output/{output_filename} --bundle-cache=false --timeout=300000
   Only render landscape 16:9.

8. SOCIAL MEDIA CAPTIONS: After rendering, generate captions and save to output/{output_filename}.captions.json:
   {{
     "twitter": "<Twitter/X caption, max 280 characters. Punchy, attention-grabbing. Include 2-3 relevant hashtags. Include the product URL.>",
     "linkedin": "<LinkedIn post, max 3000 characters. Professional but engaging. Hook in first line. Include context about the product, why it matters, and a CTA. Use line breaks for readability. Include relevant hashtags at the end.>",
     "youtube_title": "<YouTube title, max 100 characters. SEO-friendly, compelling, includes key topic.>",
     "youtube_description": "<YouTube description, max 5000 characters. First 2 lines are most important (shown in search). Include: summary, key points, product links, timestamps if applicable, relevant hashtags.>"
   }}
   - Match the tone/topic of the video
   - Twitter: short, punchy, emoji OK, must fit 280 chars
   - LinkedIn: professional, value-driven, storytelling hook
   - YouTube title: clickworthy but not clickbait
   - YouTube description: SEO-rich, include product URLs

After rendering, verify the file exists and print its size.
"""


def build_carousel_prompt(digest_content: str) -> str:
    """Build a prompt for carousel generation from daily digest."""
    today = date.today().isoformat()
    return f"""You are generating a LinkedIn carousel from today's trending news.

TODAY'S DATE: {today}

DAILY TRENDING NEWS DIGEST:
{digest_content}

MANDATORY PIPELINE — follow these steps IN THIS EXACT ORDER:

1. READ PRODUCT KNOWLEDGE (do this FIRST):
   - products/pawpad/PRODUCT.md
   - products/zynapse/PRODUCT.md
   - products/zkterminal/PRODUCT.md

2. ANALYZE NEWS & PICK PRODUCT:
   From the digest, identify the top 3-5 stories. Pick the best-fit ZkAGI product:
   - wallet/DeFi/security/seed phrase/hack → PawPad (paw.zkagi.ai)
   - APIs/privacy/ZK/generation/developer tools → Zynapse (docs.zkagi.ai/docs/getting-started/zynapse)
   - predictions/trading/signals/market/alpha → ZkTerminal (zkterminal.zkagi.ai)

3. READ the image-prompt-craft skill FIRST: .claude/skills/image-prompt-craft/SKILL.md
   Use this skill to write ai_background_prompt for EVERY slide.

4. WRITE SLIDE JSON with 5-10 slides:
   - First slide: type "hook" — bold, curiosity-driving statement
   - Middle slides: "insight" or "stat" — actual news content
   - One "product" slide — naturally tied to the news
   - Last slide: type "cta" — drives action

   Slide types and fields:
   - hook: title, body, accent_color, ai_background_prompt
   - insight: title, body, accent_color, tag, ai_background_prompt
   - stat: title (the number — keep SHORT like "$4.2T" or "50+", NOT full sentences), body (description), accent_color, ai_background_prompt
   - product: title (product name), tagline, features (list of 3-4), accent_color, ai_background_prompt
   - cta: title, body, accent_color, ai_background_prompt

   CRITICAL — PRODUCT SLIDE FEATURES MUST BE NEWS-RELEVANT:
   Do NOT always use the same generic features. Read the product's PRODUCT.md and pick
   the specific endpoints/features that DIRECTLY connect to today's news stories.
   Examples for Zynapse:
   - If news is about privacy/compliance/regulation → highlight: "ZK-proof document verification", "Verifiable AI answers", "Built-in audit trails"
   - If news is about AI generation/creative tools → highlight: "Text-to-image API", "Text-to-video API", "One API key for all AI"
   - If news is about infrastructure/compute/costs → highlight: "DePIN GPU network", "No vendor lock-in", "Crypto-native payments"
   - If news is about data provenance/healthcare → highlight: "ZK proof Q&A", "Document authenticity proofs", "HIPAA-ready privacy"
   Examples for PawPad:
   - If news is about hacks/theft → highlight: "No seed phrase to steal", "TEE-secured keys", "Social recovery"
   - If news is about onboarding/UX → highlight: "One-tap onboarding", "No seed phrase needed", "Gasless transactions"
   Examples for ZkTerminal:
   - If news is about trading/markets → highlight: "AI trading signals", "Real-time analysis", "Portfolio tracking"
   - If news is about predictions/alpha → highlight: "AI-powered predictions", "On-chain analytics", "Signal aggregation"
   The tagline should also vary — pick the most relevant one from the product doc, or write a new one that ties to the news.

   IMPORTANT — ai_background_prompt for EVERY slide:
   Use the image-prompt-craft skill to write a detailed, character-driven prompt for each slide.
   Follow the formula: [SUBJECT] + [ACTION/POSE] + [SETTING] + [ART STYLE] + [LIGHTING] + [CAMERA] + [QUALITY]
   Rules from the skill:
   - NEVER write abstract concept prompts like "blockchain technology" — always use characters, scenarios, metaphors
   - Use a cartoon tiger mascot character as the subject when appropriate
   - Match art style to slide emotion: hook=dramatic, insight=atmospheric, stat=dramatic data, product=clean showcase, cta=warm inviting
   - Always include lighting direction and quality boosters
   - Vary visual approaches across slides for visual interest

   Accent colors: #7C3AED (purple), #06B6D4 (teal), #EF4444 (red), #F59E0B (amber), #10B981 (green)
   Keep slide text SHORT — max 3-4 lines, ~15 words per line.

   Save to /tmp/carousel-slides.json

5. GENERATE CAROUSEL:
   python3 generate-carousel.py --input /tmp/carousel-slides.json
   (The script auto-generates AI backgrounds for each slide using the ai_background_prompt fields,
    and renders tiger mascot characters. It may take 2-4 minutes if AI image servers are active.)

6. WRITE LINKEDIN CAPTION to output/carousel-{today}/caption.txt:
   - Hook line (question or bold statement)
   - 2-3 short paragraphs covering the news
   - Mention the ZkAGI product naturally
   - Include the product URL
   - CTA: "Follow for daily crypto insights"
   - 3-5 hashtags
   - Under 1300 characters

7. PRINT SUMMARY:
   Print the output directory and list of files generated.
"""


# ── Phase detection keywords ────────────────────────────────────────────────

PHASE_KEYWORDS = [
    ("SKILL.md", "Reading skills..."),
    ("screenplay", "Writing screenplay..."),
    ("clone-tts", "Generating TTS audio..."),
    ("45.251.34.28", "Generating reference images..."),
    ("zynapse.zkagi.ai", "Generating reference images (fallback)..."),
    ("172.18.64.1:8001", "Generating video clips via ComfyUI..."),
    ("ZkAGIVideo.tsx", "Editing Remotion composition..."),
    ("remotion render", "Rendering final video..."),
]

CAROUSEL_PHASE_KEYWORDS = [
    ("PRODUCT.md", "Reading product info..."),
    ("carousel-slides.json", "Writing slide content..."),
    ("generate-carousel.py", "Rendering carousel slides..."),
    ("caption.txt", "Writing LinkedIn caption..."),
]


# ── Core video generation ──────────────────────────────────────────────────

async def process_video_job(job: dict):
    global current_job, current_proc
    current_job = job

    topic = job["topic"]
    chat_id = job["chat_id"]
    bot = job["bot"]

    # Use pre-built prompt/filename from digest flow, or build standard prompt
    if "prompt" in job and "output_filename" in job:
        prompt = job["prompt"]
        output_filename = job["output_filename"]
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()[:40]).strip("-")
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        output_filename = f"{slug}-{ts}.mp4"
        digest_context = job.get("digest_context", "")
        prompt = build_prompt(topic, output_filename, digest_context=digest_context)
    output_path = OUTPUT_DIR / output_filename

    await bot.send_message(chat_id, "Pipeline started. Spawning Claude Code...")
    log.info("Starting job: %s -> %s", topic, output_filename)

    proc = await asyncio.create_subprocess_exec(
        "claude",
        "-p", prompt,
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        "--verbose",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,  # merge stderr into stdout
        cwd=str(PROJECT_DIR),
    )
    current_proc = proc
    proc.stdout._limit = 10 * 1024 * 1024  # 10MB buffer

    # Read stdout line-by-line (avoids the double-read asyncio bug)
    sent_phases = set()
    try:
        while True:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=MAX_TIMEOUT)
            if not line:
                break
            line_str = line.decode("utf-8", errors="replace").rstrip()
            if line_str:
                log.info("[claude] %s", line_str[:500])
            for keyword, phase_msg in PHASE_KEYWORDS:
                if keyword in line_str and phase_msg not in sent_phases:
                    sent_phases.add(phase_msg)
                    try:
                        await bot.send_message(chat_id, phase_msg)
                    except Exception:
                        pass
                    break
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        await bot.send_message(chat_id, "Timed out after 40 minutes. Pipeline may have stalled.")
        log.error("Job timed out: %s", topic)
        current_job = None
        current_proc = None
        return

    await proc.wait()
    current_job = None
    current_proc = None

    if proc.returncode != 0:
        await bot.send_message(chat_id, f"Pipeline failed (exit {proc.returncode}).")
        log.error("Job failed: %s, exit %d", topic, proc.returncode)
        return

    # Find the output MP4
    if not output_path.exists():
        mp4s = sorted(
            OUTPUT_DIR.glob("*.mp4"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if mp4s:
            output_path = mp4s[0]
        else:
            await bot.send_message(chat_id, "Pipeline completed but no MP4 found.")
            log.error("No MP4 found for job: %s", topic)
            return

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    log.info("Output: %s (%.1f MB)", output_path.name, file_size_mb)

    # Compress if over Telegram limit
    send_path = output_path
    if file_size_mb > TELEGRAM_FILE_LIMIT_MB:
        await bot.send_message(
            chat_id,
            f"Video is {file_size_mb:.0f} MB — compressing for Telegram...",
        )
        compressed = output_path.with_name(output_path.stem + "-compressed.mp4")
        compress_proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", str(output_path),
            "-c:v", "libx264", "-crf", "28", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            str(compressed),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await compress_proc.wait()
        if compressed.exists():
            csize = compressed.stat().st_size / (1024 * 1024)
            if csize <= TELEGRAM_FILE_LIMIT_MB:
                send_path = compressed
            else:
                await bot.send_message(
                    chat_id,
                    f"Compressed to {csize:.0f} MB, still over 50 MB limit.\n"
                    f"File saved at: {output_path}",
                )
                return

    await bot.send_message(chat_id, f"Uploading ({file_size_mb:.1f} MB)...")

    with open(send_path, "rb") as f:
        await bot.send_video(
            chat_id=chat_id,
            video=f,
            caption=f"ZkAGI: {topic[:200]}",
            supports_streaming=True,
            read_timeout=300,
            write_timeout=300,
        )

    log.info("Delivered video for: %s", topic)

    # Send social media captions
    captions_path = output_path.with_suffix(".mp4.captions.json")
    if captions_path.exists():
        try:
            with open(captions_path) as f:
                captions = json.load(f)

            captions_msg = (
                "--- SOCIAL MEDIA CAPTIONS ---\n\n"
                f"TWITTER/X (280 chars):\n{captions.get('twitter', 'N/A')}\n\n"
                f"LINKEDIN:\n{captions.get('linkedin', 'N/A')}\n\n"
                f"YOUTUBE TITLE:\n{captions.get('youtube_title', 'N/A')}\n\n"
                f"YOUTUBE DESCRIPTION:\n{captions.get('youtube_description', 'N/A')}"
            )
            # Telegram message limit is 4096 chars — split if needed
            if len(captions_msg) <= 4096:
                await bot.send_message(chat_id, captions_msg)
            else:
                # Send platform by platform
                await bot.send_message(chat_id, f"TWITTER/X:\n{captions.get('twitter', 'N/A')}")
                await bot.send_message(chat_id, f"LINKEDIN:\n{captions.get('linkedin', 'N/A')}")
                await bot.send_message(chat_id, f"YOUTUBE TITLE:\n{captions.get('youtube_title', 'N/A')}\n\nYOUTUBE DESCRIPTION:\n{captions.get('youtube_description', 'N/A')}")
        except Exception as e:
            log.warning("Failed to send captions: %s", e)
    else:
        log.info("No captions file found at %s", captions_path)


# ── Carousel generation ───────────────────────────────────────────────────

async def process_carousel_job(job: dict):
    global current_job, current_proc
    current_job = job

    chat_id = job["chat_id"]
    bot = job["bot"]
    today = date.today().isoformat()
    prompt = job["prompt"]

    await bot.send_message(chat_id, "Carousel pipeline started. Spawning Claude Code...")
    log.info("Starting carousel job for %s", today)

    proc = await asyncio.create_subprocess_exec(
        "claude",
        "-p", prompt,
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        "--verbose",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(PROJECT_DIR),
    )
    current_proc = proc
    proc.stdout._limit = 10 * 1024 * 1024

    sent_phases = set()
    try:
        while True:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=600)
            if not line:
                break
            line_str = line.decode("utf-8", errors="replace").rstrip()
            if line_str:
                log.info("[claude-carousel] %s", line_str[:500])
            for keyword, phase_msg in CAROUSEL_PHASE_KEYWORDS:
                if keyword in line_str and phase_msg not in sent_phases:
                    sent_phases.add(phase_msg)
                    try:
                        await bot.send_message(chat_id, phase_msg)
                    except Exception:
                        pass
                    break
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        await bot.send_message(chat_id, "Carousel timed out after 10 minutes.")
        log.error("Carousel job timed out")
        current_job = None
        current_proc = None
        return

    await proc.wait()
    current_job = None
    current_proc = None

    if proc.returncode != 0:
        await bot.send_message(chat_id, f"Carousel pipeline failed (exit {proc.returncode}).")
        log.error("Carousel job failed, exit %d", proc.returncode)
        return

    # Find and send the carousel slides
    carousel_dir = OUTPUT_DIR / f"carousel-{today}"
    if not carousel_dir.exists():
        await bot.send_message(chat_id, "Pipeline completed but no carousel output found.")
        log.error("No carousel dir: %s", carousel_dir)
        return

    slide_files = sorted(carousel_dir.glob("slide-*.png"))
    if not slide_files:
        await bot.send_message(chat_id, "No slide images found in output.")
        return

    # Combine slides into a PDF
    from PIL import Image as PILImage
    pdf_path = carousel_dir / f"carousel-{today}.pdf"
    images = [PILImage.open(sf).convert("RGB") for sf in slide_files]
    images[0].save(pdf_path, "PDF", save_all=True, append_images=images[1:])
    for img in images:
        img.close()

    pdf_size_mb = pdf_path.stat().st_size / (1024 * 1024)
    await bot.send_message(chat_id, f"Uploading carousel PDF ({len(slide_files)} slides, {pdf_size_mb:.1f} MB)...")

    with open(pdf_path, "rb") as f:
        await bot.send_document(
            chat_id=chat_id,
            document=f,
            filename=f"carousel-{today}.pdf",
            caption=f"LinkedIn Carousel — {today} ({len(slide_files)} slides)",
        )

    # Send the caption if it exists
    caption_file = carousel_dir / "caption.txt"
    if caption_file.exists():
        caption_text = caption_file.read_text().strip()
        if caption_text:
            header = "--- LINKEDIN CAPTION ---\n\n"
            msg = header + caption_text
            if len(msg) <= 4096:
                await bot.send_message(chat_id, msg)
            else:
                await bot.send_message(chat_id, msg[:4096])

    log.info("Delivered carousel PDF for %s (%d slides)", today, len(slide_files))


# ── Job worker ──────────────────────────────────────────────────────────────

async def job_worker():
    while True:
        job = await job_queue.get()
        try:
            if job.get("job_type") == "carousel":
                await process_carousel_job(job)
            else:
                await process_video_job(job)
        except Exception as e:
            log.exception("Job worker error")
            try:
                await job["bot"].send_message(
                    job["chat_id"], f"Unexpected error: {str(e)[:500]}"
                )
            except Exception:
                pass
        finally:
            job_queue.task_done()


# ── Command handlers ────────────────────────────────────────────────────────

@authorized
async def cmd_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args) if context.args else ""
    if not topic:
        await update.message.reply_text(
            "Usage: /video <describe your video>\n\n"
            "Example:\n"
            "/video Explain why privacy matters in crypto\n"
            "/video Funny roast about people who share seed phrases\n"
            "/video PawPad wallet demo — download now"
        )
        return

    await update.message.reply_text("Fetching daily trending context...")
    digest_context = await fetch_daily_digest()

    queue_size = job_queue.qsize()
    job = {
        "topic": topic,
        "chat_id": update.effective_chat.id,
        "user_id": update.effective_user.id,
        "username": update.effective_user.username or "unknown",
        "bot": context.bot,
        "timestamp": datetime.now(),
        "digest_context": digest_context,
    }
    await job_queue.put(job)

    if current_job:
        pos = queue_size + 1
        await update.message.reply_text(
            f"Queued at position {pos}.\n"
            f"Topic: {topic}\n"
            f"Estimated wait: {pos * 15}-{pos * 25} min"
        )
    else:
        await update.message.reply_text(
            f"Starting video generation.\n"
            f"Topic: {topic}\n\n"
            f"This takes 10-25 minutes. I'll send progress updates."
        )

    log.info("Queued video from @%s: %s", job["username"], topic)


@authorized
async def cmd_video_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-generate today's planned video from the content calendar."""
    # Load calendar
    if not CALENDAR_PATH.exists():
        await update.message.reply_text("Content calendar not found (content-calendar.json).")
        return

    try:
        with open(CALENDAR_PATH) as f:
            calendar = json.load(f)
    except (json.JSONDecodeError, KeyError) as e:
        await update.message.reply_text(f"Failed to parse content calendar: {e}")
        return

    start_date = date.fromisoformat(calendar["start_date"])
    today = date.today()
    day_index = (today - start_date).days % 30
    entry = calendar["days"][day_index]

    product = entry["product"]
    mode = entry["mode"]
    angle = entry.get("angle", "topical")
    brief = entry["brief"]
    content_source = entry.get("source", "calendar")

    await update.message.reply_text(
        f"Today's video (Day {entry['day']}):\n"
        f"  Source: {content_source}\n"
        f"  Product: {product}\n"
        f"  Mode: {mode} | Angle: {angle}\n"
        f"  Brief: {brief[:120]}...\n\n"
        f"Fetching daily trending context..."
    )

    digest_context = await fetch_daily_digest()

    # Build output filename
    slug = re.sub(r"[^a-z0-9]+", "-", brief.lower()[:40]).strip("-")
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    output_filename = f"day{entry['day']}-{slug}-{ts}.mp4"

    if content_source == "digest":
        # Digest-driven: use live news as PRIMARY content
        if digest_context:
            prompt = build_digest_prompt(digest_context, output_filename, mode)
            topic = f"[DIGEST] [{mode}] Trending news → {product}"
        else:
            # Fallback to brief if digest API is down
            topic = f"[{product.upper()}] [{mode}] [{angle}] {brief}"
            prompt = build_prompt(topic, output_filename)
            log.warning("Digest API down — falling back to calendar brief for day %d", entry["day"])
    else:
        # Standard calendar flow
        topic = f"[{product.upper()}] [{mode}] [{angle}] {brief}"
        prompt = build_prompt(topic, output_filename, digest_context=digest_context)

    queue_size = job_queue.qsize()
    job = {
        "topic": topic,
        "prompt": prompt,
        "output_filename": output_filename,
        "chat_id": update.effective_chat.id,
        "user_id": update.effective_user.id,
        "username": update.effective_user.username or "unknown",
        "bot": context.bot,
        "timestamp": datetime.now(),
        "digest_context": digest_context,
        "content_source": content_source,
    }
    await job_queue.put(job)

    if current_job:
        pos = queue_size + 1
        await update.message.reply_text(
            f"Queued at position {pos}.\n"
            f"Estimated wait: {pos * 15}-{pos * 25} min"
        )
    else:
        await update.message.reply_text(
            "Starting video generation.\n"
            "This takes 10-25 minutes. I'll send progress updates."
        )

    log.info("Queued video_today from @%s: day %d — %s",
             update.effective_user.username or "unknown", entry["day"], brief[:80])


@authorized
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if current_job:
        elapsed = (datetime.now() - current_job["timestamp"]).seconds
        await update.message.reply_text(
            f"Generating:\n"
            f"  Topic: {current_job['topic'][:100]}\n"
            f"  By: @{current_job['username']}\n"
            f"  Elapsed: {elapsed // 60}m {elapsed % 60}s\n"
            f"  Queue: {job_queue.qsize()} waiting"
        )
    else:
        await update.message.reply_text(
            f"Idle. Queue: {job_queue.qsize()} waiting"
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ZkAGI Video Bot\n\n"
        "/video <topic> — Generate a video\n"
        "/video_today — Auto-generate today's planned video from calendar\n"
        "/carousel — Generate LinkedIn carousel from daily news\n"
        "/stop — Cancel current generation\n"
        "/status — Check generation status\n"
        "/help — This message\n\n"
        "Videos take 10-25 minutes. Carousels take 3-5 minutes.\n"
        "Daily digest trending context is fetched automatically."
    )


@authorized
async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_job, current_proc
    if current_proc and current_proc.returncode is None:
        current_proc.kill()
        await current_proc.wait()
        topic = current_job["topic"][:60] if current_job else "unknown"
        current_job = None
        current_proc = None
        # Drain the queue too
        while not job_queue.empty():
            try:
                job_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        await update.message.reply_text(f"Stopped: {topic}\nQueue cleared.")
        log.info("Job stopped by user: %s", topic)
    else:
        await update.message.reply_text("Nothing running right now.")


@authorized
async def cmd_carousel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a LinkedIn carousel from today's daily news digest."""
    await update.message.reply_text("Fetching daily trending context for carousel...")

    digest_context = await fetch_daily_digest()
    if not digest_context:
        await update.message.reply_text(
            "Could not fetch daily digest. Carousel needs trending news to generate slides.\n"
            "Try again later when the digest API is available."
        )
        return

    prompt = build_carousel_prompt(digest_context)

    queue_size = job_queue.qsize()
    job = {
        "job_type": "carousel",
        "topic": "LinkedIn carousel from daily digest",
        "prompt": prompt,
        "chat_id": update.effective_chat.id,
        "user_id": update.effective_user.id,
        "username": update.effective_user.username or "unknown",
        "bot": context.bot,
        "timestamp": datetime.now(),
    }
    await job_queue.put(job)

    if current_job:
        pos = queue_size + 1
        await update.message.reply_text(
            f"Queued at position {pos}.\n"
            f"Estimated wait: {pos * 5}-{pos * 10} min"
        )
    else:
        await update.message.reply_text(
            "Starting carousel generation.\n"
            "This takes 3-5 minutes. I'll send progress updates."
        )

    log.info("Queued carousel from @%s", update.effective_user.username or "unknown")


# ── Main ────────────────────────────────────────────────────────────────────

async def post_init(app: Application):
    """Start the job worker after the application initializes."""
    asyncio.create_task(job_worker())
    log.info("Job worker started")


def main():
    if not BOT_TOKEN:
        print("ERROR: Set TELEGRAM_BOT_TOKEN in .env or environment")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    # Add file logging
    fh = logging.FileHandler(LOG_DIR / "telegram-bot.log")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(fh)

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("video", cmd_video))
    app.add_handler(CommandHandler("video_today", cmd_video_today))
    app.add_handler(CommandHandler("videotoday", cmd_video_today))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("carousel", cmd_carousel))

    log.info("Bot starting — polling for updates...")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
