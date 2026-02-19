#!/usr/bin/env tsx
/**
 * create-video.ts
 *
 * THE ONE COMMAND. Give it a prompt, get back a video.
 *
 * Usage:
 *   npx tsx src/scripts/create-video.ts "Explain what PawPad wallet is"
 *   npx tsx src/scripts/create-video.ts "3 reasons ZK proofs matter" --format 9:16
 *   npx tsx src/scripts/create-video.ts --file brief.txt
 */

import { execSync } from "child_process";
import fs from "fs";
import path from "path";

function run(cmd: string, label: string) {
  console.log(`\n${"═".repeat(50)}`);
  console.log(`  ${label}`);
  console.log(`${"═".repeat(50)}\n`);
  execSync(cmd, { stdio: "inherit" });
}

async function main() {
  const args = process.argv.slice(2);

  // Parse format flag
  const fmtIdx = args.indexOf("--format");
  const format = fmtIdx !== -1 ? args.splice(fmtIdx, 2)[1] : "all";

  // Parse file flag
  const fileIdx = args.indexOf("--file");
  let prompt: string;
  if (fileIdx !== -1) {
    const filePath = args[fileIdx + 1];
    prompt = fs.readFileSync(filePath, "utf-8").trim();
  } else {
    prompt = args.join(" ");
  }

  if (!prompt) {
    console.log(`
╔═══════════════════════════════════════════════╗
║  ZkAGI Video Engine — Create Video            ║
╚═══════════════════════════════════════════════╝

Usage:
  npx tsx src/scripts/create-video.ts "Your topic here"
  npx tsx src/scripts/create-video.ts "Topic" --format 9:16
  npx tsx src/scripts/create-video.ts --file brief.txt

Examples:
  npx tsx src/scripts/create-video.ts "Explain PawPad wallet in 60 seconds"
  npx tsx src/scripts/create-video.ts "Top 3 reasons ZK proofs matter for AI privacy"
  npx tsx src/scripts/create-video.ts "Weekly crypto update: BTC at 120k, ETH ETFs surging"
`);
    process.exit(0);
  }

  console.log("╔═══════════════════════════════════════════════╗");
  console.log("║  🎬 ZkAGI Video Engine — Full Auto Pipeline  ║");
  console.log("╚═══════════════════════════════════════════════╝");
  console.log(`\n📝 Prompt: "${prompt}"`);
  console.log(`🖼️  Format: ${format}\n`);

  // Step 1: Generate script via Claude
  run(
    `npx tsx src/scripts/generate-script.ts ${JSON.stringify(prompt)}`,
    "Step 1/3: 🤖 Generating script via Claude..."
  );

  // Find the latest config file (just generated)
  const configs = fs.readdirSync("configs")
    .filter((f) => f.endsWith(".json") && f !== "template.json" && f !== "default.json")
    .map((f) => ({ name: f, time: fs.statSync(path.join("configs", f)).mtimeMs }))
    .sort((a, b) => b.time - a.time);

  if (configs.length === 0) {
    console.error("❌ No config generated");
    process.exit(1);
  }

  const configPath = path.join("configs", configs[0].name);
  console.log(`\n📄 Using config: ${configPath}`);

  // Step 2: Generate TTS audio
  run(
    `npx tsx src/scripts/generate-audio.ts --config ${configPath}`,
    "Step 2/3: 🎙️ Generating TTS audio via VoxCPM..."
  );

  // Step 3: Render video
  const manifest = JSON.parse(fs.readFileSync("public/audio/manifest.json", "utf-8"));
  const totalFrames = manifest.totalDurationFrames;

  fs.mkdirSync("output", { recursive: true });

  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const slug = (config.title || "video").toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
  const ts = new Date().toISOString().slice(0, 10);

  const formats: { id: string; label: string; suffix: string }[] = [];
  if (format === "all" || format === "16:9") formats.push({ id: "ZkAGIVideo", label: "16:9 Landscape", suffix: "landscape" });
  if (format === "all" || format === "9:16") formats.push({ id: "ZkAGIVideoVertical", label: "9:16 Vertical", suffix: "vertical" });
  if (format === "all" || format === "1:1") formats.push({ id: "ZkAGIVideoSquare", label: "1:1 Square", suffix: "square" });

  for (const f of formats) {
    const outFile = path.join("output", `${slug}-${f.suffix}-${ts}.mp4`);
    run(
      `npx remotion render ${f.id} "${outFile}" --props "${configPath}" --frames=0-${totalFrames}`,
      `Step 3/3: 🎬 Rendering ${f.label}...`
    );
  }

  console.log("\n╔═══════════════════════════════════════════════╗");
  console.log("║           ✅ Video Created!                   ║");
  console.log("╚═══════════════════════════════════════════════╝\n");
  console.log(`📁 Files in output/:`);
  formats.forEach((f) => {
    console.log(`   🎬 ${slug}-${f.suffix}-${ts}.mp4`);
  });
  console.log();
}

main().catch((e) => { console.error("❌", e); process.exit(1); });
