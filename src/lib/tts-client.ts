import fs from "fs";
import path from "path";

// ══════════════════════════════════════════════
// VoxCPM TTS Client
// Endpoint: POST https://avatar.zkagi.ai/v1/clone-tts
// Voice cloning from 3-10s reference audio
// ══════════════════════════════════════════════

const TTS_BASE_URL = process.env.TTS_URL || "https://avatar.zkagi.ai";
const TTS_ENDPOINT = `${TTS_BASE_URL}/v1/clone-tts`;

export interface TTSRequest {
  refAudioPath: string;  // Path to 3-10s WAV reference
  refText: string;       // Transcript of the reference audio
  text: string;          // Text to generate speech for
  cfgValue?: string;     // CFG scale (default "2.0")
  steps?: string;        // Inference steps (default "15")
  normalize?: string;    // Normalize audio
  denoise?: string;      // Denoise audio
}

export interface TTSResult {
  outputPath: string;
  sizeKB: number;
}

/**
 * Generate speech via VoxCPM voice cloning endpoint.
 *
 * API signature (from avatar.zkagi.ai/docs):
 *   POST /v1/clone-tts  (multipart/form-data)
 *   - ref_audio  (binary, required)
 *   - ref_text   (string, required)
 *   - text       (string, required)
 *   - cfg_value  (string|null, optional)
 *   - steps      (string|null, optional)
 *   - normalize  (string|null, optional)
 *   - denoise    (string|null, optional)
 */
export async function generateSpeech(
  request: TTSRequest,
  outputPath: string
): Promise<TTSResult> {
  if (!fs.existsSync(request.refAudioPath)) {
    throw new Error(`Reference audio not found: ${request.refAudioPath}`);
  }

  const formData = new FormData();

  // ref_audio (required) — binary voice sample
  const refBuffer = fs.readFileSync(request.refAudioPath);
  const ext = path.extname(request.refAudioPath).toLowerCase();
  const mime = ext === ".mp3" ? "audio/mpeg" : "audio/wav";
  formData.append("ref_audio", new Blob([refBuffer], { type: mime }), path.basename(request.refAudioPath));

  // ref_text (required) — transcript of reference audio
  formData.append("ref_text", request.refText);

  // text (required) — what to generate
  formData.append("text", request.text);

  // Optional tuning params
  if (request.cfgValue) formData.append("cfg_value", request.cfgValue);
  if (request.steps) formData.append("steps", request.steps);
  if (request.normalize) formData.append("normalize", request.normalize);
  if (request.denoise) formData.append("denoise", request.denoise);

  console.log(`  🎙️  "${request.text.slice(0, 60)}${request.text.length > 60 ? "..." : ""}"`);

  const response = await fetch(TTS_ENDPOINT, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => "Unknown error");
    throw new Error(`TTS failed [${response.status}]: ${errText}`);
  }

  const audioBuffer = Buffer.from(await response.arrayBuffer());
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, audioBuffer);

  const sizeKB = audioBuffer.length / 1024;
  console.log(`  ✅ ${outputPath} (${sizeKB.toFixed(1)} KB)`);

  return { outputPath, sizeKB };
}

/** Get audio duration via ffprobe (falls back to estimate) */
export async function getAudioDuration(filePath: string): Promise<number> {
  const { execSync } = await import("child_process");
  try {
    const result = execSync(
      `ffprobe -v error -show_entries format=duration -of csv=p=0 "${filePath}"`,
      { encoding: "utf-8" }
    );
    return parseFloat(result.trim());
  } catch {
    // Rough estimate: ~16KB/s for WAV
    const stats = fs.statSync(filePath);
    return stats.size / 1024 / 16;
  }
}

/** Health check */
export async function checkTTSHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${TTS_BASE_URL}/docs`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}
