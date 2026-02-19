#!/usr/bin/env tsx
// Quick test: verify VoxCPM TTS endpoint works
// Usage: npx tsx src/scripts/test-tts.ts

import fs from "fs";
import { checkTTSHealth, generateSpeech, getAudioDuration } from "../lib/tts-client";

async function main() {
  console.log("\n🧪 VoxCPM TTS Test");
  console.log("   Endpoint: https://avatar.zkagi.ai/v1/clone_tts\n");

  const ok = await checkTTSHealth();
  console.log(ok ? "✅ Server reachable" : "❌ Server unreachable");
  if (!ok) process.exit(1);

  const refPath = "./voices/paw.wav";
  if (!fs.existsSync(refPath)) {
    console.log(`\n⚠️  Add a 3-10s voice sample to ${refPath} to test TTS generation`);
    process.exit(0);
  }

  console.log("\n🎙️  Generating test speech...");
  await generateSpeech({
    refAudioPath: refPath,
    refText: "Hi, I'm Paw, your friendly guide to privacy-preserving technology.",
    text: "Welcome to ZkAGI. Today we are building the future of private AI.",
    cfgValue: "2.0",
    steps: "15",
  }, "./output/test-tts.wav");

  const dur = await getAudioDuration("./output/test-tts.wav");
  console.log(`\n✅ Test passed! Duration: ${dur.toFixed(2)}s → ./output/test-tts.wav\n`);
}

main().catch((e) => { console.error("❌", e.message); process.exit(1); });
