# /carousel — Generate LinkedIn Carousel from Daily News

You are generating a LinkedIn carousel (square slide images + caption) from the latest daily crypto/AI news digest, with at least one slide promoting a ZkAGI product.

## Step 1: Fetch the Daily Digest

Run:
```bash
curl -s http://34.67.134.209:8030/digest/daily/latest
```

If that fails or returns empty, try generating a fresh one:
```bash
curl -s -X POST http://34.67.134.209:8030/digest/daily/generate
```

Parse the JSON response. Extract the key stories, stats, and themes.

## Step 2: Analyze News & Pick Product

From the digest, identify the **top 3-5 stories** worth featuring. Then pick the **best-fit ZkAGI product** based on topic:

| Topic keywords | Product | URL |
|---|---|---|
| wallet, DeFi, security, seed phrase, self-custody, hack, theft | **PawPad** | `paw.zkagi.ai` |
| APIs, privacy, ZK, generation, AI models, infrastructure, developer tools | **Zynapse** | `docs.zkagi.ai/docs/getting-started/zynapse` |
| predictions, trading, signals, market analysis, portfolio, alpha | **ZkTerminal** | `zkterminal.zkagi.ai` |

Read the product's knowledge base for accurate talking points:
- PawPad: `products/pawpad/PRODUCT.md`
- Zynapse: `products/zynapse/PRODUCT.md`
- ZkTerminal: `products/zkterminal/PRODUCT.md`

## Step 3: Write Slide Content as JSON

Create a JSON file with **5-10 slides**. Each slide has a `type` and content fields.

### Slide types

| Type | Purpose | Required fields |
|------|---------|----------------|
| `hook` | Opening slide to grab attention | `title`, `body`, `accent_color` |
| `insight` | News story or analysis point | `title`, `body`, `accent_color`, optional `tag`, `ai_background_prompt` |
| `stat` | Big number / statistic | `title` (the number), `body` (description), `accent_color` |
| `product` | ZkAGI product promotion | `title` (product name), `tagline`, `features` (list), `accent_color` |
| `cta` | Call-to-action closing slide | `title`, `body`, `accent_color` |

### Slide structure rules

1. **First slide** must be type `hook` — a bold, curiosity-driving statement
2. **Middle slides** (2-3) should be `insight` or `stat` — the actual news content
3. **One `product` slide** — naturally tied to the news topic
4. **Last slide** must be type `cta` — drives action (follow, visit URL, etc.)
5. Use varied `accent_color` values: `#7C3AED` (purple), `#06B6D4` (teal), `#EF4444` (red), `#F59E0B` (amber), `#10B981` (green)
6. For `insight` slides, optionally add `ai_background_prompt` — a short visual description for AI-generated backgrounds

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
      "accent_color": "#EF4444"
    },
    {
      "type": "stat",
      "title": "$140B",
      "body": "Worth of crypto lost forever\nto forgotten seed phrases",
      "accent_color": "#F59E0B"
    },
    {
      "type": "insight",
      "title": "The Seed Phrase Problem",
      "body": "Write it down? It can be stolen.\nMemorize it? You'll forget.\nStore it digitally? It can be hacked.",
      "tag": "SECURITY",
      "accent_color": "#EF4444",
      "ai_background_prompt": "cracked vault door with golden light streaming through, dark moody atmosphere"
    },
    {
      "type": "product",
      "title": "PawPad",
      "tagline": "The seedless crypto wallet",
      "features": ["No seed phrase needed", "TEE-secured keys", "Social recovery", "One-tap onboarding"],
      "accent_color": "#06B6D4"
    },
    {
      "type": "cta",
      "title": "Try PawPad Today",
      "body": "Your keys. Your crypto.\nNo seed phrase required.",
      "accent_color": "#7C3AED"
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
