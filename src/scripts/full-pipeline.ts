#!/usr/bin/env tsx
// Full pipeline: TTS audio → Remotion render → MP4 output
// Usage: npx tsx src/scripts/full-pipeline.ts --config configs/my-video.json --format 16:9

import { execSync } from "child_process";
import fs from "fs";
import path from "path";

function run(cmd: string, label: string) {
  console.log(`\n${"─".repeat(50)}\n🔄 ${label}\n${"─".repeat(50)}\n`);
  execSync(cmd, { stdio: "inherit" });
}

async function main() {
  const args = process.argv.slice(2);
  const cfgIdx = args.indexOf("--config");
  const configPath = cfgIdx !== -1 ? args[cfgIdx + 1] : "configs/default.json";
  const fmtIdx = args.indexOf("--format");
  const format = fmtIdx !== -1 ? args[fmtIdx + 1] : "all";
  const ts = new Date().toISOString().slice(0, 19).replace(/[T:]/g, "-");

  console.log("╔═══════════════════════════════════════╗");
  console.log("║  ZkAGI Video Engine — Full Pipeline   ║");
  console.log("╚═══════════════════════════════════════╝");

  if (!fs.existsSync(configPath)) { console.error(`❌ ${configPath} not found`); process.exit(1); }
  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const slug = (config.title || "video").toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);

  // Step 1: Generate TTS audio
  run(`npx tsx src/scripts/generate-audio.ts --config ${configPath}`, "Step 1: Generating TTS audio via VoxCPM...");

  // Step 2: Read audio durations
  const manifest = JSON.parse(fs.readFileSync("public/audio/manifest.json", "utf-8"));
  const totalFrames = manifest.totalDurationFrames;

  // Step 3: Render
  fs.mkdirSync("output", { recursive: true });
  const formats: { id: string; label: string; suffix: string }[] = [];
  if (format === "all" || format === "16:9") formats.push({ id: "ZkAGIVideo", label: "16:9", suffix: "landscape" });
  if (format === "all" || format === "9:16") formats.push({ id: "ZkAGIVideoVertical", label: "9:16", suffix: "vertical" });
  if (format === "all" || format === "1:1") formats.push({ id: "ZkAGIVideoSquare", label: "1:1", suffix: "square" });

  for (const f of formats) {
    const out = path.join("output", `${slug}-${f.suffix}-${ts}.mp4`);
    run(`npx remotion render ${f.id} "${out}" --props "${configPath}" --timeout=300000`, `Step 2: Rendering ${f.label}...`);
  }

  console.log("\n✅ Pipeline complete! Files in output/\n");
}

main().catch((e) => { console.error("❌", e); process.exit(1); });
