import { stripe } from "../lib/stripe.js";
import { prisma } from "../lib/prisma.js";
import { config } from "../config.js";

const VIDEO_PRICE_CENTS = 500; // $5.00

export async function createCheckoutSession(videoId: string, userId: string) {
  const video = await prisma.video.findFirst({
    where: { id: videoId, userId, status: "COMPLETED", isPaid: false },
  });
  if (!video) {
    throw Object.assign(new Error("Video not found or not ready for payment"), { statusCode: 404 });
  }

  // Check for existing pending payment
  const existing = await prisma.payment.findFirst({
    where: { videoId, status: "PENDING" },
  });
  if (existing?.stripeSessionId) {
    // Return existing session if still valid
    try {
      const session = await stripe.checkout.sessions.retrieve(existing.stripeSessionId);
      if (session.status === "open") {
        return { checkoutUrl: session.url };
      }
    } catch {
      // Session expired, create new one
    }
  }

  const session = await stripe.checkout.sessions.create({
    mode: "payment",
    line_items: [
      {
        price_data: {
          currency: "usd",
          product_data: {
            name: "ZkAGI Video",
            description: `Video: ${video.topic.slice(0, 100)}`,
          },
          unit_amount: VIDEO_PRICE_CENTS,
        },
        quantity: 1,
      },
    ],
    metadata: { videoId, userId },
    success_url: `${config.FRONTEND_URL}/videos/${videoId}?payment=success`,
    cancel_url: `${config.FRONTEND_URL}/videos/${videoId}?payment=cancelled`,
  });

  await prisma.payment.create({
    data: {
      userId,
      videoId,
      amountCents: VIDEO_PRICE_CENTS,
      stripeSessionId: session.id,
      status: "PENDING",
    },
  });

  await prisma.video.update({
    where: { id: videoId },
    data: { paymentStatus: "PENDING" },
  });

  return { checkoutUrl: session.url };
}

export async function handleStripeWebhook(payload: Buffer, signature: string) {
  const event = stripe.webhooks.constructEvent(
    payload,
    signature,
    config.STRIPE_WEBHOOK_SECRET
  );

  if (event.type === "checkout.session.completed") {
    const session = event.data.object;
    const { videoId } = session.metadata || {};
    if (!videoId) return;

    await prisma.payment.updateMany({
      where: { stripeSessionId: session.id },
      data: {
        status: "PAID",
        stripePaymentIntent: session.payment_intent as string,
        paidAt: new Date(),
      },
    });

    await prisma.video.update({
      where: { id: videoId },
      data: { paymentStatus: "PAID", isPaid: true },
    });
  }
}
