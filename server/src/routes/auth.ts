import type { FastifyInstance } from "fastify";
import { WalletVerifyBody, RefreshBody } from "../types/index.js";
import { walletVerify, refreshAccessToken } from "../middleware/wallet-auth.js";

export async function authRoutes(app: FastifyInstance) {
  app.post("/api/v1/auth/wallet-verify", async (request, reply) => {
    const body = WalletVerifyBody.parse(request.body);
    try {
      const result = await walletVerify(body.walletAddress, body.message, body.signature);
      return result;
    } catch (err: any) {
      reply.code(401).send({ error: err.message });
    }
  });

  app.post("/api/v1/auth/refresh", async (request, reply) => {
    const body = RefreshBody.parse(request.body);
    try {
      const result = await refreshAccessToken(body.refreshToken);
      return result;
    } catch (err: any) {
      reply.code(401).send({ error: err.message });
    }
  });
}
