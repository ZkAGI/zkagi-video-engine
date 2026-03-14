interface PromptParams {
  topic: string;
  outputFilename: string;
  product?: string | null;
  mode: string;
  voice: string;
  customInstructions?: string | null;
  /** "calendar" (default) or "digest" */
  contentSource?: string | null;
  /** Raw digest content when contentSource is "digest" */
  digestContent?: string | null;
}

/** Build the Claude Code prompt — ported from telegram-bot.py */
export function buildPrompt(params: PromptParams): string {
  const { topic, outputFilename, customInstructions } = params;

  const customSection = customInstructions
    ? `\nADDITIONAL INSTRUCTIONS:\n${customInstructions}\n`
    : "";

  return `You are generating a complete video for the ZkAGI Video Engine.

TONE: Make this ENTERTAINING. Not boring. Not corporate. Not a lecture nobody asked for.
Write like a sharp comedian who actually knows crypto — punchy, specific, full of personality.
Use absurd analogies, roast the problem hard, drop punchlines, use named characters ("Meet Dave"),
and end with energy. If a line sounds like it belongs in a pitch deck, delete it. If the viewer
wouldn't send this to a friend, rewrite it. Every scene needs personality. Every. Single. One.

BRIEF: ${topic}
${customSection}
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
   - Import motion graphics from "../components/motion-graphics" as needed
   - For VIDEO scenes: video clip first, then Ken Burns overflow images
   - For MOTION-GRAPHIC scenes: use the component directly (no video/images), with standard overlays

   MANDATORY ENDING — EVERY video MUST end with ending clip:
   - After ALL scenes, append ONE final Sequence before global layers:
     <Sequence from={{ENDING_START}} durationInFrames={{ENDING_CLIP_FRAMES}}><AbsoluteFill><Video src={{staticFile("video/ending.mp4")}} style={{{{ width: "100%", height: "100%", objectFit: "cover" }}}} volume={{1}} startFrom={{0}} /></AbsoluteFill></Sequence>
   - ENDING_START = sum of all scene frame durations
   - ENDING_CLIP_FRAMES = 300 (ending.mp4, ~10s)
   - TOTAL_FRAMES in Root.tsx MUST include: scenes_total + 300

   URL ACCURACY — when displaying product URLs (e.g. in CtaUrl components):
   - zkterminal URL is "zkterminal.zkagi.ai" — NEVER drop the "zk" prefix
   - pawpad URL is "paw.zkagi.ai"
   - zynapse URL is "docs.zkagi.ai/docs/getting-started/zynapse"

7. RENDER: npx remotion render ZkAGIVideo output/${outputFilename} --bundle-cache=false --timeout=300000
   Only render landscape 16:9.

8. SOCIAL MEDIA CAPTIONS: After rendering, generate captions and save to output/${outputFilename}.captions.json:
   {
     "twitter": "<Twitter/X caption, max 280 characters. Punchy, attention-grabbing. Include 2-3 relevant hashtags. Include the product URL.>",
     "linkedin": "<LinkedIn post, max 3000 characters. Professional but engaging. Hook in first line. Include context about the product, why it matters, and a CTA. Use line breaks for readability. Include relevant hashtags at the end.>",
     "youtube_title": "<YouTube title, max 100 characters. SEO-friendly, compelling, includes key topic.>",
     "youtube_description": "<YouTube description, max 5000 characters. First 2 lines are most important (shown in search). Include: summary, key points, product links, timestamps if applicable, relevant hashtags.>"
   }
   - Match the tone/topic of the video
   - Twitter: short, punchy, emoji OK, must fit 280 chars
   - LinkedIn: professional, value-driven, storytelling hook
   - YouTube title: clickworthy but not clickbait
   - YouTube description: SEO-rich, include product URLs

After rendering, verify the file exists and print its size.
`;
}

/** Build digest-driven prompt — daily news is the PRIMARY content source (days 6-10) */
export function buildDigestPrompt(params: {
  digestContent: string;
  outputFilename: string;
  mode?: string;
}): string {
  const { digestContent, outputFilename, mode = "story" } = params;

  return `You are generating a complete video for the ZkAGI Video Engine.

TONE: Make this FUNNY and LIVELY. Not dry. Not corporate. Not a lecture. Think stand-up comedian
reacting to the news — punchy one-liners, absurd analogies, roasting the problem hard before
dropping the solution. The viewer should laugh at least twice and share it with a friend.
If the script reads like a press release, rewrite it. If it reads like something a bored narrator
would mumble through, rewrite it. Energy. Personality. Punchlines. Every scene.

PRIMARY CONTENT SOURCE — today's trending news digest:
${digestContent}

PRODUCT SELECTION — pick the BEST-FIT product based on the news above:
  - PawPad → wallet, security, custody, DeFi, trading agents, yield, seed phrase, keys
  - Zynapse → developer API, privacy, ZK proofs, DePIN, image/video/audio generation, content creation
  - ZkTerminal → AI playground, content creation, trading signals, prediction markets, crypto analysis
  - ZkAGI → parent brand, zero-employee enterprise, multi-product, general AI/crypto news
Pick the product whose keywords best match the trending topics.

INSTRUCTIONS:
1. Read the digest above and identify the most compelling trending story
2. Pick the best-fit product using the keyword map
3. Create a ${mode}-mode screenplay that LEADS with the trending news, then naturally weaves in the product
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

2. SCREENPLAY: Write 4-6 scenes, 15-25 words per scene. Mode: ${mode}.
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
   - CONVERSION FOCUS: Build toward the CTA: trending hook → context → product solution → proof → action

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
   - ALSO generate overflow images for scenes where TTS audio > 4.5s

5. VIDEO CLIPS: Generate ONE LTX-2 video clip per scene via LOCAL ComfyUI at http://172.18.64.1:8001
   - SKIP for motion-graphic scenes — they don't need video clips.
   - CRITICAL: Read .claude/LTX2-SKILL.md for node types and workflow
   - Save to public/scenes/scene-N-a.mp4

6. COMPOSITION: Update src/Root.tsx and src/compositions/ZkAGIVideo.tsx
   - Import reusable components from "../components"
   - Import motion graphics from "../components/motion-graphics" as needed
   - For VIDEO scenes: video clip first, then Ken Burns overflow images
   - For MOTION-GRAPHIC scenes: use the component directly, with standard overlays
   - MANDATORY ENDING: append ending.mp4 (300 frames) after all scenes
   - URL ACCURACY: zkterminal = "zkterminal.zkagi.ai" | pawpad = "paw.zkagi.ai" | zynapse = "docs.zkagi.ai/docs/getting-started/zynapse"

7. RENDER: npx remotion render ZkAGIVideo output/${outputFilename} --bundle-cache=false --timeout=300000

8. SOCIAL MEDIA CAPTIONS: Save to output/${outputFilename}.captions.json:
   {
     "twitter": "<max 280 chars, punchy, 2-3 hashtags, product URL>",
     "linkedin": "<max 3000 chars, professional, hook first line, CTA>",
     "youtube_title": "<max 100 chars, SEO-friendly>",
     "youtube_description": "<max 5000 chars, SEO-rich, product URLs>"
   }

After rendering, verify the file exists and print its size.
`;
}
