#!/usr/bin/env tsx
/**
 * generate-script.ts
 *
 * Takes a topic/prompt and auto-generates a full video config JSON.
 * Uses Claude API to write the dialogue and pick emotions/visuals.
 *
 * Usage:
 *   npx tsx src/scripts/generate-script.ts "Explain what PawPad wallet is"
 *   npx tsx src/scripts/generate-script.ts "3 reasons ZK proofs matter for AI"
 *   npx tsx src/scripts/generate-script.ts --file brief.txt
 */

import fs from "fs";
import path from "path";

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const OUTPUT_DIR = "configs";

// ── Load character registry ──
function getAvailableCharacters(): string[] {
  const charDir = path.join("public", "characters");
  if (!fs.existsSync(charDir)) return [];
  return fs.readdirSync(charDir).filter((f) =>
    fs.statSync(path.join(charDir, f)).isDirectory()
  );
}

function getCharacterPoses(charId: string): string[] {
  const poseDir = path.join("public", "characters", charId);
  if (!fs.existsSync(poseDir)) return [];
  return fs.readdirSync(poseDir)
    .filter((f) => f.endsWith(".png"))
    .map((f) => f.replace(".png", ""));
}

function getCharacterVoice(charId: string): { refAudioPath: string; refText: string } | null {
  const voicePath = path.join("voices", `${charId}.wav`);
  if (!fs.existsSync(voicePath)) return null;

  // Try to read ref text from a sidecar .txt file
  const txtPath = path.join("voices", `${charId}.txt`);
  const refText = fs.existsSync(txtPath)
    ? fs.readFileSync(txtPath, "utf-8").trim()
    : "Reference audio transcript not provided.";

  return { refAudioPath: voicePath, refText };
}

async function generateScript(prompt: string): Promise<void> {
  if (!ANTHROPIC_API_KEY) {
    console.error("❌ Set ANTHROPIC_API_KEY environment variable");
    console.error("   export ANTHROPIC_API_KEY=sk-ant-...");
    process.exit(1);
  }

  // Discover what characters are available
  const charIds = getAvailableCharacters();
  if (charIds.length === 0) {
    console.error("❌ No characters found in public/characters/");
    process.exit(1);
  }

  const characterInfo = charIds.map((id) => {
    const poses = getCharacterPoses(id);
    const voice = getCharacterVoice(id);
    return {
      id,
      availablePoses: poses,
      hasVoice: !!voice,
      voiceRefText: voice?.refText || "N/A",
    };
  });

  console.log("\n🎬 ZkAGI Video Engine — Script Generator\n");
  console.log(`📝 Prompt: "${prompt}"`);
  console.log(`🎭 Characters: ${charIds.join(", ")}`);
  console.log(`\n🤖 Generating script via Claude...\n`);

  const systemPrompt = `You are a video scriptwriter for ZkAGI, a Swiss-Indian AI infrastructure company focused on privacy-preserving AI and blockchain.

You write short-form video scripts (30-90 seconds) featuring cute tiger mascot characters. The videos explain crypto, AI, privacy tech, and Web3 concepts in a friendly, accessible way.

Available characters:
${characterInfo.map((c) => `- "${c.id}": poses available: [${c.availablePoses.join(", ")}]`).join("\n")}

Available emotions (must match a pose file or will fallback to "neutral"):
neutral, excited, thinking, serious, explaining, celebrating, waving

Available visual types:
- "talking-head" — character on left, subtitles bottom (default, use most)
- "split-screen" — character left, big keyword text right (use for key terms)
- "text-overlay" — big text center, small character (use for emphasis)
- "character-only" — character centered big (use for intro/outro)

Rules:
1. Write 3-7 scenes. Each scene is ONE character speaking ONE thought.
2. Keep each dialogue to 1-3 sentences (15-30 words ideal for TTS).
3. Alternate between characters for variety.
4. Pick emotions that match the dialogue mood.
5. Use "split-screen" with highlightText for key technical terms.
6. Start with an excited/waving intro, end with a celebrating outro.
7. Keep it conversational, not robotic. These are friendly tigers!
8. DO NOT use apostrophes or special quotes in dialogue — use simple words.

Respond with ONLY valid JSON, no markdown, no explanation. Use this exact structure:
{
  "title": "Short Video Title",
  "scenes": [
    {
      "characterId": "character-id-here",
      "dialogue": "What the character says",
      "emotion": "excited",
      "visualType": "talking-head",
      "highlightText": "Optional Key Phrase"
    }
  ],
  "style": {
    "theme": "zkagi-brand",
    "format": "16:9",
    "showSubtitles": true,
    "showCharacterName": true,
    "transitionType": "fade"
  },
  "watermark": { "text": "ZkAGI", "show": true }
}`;

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2024-01-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 2000,
      system: systemPrompt,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    console.error(`❌ Claude API error [${response.status}]: ${err}`);
    process.exit(1);
  }

  const data = await response.json();
  const text = data.content
    .map((block: any) => (block.type === "text" ? block.text : ""))
    .join("")
    .trim();

  // Parse the generated JSON
  let scriptJson: any;
  try {
    // Strip markdown fences if present
    const clean = text.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();
    scriptJson = JSON.parse(clean);
  } catch (e) {
    console.error("❌ Failed to parse Claude response as JSON:");
    console.error(text);
    process.exit(1);
  }

  // Inject full character definitions with poses and voice config
  const characters: Record<string, any> = {};
  for (const charId of charIds) {
    const poses: Record<string, string> = {};
    const availPoses = getCharacterPoses(charId);
    for (const emotion of ["neutral", "excited", "thinking", "serious", "explaining", "celebrating", "waving"]) {
      if (availPoses.includes(emotion)) {
        poses[emotion] = `/characters/${charId}/${emotion}.png`;
      } else if (availPoses.includes("neutral")) {
        poses[emotion] = `/characters/${charId}/neutral.png`;
      }
    }

    const voice = getCharacterVoice(charId);
    characters[charId] = {
      id: charId,
      name: charId.charAt(0).toUpperCase() + charId.slice(1),
      color: charId === "paw" ? "#7C3AED" : "#06B6D4",
      role: charId === "paw" ? "host" : "explainer",
      poses,
      voice: voice
        ? { refAudioPath: voice.refAudioPath, refText: voice.refText, cfgValue: "2.0", steps: "15" }
        : { refAudioPath: `./voices/${charId}.wav`, refText: "Reference text needed", cfgValue: "2.0", steps: "15" },
    };
  }

  scriptJson.characters = characters;

  // Save config
  const slug = (scriptJson.title || "video")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 50);
  const outputPath = path.join(OUTPUT_DIR, `${slug}.json`);
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(scriptJson, null, 2));

  console.log("✅ Script generated!\n");
  console.log(`📄 Config: ${outputPath}`);
  console.log(`📋 Title: ${scriptJson.title}`);
  console.log(`🎬 Scenes: ${scriptJson.scenes.length}`);
  console.log(`\nScene breakdown:`);
  scriptJson.scenes.forEach((s: any, i: number) => {
    console.log(`  ${i + 1}. [${s.characterId}/${s.emotion}] "${s.dialogue.slice(0, 60)}..."`);
  });
  console.log(`\n🎬 Next steps:`);
  console.log(`   Preview:  npm run dev`);
  console.log(`   Generate: npm run generate -- --config ${outputPath}`);
  console.log();
}

// ── CLI ──
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log("Usage:");
    console.log('  npx tsx src/scripts/generate-script.ts "Your topic or prompt"');
    console.log('  npx tsx src/scripts/generate-script.ts --file brief.txt');
    process.exit(0);
  }

  let prompt: string;
  if (args[0] === "--file") {
    const filePath = args[1];
    if (!filePath || !fs.existsSync(filePath)) {
      console.error(`❌ File not found: ${filePath}`);
      process.exit(1);
    }
    prompt = fs.readFileSync(filePath, "utf-8").trim();
  } else {
    prompt = args.join(" ");
  }

  await generateScript(prompt);
}

main().catch((e) => {
  console.error("❌", e);
  process.exit(1);
});
