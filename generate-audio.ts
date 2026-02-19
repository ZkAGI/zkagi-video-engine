import fs from "fs";
import path from "path";

const TTS_ENDPOINT = "https://avatar.zkagi.ai/v1/clone-tts";

interface Scene {
  characterId: string;
  dialogue: string;
}

interface VoiceConfig {
  refAudioPath: string;
  refText: string;
  cfgValue?: string;
  steps?: string;
}

interface Character {
  id: string;
  voice: VoiceConfig;
}

interface Config {
  scenes: Scene[];
  characters: Record<string, Character>;
}

async function generateSpeech(
  refAudioPath: string,
  refText: string,
  text: string,
  outputPath: string
): Promise<void> {
  const formData = new FormData();

  const refBuffer = fs.readFileSync(refAudioPath);
  formData.append(
    "ref_audio",
    new Blob([refBuffer], { type: "audio/wav" }),
    path.basename(refAudioPath)
  );
  formData.append("ref_text", refText);
  formData.append("text", text);
  formData.append("cfg_value", "2.0");
  formData.append("steps", "15");

  console.log(`Generating: "${text.slice(0, 50)}..."`);

  const response = await fetch(TTS_ENDPOINT, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`TTS failed [${response.status}]: ${errText}`);
  }

  const audioBuffer = Buffer.from(await response.arrayBuffer());
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, audioBuffer);

  console.log(`✅ Saved: ${outputPath} (${(audioBuffer.length / 1024).toFixed(1)} KB)`);
}

async function main() {
  const configPath = process.argv[2] || "./configs/default.json";
  const config: Config = JSON.parse(fs.readFileSync(configPath, "utf-8"));

  console.log(`\n🎙️  Generating TTS for ${config.scenes.length} scenes...\n`);

  for (let i = 0; i < config.scenes.length; i++) {
    const scene = config.scenes[i];
    const character = config.characters[scene.characterId];

    if (!character) {
      console.error(`Character not found: ${scene.characterId}`);
      continue;
    }

    const voice = character.voice;
    const refAudioPath = path.resolve(voice.refAudioPath);
    const outputPath = `./public/audio/scene-${i}.wav`;

    await generateSpeech(refAudioPath, voice.refText, scene.dialogue, outputPath);
  }

  console.log("\n✅ All audio files generated!\n");
}

main().catch(console.error);
