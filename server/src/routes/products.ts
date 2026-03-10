import type { FastifyInstance } from "fastify";
import { existsSync, createReadStream } from "node:fs";
import { authGuard } from "../middleware/auth-guard.js";
import {
  CreateProductBody,
  UpdateProductBody,
  ProductListQuery,
} from "../types/index.js";
import {
  createProduct,
  getProduct,
  listProducts,
  updateProduct,
  deleteProduct,
  uploadAsset,
  deleteAsset,
  getAssetForStreaming,
} from "../services/product-service.js";
import { verifySignedUrl } from "../lib/crypto.js";

const security: { [k: string]: string[] }[] = [{ bearerAuth: [] }, { apiKeyAuth: [] }];

const productObject = {
  type: "object",
  properties: {
    id: { type: "string", format: "uuid" },
    name: { type: "string" },
    slug: { type: "string" },
    description: { type: "string", nullable: true },
    tagline: { type: "string", nullable: true },
    websiteUrl: { type: "string", nullable: true },
    brandColors: { type: "object", nullable: true },
    category: { type: "string", nullable: true },
    isActive: { type: "boolean" },
    assets: {
      type: "array",
      items: {
        type: "object",
        properties: {
          id: { type: "string", format: "uuid" },
          type: { type: "string", enum: ["IMAGE", "VOICE", "VIDEO"] },
          filename: { type: "string" },
          mimeType: { type: "string" },
          fileSizeBytes: { type: "integer" },
          isPrimary: { type: "boolean" },
          fileUrl: { type: "string" },
          createdAt: { type: "string", format: "date-time" },
        },
      },
    },
    createdAt: { type: "string", format: "date-time" },
    updatedAt: { type: "string", format: "date-time" },
  },
} as const;

const assetObject = {
  type: "object",
  properties: {
    id: { type: "string", format: "uuid" },
    type: { type: "string", enum: ["IMAGE", "VOICE", "VIDEO"] },
    filename: { type: "string" },
    mimeType: { type: "string" },
    fileSizeBytes: { type: "integer" },
    isPrimary: { type: "boolean" },
    fileUrl: { type: "string" },
    createdAt: { type: "string", format: "date-time" },
  },
} as const;

const errorResponse = { type: "object", properties: { error: { type: "string" } } } as const;

export async function productRoutes(app: FastifyInstance) {
  app.addHook("onRequest", authGuard);

  // ── POST /api/v1/products ──
  app.post("/api/v1/products", {
    schema: {
      tags: ["Products"],
      summary: "Create a product",
      description: "Create a new product with details for custom video branding.",
      security,
      body: {
        type: "object",
        required: ["name"],
        properties: {
          name: { type: "string", minLength: 1, maxLength: 100 },
          description: { type: "string", maxLength: 2000 },
          tagline: { type: "string", maxLength: 200 },
          websiteUrl: { type: "string", format: "uri", maxLength: 500 },
          brandColors: { type: "object", additionalProperties: { type: "string" } },
          category: { type: "string", maxLength: 50 },
        },
      },
      response: { 201: productObject, 400: errorResponse },
    },
  }, async (request, reply) => {
    const input = CreateProductBody.parse(request.body);
    try {
      const product = await createProduct(request.userId!, input);
      reply.code(201).send(product);
    } catch (err: any) {
      reply.code(err.statusCode || 500).send({ error: err.message });
    }
  });

  // ── GET /api/v1/products ──
  app.get("/api/v1/products", {
    schema: {
      tags: ["Products"],
      summary: "List your products (paginated)",
      security,
      querystring: {
        type: "object",
        properties: {
          page: { type: "integer", minimum: 1, default: 1 },
          limit: { type: "integer", minimum: 1, maximum: 50, default: 20 },
        },
      },
      response: {
        200: {
          type: "object",
          properties: {
            products: { type: "array", items: productObject },
            pagination: {
              type: "object",
              properties: {
                page: { type: "integer" },
                limit: { type: "integer" },
                total: { type: "integer" },
                pages: { type: "integer" },
              },
            },
          },
        },
      },
    },
  }, async (request) => {
    const { page, limit } = ProductListQuery.parse(request.query);
    return listProducts(request.userId!, page, limit);
  });

  // ── GET /api/v1/products/:id ──
  app.get<{ Params: { id: string } }>("/api/v1/products/:id", {
    schema: {
      tags: ["Products"],
      summary: "Get product with assets",
      description: "Retrieve product details including all assets with signed download URLs (1hr expiry).",
      security,
      params: {
        type: "object",
        required: ["id"],
        properties: { id: { type: "string", format: "uuid" } },
      },
      response: { 200: productObject, 404: errorResponse },
    },
  }, async (request, reply) => {
    const product = await getProduct(request.params.id, request.userId!);
    if (!product) return reply.code(404).send({ error: "Product not found" });
    return product;
  });

  // ── PATCH /api/v1/products/:id ──
  app.patch<{ Params: { id: string } }>("/api/v1/products/:id", {
    schema: {
      tags: ["Products"],
      summary: "Update product details",
      security,
      params: {
        type: "object",
        required: ["id"],
        properties: { id: { type: "string", format: "uuid" } },
      },
      body: {
        type: "object",
        properties: {
          name: { type: "string", minLength: 1, maxLength: 100 },
          description: { type: "string", maxLength: 2000, nullable: true },
          tagline: { type: "string", maxLength: 200, nullable: true },
          websiteUrl: { type: "string", format: "uri", maxLength: 500, nullable: true },
          brandColors: { type: "object", nullable: true },
          category: { type: "string", maxLength: 50, nullable: true },
        },
      },
      response: { 200: productObject, 404: errorResponse },
    },
  }, async (request, reply) => {
    const input = UpdateProductBody.parse(request.body);
    const product = await updateProduct(request.params.id, request.userId!, input);
    if (!product) return reply.code(404).send({ error: "Product not found" });
    return product;
  });

  // ── DELETE /api/v1/products/:id ──
  app.delete<{ Params: { id: string } }>("/api/v1/products/:id", {
    schema: {
      tags: ["Products"],
      summary: "Delete product (soft-delete)",
      security,
      params: {
        type: "object",
        required: ["id"],
        properties: { id: { type: "string", format: "uuid" } },
      },
      response: {
        200: { type: "object", properties: { success: { type: "boolean" } } },
        404: errorResponse,
      },
    },
  }, async (request, reply) => {
    const ok = await deleteProduct(request.params.id, request.userId!);
    if (!ok) return reply.code(404).send({ error: "Product not found" });
    return { success: true };
  });

  // ── POST /api/v1/products/:id/images ──
  app.post<{ Params: { id: string } }>("/api/v1/products/:id/images", {
    schema: {
      tags: ["Products"],
      summary: "Upload product image",
      description: "Upload a product image (max 10MB, png/jpg/webp, up to 10 per product).",
      security,
      consumes: ["multipart/form-data"],
      params: {
        type: "object",
        required: ["id"],
        properties: { id: { type: "string", format: "uuid" } },
      },
      response: { 201: assetObject, 400: errorResponse, 404: errorResponse },
    },
  }, async (request, reply) => {
    const file = await request.file();
    if (!file) return reply.code(400).send({ error: "No file uploaded" });
    try {
      const asset = await uploadAsset(request.params.id, request.userId!, "IMAGE", file);
      reply.code(201).send(asset);
    } catch (err: any) {
      reply.code(err.statusCode || 500).send({ error: err.message });
    }
  });

  // ── POST /api/v1/products/:id/voice ──
  app.post<{ Params: { id: string } }>("/api/v1/products/:id/voice", {
    schema: {
      tags: ["Products"],
      summary: "Upload voice reference",
      description: "Upload a voice reference clip (max 5MB, wav/mp3). Replaces any existing voice.",
      security,
      consumes: ["multipart/form-data"],
      params: {
        type: "object",
        required: ["id"],
        properties: { id: { type: "string", format: "uuid" } },
      },
      response: { 201: assetObject, 400: errorResponse, 404: errorResponse },
    },
  }, async (request, reply) => {
    const file = await request.file();
    if (!file) return reply.code(400).send({ error: "No file uploaded" });
    try {
      const asset = await uploadAsset(request.params.id, request.userId!, "VOICE", file);
      reply.code(201).send(asset);
    } catch (err: any) {
      reply.code(err.statusCode || 500).send({ error: err.message });
    }
  });

  // ── POST /api/v1/products/:id/videos ──
  app.post<{ Params: { id: string } }>("/api/v1/products/:id/videos", {
    schema: {
      tags: ["Products"],
      summary: "Upload demo video",
      description: "Upload a product demo video (max 100MB, mp4/webm, up to 5 per product).",
      security,
      consumes: ["multipart/form-data"],
      params: {
        type: "object",
        required: ["id"],
        properties: { id: { type: "string", format: "uuid" } },
      },
      response: { 201: assetObject, 400: errorResponse, 404: errorResponse },
    },
  }, async (request, reply) => {
    const file = await request.file();
    if (!file) return reply.code(400).send({ error: "No file uploaded" });
    try {
      const asset = await uploadAsset(request.params.id, request.userId!, "VIDEO", file);
      reply.code(201).send(asset);
    } catch (err: any) {
      reply.code(err.statusCode || 500).send({ error: err.message });
    }
  });

  // ── DELETE /api/v1/products/:id/assets/:assetId ──
  app.delete<{ Params: { id: string; assetId: string } }>("/api/v1/products/:id/assets/:assetId", {
    schema: {
      tags: ["Products"],
      summary: "Delete a product asset",
      security,
      params: {
        type: "object",
        required: ["id", "assetId"],
        properties: {
          id: { type: "string", format: "uuid" },
          assetId: { type: "string", format: "uuid" },
        },
      },
      response: {
        200: { type: "object", properties: { success: { type: "boolean" } } },
        404: errorResponse,
      },
    },
  }, async (request, reply) => {
    const ok = await deleteAsset(request.params.assetId, request.params.id, request.userId!);
    if (!ok) return reply.code(404).send({ error: "Asset not found" });
    return { success: true };
  });
}

// ── Signed URL file serving (no auth guard — token IS the auth) ──
export async function productAssetStreamRoutes(app: FastifyInstance) {
  app.get<{ Params: { id: string; assetId: string }; Querystring: { token: string } }>(
    "/api/v1/products/:id/assets/:assetId/file",
    {
      schema: {
        tags: ["Products"],
        summary: "Serve asset file",
        description: "Download a product asset via signed URL (1hr expiry).",
        params: {
          type: "object",
          required: ["id", "assetId"],
          properties: {
            id: { type: "string", format: "uuid" },
            assetId: { type: "string", format: "uuid" },
          },
        },
        querystring: {
          type: "object",
          required: ["token"],
          properties: {
            token: { type: "string", description: "Signed URL token (1h expiry)" },
          },
        },
        response: {
          200: { type: "string", description: "Binary file stream" },
          403: errorResponse,
          404: errorResponse,
        },
      },
    },
    async (request, reply) => {
      const result = verifySignedUrl(request.query.token);
      if (!result || result.videoId !== request.params.assetId || result.type !== "asset") {
        return reply.code(403).send({ error: "Invalid or expired link" });
      }

      const asset = await getAssetForStreaming(request.params.assetId);
      if (!asset || !existsSync(asset.storagePath)) {
        return reply.code(404).send({ error: "Asset file not found" });
      }

      reply.header("Content-Type", asset.mimeType);
      reply.header("Content-Disposition", `inline; filename="${asset.filename}"`);
      return reply.send(createReadStream(asset.storagePath));
    }
  );
}
