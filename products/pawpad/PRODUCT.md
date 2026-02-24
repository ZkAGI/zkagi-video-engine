# PawPad — Product Knowledge Base

## What is PawPad?
A seedless wallet powered by Oasis TEE (Trusted Execution Environment). No seed phrases. No passwords. Your wallet keys (EVM, Solana, Zcash) are generated and stored INSIDE a hardware-secured enclave via ROFL smart contracts. Keys never leave the TEE. Signing happens inside the enclave.

**Tagline:** "Your keys, locked in hardware. No seed phrase. No way in."

**Target audience:** Crypto users tired of losing seed phrases, new users scared of self-custody complexity.

## Core Technology

### Oasis TEE (Trusted Execution Environment)
- Hardware-isolated secure enclave on Oasis Sapphire network
- Wallet private keys generated and stored INSIDE the TEE via ROFL smart contract
- Keys never leave the TEE — signing happens inside the enclave
- Even Oasis node operators cannot see what's inside the TEE
- TOTP secret also stored here
- EVM, Solana, Zcash keys all managed inside TEE
- ROFL contract endpoint: `https://p3000.m1242.opf-testnet-rofl-25.rofl.app`

### TOTP (Google Authenticator)
- During wallet creation, a QR code is generated
- User scans with Google Authenticator
- TOTP secret stored in Oasis TEE (not on device)
- Required for: new device recovery, critical operations
- NOT required for same-device use (device is already authenticated)

### Backup System
- Encrypted backup file downloaded during wallet creation
- Contains: encrypted wallet recovery data
- Protected by TOTP — needs Google Authenticator code to unlock
- Used ONLY when recovering on a new device

## User Flows

### Flow 1: TEE Wallet Creation (including TOTP setup + backup download)
```
1. User opens PawPad → taps "Create Wallet" → selects "Seedless Wallet"
2. App communicates with Oasis TEE via ROFL contract:
   - TEE generates wallet keys internally (EVM, Solana, Zcash)
   - Keys NEVER leave the TEE
   - Public addresses returned to app
3. TOTP Setup:
   - App generates TOTP secret
   - Displays QR code on screen
   - User opens Google Authenticator → scans QR code
   - User enters 6-digit code to verify setup works
   - TOTP secret stored in Oasis TEE
4. Backup Download:
   - App creates encrypted backup file (JSON)
   - Contains encrypted recovery data
   - User prompted to save/download the file
   - THIS IS THE ONLY TIME the backup is offered
5. Wallet ready:
   - Home screen shows wallet address, balance
   - Supports: Zcash, EVM chains, Solana
   - All keys secure inside TEE
```

**What happens behind the scenes:**
```
User Device                    Oasis TEE (ROFL)
    |                               |
    |--- Create wallet request ---->|
    |                               | Generates keys inside TEE
    |                               | EVM private key in TEE
    |                               | Solana private key in TEE
    |                               | Zcash private key in TEE
    |<-- Public addresses returned--|
    |                               |
    |--- Store TOTP secret -------->|
    |                               | TOTP secret stored in TEE
    |                               |
    |--- Store via API ------------>|
    |    POST /internal/vault/store |
    |    {walletId, publicParams}   |
    |<-- {ok, walletIdHash, txHash}-|
    |                               |
    | Backup file saved locally     |
```

### Flow 2: Agent Creation & Agent Dashboard
```
1. From home screen → tap "AI Trading Agent"
2. Agent Dashboard shows:
   - Agent status (Active / Paused)
   - Performance metrics (PnL, win rate)
   - Recent trades list
3. Create/Configure Agent:
   - Select risk level: Conservative / Moderate / Aggressive
   - Set trading interval (how often agent checks signals)
   - Choose tokens to trade (SOL, ZEC)
   - Enable/Disable toggle
4. How agent trades:
   - Agent receives signals from Zynapse AI
   - When signal is bullish with high confidence:
     a. Agent builds unsigned transaction
     b. Sends signing request to Oasis TEE
     c. TEE signs transaction internally (keys never leave)
     d. Signed transaction returned and broadcast to chain
   - All trades visible in PnL Dashboard
5. PnL Dashboard:
   - Profit/Loss chart over time
   - Individual trade history with entry/exit
   - Win rate percentage
   - Cumulative returns
```

### Flow 3: Recovery of Keys (New Device)
```
1. User lost phone / got new device
2. Opens PawPad → taps "Recover Wallet" → selects "Seedless Wallet"
3. Upload/paste backup file (the JSON saved during creation)
4. Enter current 6-digit TOTP code from Google Authenticator
   - Code verified against TOTP secret in Oasis TEE
   - If valid → device authenticated
5. New device now authorized to interact with TEE
6. Wallet restored:
   - Same address, same balance
   - Keys still safe inside TEE (never moved, never extracted)
   - Can sign transactions immediately
```

**What happens behind the scenes:**
```
New Device                     Oasis TEE (ROFL)
    |                               |
    |--- Upload backup + TOTP ----->|
    |    (checked against stored    |
    |     TOTP secret in TEE)       |
    |<-- TOTP valid, device auth'd -|
    |                               |
    | Device now authorized         |
    | to request signing from TEE   |
    |                               |
    |--- Retrieve wallet info ----->|
    |    POST /internal/vault/      |
    |    retrieve {walletId}        |
    |<-- {ok, public addresses} ----|
    |                               |
    | Wallet fully restored         |
    | Same addresses, ready to sign |
```

### Same Device Signing (daily use)
```
1. User wants to send transaction
2. Device already authenticated with TEE
3. App sends signing request to Oasis TEE
4. TEE signs internally — keys never leave the enclave
5. Signed transaction returned to app → broadcast to chain
```

## Key Facts for Video Scripts

### Problems PawPad Solves
- $140 billion in crypto permanently lost from lost seed phrases
- 20% of all Bitcoin is inaccessible
- Seed phrases: write 24 words on paper, lose paper = lose everything
- Custodial wallets (Coinbase, Binance): easy but they control your funds, can freeze you
- Current wallets force a choice: security OR convenience. PawPad gives both.

### PawPad USPs (Unique Selling Points)
- **Seedless**: No 24 words to write down. Ever.
- **Passwordless**: No password on same device. Already authenticated.
- **Self-custodial**: YOUR keys, not Coinbase's, not Binance's. Yours.
- **TEE-secured**: Keys live in hardware enclave. Even node operators can't see them.
- **Recoverable**: Lost your phone? Backup file + Google Authenticator = wallet back.
- **AI trading**: Built-in autonomous trading agent with PnL tracking.
- **Multi-chain**: Zcash, EVM chains, Solana — all from one wallet.

### Analogies for Videos
- "Seed phrases are like writing your bank password on a napkin and hoping you don't lose it"
- "PawPad locks your keys in a vault that nobody can break into — not even the people who built the vault"
- "It's like a bank vault that only opens for you. Lose your card? Your backup and Google Authenticator get you a new one."
- "Your keys never leave the TEE. It's like signing documents inside a bulletproof room — the signed paper comes out, but the pen never leaves."

### Links
- App: https://paw.zkagi.ai
- GitHub: https://github.com/ZkAGI/pawpad_oasis_backend, https://github.com/ZkAGI/PawPad_App_Frontend/tree/oasis
- Android APK: Available on Google Drive
- iOS: TestFlight ready
- Demo video: Available on Google Drive

## Demo Videos (Screen Recordings)

These are real product screen recordings provided by the team. Used for product showcase scenes in generated videos.

### Available Demo Clips:
```
products/pawpad/demo-clips/
├── tee-wallet-creation.mp4    ← Full flow: create → TOTP QR scan → verify code → backup download
├── agent-dashboard.mp4        ← Agent creation, config, PnL dashboard, trade history
└── key-recovery.mp4           ← Recovery: upload backup → enter TOTP → wallet restored
```

### How to Use Demo Clips in Videos:
- Claude Code reads this PRODUCT.md to understand what's shown in each clip
- Demo clips are spliced into Remotion composition between AI-generated scenes
- Voiceover explains what's happening on screen
- Before demo: AI scene builds hype ("Let me show you how easy this is...")
- During demo: Real product footage with TTS narration
- After demo: AI scene with CTA ("Try it yourself at paw.zkagi.ai")

### Demo Clip Timestamps (update after recording):
**tee-wallet-creation.mp4:**
- 0:00-0:03 — Welcome screen, "Create Wallet" button
- 0:03-0:06 — Select "Seedless Wallet"
- 0:06-0:12 — TOTP QR code displayed
- 0:12-0:18 — Google Authenticator scan + 6-digit code entry
- 0:18-0:25 — Backup file download prompt + save
- 0:25-0:30 — Wallet created, home screen with address

**agent-dashboard.mp4:**
- 0:00-0:05 — Tap "AI Trading Agent" from home
- 0:05-0:12 — Agent dashboard overview (status, metrics)
- 0:12-0:20 — Configure agent (risk level, tokens, interval)
- 0:20-0:30 — PnL dashboard, trade history, win rate

**key-recovery.mp4:**
- 0:00-0:05 — Welcome screen, "Recover Wallet"
- 0:05-0:12 — Upload/paste backup file
- 0:12-0:18 — Enter TOTP code from Google Authenticator
- 0:18-0:25 — Wallet restored, same address confirmed
