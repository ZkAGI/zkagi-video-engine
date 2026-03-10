import Fastify from "fastify";
import cors from "@fastify/cors";
import rateLimit from "@fastify/rate-limit";
import multipart from "@fastify/multipart";
import swagger from "@fastify/swagger";
import swaggerUi from "@fastify/swagger-ui";
import { config } from "./config.js";
import { healthRoutes } from "./routes/health.js";
import { authRoutes } from "./routes/auth.js";
import { videoRoutes, videoStreamRoutes } from "./routes/videos.js";
import { productRoutes, productAssetStreamRoutes } from "./routes/products.js";
import { paymentRoutes } from "./routes/payments.js";
import { apiKeyRoutes } from "./routes/api-keys.js";
import { ZodError } from "zod";

export async function buildApp() {
  const app = Fastify({
    logger: {
      transport: {
        target: "pino-pretty",
        options: { colorize: true },
      },
    },
    ajv: {
      customOptions: {
        keywords: ["example"],
      },
    },
  });

  // Add raw body content type parser for Stripe webhooks
  app.addContentTypeParser(
    "application/json",
    { parseAs: "buffer" },
    (_req, body, done) => {
      try {
        // Store raw body on the request for Stripe webhook verification
        (_req as any).rawBody = body;
        const json = JSON.parse(body.toString());
        done(null, json);
      } catch (err) {
        done(err as Error, undefined);
      }
    }
  );

  // Swagger / OpenAPI docs
  await app.register(swagger, {
    openapi: {
      info: {
        title: "ZkAGI Video Engine API",
        description:
          "AI-powered video generation platform. Authenticate with a Solana wallet or API key, submit video topics, and download the results after payment.",
        version: "1.0.0",
        contact: { name: "ZkAGI", url: "https://zkagi.ai" },
      },
      servers: [
        { url: "https://content_agent_video.zkagi.ai", description: "Production" },
      ],
      tags: [
        { name: "Health", description: "System health checks" },
        { name: "Auth", description: "Solana wallet authentication & token refresh" },
        { name: "Videos", description: "Video generation, listing, streaming & downloads" },
        { name: "Payments", description: "Stripe checkout & webhook" },
        { name: "Products", description: "Product management & asset uploads" },
        { name: "API Keys", description: "Manage programmatic access keys" },
      ],
      components: {
        securitySchemes: {
          bearerAuth: {
            type: "http",
            scheme: "bearer",
            bearerFormat: "JWT",
            description: "JWT token from wallet-verify endpoint",
          },
          apiKeyAuth: {
            type: "apiKey",
            in: "header",
            name: "X-API-Key",
            description: "API key (prefix zkv_). Create via /api/v1/api-keys",
          },
        },
      },
    },
  });

  await app.register(swaggerUi, {
    routePrefix: "/api/docs",
    uiConfig: {
      docExpansion: "list",
      deepLinking: true,
      defaultModelsExpandDepth: 3,
      tryItOutEnabled: true,
    },
    staticCSP: true,
  });

  // CORS
  await app.register(cors, {
    origin: [config.FRONTEND_URL, "https://content_agent_video.zkagi.ai"],
    credentials: true,
  });

  // Multipart file uploads
  await app.register(multipart, {
    limits: {
      fileSize: 100 * 1024 * 1024, // 100MB global max
      files: 1,
    },
  });

  // Global rate limiting
  await app.register(rateLimit, {
    max: 100,
    timeWindow: "1 minute",
  });

  // Zod validation error handler
  app.setErrorHandler((error, _request, reply) => {
    if (error instanceof ZodError) {
      return reply.code(400).send({
        error: "Validation error",
        details: error.errors.map((e) => ({
          path: e.path.join("."),
          message: e.message,
        })),
      });
    }

    app.log.error(error);
    const statusCode = (error as any).statusCode || 500;
    reply.code(statusCode).send({
      error: (error as Error).message || "Internal server error",
    });
  });

  // Routes
  await app.register(healthRoutes);
  await app.register(authRoutes);
  await app.register(videoRoutes);
  await app.register(videoStreamRoutes);
  await app.register(productRoutes);
  await app.register(productAssetStreamRoutes);
  await app.register(paymentRoutes);
  await app.register(apiKeyRoutes);

  return app;
}
