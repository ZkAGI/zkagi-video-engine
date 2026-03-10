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
  productId: z.string().uuid().optional(),
  mode: z.enum(["story", "standard"]).default("standard"),
  voice: z.enum(["pad", "paw"]).default("pad"),
  format: z.enum(["16:9", "9:16"]).default("16:9"),
  customInstructions: z.string().max(2000).optional(),
}).refine(
  (data) => !(data.product && data.productId),
  { message: "Cannot specify both 'product' and 'productId'", path: ["productId"] }
);
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

// ── Products ──

export const CreateProductBody = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(2000).optional(),
  tagline: z.string().max(200).optional(),
  websiteUrl: z.string().url().max(500).optional(),
  brandColors: z.record(z.string()).optional(),
  category: z.string().max(50).optional(),
});
export type CreateProductInput = z.infer<typeof CreateProductBody>;

export const UpdateProductBody = z.object({
  name: z.string().min(1).max(100).optional(),
  description: z.string().max(2000).optional(),
  tagline: z.string().max(200).optional(),
  websiteUrl: z.string().url().max(500).nullable().optional(),
  brandColors: z.record(z.string()).nullable().optional(),
  category: z.string().max(50).nullable().optional(),
});
export type UpdateProductInput = z.infer<typeof UpdateProductBody>;

export const ProductListQuery = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(50).default(20),
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
