# /carousel — Generate LinkedIn Carousel from Daily News

You are generating a LinkedIn carousel (square slide images + caption) from the latest daily crypto/AI news digest, with at least one slide promoting a ZkAGI product.

## Step 1: Gather Today's News

**Step 1a — Run ingestion to pull fresh articles:**
```bash
curl -s -X POST http://34.67.134.209:8030/ingest/run
```
Wait for completion (30-60 seconds).

**Step 1b — Fetch ONLY today's items directly:**
```bash
curl -s "http://34.67.134.209:8030/items?limit=100"
```
Filter the returned items to ONLY those with `created_at` matching today's date. Ignore all older items — the database has stale historical data mixed in.

**Step 1c — If enough fresh items (3+), use them directly as your news source.** Read the titles and any content/descriptions. You do NOT need the `/digest/daily/generate` endpoint — it mixes stale and fresh data. Build your carousel content directly from today's items.

**Step 1d — If no fresh items found**, fall back to a web search for today's top crypto/AI news:
```
Search: "crypto AI news today {date}"
```
Use the search results as your news source instead.

Extract the key stories, stats, and themes from whichever source you used.

## Step 2: Analyze News & Pick Product

From today's items, identify the **top 3-5 stories** worth featuring.

### Product rotation — MANDATORY

ZkAGI has 3 products. You MUST rotate which one is featured. **Do NOT default to Zynapse every time.**

**Rotation rule:** Use the day-of-month to rotate:
- Day % 3 == 0 → **PawPad** (`paw.zkagi.ai`) — seedless wallet, TEE security, social recovery
- Day % 3 == 1 → **ZkTerminal** (`zkterminal.zkagi.ai`) — AI playground, image/video gen, lip-sync, agents
- Day % 3 == 2 → **Zynapse** (`docs.zkagi.ai/docs/getting-started/zynapse`) — developer API, privacy AI infra

Today's date determines the product. Then **angle the news stories to connect to that product** — every product can be tied to any crypto/AI news with the right framing:

| Product | Angles that work with ANY news |
|---|---|
| **PawPad** | Security angle, self-custody, user protection, onboarding, "what if your wallet..." |
| **ZkTerminal** | Creative/builder angle, AI tools, content creation, "build with this yourself..." |
| **Zynapse** | Developer/infra angle, APIs, privacy, "power your app with...", behind-the-scenes tech |

Read the selected product's knowledge base for accurate talking points:
- PawPad: `products/pawpad/PRODUCT.md`
- Zynapse: `products/zynapse/PRODUCT.md`
- ZkTerminal: `products/zkterminal/PRODUCT.md`

### Product slide placement — VARY IT

Do NOT always put the product slide second-to-last. Mix it up:
- Sometimes slide 3 of 6 (mid-carousel, feels natural)
- Sometimes slide 4 of 7 (after building the narrative)
- Sometimes slide 2 (early hook into product)
The product slide should feel like a natural part of the story, not a bolted-on ad.

## Step 3: Write Slide Content as JSON

Create a JSON file with **5-10 slides**. Each slide has a `type` and content fields.

### Slide types

| Type | Purpose | Required fields |
|------|---------|----------------|
| `hook` | Opening slide to grab attention | `title`, `body`, `accent_color`, `ai_background_prompt` |
| `insight` | News story or analysis point | `title`, `body`, `accent_color`, `tag`, `ai_background_prompt` |
| `stat` | Big number / statistic | `title` (the number), `body` (description), `accent_color`, `ai_background_prompt` |
| `product` | ZkAGI product promotion | `title` (product name), `tagline`, `features` (list), `accent_color`, `ai_background_prompt` |
| `cta` | Call-to-action closing slide | `title`, `body`, `accent_color`, `ai_background_prompt` |

### ai_background_prompt — MANDATORY for every slide

Read `.claude/skills/image-prompt-craft/SKILL.md` FIRST, then craft a prompt for each slide.

Follow the formula: `[SUBJECT] + [ACTION/POSE] + [SETTING] + [ART STYLE] + [LIGHTING] + [CAMERA] + [QUALITY]`

Rules:
- NEVER write abstract concept prompts ("blockchain technology") — use characters, scenarios, metaphors
- Include a cartoon tiger mascot character in the scene when relevant
- Match style to emotion: hook=dramatic, insight=atmospheric, stat=data visualization, product=clean showcase, cta=warm inviting
- Always specify lighting and quality boosters
- Vary visual approaches across slides

### Slide structure rules

1. **First slide** must be type `hook` — a bold, curiosity-driving statement
2. **Middle slides** (2-3) should be `insight` or `stat` — the actual news content
3. **One `product` slide** — naturally tied to the news topic
4. **Last slide** must be type `cta` — drives action (follow, visit URL, etc.)
5. Use varied `accent_color` values: `#7C3AED` (purple), `#06B6D4` (teal), `#EF4444` (red), `#F59E0B` (amber), `#10B981` (green)

### JSON schema

```json
{
  "date": "2026-03-14",
  "product": "PawPad",
  "product_url": "paw.zkagi.ai",
  "slides": [
    {
      "type": "hook",
      "title": "Bitcoin Just Broke $120k",
      "body": "But 20% of all BTC is permanently lost.\nHere's what you need to know.",
      "accent_color": "#EF4444",
      "ai_background_prompt": "A nervous cartoon tiger clutching an enormous golden Bitcoin coin to its chest, shadowy hands reaching from every direction trying to grab it, dark vault setting with red emergency lighting and scattered crypto coins on the floor, Pixar 3D render style, dramatic red rim lighting with volumetric rays, low angle hero shot, highly detailed, sharp focus, cinematic composition"
    },
    {
      "type": "stat",
      "title": "$140B",
      "body": "Worth of crypto lost forever\nto forgotten seed phrases",
      "accent_color": "#F59E0B",
      "ai_background_prompt": "A massive pile of golden coins and crypto tokens falling into a dark bottomless pit, a tiny cartoon tiger standing at the edge looking down in shock, amber and gold volumetric light rays from the coins, Pixar 3D style, dramatic low angle, highly detailed, dark moody atmosphere, cinematic"
    },
    {
      "type": "insight",
      "title": "The Seed Phrase Problem",
      "body": "Write it down? It can be stolen.\nMemorize it? You'll forget.\nStore it digitally? It can be hacked.",
      "tag": "SECURITY",
      "accent_color": "#EF4444",
      "ai_background_prompt": "A cartoon tiger character nervously juggling three fragile glass keys while standing on a tightrope over a dark abyss, shadowy figures below waiting to catch dropped keys, dramatic red spotlight from above, Pixar 3D render, tense atmospheric lighting, cinematic wide shot, highly detailed"
    },
    {
      "type": "product",
      "title": "PawPad",
      "tagline": "The seedless crypto wallet",
      "features": ["No seed phrase needed", "TEE-secured keys", "Social recovery", "One-tap onboarding"],
      "accent_color": "#06B6D4",
      "ai_background_prompt": "A confident cartoon tiger presenting a sleek glowing teal shield-shaped wallet floating above its paw, holographic UI panels showing security features orbit around it, clean futuristic stage with teal accent lighting and subtle grid floor, Pixar 3D style, professional clean lighting, front-facing hero shot, highly detailed"
    },
    {
      "type": "cta",
      "title": "Try PawPad Today",
      "body": "Your keys. Your crypto.\nNo seed phrase required.",
      "accent_color": "#7C3AED",
      "ai_background_prompt": "A cartoon tiger mascot with a purple headset reaching toward the viewer with a warm inviting smile, a glowing purple portal doorway behind it radiating warm light, floating sparkle particles and crypto symbols, Pixar 3D render, warm purple backlighting with soft lens flare, medium close-up, highly detailed, inviting atmosphere"
    }
  ]
}
```

## Step 4: Generate the Carousel

Save the JSON to a temp file, then run:

```bash
python3 generate-carousel.py --input /tmp/carousel-slides.json
```

This will output slides to `output/carousel-{date}/slide-{N}.png`.

## Step 5: Write the LinkedIn Caption

Write a LinkedIn-optimized caption to `output/carousel-{date}/caption.txt`:

- Start with a hook line (question or bold statement)
- 2-3 short paragraphs covering the news
- Mention the ZkAGI product naturally (not salesy)
- Include the product URL
- End with a CTA: "Follow for daily crypto insights"
- Add 3-5 relevant hashtags
- Keep it under 1300 characters (LinkedIn limit for full visibility)

## Step 6: Print Summary

After everything completes, print:

```
Carousel generated!
  Slides: {count} slides
  Output: output/carousel-{date}/
  Product: {product_name} ({product_url})

Caption preview:
{first 200 chars of caption}...

Files:
  - output/carousel-{date}/slide-1.png
  - output/carousel-{date}/slide-2.png
  ...
  - output/carousel-{date}/caption.txt
```

## Rules

- ALWAYS include at least one `product` slide
- ALWAYS make the hook slide genuinely interesting (not generic)
- Keep slide text SHORT — max 3-4 lines per slide, ~15 words per line
- Make stats dramatic — round numbers, use $ or % symbols
- The product slide should feel like a natural solution to the problem discussed
- If AI image generation fails, the script handles fallback automatically — do not retry manually
- Use today's date for the output folder
