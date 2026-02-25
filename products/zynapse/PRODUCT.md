# Zynapse API — Product Knowledge Base

## What is Zynapse?
Zynapse is ZkAGI's developer API platform. It's the infrastructure layer that powers ZkTerminal and any third-party app. Developers use Zynapse APIs to add privacy-preserving AI capabilities to their own apps — image gen, video gen, ZK proof document Q&A, and more. One API key, all AI capabilities.

**Tagline:** "One API. All of AI. Privacy included."

**Base URL:** `https://zynapse.zkagi.ai`

**Target audience:** Developers, startups, enterprises building AI-powered apps who need privacy, crypto integration, or don't want to depend on OpenAI/Google.

## API Endpoints

### 1. Generate ZK Proof for a Document
Upload any document → get a cryptographic proof artifact back.
```
POST /v1/generate_proof
Content-Type: multipart/form-data
Header: X-API-Key: <your_key>
Body: file (PDF/image/text)

Response: { proof_version, doc_hash, created_at, segments }
```
**Use cases:** Healthcare records, legal documents, financial reports — prove document authenticity without exposing content.

### 2. Knowledgebase Q&A with Proof
Ask questions about a document using the proof from step 1.
```
POST /v1/ask
Content-Type: multipart/form-data
Header: X-API-Key: <your_key>
Body: query (string) + proof_file (JSON from /v1/generate_proof)

Response: { answer, references, used_proof, latency_ms }
```
**Example:** Upload a medical report → generate proof → ask "What were the test results?" → get answer with proof that it came from YOUR document.

### 3. Generate Image
Text-to-image rendering on ZkAGI's GPU infrastructure.
```
POST /v1/generate/image
Content-Type: application/json
Header: X-API-Key: <your_key>
Body: { prompt, width, height, num_steps, guidance, seed, strength }

Response: PNG image bytes
```

### 4. Generate Video
Text-to-video rendering.
```
POST /v1/generate-video
Content-Type: application/json
Header: X-API-Key: <your_key>
Body: { prompt, fast_mode, lora_scale, num_frames, aspect_ratio, sample_shift, sample_steps, frames_per_second, sample_guide_scale }

Response: { job_id, status, eta_seconds, download_url }
```
**Modes:** Fast / Balanced / Quality

### 5. Admin: User & API Key Management
```
POST /add-user          — Add new user
POST /generate-api-key  — Create API key with scopes + TTL
POST /delete-api-key    — Revoke an API key
```

## Quick Reference Table

| Feature | Method | Path | Auth | Content-Type |
|---------|--------|------|------|-------------|
| Ask with proof | POST | `/v1/ask` | X-API-Key | multipart/form-data |
| Generate proof | POST | `/v1/generate_proof` | X-API-Key | multipart/form-data |
| Generate image | POST | `/v1/generate/image` | X-API-Key | application/json |
| Generate video | POST | `/v1/generate-video` | X-API-Key | application/json |
| Generate API key | POST | `/generate-api-key` | Admin | application/json |
| Delete API key | POST | `/delete-api-key` | Admin | application/json |

## Key Differentiators vs Competitors

| Feature | Zynapse | OpenAI API | Google Gemini | Replicate |
|---------|---------|-----------|---------------|-----------|
| Image gen | ✅ | ✅ (DALL-E) | ✅ (Imagen) | ✅ |
| Video gen | ✅ | ❌ | Limited | ✅ |
| ZK proof Q&A | ✅ | ❌ | ❌ | ❌ |
| Privacy-preserving | ✅ (ZK + TEE) | ❌ | ❌ | ❌ |
| Crypto payments | ✅ (ETH + SOL) | ❌ | ❌ | ❌ |
| Self-hosted GPU infra | ✅ (DePIN) | ❌ | ❌ | Partially |
| Document provenance | ✅ (ZK proofs) | ❌ | ❌ | ❌ |
| x402 micropayments | ✅ (coming) | ❌ | ❌ | ❌ |

## What Makes Zynapse Special

1. **Privacy by Default:** Every API call runs on ZkAGI's decentralized GPU network with ZK proofs. Your prompts, documents, and data are never stored or used for training.

2. **Document Provenance (ZK Proofs):** No other API offers this. Upload a document → get a cryptographic proof → ask questions with verifiable answers. Revolutionary for healthcare, legal, finance.

3. **One API, Everything:** Image gen, video gen, lip-sync, document Q&A, proof generation — all from one API key. No juggling 5 different services.

4. **Crypto-Native:** Pay with ETH or SOL. API keys with scopes and TTL. Built for Web3 developers.

5. **DePIN Infrastructure:** Powered by a decentralized network of GPU providers, not a single data center. More resilient, more private, more censorship-resistant.

## Analogies for Videos
- "OpenAI charges you to use their API and keeps your data. Zynapse gives you the same power but your data stays YOUR data."
- "One API key. Image gen. Video gen. Lip-sync. Document Q&A with cryptographic proof. Try doing THAT with OpenAI."
- "Imagine proving a medical diagnosis is real without showing anyone the actual medical records. That's what ZK proof Q&A does."
- "Building an AI app? Don't give OpenAI your users' data. Use Zynapse. Same capabilities, zero surveillance."

## Problems Zynapse Solves
- Developers forced to use OpenAI/Google APIs that harvest user data
- No existing API offers ZK proof document verification
- Healthcare/legal apps need AI Q&A without HIPAA/compliance violations
- Web3 developers need crypto payment options for AI APIs
- Enterprise customers need privacy guarantees for sensitive documents

## Code Examples for Videos

### Python — Generate Image
```python
import requests
r = requests.post('https://zynapse.zkagi.ai/v1/generate/image',
  headers={'X-API-Key': 'YOUR_KEY', 'Content-Type': 'application/json'},
  json={"prompt": "a tiger wearing sunglasses", "width": 1024, "height": 1024}
)
open('tiger.png', 'wb').write(r.content)
```

### Node.js — ZK Proof Q&A
```javascript
// Step 1: Generate proof from document
const proofForm = new FormData();
proofForm.append("file", fs.createReadStream("medical_report.pdf"));
const proof = await fetch("https://zynapse.zkagi.ai/v1/generate_proof", {
  method: "POST",
  headers: { "X-API-Key": API_KEY },
  body: proofForm
}).then(r => r.json());

// Step 2: Ask question with proof
const askForm = new FormData();
askForm.append("query", "What were the blood test results?");
askForm.append("proof_file", new Blob([JSON.stringify(proof)]), "proof.json");
const answer = await fetch("https://zynapse.zkagi.ai/v1/ask", {
  method: "POST",
  headers: { "X-API-Key": API_KEY },
  body: askForm
}).then(r => r.json());
// { answer: "Hemoglobin: 14.2...", used_proof: true }
```

## Links
- API Docs: https://docs.zkagi.ai/docs/getting-started/zynapse
- Base URL: https://zynapse.zkagi.ai
- GitHub: https://github.com/ZkAGI

## Demo Videos (Screen Recordings)
```
products/zynapse/demo-clips/
├── api-image-gen.mp4          ← curl command → image generated
├── api-video-gen.mp4          ← curl command → video job started → download
├── zk-proof-qa.mp4            ← Upload doc → generate proof → ask question → verified answer
└── api-key-management.mp4     ← Generate key → set scopes → test
```
