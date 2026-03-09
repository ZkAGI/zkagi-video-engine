import jwt from "jsonwebtoken";
import { config } from "../config.js";
import { verifyWalletSignature } from "../lib/solana.js";
import { prisma } from "../lib/prisma.js";
import type { JwtPayload } from "../types/index.js";

const TOKEN_EXPIRY = "24h";
const REFRESH_EXPIRY = "7d";

/** Verify wallet signature & issue JWT. Auto-creates user on first login. */
export async function walletVerify(
  walletAddress: string,
  message: string,
  signature: string
): Promise<{ accessToken: string; refreshToken: string; userId: string }> {
  // Validate message contains a recent timestamp (within 5 minutes)
  const timestampMatch = message.match(/Timestamp: (\d+)/);
  if (timestampMatch) {
    const msgTimestamp = parseInt(timestampMatch[1], 10);
    const now = Date.now();
    if (Math.abs(now - msgTimestamp) > 5 * 60 * 1000) {
      throw new Error("Message timestamp expired");
    }
  }

  const valid = verifyWalletSignature(walletAddress, message, signature);
  if (!valid) {
    throw new Error("Invalid wallet signature");
  }

  // Upsert user
  const user = await prisma.user.upsert({
    where: { walletAddress },
    update: {},
    create: { walletAddress },
  });

  const payload: Omit<JwtPayload, "iat" | "exp"> = {
    sub: user.id,
    wallet: user.walletAddress,
  };

  const accessToken = jwt.sign(payload, config.JWT_SECRET, { expiresIn: TOKEN_EXPIRY });
  const refreshToken = jwt.sign({ ...payload, type: "refresh" }, config.JWT_SECRET, {
    expiresIn: REFRESH_EXPIRY,
  });

  return { accessToken, refreshToken, userId: user.id };
}

/** Verify and refresh an access token */
export async function refreshAccessToken(
  refreshToken: string
): Promise<{ accessToken: string }> {
  const decoded = jwt.verify(refreshToken, config.JWT_SECRET) as JwtPayload & { type?: string };
  if (decoded.type !== "refresh") {
    throw new Error("Invalid refresh token");
  }

  const payload: Omit<JwtPayload, "iat" | "exp"> = {
    sub: decoded.sub,
    wallet: decoded.wallet,
  };

  const accessToken = jwt.sign(payload, config.JWT_SECRET, { expiresIn: TOKEN_EXPIRY });
  return { accessToken };
}

/** Extract and verify JWT from Authorization header */
export function verifyJwt(token: string): JwtPayload {
  return jwt.verify(token, config.JWT_SECRET) as JwtPayload;
}
