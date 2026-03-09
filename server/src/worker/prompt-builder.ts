interface PromptParams {
  topic: string;
  outputFilename: string;
  product?: string | null;
  mode: string;
  voice: string;
  customInstructions?: string | null;
}

/** Build the Claude Code prompt — ported from telegram-bot.py:93-204 */
export function buildPrompt(params: PromptParams): string {
  const { topic, outputFilename, customInstructions } = params;

  const customSection = customInstructions
    ? `\nADDITIONAL INSTRUCTIONS:\n${customInstructions}\n`
    : "";

  return `You are generating a complete video for the ZkAGI Video Engine.

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
     * Product URLs: pawpad = paw.zkagi.ai | zynapse = zynapse.zkagi.ai | zkterminal = zkterminal.zkagi.ai
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

   MANDATORY ENDING — EVERY video MUST end with BrandOutro + ending clip:
   - After ALL scenes, append TWO final Sequences before global layers:
     1. BrandOutro (275 frames): <Sequence from={{ENDING_START}} durationInFrames={{ENDING_FRAMES}}><BrandOutro durationInFrames={{ENDING_FRAMES}} color={{PAD_COLOR}} /></Sequence>
     2. Ending clip (ENDING_CLIP_FRAMES): <Sequence from={{ENDING_START + ENDING_FRAMES}} durationInFrames={{ENDING_CLIP_FRAMES}}><AbsoluteFill><Video src={{staticFile("video/ending.mp4")}} style={{{{ width: "100%", height: "100%", objectFit: "cover" }}}} volume={{1}} startFrom={{0}} /></AbsoluteFill></Sequence>
   - ENDING_START = sum of all scene frame durations
   - ENDING_FRAMES = 275 (BrandOutro, 9.17s)
   - ENDING_CLIP_FRAMES = 300 (ending.mp4, ~10s)
   - TOTAL_FRAMES in Root.tsx MUST include BOTH: scenes_total + 275 + 300

   URL ACCURACY — when displaying product URLs (e.g. in CtaUrl components):
   - zkterminal URL is "zkterminal.zkagi.ai" — NEVER drop the "zk" prefix
   - pawpad URL is "paw.zkagi.ai"
   - zynapse URL is "zynapse.zkagi.ai"

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
