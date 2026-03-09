import type { FastifyRequest, FastifyReply } from "fastify";
import { verifyJwt } from "./wallet-auth.js";
import { verifyApiKey } from "./api-key-auth.js";

/** Unified auth: accepts Bearer JWT or X-API-Key header */
export async function authGuard(request: FastifyRequest, reply: FastifyReply) {
  // Try JWT first
  const authHeader = request.headers.authorization;
  if (authHeader?.startsWith("Bearer ")) {
    try {
      const token = authHeader.slice(7);
      const payload = verifyJwt(token);
      request.userId = payload.sub;
      request.walletAddress = payload.wallet;
      return;
    } catch {
      // Fall through to API key
    }
  }

  // Try API key
  const apiKey = request.headers["x-api-key"] as string | undefined;
  if (apiKey) {
    const userId = await verifyApiKey(apiKey);
    if (userId) {
      request.userId = userId;
      return;
    }
  }

  reply.code(401).send({ error: "Unauthorized" });
}
