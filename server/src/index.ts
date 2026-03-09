import { buildApp } from "./app.js";
import { config } from "./config.js";
import { prisma } from "./lib/prisma.js";
import { redis } from "./lib/redis.js";

async function main() {
  const app = await buildApp();

  // Graceful shutdown
  const shutdown = async () => {
    console.log("Shutting down...");
    await app.close();
    await prisma.$disconnect();
    redis.disconnect();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  try {
    await app.listen({ port: config.PORT, host: "0.0.0.0" });
    console.log(`Server running on http://0.0.0.0:${config.PORT}`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

main();
