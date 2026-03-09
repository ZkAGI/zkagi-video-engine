import { createHmac, randomBytes, createHash } from "node:crypto";
import { config } from "../config.js";

/** Generate a random API key with zkv_ prefix */
export function generateApiKey(): { raw: string; hash: string; prefix: string } {
  const bytes = randomBytes(32);
  const raw = `zkv_${bytes.toString("hex")}`;
  const hash = hashApiKey(raw);
  const prefix = raw.slice(0, 12); // "zkv_" + 8 hex chars
  return { raw, hash, prefix };
}

/** SHA-256 hash of an API key for storage */
export function hashApiKey(key: string): string {
  return createHash("sha256").update(key).digest("hex");
}

/** Create a signed URL token */
export function signUrl(videoId: string, type: "preview" | "download", expiresAt: number): string {
  const payload = `${videoId}:${type}:${expiresAt}`;
  const sig = createHmac("sha256", config.URL_SIGNING_SECRET)
    .update(payload)
    .digest("hex");
  return Buffer.from(JSON.stringify({ videoId, type, expiresAt, sig })).toString("base64url");
}

/** Verify a signed URL token */
export function verifySignedUrl(token: string): { videoId: string; type: string } | null {
  try {
    const { videoId, type, expiresAt, sig } = JSON.parse(
      Buffer.from(token, "base64url").toString()
    );
    if (Date.now() > expiresAt) return null;
    const expected = createHmac("sha256", config.URL_SIGNING_SECRET)
      .update(`${videoId}:${type}:${expiresAt}`)
      .digest("hex");
    if (sig !== expected) return null;
    return { videoId, type };
  } catch {
    return null;
  }
}
