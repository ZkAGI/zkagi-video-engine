import type { FastifyInstance } from "fastify";
import { prisma } from "../lib/prisma.js";
import { redis } from "../lib/redis.js";
import { config } from "../config.js";

export async function healthRoutes(app: FastifyInstance) {
  app.get("/api/v1/health", async (_request, reply) => {
    const checks: Record<string, { status: string; latencyMs?: number }> = {};

    // Database
    const dbStart = Date.now();
    try {
      await prisma.$queryRaw`SELECT 1`;
      checks.database = { status: "ok", latencyMs: Date.now() - dbStart };
    } catch {
      checks.database = { status: "error", latencyMs: Date.now() - dbStart };
    }

    // Redis
    const redisStart = Date.now();
    try {
      await redis.ping();
      checks.redis = { status: "ok", latencyMs: Date.now() - redisStart };
    } catch {
      checks.redis = { status: "error", latencyMs: Date.now() - redisStart };
    }

    // ComfyUI
    const comfyStart = Date.now();
    try {
      const resp = await fetch(`${config.COMFYUI_URL}/system_stats`);
      checks.comfyui = {
        status: resp.ok ? "ok" : "error",
        latencyMs: Date.now() - comfyStart,
      };
    } catch {
      checks.comfyui = { status: "unreachable", latencyMs: Date.now() - comfyStart };
    }

    const allOk = Object.values(checks).every((c) => c.status === "ok");
    reply.code(allOk ? 200 : 503).send({
      status: allOk ? "healthy" : "degraded",
      checks,
      timestamp: new Date().toISOString(),
    });
  });
}
