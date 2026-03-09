import { prisma } from "../lib/prisma.js";

/** Phase detection keywords — ported from telegram-bot.py:214-223 */
const PHASE_KEYWORDS: [string, string, string][] = [
  ["SKILL.md", "Reading skills...", "PROCESSING"],
  ["screenplay", "Writing screenplay...", "PROCESSING"],
  ["clone-tts", "Generating TTS audio...", "PROCESSING"],
  ["45.251.34.28", "Generating reference images...", "PROCESSING"],
  ["zynapse.zkagi.ai", "Generating reference images (fallback)...", "PROCESSING"],
  ["172.18.64.1:8001", "Generating video clips via ComfyUI...", "PROCESSING"],
  ["ZkAGIVideo.tsx", "Editing Remotion composition...", "PROCESSING"],
  ["remotion render", "Rendering final video...", "RENDERING"],
  ["captions.json", "Generating captions...", "RENDERING"],
];

export class ProgressTracker {
  private videoId: string;
  private sentPhases = new Set<string>();

  constructor(videoId: string) {
    this.videoId = videoId;
  }

  /** Parse a line of Claude output and update progress if a phase keyword matches */
  async processLine(line: string): Promise<void> {
    for (const [keyword, phaseDetail, status] of PHASE_KEYWORDS) {
      if (line.includes(keyword) && !this.sentPhases.has(phaseDetail)) {
        this.sentPhases.add(phaseDetail);
        await prisma.video.update({
          where: { id: this.videoId },
          data: {
            phase: keyword,
            phaseDetail,
            status: status as any,
          },
        });
        break;
      }
    }
  }
}
