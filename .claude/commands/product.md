# /product — Add Product Context

You are adding product context (text, images, videos, voices) to the video engine's product knowledge base.

## Current Product Structure

```
products/
├── pawpad/
│   ├── PRODUCT.md          # Product knowledge base
│   ├── demo-clips/         # Screen recordings, product demos (.mp4)
│   ├── images/             # Reference images, screenshots, logos (.png/.jpg)
│   └── voices/             # Product-specific voice references (.wav)
├── zkterminal/
│   ├── PRODUCT.md
│   ├── demo-clips/
│   ├── images/
│   └── voices/
└── zynapse/
    ├── PRODUCT.md
    ├── demo-clips/
    ├── images/
    └── voices/

voices/                     # Global voice references (paw.wav, pad.wav)
public/video/               # Global video assets (ending.mp4, etc.)
```

## Step 1: Ask which product

Use AskUserQuestion to ask:
- **Which product?** Options: PawPad, ZkTerminal, Zynapse, New Product
- If "New Product": ask for the product name, then create `products/{name}/PRODUCT.md` with a blank template

## Step 2: Ask what type of context to add

Use AskUserQuestion to ask:
- **What do you want to add?** Options:
  - **Product info** — Update PRODUCT.md with features, links, descriptions, API details, pricing, target audience, USPs
  - **Demo video** — Add a screen recording or product demo clip (.mp4) to demo-clips/
  - **Reference image** — Add screenshots, logos, UI mockups (.png/.jpg) to images/
  - **Voice reference** — Add a voice .wav file for TTS cloning to voices/

## Step 3: Handle each type

### Product info
- Ask the user to describe what to add (feature, endpoint, description, link, etc.)
- Read the existing `products/{product}/PRODUCT.md`
- Append or update the relevant section
- Keep the existing format and structure
- DO NOT rewrite the whole file — only add/update the specific section

### Demo video
- Ask the user for the file path (local path or URL)
- Ask for a short description of what the clip shows
- Create the `demo-clips/` folder if it doesn't exist: `mkdir -p products/{product}/demo-clips/`
- Copy the file: `cp {source} products/{product}/demo-clips/{descriptive-name}.mp4`
- Get the video duration with ffprobe
- Update PRODUCT.md to reference the new clip under a "## Demo Clips" section:
  ```
  - `demo-clips/{name}.mp4` (duration: Xs) — Description
  ```

### Reference image
- Ask the user for the file path
- Ask for a short description
- Create the `images/` folder if it doesn't exist: `mkdir -p products/{product}/images/`
- Copy the file: `cp {source} products/{product}/images/{descriptive-name}.png`
- Update PRODUCT.md to reference it under a "## Reference Images" section:
  ```
  - `images/{name}.png` — Description
  ```

### Voice reference
- Ask the user for:
  1. The .wav file path
  2. The reference text (exact words spoken in the audio)
  3. A name for the voice
- Create the `voices/` folder if it doesn't exist: `mkdir -p products/{product}/voices/`
- Copy the file: `cp {source} products/{product}/voices/{name}.wav`
- Save the reference text: write to `products/{product}/voices/{name}.txt`
- Update PRODUCT.md to reference it under a "## Voices" section:
  ```
  - `voices/{name}.wav` — ref_text: "exact words here"
  ```

## Step 4: Confirm

After adding, show the user:
- What was added and where
- The updated section of PRODUCT.md

## New Product Template

When creating a new product, use this template for PRODUCT.md:

```markdown
# {Product Name}

## Overview
{Brief description}

## Links
- Website: {url}
- Docs: {url}

## Key Features
- {feature 1}
- {feature 2}

## Target Audience
{who is this for}

## USP (Unique Selling Point)
{what makes this different}

## Video Talking Points
{key messages to hit in promotional videos}

## Demo Clips
{none yet}

## Reference Images
{none yet}

## Voices
{none yet}
```

## Rules
- NEVER delete existing content — only ADD or UPDATE
- Keep file names lowercase with hyphens (e.g., `wallet-creation-flow.mp4`)
- Always verify files exist before copying (check with ls)
- Always get video duration with ffprobe after copying
- Always confirm the update with the user before writing
