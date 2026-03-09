import { mkdir, cp, symlink, readdir, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { config } from "../config.js";

const WORKSPACES_DIR = path.join(config.PROJECT_ROOT, "workspaces");

/** Files/dirs to copy (Claude modifies these) */
const COPY_ITEMS = ["src", "package.json", "tsconfig.json", "remotion.config.ts"];

/** Dirs to symlink (read-only shared assets) */
const SYMLINK_DIRS = [
  "node_modules",
  "voices",
  "products",
  ".claude",
];

/** Subdirs inside public/ to symlink */
const PUBLIC_SYMLINKS = ["sfx", "video"];

/** Subdirs inside public/ to create empty */
const PUBLIC_EMPTY_DIRS = ["scenes", "audio"];

export async function createWorkspace(videoId: string): Promise<string> {
  const workDir = path.join(WORKSPACES_DIR, videoId);
  const projectRoot = config.PROJECT_ROOT;

  // Create workspace
  await mkdir(workDir, { recursive: true });
  await mkdir(path.join(workDir, "output"), { recursive: true });
  await mkdir(path.join(workDir, "public"), { recursive: true });

  // Copy files Claude will modify
  for (const item of COPY_ITEMS) {
    const src = path.join(projectRoot, item);
    const dest = path.join(workDir, item);
    if (existsSync(src)) {
      await cp(src, dest, { recursive: true });
    }
  }

  // Symlink shared directories
  for (const dir of SYMLINK_DIRS) {
    const src = path.join(projectRoot, dir);
    const dest = path.join(workDir, dir);
    if (existsSync(src) && !existsSync(dest)) {
      await symlink(src, dest);
    }
  }

  // Symlink public subdirs (read-only shared)
  for (const dir of PUBLIC_SYMLINKS) {
    const src = path.join(projectRoot, "public", dir);
    const dest = path.join(workDir, "public", dir);
    if (existsSync(src) && !existsSync(dest)) {
      await symlink(src, dest);
    }
  }

  // Create empty public subdirs for generated content
  for (const dir of PUBLIC_EMPTY_DIRS) {
    await mkdir(path.join(workDir, "public", dir), { recursive: true });
  }

  return workDir;
}

export async function cleanupWorkspace(videoId: string): Promise<void> {
  const workDir = path.join(WORKSPACES_DIR, videoId);
  if (existsSync(workDir)) {
    await rm(workDir, { recursive: true, force: true });
  }
}

/** Find the output MP4 in a workspace */
export async function findOutputMp4(videoId: string): Promise<string | null> {
  const outputDir = path.join(WORKSPACES_DIR, videoId, "output");
  if (!existsSync(outputDir)) return null;

  const files = await readdir(outputDir);
  const mp4s = files
    .filter((f) => f.endsWith(".mp4"))
    .sort()
    .reverse();

  return mp4s.length > 0 ? path.join(outputDir, mp4s[0]) : null;
}

/** Find captions JSON for a video */
export async function findCaptionsJson(videoId: string): Promise<string | null> {
  const outputDir = path.join(WORKSPACES_DIR, videoId, "output");
  if (!existsSync(outputDir)) return null;

  const files = await readdir(outputDir);
  const captions = files.find((f) => f.endsWith(".captions.json"));
  return captions ? path.join(outputDir, captions) : null;
}
