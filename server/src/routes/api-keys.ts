import type { FastifyInstance } from "fastify";
import { authGuard } from "../middleware/auth-guard.js";
import { prisma } from "../lib/prisma.js";
import { generateApiKey } from "../lib/crypto.js";
import { CreateApiKeyBody } from "../types/index.js";

const security: { [k: string]: string[] }[] = [{ bearerAuth: [] }, { apiKeyAuth: [] }];

export async function apiKeyRoutes(app: FastifyInstance) {
  app.addHook("onRequest", authGuard);

  app.post("/api/v1/api-keys", {
    schema: {
      tags: ["API Keys"],
      summary: "Create API key",
      description:
        "Generate a new API key for programmatic access. The full key is returned ONLY once — save it immediately.",
      security,
      body: {
        type: "object",
        required: ["name"],
        properties: {
          name: {
            type: "string",
            minLength: 1,
            maxLength: 100,
            description: "Human-friendly label for this key",
            example: "My CI/CD pipeline",
          },
        },
      },
      response: {
        200: {
          type: "object",
          properties: {
            key: { type: "string", description: "Full API key (shown only once!)", example: "zkv_a1b2c3d4..." },
            prefix: { type: "string", description: "Key prefix for identification", example: "zkv_a1b2c3d4" },
            name: { type: "string" },
            message: { type: "string" },
          },
        },
      },
    },
  }, async (request) => {
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

  app.get("/api/v1/api-keys", {
    schema: {
      tags: ["API Keys"],
      summary: "List your API keys",
      description: "Returns all active (non-revoked) API keys for the authenticated user.",
      security,
      response: {
        200: {
          type: "object",
          properties: {
            keys: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  id: { type: "string", format: "uuid" },
                  name: { type: "string" },
                  keyPrefix: { type: "string", example: "zkv_a1b2c3d4" },
                  createdAt: { type: "string", format: "date-time" },
                },
              },
            },
          },
        },
      },
    },
  }, async (request) => {
    const keys = await prisma.apiKey.findMany({
      where: { userId: request.userId!, revokedAt: null },
      select: { id: true, name: true, keyPrefix: true, createdAt: true },
      orderBy: { createdAt: "desc" },
    });
    return { keys };
  });

  app.delete<{ Params: { id: string } }>("/api/v1/api-keys/:id", {
    schema: {
      tags: ["API Keys"],
      summary: "Revoke API key",
      description: "Soft-deletes an API key. The key will immediately stop working.",
      security,
      params: {
        type: "object",
        required: ["id"],
        properties: {
          id: { type: "string", format: "uuid" },
        },
      },
      response: {
        200: {
          type: "object",
          properties: { success: { type: "boolean" } },
        },
        404: { type: "object", properties: { error: { type: "string" } } },
      },
    },
  }, async (request, reply) => {
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
