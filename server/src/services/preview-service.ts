import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { existsSync } from "node:fs";
import path from "node:path";

const execFileAsync = promisify(execFile);

/** Generate a 5-second watermarked preview from a full video */
export async function generatePreview(fullVideoPath: string, outputDir: string): Promise<string> {
  const previewPath = path.join(outputDir, "preview.mp4");

  await execFileAsync("ffmpeg", [
    "-y",
    "-i", fullVideoPath,
    "-t", "5",
    "-vf", "drawtext=text='PREVIEW':fontsize=72:fontcolor=white@0.4:x=(w-tw)/2:y=(h-th)/2",
    "-c:v", "libx264",
    "-crf", "23",
    "-preset", "fast",
    "-c:a", "aac",
    previewPath,
  ]);

  return previewPath;
}

/** Extract a thumbnail from the video at 1 second */
export async function extractThumbnail(fullVideoPath: string, outputDir: string): Promise<string> {
  const thumbnailPath = path.join(outputDir, "thumbnail.jpg");

  await execFileAsync("ffmpeg", [
    "-y",
    "-i", fullVideoPath,
    "-ss", "1",
    "-vframes", "1",
    "-q:v", "2",
    thumbnailPath,
  ]);

  return thumbnailPath;
}

/** Get video duration in seconds via ffprobe */
export async function getVideoDuration(videoPath: string): Promise<number> {
  const { stdout } = await execFileAsync("ffprobe", [
    "-v", "quiet",
    "-show_entries", "format=duration",
    "-of", "csv=p=0",
    videoPath,
  ]);
  return parseFloat(stdout.trim());
}
