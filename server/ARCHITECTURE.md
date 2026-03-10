# ZkAGI Video Engine — Multi-Tenant Platform

## Overview

The ZkAGI Video Engine generates AI-powered marketing videos using a pipeline of TTS, image generation, LTX-2 video clips, and Remotion rendering. This document describes the multi-tenant architecture that allows multiple users (humans via web app, AI agents via API) to order, pay for, and download videos.

---

## How It Works (End to End)

### For a Human User (React Frontend + Solana Wallet)

```
1. User connects Solana wallet on the React frontend
2. Frontend asks user to sign a message: "Sign in to ZkAGI Video Engine. Timestamp: 1709913600000"
3. Frontend sends POST /api/v1/auth/wallet-verify with { walletAddress, message, signature }
4. Server verifies the Ed25519 signature using tweetnacl
5. If valid → auto-creates user record (first time) or finds existing user
6. Server issues JWT (24h) + refresh token (7d)
7. All subsequent requests use Authorization: Bearer <jwt>
```

```
8.  User fills out a form: topic, product (pawpad/zynapse/zkterminal), format (16:9)
9.  Frontend sends POST /api/v1/videos with the brief
10. Server creates a video record (status: QUEUED) and adds a job to BullMQ
11. Frontend polls GET /api/v1/videos/:id every 5-10 seconds for status updates
12. Server returns current phase: "Writing screenplay...", "Generating TTS...", etc.
```

```
13. Video completes (15-25 minutes later)
14. Server generates a 5-second watermarked preview via ffmpeg
15. User sees the preview on the frontend (free, no payment needed)
16. User clicks "Pay $5 to download"
17. Frontend sends POST /api/v1/payments/checkout { videoId }
18. Server creates a Stripe Checkout Session → returns checkout URL
19. User is redirected to Stripe, enters card details, pays $5
20. Stripe sends a webhook to POST /api/v1/payments/webhook
21. Server marks video as PAID
22. Frontend shows "Download" button with a signed URL (valid 24 hours)
23. User downloads the full MP4 + social media captions
```

### For an AI Agent (REST API + API Key)

```
1. Agent owner connects wallet, goes to API Keys page
2. Creates an API key → gets back zkv_a1b2c3d4e5f6... (shown once)
3. Server stores only the SHA-256 hash of the key

4. Agent calls POST /api/v1/videos with header X-API-Key: zkv_...
   Body: { "topic": "Why PawPad is the safest Solana wallet", "product": "pawpad" }
5. Server looks up key hash → finds user → creates video job
6. Agent polls GET /api/v1/videos/:id for status
7. When complete, agent creates checkout → pays via Stripe
8. Agent downloads video via signed URL
```

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  React Frontend │     │   AI Agents     │
│  (Solana Wallet)│     │  (API Key)      │
└────────┬────────┘     └────────┬────────┘
         │    Bearer JWT         │  X-API-Key header
         └───────────┬──────────┘
                     ▼
          ┌──────────────────┐
          │ Cloudflare Tunnel│  content_agent_video.zkagi.ai
          └────────┬─────────┘
                   ▼
           ┌─────────────────┐
           │  Fastify API    │  :3001
           │  (auth-guard)   │
           │  (@fastify/     │
           │   multipart)    │
           └──┬──────┬───┬───┘
              │      │   │
     ┌────────▼──┐ ┌─▼───▼────┐
     │ PostgreSQL│ │  Redis   │
     │  (data)   │ │  (queue) │
     └───────────┘ └────┬─────┘
                        │ BullMQ
     ┌───────────┐ ┌────▼─────┐
     │  uploads/ │ │  Worker  │  concurrency = 1
     │  (assets) │ │          │  (single GPU)
     └───────────┘ └────┬─────┘
                        │ spawns
                   ┌────▼──────┐
                   │Claude Code│  in isolated workspace
                   │   CLI     │
                   └────┬──────┘
                        │ orchestrates
            ┌───────────┼───────────┐
            ▼           ▼           ▼
       Image Gen    ComfyUI     VoxCPM TTS
       (reference   LTX-2      (voice clone)
        frames)    (video)
                        │
                  ┌─────▼─────┐
                  │  Remotion  │  render → MP4
                  └─────┬─────┘
                        │
                  ┌─────▼─────┐
                  │  ffmpeg   │  5s preview + watermark
                  └───────────┘
```

---

## Database Tables

| Table | Purpose |
|-------|---------|
| **users** | Solana wallet address, display name, email |
| **products** | User-uploaded product details (name, slug, description, tagline, website, brand colors, category) |
| **product_assets** | Files attached to products (images, voice clips, demo videos) with type, path, MIME info |
| **videos** | Topic, status, file paths, payment status, captions. Optional `product_id` FK to products |
| **payments** | Stripe session/intent, amount ($5), paid timestamp |
| **api_keys** | SHA-256 hash of key, prefix for display, revoke support |

### Video Status Flow

```
QUEUED → PROCESSING → RENDERING → COMPLETED
                                       │
                                  [user pays $5]
                                       │
                                  isPaid = true
                                       │
                                  download unlocked

Any step can → FAILED (with reason)
```

### Payment Status Flow

```
UNPAID → PENDING (checkout created) → PAID (webhook confirmed)
                                         │
                                    REFUNDED (manual)
```

---

## Worker Pipeline (What Happens Inside)

When a job is picked up from the queue:

```
1. Pre-flight     │ Ping ComfyUI at http://172.18.64.1:8001/system_stats
                  │ If unreachable → throw error → BullMQ retries in 60s
                  │
2. Workspace      │ Create workspaces/{video-id}/
                  │   - Copy: src/, package.json, tsconfig.json, remotion.config.ts
                  │   - Symlink: node_modules, voices, products, .claude, public/sfx, public/video
                  │   - Empty: public/scenes/, public/audio/, output/
                  │
3. Spawn Claude   │ claude -p <prompt> --dangerously-skip-permissions
                  │   --output-format stream-json --verbose
                  │ Working directory = workspace (isolated from other jobs)
                  │
4. Track Progress │ Parse stdout line-by-line for keywords:
                  │   "SKILL.md"        → Reading skills...
                  │   "screenplay"      → Writing screenplay...
                  │   "clone-tts"       → Generating TTS audio...
                  │   "45.251.34.28"    → Generating images...
                  │   "172.18.64.1"     → Generating video clips...
                  │   "ZkAGIVideo.tsx"  → Composing video...
                  │   "remotion render" → Rendering final video...
                  │ Each phase change updates the database in real-time
                  │
5. Post-process   │ Find output MP4 in workspace
                  │ Copy to permanent storage: output/videos/{video-id}.mp4
                  │ Generate 5s watermarked preview via ffmpeg
                  │ Extract thumbnail at t=1s
                  │ Read captions JSON if exists
                  │ Update DB: status=COMPLETED, paths, duration, file size
                  │
6. Cleanup        │ Delete workspace directory
```

**Timeout:** 40 minutes hard limit. If Claude hasn't finished, the process is killed.
**Retries:** 1 retry with exponential backoff (60s base).
**Concurrency:** 1 job at a time (single RTX 5090 GPU).

---

## Workspace Isolation

Each video job runs in its own directory so multiple jobs don't interfere:

```
workspaces/
  {video-id}/
    src/                    ← COPY (Claude rewrites Root.tsx, ZkAGIVideo.tsx)
    package.json            ← COPY
    tsconfig.json           ← COPY
    remotion.config.ts      ← COPY
    node_modules/           → SYMLINK to project root (read-only, ~500MB saved)
    voices/                 → SYMLINK (shared voice reference files)
    products/               → SYMLINK (product assets)
    .claude/                → SYMLINK (skills, settings)
    public/
      sfx/                  → SYMLINK (shared sound effects)
      video/                → SYMLINK (shared ending.mp4)
      scenes/               ← EMPTY (generated images + video clips land here)
      audio/                ← EMPTY (generated TTS audio lands here)
    output/                 ← EMPTY (rendered MP4 lands here)
```

After completion, the MP4 is copied to permanent storage and the workspace is deleted.

---

## Security Model

| Layer | Mechanism |
|-------|-----------|
| **Wallet Auth** | Ed25519 signature verified via tweetnacl. Message must include a timestamp within 5 minutes. |
| **JWT** | Issued on wallet verify. 24-hour expiry. Contains user ID + wallet address. |
| **API Keys** | Prefixed `zkv_` + 32 random bytes. Only SHA-256 hash stored in DB. Shown once on creation. |
| **Auth Guard** | Every protected route checks: Bearer JWT first, then X-API-Key header. |
| **Video Access** | Preview/download URLs are HMAC-SHA256 signed with expiry (1hr preview, 24hr download). |
| **Asset Access** | Product asset file URLs are HMAC-SHA256 signed with 1hr expiry. Same mechanism as video URLs. |
| **Upload Limits** | Images: 10MB/10 per product. Voice: 5MB/1 per product. Videos: 100MB/5 per product. Max 20 products per user. |
| **Payment Gate** | Download endpoint checks `video.isPaid === true` before streaming file. |
| **Stripe Webhook** | Signature verified via `stripe.webhooks.constructEvent()`. |
| **Rate Limits** | 5 videos/hour, 20/day per user. Global: 100 requests/minute. |

---

## API Endpoints Summary

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/v1/auth/wallet-verify` | None | Sign in with Solana wallet |
| POST | `/api/v1/auth/refresh` | None | Refresh access token |
| POST | `/api/v1/videos` | Required | Submit video request (supports optional `productId`) |
| GET | `/api/v1/videos` | Required | List your videos (paginated) |
| GET | `/api/v1/videos/:id` | Required | Get video status + URLs |
| DELETE | `/api/v1/videos/:id` | Required | Cancel queued video |
| GET | `/api/v1/videos/:id/preview` | Signed URL | Stream 5s watermarked preview |
| GET | `/api/v1/videos/:id/download` | Signed URL + Paid | Stream full video |
| POST | `/api/v1/products` | Required | Create product with details |
| GET | `/api/v1/products` | Required | List your products (paginated) |
| GET | `/api/v1/products/:id` | Required | Get product + all assets with signed URLs |
| PATCH | `/api/v1/products/:id` | Required | Update product details |
| DELETE | `/api/v1/products/:id` | Required | Soft-delete product |
| POST | `/api/v1/products/:id/images` | Required | Upload product image (max 10MB, up to 10) |
| POST | `/api/v1/products/:id/voice` | Required | Upload voice reference (max 5MB, replaces existing) |
| POST | `/api/v1/products/:id/videos` | Required | Upload demo video (max 100MB, up to 5) |
| DELETE | `/api/v1/products/:id/assets/:assetId` | Required | Delete a specific asset |
| GET | `/api/v1/products/:id/assets/:assetId/file` | Signed URL | Serve asset file (1hr expiry) |
| POST | `/api/v1/payments/checkout` | Required | Create Stripe checkout |
| POST | `/api/v1/payments/webhook` | Stripe sig | Handle payment confirmation |
| POST | `/api/v1/api-keys` | Required | Create API key |
| GET | `/api/v1/api-keys` | Required | List your API keys |
| DELETE | `/api/v1/api-keys/:id` | Required | Revoke API key |
| GET | `/api/v1/health` | None | System health check |

---

## Product Uploads & Storage

Users can upload custom product assets (images, voice clips, demo videos) instead of using only the hardcoded pawpad/zynapse/zkterminal products. Uploaded files are stored on disk:

```
server/uploads/
  {userId}/
    {productId}/
      images/      ← PNG/JPG/WebP, max 10MB each, up to 10
      voices/      ← WAV/MP3, max 5MB, 1 per product (replaces on re-upload)
      videos/      ← MP4/WebM, max 100MB each, up to 5
```

Asset files are served via HMAC-signed URLs (1hr expiry), same mechanism as video preview/download. When creating a video, users can pass `productId` instead of the `product` enum to use their custom product.

**Cloudflare Tunnel:** The API is exposed via a Cloudflare tunnel (`cloudflared` systemd service). The default Cloudflare upload limit is **100MB** for free/pro plans, which matches the max video upload size. No tunnel config changes needed for the product upload endpoints.

---

## Running It

```bash
# Terminal 1: Start services
sudo service postgresql start
sudo service redis-server start

# Terminal 2: API Server
cd server
npx tsx src/index.ts

# Terminal 3: Video Worker
cd server
npx tsx src/worker/video-worker.ts

# Terminal 4: Stripe webhook forwarding (local dev)
stripe listen --forward-to localhost:3001/api/v1/payments/webhook
```

## Cost Structure

- **Preview:** Free (5 seconds, watermarked)
- **Full video:** $5 per video (via Stripe)
- **Generation cost:** ~15-25 min GPU time on RTX 5090
