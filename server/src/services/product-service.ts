import { mkdir, unlink } from "node:fs/promises";
import { join } from "node:path";
import { pipeline } from "node:stream/promises";
import { createWriteStream } from "node:fs";
import { randomUUID } from "node:crypto";
import { prisma } from "../lib/prisma.js";
import { signUrl } from "../lib/crypto.js";
import { config } from "../config.js";
import type { CreateProductInput, UpdateProductInput } from "../types/index.js";
import type { AssetType } from "@prisma/client";
import type { MultipartFile } from "@fastify/multipart";

const MAX_PRODUCTS_PER_USER = 20;

const ASSET_LIMITS: Record<AssetType, { maxBytes: number; maxCount: number; extensions: string[]; mimeTypes: string[] }> = {
  IMAGE: {
    maxBytes: 10 * 1024 * 1024, // 10MB
    maxCount: 10,
    extensions: [".png", ".jpg", ".jpeg", ".webp"],
    mimeTypes: ["image/png", "image/jpeg", "image/webp"],
  },
  VOICE: {
    maxBytes: 5 * 1024 * 1024, // 5MB
    maxCount: 1, // replaces existing
    extensions: [".wav", ".mp3"],
    mimeTypes: ["audio/wav", "audio/mpeg", "audio/x-wav"],
  },
  VIDEO: {
    maxBytes: 100 * 1024 * 1024, // 100MB
    maxCount: 5,
    extensions: [".mp4", ".webm"],
    mimeTypes: ["video/mp4", "video/webm"],
  },
};

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 60);
}

function uploadsDir(userId: string, productId: string, assetType: string): string {
  return join(config.PROJECT_ROOT, "uploads", userId, productId, assetType.toLowerCase() + "s");
}

// ── CRUD ──

export async function createProduct(userId: string, input: CreateProductInput) {
  const count = await prisma.product.count({ where: { userId, isActive: true } });
  if (count >= MAX_PRODUCTS_PER_USER) {
    throw Object.assign(new Error(`Maximum ${MAX_PRODUCTS_PER_USER} products per user`), { statusCode: 400 });
  }

  let slug = slugify(input.name);
  const existing = await prisma.product.findUnique({ where: { userId_slug: { userId, slug } } });
  if (existing) {
    slug = `${slug}-${randomUUID().slice(0, 6)}`;
  }

  const product = await prisma.product.create({
    data: {
      userId,
      name: input.name,
      slug,
      description: input.description,
      tagline: input.tagline,
      websiteUrl: input.websiteUrl,
      brandColors: input.brandColors ?? undefined,
      category: input.category,
    },
  });

  // Pre-create upload directories
  await Promise.all(
    ["images", "voices", "videos"].map((dir) =>
      mkdir(join(config.PROJECT_ROOT, "uploads", userId, product.id, dir), { recursive: true })
    )
  );

  return product;
}

export async function getProduct(productId: string, userId: string) {
  const product = await prisma.product.findFirst({
    where: { id: productId, userId, isActive: true },
    include: { assets: { orderBy: { createdAt: "asc" } } },
  });
  if (!product) return null;

  // Generate signed URLs for assets
  const assets = product.assets.map((asset) => {
    const token = signUrl(asset.id, "asset", Date.now() + 60 * 60 * 1000); // 1hr
    return {
      id: asset.id,
      type: asset.type,
      filename: asset.filename,
      mimeType: asset.mimeType,
      fileSizeBytes: asset.fileSizeBytes,
      isPrimary: asset.isPrimary,
      fileUrl: `/api/v1/products/${productId}/assets/${asset.id}/file?token=${token}`,
      createdAt: asset.createdAt,
    };
  });

  return {
    id: product.id,
    name: product.name,
    slug: product.slug,
    description: product.description,
    tagline: product.tagline,
    websiteUrl: product.websiteUrl,
    brandColors: product.brandColors,
    category: product.category,
    isActive: product.isActive,
    assets,
    createdAt: product.createdAt,
    updatedAt: product.updatedAt,
  };
}

export async function listProducts(userId: string, page: number, limit: number) {
  const where = { userId, isActive: true };

  const [products, total] = await Promise.all([
    prisma.product.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip: (page - 1) * limit,
      take: limit,
      include: {
        _count: { select: { assets: true, videos: true } },
      },
    }),
    prisma.product.count({ where }),
  ]);

  return {
    products: products.map((p) => ({
      id: p.id,
      name: p.name,
      slug: p.slug,
      description: p.description,
      tagline: p.tagline,
      category: p.category,
      assetCount: p._count.assets,
      videoCount: p._count.videos,
      createdAt: p.createdAt,
      updatedAt: p.updatedAt,
    })),
    pagination: { page, limit, total, pages: Math.ceil(total / limit) },
  };
}

export async function updateProduct(productId: string, userId: string, input: UpdateProductInput) {
  const product = await prisma.product.findFirst({
    where: { id: productId, userId, isActive: true },
  });
  if (!product) return null;

  // If name changed, regenerate slug
  let slug: string | undefined;
  if (input.name && input.name !== product.name) {
    slug = slugify(input.name);
    const existing = await prisma.product.findUnique({ where: { userId_slug: { userId, slug } } });
    if (existing && existing.id !== productId) {
      slug = `${slug}-${randomUUID().slice(0, 6)}`;
    }
  }

  return prisma.product.update({
    where: { id: productId },
    data: {
      ...(input.name !== undefined && { name: input.name }),
      ...(slug && { slug }),
      ...(input.description !== undefined && { description: input.description }),
      ...(input.tagline !== undefined && { tagline: input.tagline }),
      ...(input.websiteUrl !== undefined && { websiteUrl: input.websiteUrl }),
      ...(input.brandColors !== undefined && { brandColors: input.brandColors ?? undefined }),
      ...(input.category !== undefined && { category: input.category }),
    },
  });
}

export async function deleteProduct(productId: string, userId: string) {
  const product = await prisma.product.findFirst({
    where: { id: productId, userId, isActive: true },
  });
  if (!product) return false;

  await prisma.product.update({
    where: { id: productId },
    data: { isActive: false },
  });
  return true;
}

// ── Asset uploads ──

export async function uploadAsset(
  productId: string,
  userId: string,
  assetType: AssetType,
  file: MultipartFile
) {
  // Verify ownership
  const product = await prisma.product.findFirst({
    where: { id: productId, userId, isActive: true },
  });
  if (!product) {
    throw Object.assign(new Error("Product not found"), { statusCode: 404 });
  }

  const limits = ASSET_LIMITS[assetType];

  // Validate MIME type
  if (!limits.mimeTypes.includes(file.mimetype)) {
    throw Object.assign(
      new Error(`Invalid file type. Accepted: ${limits.extensions.join(", ")}`),
      { statusCode: 400 }
    );
  }

  // Validate extension
  const ext = "." + (file.filename.split(".").pop()?.toLowerCase() ?? "");
  if (!limits.extensions.includes(ext)) {
    throw Object.assign(
      new Error(`Invalid file extension. Accepted: ${limits.extensions.join(", ")}`),
      { statusCode: 400 }
    );
  }

  // Check count limit
  const existingCount = await prisma.productAsset.count({
    where: { productId, type: assetType },
  });

  // For VOICE, replace existing
  if (assetType === "VOICE" && existingCount >= limits.maxCount) {
    const existing = await prisma.productAsset.findFirst({
      where: { productId, type: "VOICE" },
    });
    if (existing) {
      await deleteAssetInternal(existing.id);
    }
  } else if (existingCount >= limits.maxCount) {
    throw Object.assign(
      new Error(`Maximum ${limits.maxCount} ${assetType.toLowerCase()} assets per product`),
      { statusCode: 400 }
    );
  }

  // Write file to disk
  const dir = uploadsDir(userId, productId, assetType);
  await mkdir(dir, { recursive: true });

  const storedFilename = `${randomUUID()}${ext}`;
  const storagePath = join(dir, storedFilename);

  let fileSizeBytes = 0;
  const writeStream = createWriteStream(storagePath);

  // Stream to disk while counting bytes
  const fileStream = file.file;
  fileStream.on("data", (chunk: Buffer) => {
    fileSizeBytes += chunk.length;
    if (fileSizeBytes > limits.maxBytes) {
      fileStream.destroy(new Error(`File exceeds ${limits.maxBytes / (1024 * 1024)}MB limit`));
    }
  });

  try {
    await pipeline(fileStream, writeStream);
  } catch (err: any) {
    // Cleanup partial file
    try { await unlink(storagePath); } catch {}
    if (err.message.includes("limit")) {
      throw Object.assign(new Error(err.message), { statusCode: 400 });
    }
    throw err;
  }

  const asset = await prisma.productAsset.create({
    data: {
      productId,
      type: assetType,
      filename: file.filename,
      storagePath,
      mimeType: file.mimetype,
      fileSizeBytes,
      isPrimary: existingCount === 0, // first of its type is primary
    },
  });

  const token = signUrl(asset.id, "asset", Date.now() + 60 * 60 * 1000);
  return {
    id: asset.id,
    type: asset.type,
    filename: asset.filename,
    mimeType: asset.mimeType,
    fileSizeBytes: asset.fileSizeBytes,
    isPrimary: asset.isPrimary,
    fileUrl: `/api/v1/products/${productId}/assets/${asset.id}/file?token=${token}`,
    createdAt: asset.createdAt,
  };
}

async function deleteAssetInternal(assetId: string) {
  const asset = await prisma.productAsset.findUnique({ where: { id: assetId } });
  if (!asset) return;
  try { await unlink(asset.storagePath); } catch {}
  await prisma.productAsset.delete({ where: { id: assetId } });
}

export async function deleteAsset(assetId: string, productId: string, userId: string) {
  const asset = await prisma.productAsset.findFirst({
    where: { id: assetId, productId },
    include: { product: { select: { userId: true } } },
  });
  if (!asset || asset.product.userId !== userId) return false;

  try { await unlink(asset.storagePath); } catch {}
  await prisma.productAsset.delete({ where: { id: assetId } });
  return true;
}

export async function getAssetForStreaming(assetId: string) {
  return prisma.productAsset.findUnique({
    where: { id: assetId },
    select: { storagePath: true, mimeType: true, filename: true },
  });
}
