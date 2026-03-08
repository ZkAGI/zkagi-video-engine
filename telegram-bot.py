#!/usr/bin/env python3
"""
ZkAGI Video Engine — Telegram Bot

Send /video <topic> to generate a complete video via Claude Code.
Send /video_today to auto-generate today's planned video from the content calendar.
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
DIGEST_API_URL = "http://34.67.134.209:8030/digest/daily/generate"
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
    """Fetch trending daily digest from the digest API. Non-blocking — returns empty string on failure."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(DIGEST_API_URL)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", "")
            if content:
                log.info("Fetched daily digest (%d chars)", len(content))
            return content
    except Exception as e:
        log.warning("Failed to fetch daily digest: %s", e)
        return ""


# ── Claude prompt ───────────────────────────────────────────────────────────

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
   - .claude/LTX2-SKILL.md

2. SCREENPLAY: Write 4-6 scenes, 15-25 words per scene. Pick story or standard mode based on the brief.
   - VOICE: ALWAYS use "pad" character for ALL scenes. Never use "paw". pad is the ONLY voice.
   - LANGUAGE: ALL dialogue MUST be in English. ONLY English. No exceptions. No non-English words.
     If the TTS receives non-English text it produces garbage audio. Write ONLY plain English.
   - For each scene, also write a short VISUAL DESCRIPTION (what should be shown on screen).
     This visual description will be used as the text prompt for LTX-2 video generation.
   - CONVERSION FOCUS: Every video must drive action. Include in your screenplay:
     * TARGET AUDIENCE: Identify who this video is for (e.g. crypto traders, developers, solo founders)
     * CTA (Call To Action): The FINAL scene MUST end with a clear CTA — a URL, "try it now", "download today"
     * Product URLs: pawpad = paw.zkagi.ai | zynapse = zynapse.zkagi.ai | zkterminal = terminal.zkagi.ai
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
   - CRITICAL: Read .claude/LTX2-SKILL.md and use ONLY the local LTX-2 nodes listed there
   - NEVER use BFL, Flux, or any cloud/API nodes — they require login and WILL fail
   - Use ONLY these local node types: LTXAVTextEncoderLoader, EmptyLTXVLatentVideo, LTXVImgToVideo, LTXVConditioning, LTXVScheduler, LTXVPreprocess, LTXVConcatAVLatent, LTXVSeparateAVLatent, LTXVEmptyLatentAudio, CFGGuider, KSamplerSelect, SamplerCustomAdvanced, RandomNoise, CLIPTextEncode, LoadImage, VAEDecode, SaveVideo
   - Available models: ckpt_name="ltx-2-19b-dev-fp8.safetensors", text_encoder="gemma_3_12B_it.safetensors"
   - Input: scene-N-a.png as reference image
   - TEXT PROMPT: Use the scene's VISUAL DESCRIPTION as the CLIPTextEncode prompt for LTX-2.
     This drives the motion/animation of the video. Describe movement and action.
   - Save to public/scenes/scene-N-a.mp4
   - Each video clip is ~3.88s (97 frames at 25fps)

6. COMPOSITION: Update src/Root.tsx and src/compositions/ZkAGIVideo.tsx
   - DO NOT use TalkingCharacter — it has been deleted. No character overlays.

   VIDEO-FIRST VISUAL STRATEGY — video clips are the PRIMARY visual:
   - ALWAYS start each scene with the LTX-2 video clip (scene-N-a.mp4)
   - If TTS audio <= 4.5s: use ONLY the video clip. No images needed.
   - If TTS audio > 4.5s: play the video clip FIRST (~3.88s), THEN fill remaining
     time with Ken Burns images (scene-N-b.png, scene-N-c.png etc.)
   - Ken Burns images are OVERFLOW ONLY — they pad the remaining duration after the video ends.
   - Use 8-frame crossfade (SubClipFade) between video→image and image→image transitions.
   - Ken Burns directions: alternate zoom-in, pan-left, pan-right, zoom-out for variety.
   - Calculate precisely: scene_frames = audio_duration * 30 (fps), video_frames = 97

7. RENDER: npx remotion render ZkAGIVideo output/{output_filename} --bundle-cache=false --timeout=300000
   Only render landscape 16:9.

After rendering, verify the file exists and print its size.
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


# ── Core video generation ──────────────────────────────────────────────────

async def process_video_job(job: dict):
    global current_job, current_proc
    current_job = job

    topic = job["topic"]
    chat_id = job["chat_id"]
    bot = job["bot"]

    # Build output filename
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()[:40]).strip("-")
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    output_filename = f"{slug}-{ts}.mp4"
    output_path = OUTPUT_DIR / output_filename

    digest_context = job.get("digest_context", "")
    prompt = build_prompt(topic, output_filename, digest_context=digest_context)

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


# ── Job worker ──────────────────────────────────────────────────────────────

async def job_worker():
    while True:
        job = await job_queue.get()
        try:
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
    angle = entry["angle"]
    brief = entry["brief"]

    await update.message.reply_text(
        f"Today's video (Day {entry['day']}):\n"
        f"  Product: {product}\n"
        f"  Mode: {mode} | Angle: {angle}\n"
        f"  Brief: {brief}\n\n"
        f"Fetching daily trending context..."
    )

    digest_context = await fetch_daily_digest()

    topic = f"[{product.upper()}] [{mode}] [{angle}] {brief}"

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
        "/stop — Cancel current generation\n"
        "/status — Check generation status\n"
        "/help — This message\n\n"
        "Videos take 10-25 minutes to generate.\n"
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

    log.info("Bot starting — polling for updates...")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
