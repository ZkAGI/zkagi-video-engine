import { Queue } from "bullmq";
import { prisma } from "../lib/prisma.js";
import type { CreateVideoInput } from "../types/index.js";
import { signUrl } from "../lib/crypto.js";
import { config } from "../config.js";

const videoQueue = new Queue("video-generation", { connection: { url: config.REDIS_URL } });

export async function createVideo(userId: string, input: CreateVideoInput) {
  // Rate limit: 5 videos/hour, 20/day
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
  const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);

  const [hourCount, dayCount] = await Promise.all([
    prisma.video.count({
      where: { userId, createdAt: { gte: oneHourAgo } },
    }),
    prisma.video.count({
      where: { userId, createdAt: { gte: oneDayAgo } },
    }),
  ]);

  if (hourCount >= 5) {
    throw Object.assign(new Error("Rate limit: max 5 videos per hour"), { statusCode: 429 });
  }
  if (dayCount >= 20) {
    throw Object.assign(new Error("Rate limit: max 20 videos per day"), { statusCode: 429 });
  }

  // Count queued videos for position
  const queuedCount = await prisma.video.count({
    where: { status: "QUEUED" },
  });

  // Validate productId ownership if provided
  if (input.productId) {
    const product = await prisma.product.findFirst({
      where: { id: input.productId, userId, isActive: true },
    });
    if (!product) {
      throw Object.assign(new Error("Product not found"), { statusCode: 404 });
    }
  }

  const video = await prisma.video.create({
    data: {
      userId,
      topic: input.topic,
      product: input.product,
      productId: input.productId,
      mode: input.mode,
      voice: input.voice,
      format: input.format,
      customInstructions: input.customInstructions,
      queuePosition: queuedCount + 1,
    },
  });

  // Add to BullMQ
  await videoQueue.add(
    "generate",
    { videoId: video.id },
    {
      jobId: video.id,
      attempts: 2,
      backoff: { type: "exponential", delay: 60_000 },
      removeOnComplete: 100,
      removeOnFail: 50,
    }
  );

  return video;
}

export async function getVideo(videoId: string, userId: string) {
  const video = await prisma.video.findFirst({
    where: { id: videoId, userId },
  });
  if (!video) return null;

  // Generate signed URLs
  let previewUrl: string | undefined;
  let downloadUrl: string | undefined;

  if (video.previewPath) {
    const token = signUrl(video.id, "preview", Date.now() + 60 * 60 * 1000); // 1hr
    previewUrl = `/api/v1/videos/${video.id}/preview?token=${token}`;
  }
  if (video.isPaid && video.fullVideoPath) {
    const token = signUrl(video.id, "download", Date.now() + 24 * 60 * 60 * 1000); // 24hr
    downloadUrl = `/api/v1/videos/${video.id}/download?token=${token}`;
  }

  return {
    id: video.id,
    topic: video.topic,
    product: video.product,
    productId: video.productId,
    mode: video.mode,
    voice: video.voice,
    format: video.format,
    status: video.status,
    phase: video.phase,
    phaseDetail: video.phaseDetail,
    queuePosition: video.queuePosition,
    durationSeconds: video.durationSeconds,
    fileSizeMb: video.fileSizeMb,
    captions: video.captions,
    paymentStatus: video.paymentStatus,
    isPaid: video.isPaid,
    failureReason: video.failureReason,
    previewUrl,
    downloadUrl,
    createdAt: video.createdAt,
    startedAt: video.startedAt,
    completedAt: video.completedAt,
  };
}

export async function listVideos(userId: string, page: number, limit: number, status?: string) {
  const where: any = { userId };
  if (status) where.status = status;

  const [videos, total] = await Promise.all([
    prisma.video.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip: (page - 1) * limit,
      take: limit,
      select: {
        id: true,
        topic: true,
        product: true,
        status: true,
        phase: true,
        paymentStatus: true,
        isPaid: true,
        durationSeconds: true,
        createdAt: true,
        completedAt: true,
      },
    }),
    prisma.video.count({ where }),
  ]);

  return {
    videos,
    pagination: {
      page,
      limit,
      total,
      pages: Math.ceil(total / limit),
    },
  };
}

export async function cancelVideo(videoId: string, userId: string) {
  const video = await prisma.video.findFirst({
    where: { id: videoId, userId, status: "QUEUED" },
  });
  if (!video) return false;

  await prisma.video.update({
    where: { id: videoId },
    data: { status: "FAILED", failureReason: "Cancelled by user" },
  });

  // Remove from queue
  const job = await videoQueue.getJob(videoId);
  if (job) await job.remove();

  return true;
}
