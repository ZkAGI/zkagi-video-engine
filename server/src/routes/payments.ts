import type { FastifyInstance } from "fastify";
import { authGuard } from "../middleware/auth-guard.js";
import { CheckoutBody } from "../types/index.js";
import { createCheckoutSession, handleStripeWebhook } from "../services/payment-service.js";

export async function paymentRoutes(app: FastifyInstance) {
  // Checkout requires auth
  app.post("/api/v1/payments/checkout", { onRequest: authGuard }, async (request, reply) => {
    const { videoId } = CheckoutBody.parse(request.body);
    try {
      const result = await createCheckoutSession(videoId, request.userId!);
      return result;
    } catch (err: any) {
      reply.code(err.statusCode || 500).send({ error: err.message });
    }
  });

  // Stripe webhook — needs raw body, NO auth guard
  app.post("/api/v1/payments/webhook", async (request, reply) => {
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
