import { prisma } from "../lib/prisma.js";
import { hashApiKey } from "../lib/crypto.js";

/** Look up a user by API key. Returns userId or null. */
export async function verifyApiKey(key: string): Promise<string | null> {
  if (!key.startsWith("zkv_")) return null;

  const hash = hashApiKey(key);
  const apiKey = await prisma.apiKey.findUnique({
    where: { keyHash: hash },
    select: { userId: true, revokedAt: true },
  });

  if (!apiKey || apiKey.revokedAt) return null;
  return apiKey.userId;
}
