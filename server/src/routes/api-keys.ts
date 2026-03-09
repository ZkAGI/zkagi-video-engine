import type { FastifyInstance } from "fastify";
import { authGuard } from "../middleware/auth-guard.js";
import { prisma } from "../lib/prisma.js";
import { generateApiKey } from "../lib/crypto.js";
import { CreateApiKeyBody } from "../types/index.js";

export async function apiKeyRoutes(app: FastifyInstance) {
  app.addHook("onRequest", authGuard);

  app.post("/api/v1/api-keys", async (request) => {
    const { name } = CreateApiKeyBody.parse(request.body);
    const { raw, hash, prefix } = generateApiKey();

    await prisma.apiKey.create({
      data: {
        userId: request.userId!,
        name,
        keyHash: hash,
        keyPrefix: prefix,
      },
    });

    return {
      key: raw, // shown only once
      prefix,
      name,
      message: "Save this key — it won't be shown again.",
    };
  });

  app.get("/api/v1/api-keys", async (request) => {
    const keys = await prisma.apiKey.findMany({
      where: { userId: request.userId!, revokedAt: null },
      select: { id: true, name: true, keyPrefix: true, createdAt: true },
      orderBy: { createdAt: "desc" },
    });
    return { keys };
  });

  app.delete<{ Params: { id: string } }>("/api/v1/api-keys/:id", async (request, reply) => {
    const { id } = request.params;
    const key = await prisma.apiKey.findFirst({
      where: { id, userId: request.userId! },
    });
    if (!key) {
      return reply.code(404).send({ error: "API key not found" });
    }
    await prisma.apiKey.update({
      where: { id },
      data: { revokedAt: new Date() },
    });
    return { success: true };
  });
}
