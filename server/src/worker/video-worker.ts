import { Worker } from "bullmq";
import { spawn } from "node:child_process";
import { readFile, stat, cp } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { prisma } from "../lib/prisma.js";
import { config } from "../config.js";
import { buildPrompt } from "./prompt-builder.js";
import { ProgressTracker } from "./progress-tracker.js";
import {
  createWorkspace,
  cleanupWorkspace,
  findOutputMp4,
  findCaptionsJson,
} from "./workspace-manager.js";
import { generatePreview, extractThumbnail, getVideoDuration } from "../services/preview-service.js";

const MAX_TIMEOUT_MS = 40 * 60 * 1000; // 40 minutes
const PERMANENT_OUTPUT = path.join(config.PROJECT_ROOT, "output", "videos");

async function ensureOutputDir() {
  const { mkdir } = await import("node:fs/promises");
  await mkdir(PERMANENT_OUTPUT, { recursive: true });
}

/** Pre-flight: check ComfyUI is reachable */
async function checkComfyUI(): Promise<boolean> {
  try {
    const resp = await fetch(`${config.COMFYUI_URL}/system_stats`);
    return resp.ok;
  } catch {
    return false;
  }
}

const worker = new Worker(
  "video-generation",
  async (job) => {
    const { videoId } = job.data;
    const log = (msg: string) => console.log(`[worker:${videoId.slice(0, 8)}] ${msg}`);

    log("Starting job");

    // Pre-flight check
    const comfyOk = await checkComfyUI();
    if (!comfyOk) {
      throw new Error("ComfyUI unreachable — will retry");
    }

    // Load video record
    const video = await prisma.video.findUnique({ where: { id: videoId } });
    if (!video) throw new Error("Video record not found");

    // Update status
    await prisma.video.update({
      where: { id: videoId },
      data: { status: "PROCESSING", startedAt: new Date() },
    });

    // Create isolated workspace
    const workDir = await createWorkspace(videoId);
    log(`Workspace: ${workDir}`);

    // Build output filename
    const slug = video.topic
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .slice(0, 40)
      .replace(/-$/, "");
    const ts = new Date().toISOString().slice(0, 16).replace(/[T:]/g, "-");
    const outputFilename = `${slug}-${ts}.mp4`;

    // Build prompt
    const prompt = buildPrompt({
      topic: video.topic,
      outputFilename,
      product: video.product,
      mode: video.mode,
      voice: video.voice,
      customInstructions: video.customInstructions,
    });

    // Spawn Claude Code CLI
    const tracker = new ProgressTracker(videoId);

    await new Promise<void>((resolve, reject) => {
      const proc = spawn(
        "claude",
        ["-p", prompt, "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"],
        {
          cwd: workDir,
          stdio: ["ignore", "pipe", "pipe"],
        }
      );

      let timeoutHandle = setTimeout(() => {
        proc.kill("SIGKILL");
        reject(new Error("Job timed out after 40 minutes"));
      }, MAX_TIMEOUT_MS);

      const processStream = (stream: NodeJS.ReadableStream) => {
        let buffer = "";
        stream.on("data", (chunk: Buffer) => {
          buffer += chunk.toString();
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (line.trim()) {
              log(line.slice(0, 200));
              tracker.processLine(line).catch(() => {});
            }
          }
        });
      };

      processStream(proc.stdout!);
      processStream(proc.stderr!);

      proc.on("close", (code) => {
        clearTimeout(timeoutHandle);
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Claude exited with code ${code}`));
        }
      });

      proc.on("error", (err) => {
        clearTimeout(timeoutHandle);
        reject(err);
      });
    });

    // Find output MP4
    const mp4Path = await findOutputMp4(videoId);
    if (!mp4Path) {
      throw new Error("Pipeline completed but no MP4 found");
    }

    log(`Output: ${mp4Path}`);

    // Move to permanent storage
    await ensureOutputDir();
    const permanentPath = path.join(PERMANENT_OUTPUT, `${videoId}.mp4`);
    await cp(mp4Path, permanentPath);

    // Generate preview + thumbnail
    const previewPath = await generatePreview(permanentPath, PERMANENT_OUTPUT);
    const permanentPreview = path.join(PERMANENT_OUTPUT, `${videoId}-preview.mp4`);
    await cp(previewPath, permanentPreview);

    const thumbnailPath = await extractThumbnail(permanentPath, PERMANENT_OUTPUT);
    const permanentThumbnail = path.join(PERMANENT_OUTPUT, `${videoId}-thumb.jpg`);
    await cp(thumbnailPath, permanentThumbnail);

    // Get duration + file size
    const duration = await getVideoDuration(permanentPath);
    const fileInfo = await stat(permanentPath);
    const fileSizeMb = fileInfo.size / (1024 * 1024);

    // Load captions if they exist
    let captions = null;
    const captionsPath = await findCaptionsJson(videoId);
    if (captionsPath && existsSync(captionsPath)) {
      try {
        captions = JSON.parse(await readFile(captionsPath, "utf-8"));
      } catch {
        log("Failed to parse captions");
      }
    }

    // Update DB
    await prisma.video.update({
      where: { id: videoId },
      data: {
        status: "COMPLETED",
        fullVideoPath: permanentPath,
        previewPath: permanentPreview,
        thumbnailPath: permanentThumbnail,
        durationSeconds: duration,
        fileSizeMb,
        captions,
        completedAt: new Date(),
        phase: "complete",
        phaseDetail: "Video ready",
      },
    });

    // Cleanup workspace
    await cleanupWorkspace(videoId);

    log(`Completed in ${((Date.now() - (video.startedAt?.getTime() || Date.now())) / 60000).toFixed(1)} minutes`);
  },
  {
    connection: { url: config.REDIS_URL },
    concurrency: 1,
    removeOnComplete: { count: 100 },
    removeOnFail: { count: 50 },
  }
);

worker.on("failed", async (job, err) => {
  const videoId = job?.data?.videoId;
  if (videoId) {
    console.error(`[worker:${videoId.slice(0, 8)}] Failed: ${err.message}`);
    await prisma.video.update({
      where: { id: videoId },
      data: {
        status: "FAILED",
        failureReason: err.message.slice(0, 500),
        retryCount: { increment: 1 },
      },
    });
    // Cleanup workspace on failure too
    await cleanupWorkspace(videoId).catch(() => {});
  }
});

worker.on("completed", (job) => {
  console.log(`[worker] Job ${job.id} completed`);
});

console.log("Video worker started — waiting for jobs...");

export { worker };
