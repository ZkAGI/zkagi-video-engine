import type { FastifyInstance } from "fastify";
import { createReadStream, existsSync } from "node:fs";
import { authGuard } from "../middleware/auth-guard.js";
import { CreateVideoBody, VideoListQuery } from "../types/index.js";
import { createVideo, getVideo, listVideos, cancelVideo } from "../services/video-service.js";
import { verifySignedUrl } from "../lib/crypto.js";
import { prisma } from "../lib/prisma.js";

export async function videoRoutes(app: FastifyInstance) {
  // All routes require auth
  app.addHook("onRequest", authGuard);

  app.post("/api/v1/videos", async (request, reply) => {
    const input = CreateVideoBody.parse(request.body);
    try {
      const video = await createVideo(request.userId!, input);
      reply.code(201).send(video);
    } catch (err: any) {
      reply.code(err.statusCode || 500).send({ error: err.message });
    }
  });

  app.get("/api/v1/videos", async (request) => {
    const { page, limit, status } = VideoListQuery.parse(request.query);
    return listVideos(request.userId!, page, limit, status);
  });

  app.get<{ Params: { id: string } }>("/api/v1/videos/:id", async (request, reply) => {
    const video = await getVideo(request.params.id, request.userId!);
    if (!video) return reply.code(404).send({ error: "Video not found" });
    return video;
  });

  app.delete<{ Params: { id: string } }>("/api/v1/videos/:id", async (request, reply) => {
    const ok = await cancelVideo(request.params.id, request.userId!);
    if (!ok) return reply.code(404).send({ error: "Video not found or not cancellable" });
    return { success: true };
  });
}

// These routes handle signed URL access (no auth guard — token IS the auth)
export async function videoStreamRoutes(app: FastifyInstance) {
  app.get<{ Params: { id: string }; Querystring: { token: string } }>(
    "/api/v1/videos/:id/preview",
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
