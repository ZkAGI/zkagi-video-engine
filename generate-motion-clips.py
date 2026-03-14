#!/usr/bin/env python3
"""
Generate professional motion-graphic video clips by:
1. Pre-rendering template images with PIL (768x512 PNG)
2. Feeding them to LTX-2.3 image-to-video at low strength to add subtle ambient motion

Usage examples:
  python3 generate-motion-clips.py --type metric --value "$847" --label "Monthly API cost"
  python3 generate-motion-clips.py --type comparison --left-title "Before" --left-items "Slow,Manual,Costly" --right-title "After" --right-items "Fast,Automated,Cheap"
  python3 generate-motion-clips.py --type product --name "Zynapse" --tagline "AI-powered content" --features "Image Gen,Video Gen,Audio Gen" --url "docs.zkagi.ai"
  python3 generate-motion-clips.py --type headline --tag "BREAKING" --headline "Bitcoin hits new ATH"
  python3 generate-motion-clips.py --type price --symbol "BTC" --price "118,520" --change "+5.2%" --positive
  python3 generate-motion-clips.py --type grid --title "Platform Stats" --stats "10M:API Calls,99.9%:Uptime,<50ms:Latency,1000+:Users"
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMFY_URL = "http://172.18.64.1:8001"
W, H = 768, 512

FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
FONT_PATH = os.path.join(FONT_DIR, "Inter-Bold.ttf")

MOTION_PROMPT = (
    "Subtle particle drift upward, gentle pulsing glow, slight ambient motion. "
    "No text changes, no layout shifts, no number changes."
)
NEGATIVE_PROMPT = (
    "text change, letter change, number change, layout shift, "
    "jittery, blurry, deformed"
)

# Default accent colors
DEFAULT_ACCENT = "#7C3AED"  # Purple
TEAL_ACCENT = "#06B6D4"


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

def _ensure_font():
    """Download Inter-Bold.ttf if it doesn't exist locally."""
    if os.path.isfile(FONT_PATH):
        return
    os.makedirs(FONT_DIR, exist_ok=True)
    url = (
        "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
    )
    zip_path = os.path.join(FONT_DIR, "Inter.zip")
    print(f"Downloading Inter font from {url} ...")
    urllib.request.urlretrieve(url, zip_path)
    import zipfile
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find Inter-Bold.ttf inside the archive
        for name in zf.namelist():
            if name.endswith("Inter-Bold.ttf"):
                data = zf.read(name)
                with open(FONT_PATH, "wb") as f:
                    f.write(data)
                print(f"Extracted {name} -> {FONT_PATH}")
                break
        else:
            # Fallback: look for any Bold variant
            for name in zf.namelist():
                if "Bold" in name and name.endswith(".ttf"):
                    data = zf.read(name)
                    with open(FONT_PATH, "wb") as f:
                        f.write(data)
                    print(f"Extracted {name} -> {FONT_PATH}")
                    break
    if os.path.isfile(zip_path):
        os.remove(zip_path)
    if not os.path.isfile(FONT_PATH):
        print("WARNING: Could not extract Inter-Bold.ttf; will use default font.")


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Load Inter-Bold at the given size, falling back to the default font."""
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except (IOError, OSError):
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Drawing utilities
# ---------------------------------------------------------------------------

def hex_to_rgb(h: str) -> tuple:
    """Convert '#RRGGBB' to (R, G, B)."""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB tuples."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_gradient(draw, w, h, c1, c2, direction="vertical"):
    """Fill the canvas with a smooth linear gradient."""
    steps = h if direction == "vertical" else w
    for i in range(steps):
        t = i / max(steps - 1, 1)
        c = lerp_color(c1, c2, t)
        if direction == "vertical":
            draw.line([(0, i), (w, i)], fill=c)
        else:
            draw.line([(i, 0), (i, h)], fill=c)


def draw_dark_bg(draw, w, h):
    """Standard dark blue-purple gradient background."""
    draw_gradient(draw, w, h, (15, 12, 35), (8, 6, 22))


def add_glow(img, x, y, radius, color, intensity=80):
    """Add a soft radial glow at (x, y)."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -2):
        alpha = int(intensity * (1 - r / radius))
        od.ellipse([x - r, y - r, x + r, y + r], fill=(*color, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def draw_accent_line(draw, y, w, color, thickness=2):
    """Draw a thin horizontal accent line across the full width."""
    draw.rectangle([0, y, w, y + thickness], fill=color)


def draw_rounded_card(draw, bbox, fill, radius=16):
    """Draw a rounded rectangle card background."""
    draw.rounded_rectangle(bbox, radius=radius, fill=fill)


def draw_particles(draw, w, h, color, count=25, size_range=(1, 3)):
    """Scatter small circular particles across the canvas."""
    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)
        s = random.randint(*size_range)
        draw.ellipse([x - s, y - s, x + s, y + s], fill=color)


def text_bbox_size(draw, text, font):
    """Return (width, height) of rendered text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# ---------------------------------------------------------------------------
# Template renderers
# ---------------------------------------------------------------------------

def render_metric(value: str, label: str, sublabel: str = "",
                  accent: str = DEFAULT_ACCENT) -> Image.Image:
    """Large centered metric with label beneath."""
    accent_rgb = hex_to_rgb(accent)
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    draw_dark_bg(draw, W, H)

    # Accent glow behind the value
    img = add_glow(img, W // 2, H // 2 - 30, 220, accent_rgb, intensity=50)
    draw = ImageDraw.Draw(img)

    # Thin accent line at top
    draw_accent_line(draw, 30, W, (*accent_rgb,), thickness=3)

    # Value text
    font_val = load_font(96)
    vw, vh = text_bbox_size(draw, value, font_val)
    draw.text(((W - vw) // 2, (H - vh) // 2 - 50), value,
              fill=(255, 255, 255), font=font_val)

    # Label text
    font_lbl = load_font(28)
    lw, lh = text_bbox_size(draw, label, font_lbl)
    draw.text(((W - lw) // 2, (H - vh) // 2 - 50 + vh + 20), label,
              fill=(180, 180, 200), font=font_lbl)

    # Sublabel text
    if sublabel:
        font_sub = load_font(20)
        sw, sh = text_bbox_size(draw, sublabel, font_sub)
        draw.text(((W - sw) // 2, (H - vh) // 2 - 50 + vh + 20 + lh + 12),
                  sublabel, fill=accent_rgb, font=font_sub)

    # Bottom accent line
    draw_accent_line(draw, H - 35, W, (*accent_rgb,), thickness=3)

    # Subtle particles
    draw_particles(draw, W, H, (40, 30, 70), count=30)

    return img.convert("RGB")


def render_comparison(left_title: str, left_items: list,
                      right_title: str, right_items: list) -> Image.Image:
    """Side-by-side comparison with two card columns."""
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    draw_dark_bg(draw, W, H)

    gap = 24
    card_w = (W - gap * 3) // 2
    card_h = H - gap * 2
    left_x = gap
    right_x = gap * 2 + card_w

    # Left card (reddish tint -- "before" feel)
    draw_rounded_card(draw, [left_x, gap, left_x + card_w, gap + card_h],
                      fill=(30, 18, 22), radius=14)
    # Right card (greenish tint -- "after" feel)
    draw_rounded_card(draw, [right_x, gap, right_x + card_w, gap + card_h],
                      fill=(18, 30, 22), radius=14)

    font_title = load_font(30)
    font_item = load_font(22)

    # Left column
    ltw, lth = text_bbox_size(draw, left_title, font_title)
    draw.text((left_x + (card_w - ltw) // 2, gap + 28), left_title,
              fill=(255, 120, 120), font=font_title)
    draw_accent_line(draw, gap + 28 + lth + 12, left_x + card_w,
                     (255, 80, 80), thickness=2)
    # Adjust accent line to start at left_x
    draw.rectangle([left_x + 20, gap + 28 + lth + 12,
                     left_x + card_w - 20, gap + 28 + lth + 14],
                    fill=(255, 80, 80))
    for i, item in enumerate(left_items):
        y_pos = gap + 28 + lth + 30 + i * 40
        draw.text((left_x + 32, y_pos), f"- {item}",
                  fill=(200, 180, 180), font=font_item)

    # Right column
    rtw, rth = text_bbox_size(draw, right_title, font_title)
    draw.text((right_x + (card_w - rtw) // 2, gap + 28), right_title,
              fill=(120, 255, 160), font=font_title)
    draw.rectangle([right_x + 20, gap + 28 + rth + 12,
                     right_x + card_w - 20, gap + 28 + rth + 14],
                    fill=(80, 255, 120))
    for i, item in enumerate(right_items):
        y_pos = gap + 28 + rth + 30 + i * 40
        draw.text((right_x + 32, y_pos), f"+ {item}",
                  fill=(180, 220, 190), font=font_item)

    # Center divider line
    mid_x = W // 2
    draw.rectangle([mid_x - 1, gap + 20, mid_x + 1, gap + card_h - 20],
                    fill=(60, 60, 80))

    # VS badge
    font_vs = load_font(20)
    vsw, vsh = text_bbox_size(draw, "VS", font_vs)
    badge_r = 22
    draw.ellipse([mid_x - badge_r, H // 2 - badge_r,
                  mid_x + badge_r, H // 2 + badge_r],
                 fill=(50, 40, 70))
    draw.text((mid_x - vsw // 2, H // 2 - vsh // 2), "VS",
              fill=(180, 180, 220), font=font_vs)

    draw_particles(draw, W, H, (50, 40, 70), count=20)
    return img.convert("RGB")


def render_product(name: str, tagline: str, features: list,
                   url: str) -> Image.Image:
    """Product showcase with name, tagline, feature pills, and URL."""
    accent_rgb = hex_to_rgb(TEAL_ACCENT)
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    draw_dark_bg(draw, W, H)

    # Glow behind product name
    img = add_glow(img, W // 2, 130, 200, accent_rgb, intensity=40)
    draw = ImageDraw.Draw(img)

    # Product name
    font_name = load_font(56)
    nw, nh = text_bbox_size(draw, name, font_name)
    draw.text(((W - nw) // 2, 80), name, fill=(255, 255, 255), font=font_name)

    # Tagline
    font_tag = load_font(24)
    tw, th = text_bbox_size(draw, tagline, font_tag)
    draw.text(((W - tw) // 2, 80 + nh + 16), tagline,
              fill=(160, 180, 200), font=font_tag)

    # Feature pills
    font_feat = load_font(20)
    pill_y = 80 + nh + 16 + th + 40
    total_pill_w = 0
    pill_sizes = []
    for feat in features:
        fw, fh = text_bbox_size(draw, feat, font_feat)
        pw = fw + 32
        ph = fh + 16
        pill_sizes.append((pw, ph, feat))
        total_pill_w += pw
    spacing = 16
    total_w = total_pill_w + spacing * max(len(features) - 1, 0)
    start_x = (W - total_w) // 2

    cx = start_x
    for pw, ph, feat in pill_sizes:
        draw.rounded_rectangle([cx, pill_y, cx + pw, pill_y + ph],
                               radius=ph // 2, fill=(accent_rgb[0] // 4,
                                                      accent_rgb[1] // 4,
                                                      accent_rgb[2] // 4),
                               outline=accent_rgb, width=2)
        fw, fh = text_bbox_size(draw, feat, font_feat)
        draw.text((cx + (pw - fw) // 2, pill_y + (ph - fh) // 2), feat,
                  fill=accent_rgb, font=font_feat)
        cx += pw + spacing

    # URL at bottom
    font_url = load_font(22)
    uw, uh = text_bbox_size(draw, url, font_url)
    url_y = H - 70
    draw.rounded_rectangle([(W - uw) // 2 - 20, url_y - 8,
                             (W + uw) // 2 + 20, url_y + uh + 8],
                            radius=10, fill=(20, 30, 40), outline=accent_rgb,
                            width=1)
    draw.text(((W - uw) // 2, url_y), url, fill=accent_rgb, font=font_url)

    # Accent line at top
    draw_accent_line(draw, 20, W, accent_rgb, thickness=3)

    draw_particles(draw, W, H, (accent_rgb[0] // 3, accent_rgb[1] // 3,
                                 accent_rgb[2] // 3), count=30)
    return img.convert("RGB")


def render_headline(tag: str, headline: str,
                    source: str = "") -> Image.Image:
    """Breaking-news style headline card."""
    accent_rgb = hex_to_rgb("#EF4444")  # Red for breaking news
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    draw_dark_bg(draw, W, H)

    # Tag badge (e.g. "BREAKING")
    font_tag = load_font(18)
    tw, th = text_bbox_size(draw, tag.upper(), font_tag)
    badge_x = (W - tw - 24) // 2
    badge_y = 120
    draw.rounded_rectangle([badge_x, badge_y, badge_x + tw + 24,
                             badge_y + th + 12],
                            radius=(th + 12) // 2, fill=accent_rgb)
    draw.text((badge_x + 12, badge_y + 6), tag.upper(),
              fill=(255, 255, 255), font=font_tag)

    # Headline -- wrap if needed
    font_hl = load_font(42)
    # Simple word-wrap
    words = headline.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        test_w, _ = text_bbox_size(draw, test, font_hl)
        if test_w > W - 100:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    hl_y = badge_y + th + 12 + 30
    for line in lines:
        lw, lh = text_bbox_size(draw, line, font_hl)
        draw.text(((W - lw) // 2, hl_y), line,
                  fill=(255, 255, 255), font=font_hl)
        hl_y += lh + 10

    # Source
    if source:
        font_src = load_font(18)
        sw, sh = text_bbox_size(draw, source, font_src)
        draw.text(((W - sw) // 2, hl_y + 20), source,
                  fill=(120, 120, 140), font=font_src)

    # Red accent lines
    draw_accent_line(draw, 50, W, accent_rgb, thickness=3)
    draw_accent_line(draw, H - 50, W, accent_rgb, thickness=3)

    # Glow behind headline
    img = add_glow(img, W // 2, H // 2, 200, accent_rgb, intensity=30)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, W, H, (60, 20, 20), count=20)
    return img.convert("RGB")


def render_price(symbol: str, price: str, change: str,
                 positive: bool = True) -> Image.Image:
    """Crypto/stock price ticker card."""
    green = (34, 197, 94)
    red = (239, 68, 68)
    accent_rgb = green if positive else red
    arrow = "^" if positive else "v"

    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    draw_dark_bg(draw, W, H)

    # Glow behind price area
    img = add_glow(img, W // 2, H // 2, 220, accent_rgb, intensity=40)
    draw = ImageDraw.Draw(img)

    # Symbol
    font_sym = load_font(36)
    sw, sh = text_bbox_size(draw, symbol, font_sym)
    draw.text(((W - sw) // 2, 100), symbol, fill=(180, 180, 200),
              font=font_sym)

    # Price
    price_str = f"${price}"
    font_price = load_font(80)
    pw, ph = text_bbox_size(draw, price_str, font_price)
    draw.text(((W - pw) // 2, 160), price_str, fill=(255, 255, 255),
              font=font_price)

    # Change badge
    change_str = f"{arrow} {change}"
    font_chg = load_font(32)
    cw, ch = text_bbox_size(draw, change_str, font_chg)
    badge_x = (W - cw - 28) // 2
    badge_y = 160 + ph + 24
    draw.rounded_rectangle([badge_x, badge_y, badge_x + cw + 28,
                             badge_y + ch + 14],
                            radius=(ch + 14) // 2, fill=(accent_rgb[0] // 5,
                                                          accent_rgb[1] // 5,
                                                          accent_rgb[2] // 5),
                            outline=accent_rgb, width=2)
    draw.text((badge_x + 14, badge_y + 7), change_str, fill=accent_rgb,
              font=font_chg)

    # Sparkline decoration at the bottom
    import math
    sparkline_y = H - 80
    points = []
    for x in range(60, W - 60):
        t = (x - 60) / (W - 120)
        if positive:
            y = sparkline_y - int(30 * t + 15 * math.sin(t * 12))
        else:
            y = sparkline_y + int(30 * t - 15 * math.sin(t * 12)) - 40
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=accent_rgb, width=2)

    # Accent lines
    draw_accent_line(draw, 30, W, accent_rgb, thickness=3)
    draw_accent_line(draw, H - 30, W, accent_rgb, thickness=3)

    draw_particles(draw, W, H, (accent_rgb[0] // 4, accent_rgb[1] // 4,
                                 accent_rgb[2] // 4), count=25)
    return img.convert("RGB")


def render_grid(title: str, stats: list) -> Image.Image:
    """Grid of stat cards (value:label pairs)."""
    accent_rgb = hex_to_rgb(DEFAULT_ACCENT)
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    draw_dark_bg(draw, W, H)

    # Title
    font_title = load_font(32)
    tw, th = text_bbox_size(draw, title, font_title)
    draw.text(((W - tw) // 2, 35), title, fill=(255, 255, 255),
              font=font_title)
    draw_accent_line(draw, 35 + th + 12, W, accent_rgb, thickness=2)

    # Grid layout: determine rows and columns
    n = len(stats)
    if n <= 3:
        cols = n
    elif n <= 4:
        cols = 2
    elif n <= 6:
        cols = 3
    else:
        cols = 4
    rows = (n + cols - 1) // cols

    grid_top = 35 + th + 30
    grid_bottom = H - 30
    avail_h = grid_bottom - grid_top
    avail_w = W - 60

    card_w = (avail_w - (cols - 1) * 16) // cols
    card_h = (avail_h - (rows - 1) * 16) // rows

    font_val = load_font(36)
    font_lbl = load_font(16)

    for i, (val, lbl) in enumerate(stats):
        row = i // cols
        col = i % cols
        cx = 30 + col * (card_w + 16)
        cy = grid_top + row * (card_h + 16)

        # Card background
        draw_rounded_card(draw, [cx, cy, cx + card_w, cy + card_h],
                          fill=(22, 18, 40), radius=12)

        # Card border highlight
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h],
                               radius=12, outline=(50, 40, 80), width=1)

        # Value centered
        vw, vh = text_bbox_size(draw, val, font_val)
        draw.text((cx + (card_w - vw) // 2, cy + (card_h - vh) // 2 - 14),
                  val, fill=accent_rgb, font=font_val)

        # Label centered below value
        lw, lh = text_bbox_size(draw, lbl, font_lbl)
        draw.text((cx + (card_w - lw) // 2,
                   cy + (card_h - vh) // 2 - 14 + vh + 8),
                  lbl, fill=(140, 140, 160), font=font_lbl)

    # Glow behind grid center
    img = add_glow(img, W // 2, (grid_top + grid_bottom) // 2, 200,
                   accent_rgb, intensity=25)
    draw = ImageDraw.Draw(img)
    draw_particles(draw, W, H, (40, 30, 60), count=20)
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# ComfyUI: Image upload + I2V workflow
# ---------------------------------------------------------------------------

def upload_image(image_path: str) -> str:
    """Upload an image to ComfyUI and return the server-side filename."""
    filename = os.path.basename(image_path)
    with open(image_path, "rb") as f:
        file_data = f.read()

    # Build multipart/form-data manually (no external deps)
    boundary = f"----PythonBoundary{random.randint(100000, 999999)}"
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += (
        f'Content-Disposition: form-data; name="image"; '
        f'filename="{filename}"\r\n'
    ).encode()
    body += b"Content-Type: image/png\r\n\r\n"
    body += file_data
    body += b"\r\n"
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="overwrite"\r\n\r\n'
    body += b"true\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    server_name = result.get("name", filename)
    print(f"  Uploaded image: {server_name}")
    return server_name


def build_i2v_workflow(image_name: str, prefix: str, seed: int,
                       strength: float = 0.25) -> dict:
    """
    Build an LTX-2.3 image-to-video workflow for ComfyUI.

    Uses DualCLIPLoader, LTXVPreprocess, LTXVImgToVideo at low strength
    to preserve the template layout while adding subtle ambient motion.
    """
    return {
        # 1: CheckpointLoaderSimple -> MODEL(0), CLIP(1, unused), VAE(2)
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors",
            },
        },
        # 2: DualCLIPLoader -> CLIP(0)
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "gemma_3_12B_it.safetensors",
                "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                "type": "ltx",
            },
        },
        # 3: LoraLoaderModelOnly -> MODEL(0)
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": "ltx-2.3-distilled-lora-384.safetensors",
                "strength_model": 1.0,
            },
        },
        # 4: LoadImage -> IMAGE(0)
        "4": {
            "class_type": "LoadImage",
            "inputs": {
                "image": image_name,
            },
        },
        # 5: LTXVPreprocess -> IMAGE(0)
        "5": {
            "class_type": "LTXVPreprocess",
            "inputs": {
                "image": ["4", 0],
                "img_compression": 35,
            },
        },
        # 6: CLIPTextEncode (positive) -> CONDITIONING(0)
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": MOTION_PROMPT,
                "clip": ["2", 0],
            },
        },
        # 7: CLIPTextEncode (negative) -> CONDITIONING(0)
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": NEGATIVE_PROMPT,
                "clip": ["2", 0],
            },
        },
        # 8: LTXVConditioning -> positive(0), negative(1)
        "8": {
            "class_type": "LTXVConditioning",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "frame_rate": 25,
            },
        },
        # 9: LTXVImgToVideo -> positive(0), negative(1), latent(2)
        "9": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["8", 0],
                "negative": ["8", 1],
                "vae": ["1", 2],
                "image": ["5", 0],
                "width": W,
                "height": H,
                "length": 97,
                "batch_size": 1,
                "strength": strength,
            },
        },
        # 10: LTXVScheduler -> SIGMAS(0)
        "10": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 8,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["9", 2],
            },
        },
        # 11: RandomNoise -> NOISE(0)
        "11": {
            "class_type": "RandomNoise",
            "inputs": {
                "noise_seed": seed,
            },
        },
        # 12: CFGGuider -> GUIDER(0)
        "12": {
            "class_type": "CFGGuider",
            "inputs": {
                "model": ["3", 0],
                "positive": ["8", 0],
                "negative": ["8", 1],
                "cfg": 1.0,
            },
        },
        # 13: KSamplerSelect -> SAMPLER(0)
        "13": {
            "class_type": "KSamplerSelect",
            "inputs": {
                "sampler_name": "euler",
            },
        },
        # 14: SamplerCustomAdvanced -> LATENT(0), denoised(1)
        "14": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["11", 0],
                "guider": ["12", 0],
                "sampler": ["13", 0],
                "sigmas": ["10", 0],
                "latent_image": ["9", 2],
            },
        },
        # 15: VAEDecode -> IMAGE(0)
        "15": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["14", 0],
                "vae": ["1", 2],
            },
        },
        # 16: CreateVideo -> VIDEO(0)
        "16": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["15", 0],
                "fps": 25.0,
            },
        },
        # 17: SaveVideo
        "17": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["16", 0],
                "filename_prefix": prefix,
                "format": "mp4",
                "codec": "h264",
            },
        },
    }


def submit_workflow(workflow: dict) -> str:
    """Submit a workflow to ComfyUI and return the prompt_id."""
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["prompt_id"]


def poll_completion(prompt_id: str, timeout: int = 300) -> dict | None:
    """Poll ComfyUI history until the workflow completes or times out."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(
                f"{COMFY_URL}/history/{prompt_id}"
            ) as resp:
                history = json.loads(resp.read())
            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {}).get("status_str", "")
                if status == "error":
                    msgs = entry.get("status", {}).get("messages", [])
                    print(f"  ERROR: {msgs}")
                    return None
                outputs = entry.get("outputs", {})
                if outputs:
                    return outputs
        except Exception as e:
            print(f"  Poll error: {e}")
        time.sleep(5)
    print(f"  TIMEOUT after {timeout}s")
    return None


def download_video(outputs: dict, dest: str) -> bool:
    """Find the MP4 file in ComfyUI outputs and download it."""
    for nid, out in outputs.items():
        for key in ["gifs", "videos", "images"]:
            if key in out:
                for item in out[key]:
                    fn = item.get("filename", "")
                    subfolder = item.get("subfolder", "")
                    if fn.endswith(".mp4") or fn.endswith(".webm"):
                        url = (
                            f"{COMFY_URL}/view?"
                            f"filename={urllib.parse.quote(fn)}&type=output"
                        )
                        if subfolder:
                            url += f"&subfolder={urllib.parse.quote(subfolder)}"
                        urllib.request.urlretrieve(url, dest)
                        size = os.path.getsize(dest)
                        print(f"  Downloaded: {dest} ({size:,} bytes)")
                        return True
    print("  No video file found in outputs")
    return False


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def generate_motion_clip(template_type: str, args: argparse.Namespace):
    """Render a template image, upload it, run I2V, and download the result."""

    # 1. Ensure font is available
    _ensure_font()

    # 2. Render the template image
    print(f"\n{'=' * 60}")
    print(f"Rendering template: {template_type}")
    print(f"{'=' * 60}")

    if template_type == "metric":
        img = render_metric(
            value=args.value,
            label=args.label,
            sublabel=getattr(args, "sublabel", "") or "",
            accent=getattr(args, "accent", DEFAULT_ACCENT) or DEFAULT_ACCENT,
        )
    elif template_type == "comparison":
        img = render_comparison(
            left_title=args.left_title,
            left_items=[s.strip() for s in args.left_items.split(",")],
            right_title=args.right_title,
            right_items=[s.strip() for s in args.right_items.split(",")],
        )
    elif template_type == "product":
        img = render_product(
            name=args.name,
            tagline=args.tagline,
            features=[s.strip() for s in args.features.split(",")],
            url=args.url,
        )
    elif template_type == "headline":
        img = render_headline(
            tag=args.tag,
            headline=args.headline,
            source=getattr(args, "source", "") or "",
        )
    elif template_type == "price":
        img = render_price(
            symbol=args.symbol,
            price=args.price,
            change=args.change,
            positive=args.positive,
        )
    elif template_type == "grid":
        pairs = []
        for entry in args.stats.split(","):
            parts = entry.strip().split(":", 1)
            if len(parts) == 2:
                pairs.append((parts[0].strip(), parts[1].strip()))
            else:
                pairs.append((parts[0].strip(), ""))
        img = render_grid(title=args.title, stats=pairs)
    else:
        print(f"Unknown template type: {template_type}")
        sys.exit(1)

    # Determine output path
    output = getattr(args, "output", None)
    if not output:
        output = f"public/scenes/motion-{template_type}.mp4"
    output = os.path.abspath(output)
    os.makedirs(os.path.dirname(output), exist_ok=True)

    # Save the template PNG (next to the output video)
    template_png = output.rsplit(".", 1)[0] + "-template.png"
    img.save(template_png, "PNG")
    print(f"  Template saved: {template_png}")

    # 3. Upload the template image to ComfyUI
    print(f"\nUploading template to ComfyUI...")
    server_image_name = upload_image(template_png)

    # 4. Build and submit the I2V workflow
    seed = random.randint(1, 2**31)
    prefix = os.path.splitext(os.path.basename(output))[0].replace("-", "_")
    workflow = build_i2v_workflow(
        image_name=server_image_name,
        prefix=prefix,
        seed=seed,
        strength=0.25,
    )
    print(f"\nSubmitting I2V workflow (seed={seed}, strength=0.25)...")
    prompt_id = submit_workflow(workflow)
    print(f"  Prompt ID: {prompt_id}")

    # 5. Poll for completion
    print(f"  Polling for completion...")
    outputs = poll_completion(prompt_id, timeout=300)
    if not outputs:
        print("  FAILED: workflow did not complete")
        sys.exit(1)

    # 6. Download the result
    if not download_video(outputs, output):
        print("  FAILED: could not download video")
        sys.exit(1)

    # 7. Verify duration
    try:
        dur = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", output],
            capture_output=True, text=True,
        )
        print(f"  Duration: {dur.stdout.strip()}s")
    except FileNotFoundError:
        print("  (ffprobe not found, skipping duration check)")

    print(f"\n{'=' * 60}")
    print(f"Motion clip generated: {output}")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate professional motion-graphic video clips.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--type", required=True,
        choices=["metric", "comparison", "product", "headline", "price",
                 "grid"],
        help="Template type to render.",
    )
    parser.add_argument("--output", "-o", default=None,
                        help="Output MP4 path (default: public/scenes/motion-<type>.mp4)")

    # metric
    parser.add_argument("--value", help="[metric] Large value text")
    parser.add_argument("--label", help="[metric/price] Label text")
    parser.add_argument("--sublabel", default="",
                        help="[metric] Smaller sublabel text")
    parser.add_argument("--accent", default=DEFAULT_ACCENT,
                        help="[metric] Accent hex color (default: #7C3AED)")

    # comparison
    parser.add_argument("--left-title", help="[comparison] Left column title")
    parser.add_argument("--left-items",
                        help="[comparison] Comma-separated left items")
    parser.add_argument("--right-title",
                        help="[comparison] Right column title")
    parser.add_argument("--right-items",
                        help="[comparison] Comma-separated right items")

    # product
    parser.add_argument("--name", help="[product] Product name")
    parser.add_argument("--tagline", help="[product] Product tagline")
    parser.add_argument("--features",
                        help="[product] Comma-separated feature list")
    parser.add_argument("--url", help="[product] Product URL")

    # headline
    parser.add_argument("--tag", help="[headline] Tag badge text (e.g. BREAKING)")
    parser.add_argument("--headline", help="[headline] Headline text")
    parser.add_argument("--source", default="",
                        help="[headline] Source attribution")

    # price
    parser.add_argument("--symbol", help="[price] Ticker symbol (e.g. BTC)")
    parser.add_argument("--price", help="[price] Price value (e.g. 118,520)")
    parser.add_argument("--change",
                        help="[price] Change string (e.g. +5.2%%)")
    parser.add_argument("--positive", action="store_true", default=False,
                        help="[price] If set, show green (up); otherwise red (down)")

    # grid
    parser.add_argument("--title", help="[grid] Grid title")
    parser.add_argument("--stats",
                        help='[grid] Stats in "value:label,value:label" format')

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    generate_motion_clip(args.type, args)
