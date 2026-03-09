import type { FastifyInstance } from "fastify";
import { authGuard } from "../middleware/auth-guard.js";
import { CheckoutBody } from "../types/index.js";
import { createCheckoutSession, handleStripeWebhook } from "../services/payment-service.js";

export async function paymentRoutes(app: FastifyInstance) {
  // Checkout requires auth
  app.post("/api/v1/payments/checkout", {
    onRequest: authGuard,
    schema: {
      tags: ["Payments"],
      summary: "Create Stripe checkout",
      description:
        "Creates a Stripe Checkout Session for a $5 video purchase. Returns a URL to redirect the user to Stripe's hosted checkout page.",
      security: [{ bearerAuth: [] }, { apiKeyAuth: [] }] as { [k: string]: string[] }[],
      body: {
        type: "object",
        required: ["videoId"],
        properties: {
          videoId: {
            type: "string",
            format: "uuid",
            description: "ID of the completed video to purchase",
          },
        },
      },
      response: {
        200: {
          type: "object",
          properties: {
            checkoutUrl: {
              type: "string",
              format: "uri",
              description: "Stripe hosted checkout URL — redirect the user here",
            },
            sessionId: {
              type: "string",
              description: "Stripe Checkout Session ID",
            },
          },
        },
        400: { type: "object", properties: { error: { type: "string" } } },
        404: { type: "object", properties: { error: { type: "string" } } },
      },
    },
  }, async (request, reply) => {
    const { videoId } = CheckoutBody.parse(request.body);
    try {
      const result = await createCheckoutSession(videoId, request.userId!);
      return result;
    } catch (err: any) {
      reply.code(err.statusCode || 500).send({ error: err.message });
    }
  });

  // Stripe webhook — needs raw body, NO auth guard
  app.post("/api/v1/payments/webhook", {
    schema: {
      tags: ["Payments"],
      summary: "Stripe webhook (internal)",
      description:
        "Handles Stripe webhook events. Called by Stripe servers — verified via stripe-signature header. Do NOT call this manually.",
      response: {
        200: {
          type: "object",
          properties: { received: { type: "boolean" } },
        },
        400: { type: "object", properties: { error: { type: "string" } } },
      },
    },
  }, async (request, reply) => {
    const signature = request.headers["stripe-signature"] as string;
    if (!signature) {
      return reply.code(400).send({ error: "Missing stripe-signature header" });
    }

    try {
      const rawBody = (request as any).rawBody as Buffer;
      await handleStripeWebhook(rawBody, signature);
      return { received: true };
    } catch (err: any) {
      app.log.error("Stripe webhook error: %s", err.message);
      reply.code(400).send({ error: err.message });
    }
  });
}
