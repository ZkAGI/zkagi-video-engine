import { z } from "zod";

// ── Auth ──

export const WalletVerifyBody = z.object({
  walletAddress: z.string(),
  message: z.string(),
  signature: z.string(),
});

export const RefreshBody = z.object({
  refreshToken: z.string(),
});

// ── Videos ──

export const CreateVideoBody = z.object({
  topic: z.string().min(3).max(500),
  product: z.enum(["pawpad", "zynapse", "zkterminal"]).optional(),
  mode: z.enum(["story", "standard"]).default("standard"),
  voice: z.enum(["pad", "paw"]).default("pad"),
  format: z.enum(["16:9", "9:16"]).default("16:9"),
  customInstructions: z.string().max(2000).optional(),
});
export type CreateVideoInput = z.infer<typeof CreateVideoBody>;

export const VideoListQuery = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(50).default(20),
  status: z.enum(["QUEUED", "PROCESSING", "RENDERING", "COMPLETED", "FAILED"]).optional(),
});

// ── Payments ──

export const CheckoutBody = z.object({
  videoId: z.string().uuid(),
});

// ── API Keys ──

export const CreateApiKeyBody = z.object({
  name: z.string().min(1).max(100),
});

// ── JWT Payload ──

export interface JwtPayload {
  sub: string; // user id
  wallet: string;
  iat: number;
  exp: number;
}

// ── Fastify extensions ──

declare module "fastify" {
  interface FastifyRequest {
    userId?: string;
    walletAddress?: string;
  }
}
