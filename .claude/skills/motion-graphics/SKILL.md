# Motion Graphics Components — Skill Guide

Use these Remotion components for **data-driven scenes** that would look better as clean motion graphics than as LTX-2.3 video clips. They render pixel-perfect 1920x1080 frames with smooth spring animations.

## When to Use Motion Graphics vs LTX-2 Video

| Scenario | Use |
|----------|-----|
| Showing a price, stat, or number | **Motion graphic** (PriceTicker, DataMetric) |
| Revealing a product with features/URL | **Motion graphic** (ProductShowcase) |
| Comparing old vs new, before/after | **Motion graphic** (AnimatedComparison) |
| Showing multiple metrics side-by-side | **Motion graphic** (StatGrid) |
| Introducing a trending news topic | **Motion graphic** (NewsHeadline) |
| Character action, environment, abstract visuals | **LTX-2.3 video** |
| Cinematic b-roll, mood shots | **LTX-2.3 video** or **Ken Burns image** |

**RULE: Use 1-2 motion graphic scenes per video MAX.** Don't overuse them — they work best as contrast against video/image scenes.

**BEST PLACEMENT:**
- **Hook scene** (scene 0-1): DataMetric or NewsHeadline for a shocking stat or trending topic
- **Product reveal** (scene 2-3): ProductShowcase or StatGrid
- **CTA scene** (final scene): ProductShowcase with URL

---

## Available Components

### Import

```tsx
import {
  PriceTicker,
  DataMetric,
  NewsHeadline,
  ProductShowcase,
  StatGrid,
  AnimatedComparison,
} from "../components/motion-graphics";
```

---

### 1. `PriceTicker`

Crypto price display with counter roll, arrow bounce, and percentage change.

```tsx
<PriceTicker
  symbol="BTC"
  price="$118,520"
  change="+4.2%"
  isPositive={true}
  accentColor="#F59E0B"
  durationInFrames={240}
/>
```

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `symbol` | string | yes | Ticker symbol (e.g. "BTC", "ETH") |
| `price` | string | yes | Formatted price (e.g. "$118,520") |
| `change` | string | yes | Change percentage (e.g. "+4.2%") |
| `isPositive` | boolean | yes | Green arrow up or red arrow down |
| `accentColor` | string | no | Border/glow color (default: #7C3AED) |
| `durationInFrames` | number | yes | Scene duration |

---

### 2. `DataMetric`

Big stat reveal — number counts up with easing, label slides in below.

```tsx
<DataMetric
  value="$140B"
  label="Lost to crypto hacks since 2017"
  sublabel="Source: Chainalysis 2026 Report"
  accentColor="#EF4444"
  durationInFrames={240}
/>
```

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `value` | string | yes | The big number (e.g. "$140B", "847", "99.9%") |
| `label` | string | yes | Description text below |
| `sublabel` | string | no | Optional source or secondary text |
| `accentColor` | string | no | Accent color (default: #7C3AED) |
| `durationInFrames` | number | yes | Scene duration |

---

### 3. `NewsHeadline`

Trending topic intro with typewriter headline and tag badge.

```tsx
<NewsHeadline
  tag="TRENDING"
  headline="Bitcoin breaks $120k as institutional FOMO hits new highs"
  source="CoinDesk, March 2026"
  accentColor="#EF4444"
  durationInFrames={240}
/>
```

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `tag` | string | yes | Badge text (e.g. "BREAKING", "TRENDING") |
| `headline` | string | yes | Main headline |
| `source` | string | no | Attribution text |
| `accentColor` | string | no | Tag/line color (default: #EF4444) |
| `durationInFrames` | number | yes | Scene duration |

---

### 4. `ProductShowcase`

Product feature highlight — name springs in, features pop one-by-one, URL glows.

```tsx
<ProductShowcase
  name="PawPad"
  tagline="The seedless crypto wallet"
  features={["TEE-secured keys", "AI trading agent", "Multi-chain DeFi", "No seed phrase"]}
  url="paw.zkagi.ai"
  accentColor="#06B6D4"
  durationInFrames={300}
/>
```

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | yes | Product name |
| `tagline` | string | yes | One-line description |
| `features` | string[] | yes | 2-5 feature bullet points |
| `url` | string | yes | Product URL |
| `accentColor` | string | no | Accent color (default: #7C3AED) |
| `durationInFrames` | number | yes | Scene duration |

---

### 5. `StatGrid`

Multi-metric comparison — cards appear staggered with spring, values count up.

```tsx
<StatGrid
  title="The Zero-Employee Advantage"
  stats={[
    { value: "15", label: "Traditional employees" },
    { value: "0", label: "ZkAGI employees" },
    { value: "$80k", label: "Monthly burn (old)" },
    { value: "$49", label: "Monthly API cost" },
  ]}
  accentColor="#8B5CF6"
  durationInFrames={300}
/>
```

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | no | Optional heading above grid |
| `stats` | `{ value: string; label: string }[]` | yes | 2-4 stat items |
| `accentColor` | string | no | Card accent (default: #7C3AED) |
| `durationInFrames` | number | yes | Scene duration |

---

### 6. `AnimatedComparison`

Side-by-side comparison — center divider draws, items slide in from each side.

```tsx
<AnimatedComparison
  left={{
    title: "Traditional",
    items: ["15 employees", "$80k/month", "3 months to launch", "Data breaches"],
    color: "#EF4444",
  }}
  right={{
    title: "ZkAGI",
    items: ["0 employees", "$49/month", "3 days to launch", "ZK-proven privacy"],
    color: "#10B981",
  }}
  accentColor="#7C3AED"
  durationInFrames={300}
/>
```

**Props:**
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `left` | `{ title: string; items: string[]; color?: string }` | yes | Left side (usually the "bad" option) |
| `right` | `{ title: string; items: string[]; color?: string }` | yes | Right side (usually the "good" option) |
| `accentColor` | string | no | Divider color (default: #7C3AED) |
| `durationInFrames` | number | yes | Scene duration |

---

## Integration Pattern

A motion graphic scene **replaces** the video clip + Ken Burns images for that scene. The audio and subtitle overlays still work the same way.

```tsx
{/* Motion graphic scene — no video clip or images needed */}
<Sequence from={START[1]} durationInFrames={S1}>
  {/* Motion graphic fills the entire scene */}
  <DataMetric
    value="$847"
    label="Monthly API subscription cost before Zynapse"
    accentColor="#EF4444"
    durationInFrames={S1}
  />
  {/* Standard overlays still apply */}
  <BottomGradient intensity={0.7} />
  <TopicBadge label="THE PROBLEM" color="#EF4444" durationInFrames={S1} />
  <WordPopSubtitles text={scenes[1].dialogue} accentColor="#EF4444" durationInFrames={S1}
    highlightWords={["API", "bills", "subscriptions"]} />
  <Audio src={staticFile("audio/scene-1.wav")} />
</Sequence>
```

**Key points:**
- Motion graphic scenes do NOT need `scene-N-a.mp4` video or `scene-N-b.png` images
- Skip image generation and video clip generation for these scenes
- The component provides its own full-screen background
- Subtitle, TopicBadge, BottomGradient, and Audio layers overlay as normal
- ScreenShake can optionally wrap the motion graphic for impact

## Scene Type in Screenplay

When writing the screenplay, mark each scene with a visual type:

```
Scene 1: "THE PROBLEM"
Type: motion-graphic (DataMetric)
Dialogue: "Eight hundred forty-seven dollars. That's what one developer spent monthly on AI API subscriptions."
Visual: DataMetric showing "$847" with label "Monthly API cost"
```

vs.

```
Scene 2: "THE DISCOVERY"
Type: video
Dialogue: "Then he found Zynapse. One API. One bill. Zero drama."
Visual: Developer at laptop, discovering Zynapse dashboard, camera zooms into screen
```

This tells the pipeline to skip image/video generation for motion-graphic scenes.

---

## ComfyUI Motion Graphics Pipeline (Advanced)

For higher-quality motion graphics, use `generate-motion-clips.py` which renders PIL templates and feeds them through LTX-2.3 image-to-video at low strength for subtle ambient motion.

### How It Works

1. **PIL Template Rendering** — creates a 768x512 PNG with clean typography on a dark gradient background
2. **LTX-2.3 Image-to-Video** — feeds the template to ComfyUI at **low strength (0.2-0.3)** to add subtle motion (particle drift, glow pulses, gentle camera) while preserving the text/layout
3. **Output** — a 3.88s (97 frames at 25fps) video clip with professional ambient motion

### Template Types

| Type | Visual | Use Case |
|------|--------|----------|
| `metric` | Big number + label centered | Shocking stat reveal |
| `comparison` | Two-column left vs right | Before/after contrast |
| `product` | Product name + features + URL | Product showcase / CTA |
| `headline` | News headline with tag badge | Trending topic intro |
| `price` | Ticker symbol + price + change% | Crypto price display |
| `grid` | 2x2 or 1x4 stat cards | Multi-metric comparison |

### Usage

```bash
python3 generate-motion-clips.py --type metric --value "\$847" --label "Monthly API cost" --output scene-1-a.mp4
python3 generate-motion-clips.py --type product --name "PawPad" --tagline "The seedless wallet" --features "TEE keys,AI agent,Multi-chain" --url "paw.zkagi.ai" --output scene-5-a.mp4
```

### Key Details

- Motion prompt focuses on ambient effects: particles, glows, subtle camera push
- Negative prompt includes: "text change, letter change, number change, layout shift"
- The low i2v strength (0.25) preserves the template layout while adding life
- Font: Inter-Bold.ttf stored in `assets/fonts/`
- These clips can replace React motion-graphic components in the Remotion composition

### Fallback

The React/Remotion motion-graphic components (PriceTicker, DataMetric, etc.) still work as a fallback. If ComfyUI is unavailable, use them directly in the composition instead.
