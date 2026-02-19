#!/usr/bin/env tsx
// Generate TTS audio for all scenes via VoxCPM (avatar.zkagi.ai)
// Usage: npx tsx src/scripts/generate-audio.ts --config configs/my-video.json

import fs from "fs";
import path from "path";
import { VideoConfigSchema, type VideoConfig } from "../types";
import { generateSpeech, getAudioDuration, checkTTSHealth } from "../lib/tts-client";

async function main() {
  const configIdx = process.argv.indexOf("--config");
  const configPath = configIdx !== -1 ? process.argv[configIdx + 1] : "configs/default.json";

  console.log("\n🎬 ZkAGI Video Engine — Audio Generation");
  console.log(`📄 Config: ${configPath}\n`);

  if (!fs.existsSync(configPath)) { console.error(`❌ Not found: ${configPath}`); process.exit(1); }

  const config: VideoConfig = VideoConfigSchema.parse(JSON.parse(fs.readFileSync(configPath, "utf-8")));
  console.log(`📋 "${config.title}" — ${config.scenes.length} scenes\n`);

  console.log("🔌 Checking VoxCPM server...");
  if (!(await checkTTSHealth())) { console.error("❌ Cannot reach https://avatar.zkagi.ai"); process.exit(1); }
  console.log("✅ VoxCPM is online\n");

  const audioDir = path.join("public", "audio");
  fs.mkdirSync(audioDir, { recursive: true });

  const meta: { index: number; path: string; duration: number }[] = [];

  for (let i = 0; i < config.scenes.length; i++) {
    const scene = config.scenes[i];
    const char = config.characters[scene.characterId];
    if (!char) { console.error(`❌ Character "${scene.characterId}" not found`); process.exit(1); }

    console.log(`\n── Scene ${i + 1}/${config.scenes.length} (${char.name}, ${scene.emotion}) ──`);
    const out = path.join(audioDir, `scene-${i}.wav`);

    await generateSpeech({
      refAudioPath: char.voice.refAudioPath,
      refText: char.voice.refText,
      text: scene.dialogue,
      cfgValue: char.voice.cfgValue,
      steps: char.voice.steps,
    }, out);

    const dur = await getAudioDuration(out);
    console.log(`  ⏱️  ${dur.toFixed(2)}s`);
    meta.push({ index: i, path: out, duration: dur });
  }

  const total = meta.reduce((s, m) => s + m.duration, 0);
  fs.writeFileSync(path.join(audioDir, "manifest.json"), JSON.stringify({
    config, audioMeta: meta, totalDurationFrames: Math.ceil(total * 30) + 30,
    generatedAt: new Date().toISOString(),
  }, null, 2));

  console.log(`\n✅ Done! Total: ${total.toFixed(1)}s (${Math.ceil(total * 30)} frames)`);
  console.log(`\n🎬 Next: npx remotion render ZkAGIVideo out/video.mp4 --props ${configPath}\n`);
}

main().catch((e) => { console.error("❌", e); process.exit(1); });
