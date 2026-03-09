import Fastify from "fastify";
import cors from "@fastify/cors";
import rateLimit from "@fastify/rate-limit";
import { config } from "./config.js";
import { healthRoutes } from "./routes/health.js";
import { authRoutes } from "./routes/auth.js";
import { videoRoutes, videoStreamRoutes } from "./routes/videos.js";
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

  // CORS
  await app.register(cors, {
    origin: config.FRONTEND_URL,
    credentials: true,
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
  await app.register(paymentRoutes);
  await app.register(apiKeyRoutes);

  return app;
}
