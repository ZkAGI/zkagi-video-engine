import type { FastifyInstance } from "fastify";
import { WalletVerifyBody, RefreshBody } from "../types/index.js";
import { walletVerify, refreshAccessToken } from "../middleware/wallet-auth.js";

export async function authRoutes(app: FastifyInstance) {
  app.post("/api/v1/auth/wallet-verify", {
    schema: {
      tags: ["Auth"],
      summary: "Sign in with Solana wallet",
      description:
        "Verify a signed message from a Solana wallet. Returns JWT access token (24h) and refresh token (7d). Creates user on first login.",
      body: {
        type: "object",
        required: ["walletAddress", "message", "signature"],
        properties: {
          walletAddress: {
            type: "string",
            description: "Solana wallet public key (base58)",
            example: "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
          },
          message: {
            type: "string",
            description:
              "Message containing a timestamp within the last 5 minutes",
            example: "Sign in to ZkAGI Video Engine\nTimestamp: 1709913600000",
          },
          signature: {
            type: "string",
            description: "Ed25519 signature of the message (base58 encoded)",
            example: "5K3t...",
          },
        },
      },
      response: {
        200: {
          type: "object",
          properties: {
            accessToken: { type: "string", description: "JWT (24h expiry)" },
            refreshToken: { type: "string", description: "Refresh token (7d expiry)" },
            user: {
              type: "object",
              properties: {
                id: { type: "string", format: "uuid" },
                walletAddress: { type: "string" },
              },
            },
          },
        },
        401: {
          type: "object",
          properties: { error: { type: "string" } },
        },
      },
    },
  }, async (request, reply) => {
    const body = WalletVerifyBody.parse(request.body);
    try {
      const result = await walletVerify(body.walletAddress, body.message, body.signature);
      return result;
    } catch (err: any) {
      reply.code(401).send({ error: err.message });
    }
  });

  app.post("/api/v1/auth/refresh", {
    schema: {
      tags: ["Auth"],
      summary: "Refresh access token",
      description: "Exchange a valid refresh token for a new JWT access token.",
      body: {
        type: "object",
        required: ["refreshToken"],
        properties: {
          refreshToken: {
            type: "string",
            description: "Refresh token obtained from wallet-verify",
          },
        },
      },
      response: {
        200: {
          type: "object",
          properties: {
            accessToken: { type: "string" },
            refreshToken: { type: "string" },
          },
        },
        401: {
          type: "object",
          properties: { error: { type: "string" } },
        },
      },
    },
  }, async (request, reply) => {
    const body = RefreshBody.parse(request.body);
    try {
      const result = await refreshAccessToken(body.refreshToken);
      return result;
    } catch (err: any) {
      reply.code(401).send({ error: err.message });
    }
  });
}
