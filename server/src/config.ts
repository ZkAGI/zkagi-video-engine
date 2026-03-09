import { z } from "zod";
import "dotenv/config";

const envSchema = z.object({
  DATABASE_URL: z.string(),
  REDIS_URL: z.string().default("redis://localhost:6379"),
  PORT: z.coerce.number().default(3001),
  FRONTEND_URL: z.string().default("http://localhost:3000"),
  JWT_SECRET: z.string().min(16),
  URL_SIGNING_SECRET: z.string().min(16),
  STRIPE_SECRET_KEY: z.string(),
  STRIPE_WEBHOOK_SECRET: z.string(),
  PROJECT_ROOT: z.string(),
  COMFYUI_URL: z.string().default("http://172.18.64.1:8001"),
});

export type Config = z.infer<typeof envSchema>;

function loadConfig(): Config {
  const result = envSchema.safeParse(process.env);
  if (!result.success) {
    console.error("Invalid environment variables:");
    for (const issue of result.error.issues) {
      console.error(`  ${issue.path.join(".")}: ${issue.message}`);
    }
    process.exit(1);
  }
  return result.data;
}

export const config = loadConfig();
