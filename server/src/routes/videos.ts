import type { FastifyInstance } from "fastify";
import { createReadStream, existsSync } from "node:fs";
import { authGuard } from "../middleware/auth-guard.js";
import { CreateVideoBody, VideoListQuery } from "../types/index.js";
import { createVideo, getVideo, listVideos, cancelVideo } from "../services/video-service.js";
import { verifySignedUrl } from "../lib/crypto.js";
import { prisma } from "../lib/prisma.js";

const videoObject = {
  type: "object",
  properties: {
    id: { type: "string", format: "uuid" },
    topic: { type: "string" },
    product: { type: "string", nullable: true, enum: ["pawpad", "zynapse", "zkterminal"] },
    mode: { type: "string", enum: ["standard", "story"] },
    voice: { type: "string", enum: ["pad", "paw"] },
    format: { type: "string", enum: ["16:9", "9:16"] },
    customInstructions: { type: "string", nullable: true },
    status: { type: "string", enum: ["QUEUED", "PROCESSING", "RENDERING", "COMPLETED", "FAILED"] },
    phase: { type: "string", nullable: true },
    phaseDetail: { type: "string", nullable: true },
    queuePosition: { type: "number", nullable: true },
    durationSeconds: { type: "number", nullable: true },
    fileSizeMb: { type: "number", nullable: true },
    paymentStatus: { type: "string", enum: ["UNPAID", "PENDING", "PAID", "REFUNDED"] },
    isPaid: { type: "boolean" },
    failureReason: { type: "string", nullable: true },
    previewUrl: { type: "string", nullable: true, description: "Signed URL to 5s watermarked preview (1h expiry)" },
    downloadUrl: { type: "string", nullable: true, description: "Signed URL to full video (24h expiry, requires payment)" },
    createdAt: { type: "string", format: "date-time" },
    completedAt: { type: "string", format: "date-time", nullable: true },
  },
} as const;

const security: { [k: string]: string[] }[] = [{ bearerAuth: [] }, { apiKeyAuth: [] }];

export async function videoRoutes(app: FastifyInstance) {
  // All routes require auth
  app.addHook("onRequest", authGuard);

  app.post("/api/v1/videos", {
    schema: {
      tags: ["Videos"],
      summary: "Submit video request",
      description:
        "Queue a new AI video generation job. Rate limited to 5/hour and 20/day per user.",
      security,
      body: {
        type: "object",
        required: ["topic"],
        properties: {
          topic: {
            type: "string",
            minLength: 3,
            maxLength: 500,
            description: "Video topic or brief",
            example: "How Solana achieves 65,000 TPS",
          },
          product: {
            type: "string",
            enum: ["pawpad", "zynapse", "zkterminal"],
            description: "Optional product focus",
          },
          mode: {
            type: "string",
            enum: ["standard", "story"],
            default: "standard",
            description: "Screenplay style",
          },
          voice: {
            type: "string",
            enum: ["pad", "paw"],
            default: "pad",
            description: "Narrator voice (pad = explainer tiger, paw = host tiger)",
          },
          format: {
            type: "string",
            enum: ["16:9", "9:16"],
            default: "16:9",
            description: "Video aspect ratio",
          },
          customInstructions: {
            type: "string",
            maxLength: 2000,
            description: "Optional custom instructions for the screenplay",
          },
        },
      },
      response: {
        201: videoObject,
        400: { type: "object", properties: { error: { type: "string" } } },
        429: { type: "object", properties: { error: { type: "string" } } },
      },
    },
  }, async (request, reply) => {
    const input = CreateVideoBody.parse(request.body);
    try {
      const video = await createVideo(request.userId!, input);
      reply.code(201).send(video);
    } catch (err: any) {
      reply.code(err.statusCode || 500).send({ error: err.message });
    }
  });

  app.get("/api/v1/videos", {
    schema: {
      tags: ["Videos"],
      summary: "List your videos (paginated)",
      description: "Returns a paginated list of videos for the authenticated user.",
      security,
      querystring: {
        type: "object",
        properties: {
          page: { type: "integer", minimum: 1, default: 1 },
          limit: { type: "integer", minimum: 1, maximum: 50, default: 20 },
          status: {
            type: "string",
            enum: ["QUEUED", "PROCESSING", "RENDERING", "COMPLETED", "FAILED"],
            description: "Filter by status",
          },
        },
      },
      response: {
        200: {
          type: "object",
          properties: {
            videos: { type: "array", items: videoObject },
            total: { type: "integer" },
            page: { type: "integer" },
            limit: { type: "integer" },
          },
        },
      },
    },
  }, async (request) => {
    const { page, limit, status } = VideoListQuery.parse(request.query);
    return listVideos(request.userId!, page, limit, status);
  });

  app.get<{ Params: { id: string } }>("/api/v1/videos/:id", {
    schema: {
      tags: ["Videos"],
      summary: "Get video status + URLs",
      description:
        "Retrieve a video by ID including signed preview/download URLs when available.",
      security,
      params: {
        type: "object",
        required: ["id"],
        properties: {
          id: { type: "string", format: "uuid" },
        },
      },
      response: {
        200: videoObject,
        404: { type: "object", properties: { error: { type: "string" } } },
      },
    },
  }, async (request, reply) => {
    const video = await getVideo(request.params.id, request.userId!);
    if (!video) return reply.code(404).send({ error: "Video not found" });
    return video;
  });

  app.delete<{ Params: { id: string } }>("/api/v1/videos/:id", {
    schema: {
      tags: ["Videos"],
      summary: "Cancel queued video",
      description: "Cancel a video that is still in QUEUED status. Cannot cancel videos already processing.",
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
    const ok = await cancelVideo(request.params.id, request.userId!);
    if (!ok) return reply.code(404).send({ error: "Video not found or not cancellable" });
    return { success: true };
  });
}

// These routes handle signed URL access (no auth guard — token IS the auth)
export async function videoStreamRoutes(app: FastifyInstance) {
  app.get<{ Params: { id: string }; Querystring: { token: string } }>(
    "/api/v1/videos/:id/preview",
    {
      schema: {
        tags: ["Videos"],
        summary: "Stream 5s watermarked preview",
        description:
          "Stream the 5-second watermarked preview clip. Requires a signed URL token (obtained from GET /videos/:id).",
        params: {
          type: "object",
          required: ["id"],
          properties: { id: { type: "string", format: "uuid" } },
        },
        querystring: {
          type: "object",
          required: ["token"],
          properties: {
            token: { type: "string", description: "Signed URL token (1h expiry)" },
          },
        },
        response: {
          200: { type: "string", description: "video/mp4 stream" },
          403: { type: "object", properties: { error: { type: "string" } } },
          404: { type: "object", properties: { error: { type: "string" } } },
        },
      },
    },
    async (request, reply) => {
      const result = verifySignedUrl(request.query.token);
      if (!result || result.videoId !== request.params.id || result.type !== "preview") {
        return reply.code(403).send({ error: "Invalid or expired link" });
      }

      const video = await prisma.video.findUnique({
        where: { id: request.params.id },
        select: { previewPath: true },
      });
      if (!video?.previewPath || !existsSync(video.previewPath)) {
        return reply.code(404).send({ error: "Preview not available" });
      }

      reply.header("Content-Type", "video/mp4");
      return reply.send(createReadStream(video.previewPath));
    }
  );

  app.get<{ Params: { id: string }; Querystring: { token: string } }>(
    "/api/v1/videos/:id/download",
    {
      schema: {
        tags: ["Videos"],
        summary: "Stream full video (paid)",
        description:
          "Download the full video file. Requires a signed URL token AND the video must be paid for ($5 via Stripe checkout).",
        params: {
          type: "object",
          required: ["id"],
          properties: { id: { type: "string", format: "uuid" } },
        },
        querystring: {
          type: "object",
          required: ["token"],
          properties: {
            token: { type: "string", description: "Signed URL token (24h expiry)" },
          },
        },
        response: {
          200: { type: "string", description: "video/mp4 stream (Content-Disposition: attachment)" },
          402: { type: "object", properties: { error: { type: "string" } } },
          403: { type: "object", properties: { error: { type: "string" } } },
          404: { type: "object", properties: { error: { type: "string" } } },
        },
      },
    },
    async (request, reply) => {
      const result = verifySignedUrl(request.query.token);
      if (!result || result.videoId !== request.params.id || result.type !== "download") {
        return reply.code(403).send({ error: "Invalid or expired link" });
      }

      const video = await prisma.video.findUnique({
        where: { id: request.params.id },
        select: { fullVideoPath: true, isPaid: true, topic: true },
      });
      if (!video?.isPaid) {
        return reply.code(402).send({ error: "Payment required" });
      }
      if (!video.fullVideoPath || !existsSync(video.fullVideoPath)) {
        return reply.code(404).send({ error: "Video file not found" });
      }

      const filename = video.topic.replace(/[^a-z0-9]+/gi, "-").slice(0, 50) + ".mp4";
      reply.header("Content-Type", "video/mp4");
      reply.header("Content-Disposition", `attachment; filename="${filename}"`);
      return reply.send(createReadStream(video.fullVideoPath));
    }
  );
}
