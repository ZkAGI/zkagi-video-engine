#!/usr/bin/env python3
"""
Generate LinkedIn carousel slides (1080x1080 PNG) from a JSON definition.

Usage:
  python3 generate-carousel.py --input slides.json
  python3 generate-carousel.py --json '{"date":"2026-03-14","slides":[...]}'
  cat slides.json | python3 generate-carousel.py

Each slide is rendered as a 1080x1080 PNG with dark gradient backgrounds,
accent colors, and optional AI-generated background images.
"""

import argparse
import io
import json
import math
import os
import random
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

W, H = 1080, 1080

FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "Inter-Bold.ttf")

# Dark gradient colors (matches video engine aesthetic)
BG_TOP = (15, 12, 35)
BG_BOTTOM = (8, 6, 22)

# Accent color palette
ACCENT_COLORS = {
    "purple": "#7C3AED",
    "teal":   "#06B6D4",
    "red":    "#EF4444",
    "amber":  "#F59E0B",
    "green":  "#10B981",
}

# Image generation servers
PRIMARY_IMG_SERVER = "http://45.251.34.28:8010/generate"
ZYNAPSE_IMG_SERVER = "https://zynapse.zkagi.ai/v1/generate/image"
ZYNAPSE_API_KEY = "758b5e2a-f9f5-4531-a062-6de90371ab9f"

# ---------------------------------------------------------------------------
# Font helpers (same pattern as generate-motion-clips.py)
# ---------------------------------------------------------------------------

def _ensure_font():
    """Download Inter-Bold.ttf if it doesn't exist locally."""
    if os.path.isfile(FONT_BOLD_PATH):
        return
    os.makedirs(FONT_DIR, exist_ok=True)
    url = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
    zip_path = os.path.join(FONT_DIR, "Inter.zip")
    print(f"Downloading Inter font from {url} ...")
    urllib.request.urlretrieve(url, zip_path)
    import zipfile
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith("Inter-Bold.ttf"):
                data = zf.read(name)
                with open(FONT_BOLD_PATH, "wb") as f:
                    f.write(data)
                print(f"Extracted {name} -> {FONT_BOLD_PATH}")
                break
        else:
            for name in zf.namelist():
                if "Bold" in name and name.endswith(".ttf"):
                    data = zf.read(name)
                    with open(FONT_BOLD_PATH, "wb") as f:
                        f.write(data)
                    print(f"Extracted {name} -> {FONT_BOLD_PATH}")
                    break
    if os.path.isfile(zip_path):
        os.remove(zip_path)
    if not os.path.isfile(FONT_BOLD_PATH):
        print("WARNING: Could not extract Inter-Bold.ttf; using default font.")


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Load Inter-Bold at the given size, falling back to default."""
    try:
        return ImageFont.truetype(FONT_BOLD_PATH, size)
    except (IOError, OSError):
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Drawing utilities
# ---------------------------------------------------------------------------

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_gradient(draw, w, h, c1, c2):
    """Vertical linear gradient."""
    for i in range(h):
        t = i / max(h - 1, 1)
        c = lerp_color(c1, c2, t)
        draw.line([(0, i), (w, i)], fill=c)


def draw_dark_bg(img):
    """Standard dark background gradient on an RGBA image."""
    draw = ImageDraw.Draw(img)
    draw_gradient(draw, W, H, BG_TOP, BG_BOTTOM)
    return draw


def add_glow(img, x, y, radius, color, intensity=60):
    """Soft radial glow at (x, y) on an RGBA image."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -3):
        alpha = int(intensity * (1 - r / radius))
        od.ellipse([x - r, y - r, x + r, y + r], fill=(*color, alpha))
    return Image.alpha_composite(img, overlay)


def draw_particles(draw, w, h, color, count=30, size_range=(1, 3)):
    """Scatter small particles across the canvas. Color should be (R,G,B)."""
    rgb = color[:3]
    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)
        s = random.randint(*size_range)
        alpha = random.randint(40, 140)
        draw.ellipse([x - s, y - s, x + s, y + s], fill=(*rgb, alpha))


def text_bbox_size(draw, text, font):
    """Return (width, height) of rendered text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text_wrapped(draw, text, x, y, max_width, font, fill=(255, 255, 255),
                      line_spacing=8):
    """Draw text with manual line wrapping. Returns total height drawn."""
    lines = []
    for raw_line in text.split("\n"):
        if not raw_line.strip():
            lines.append("")
            continue
        # Wrap each line to fit max_width
        words = raw_line.split()
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            tw, _ = text_bbox_size(draw, test, font)
            if tw > max_width and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

    total_h = 0
    for line in lines:
        _, lh = text_bbox_size(draw, line or " ", font)
        draw.text((x, y + total_h), line, fill=fill, font=font)
        total_h += lh + line_spacing
    return total_h


def draw_text_centered(draw, text, y, w, font, fill=(255, 255, 255)):
    """Draw single-line text horizontally centered."""
    tw, th = text_bbox_size(draw, text, font)
    draw.text(((w - tw) // 2, y), text, fill=fill, font=font)
    return th


def draw_text_centered_wrapped(draw, text, y, w, font, fill=(255, 255, 255),
                                line_spacing=8, max_width=None):
    """Draw multi-line text, each line horizontally centered."""
    if max_width is None:
        max_width = w - 120
    lines = []
    for raw_line in text.split("\n"):
        if not raw_line.strip():
            lines.append("")
            continue
        words = raw_line.split()
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            tw, _ = text_bbox_size(draw, test, font)
            if tw > max_width and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

    total_h = 0
    for line in lines:
        lw, lh = text_bbox_size(draw, line or " ", font)
        draw.text(((w - lw) // 2, y + total_h), line, fill=fill, font=font)
        total_h += lh + line_spacing
    return total_h


# ---------------------------------------------------------------------------
# AI background generation (with fallback)
# ---------------------------------------------------------------------------

def generate_ai_background(prompt: str) -> Image.Image | None:
    """Try to generate a 1080x1080 background image via AI servers."""
    # Try primary server
    bg = _try_primary_server(prompt)
    if bg:
        return bg
    # Try Zynapse fallback
    bg = _try_zynapse_server(prompt)
    if bg:
        return bg
    print(f"  AI background failed for: {prompt[:50]}... using gradient only")
    return None


def _try_primary_server(prompt: str) -> Image.Image | None:
    try:
        payload = json.dumps({
            "prompt": prompt,
            "width": 1080,
            "height": 1080,
            "num_steps": 20,
            "guidance": 3.5,
        }).encode()
        req = urllib.request.Request(
            PRIMARY_IMG_SERVER,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=60)
        data = resp.read()
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception as e:
        print(f"  Primary img server failed: {e}")
        return None


def _try_zynapse_server(prompt: str) -> Image.Image | None:
    try:
        payload = json.dumps({
            "prompt": prompt,
            "width": 1080,
            "height": 1080,
            "num_steps": 24,
            "guidance": 3.5,
            "strength": 1,
        }).encode()
        req = urllib.request.Request(
            ZYNAPSE_IMG_SERVER,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": ZYNAPSE_API_KEY,
            },
        )
        resp = urllib.request.urlopen(req, timeout=120)
        data = resp.read()
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception as e:
        print(f"  Zynapse img server failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Common overlays (applied to every slide)
# ---------------------------------------------------------------------------

def apply_overlays(img, slide_num, total_slides):
    """Add slide number, watermark, and progress dots."""
    draw = ImageDraw.Draw(img)

    # Slide number — bottom right
    font_num = load_font(24)
    num_text = f"{slide_num}/{total_slides}"
    nw, nh = text_bbox_size(draw, num_text, font_num)
    draw.text((W - nw - 40, H - nh - 40), num_text,
              fill=(255, 255, 255, 100), font=font_num)

    # ZkAGI watermark — top right
    font_wm = load_font(20)
    wm_text = "ZkAGI"
    ww, wh = text_bbox_size(draw, wm_text, font_wm)
    draw.text((W - ww - 40, 36), wm_text,
              fill=(124, 58, 237, 80), font=font_wm)

    # Progress dots — bottom center
    dot_r = 5
    dot_spacing = 18
    total_dot_w = total_slides * dot_spacing
    start_x = (W - total_dot_w) // 2
    dot_y = H - 45
    for i in range(total_slides):
        cx = start_x + i * dot_spacing + dot_r
        if i + 1 == slide_num:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r],
                         fill=(255, 255, 255, 220))
        else:
            draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r],
                         fill=(255, 255, 255, 60))

    return img


# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------

def render_hook(slide, img):
    """Large centered title + body with accent glow and particles."""
    accent = hex_to_rgb(slide.get("accent_color", "#7C3AED"))
    draw = draw_dark_bg(img)

    # Accent glow behind title area
    img = add_glow(img, W // 2, H // 2 - 80, 350, accent, intensity=40)
    draw = ImageDraw.Draw(img)

    # Particles
    draw_particles(draw, W, H, accent, count=40, size_range=(1, 4))

    # Top accent line
    draw.rectangle([80, 120, W - 80, 124], fill=(*accent, 180))

    # Title
    font_title = load_font(64)
    title = slide.get("title", "")
    title_h = draw_text_centered_wrapped(draw, title, 200, W, font_title,
                                          fill=(255, 255, 255), max_width=W - 160)

    # Body
    font_body = load_font(32)
    body = slide.get("body", "")
    body_y = 200 + title_h + 40
    draw_text_centered_wrapped(draw, body, body_y, W, font_body,
                                fill=(200, 200, 220), max_width=W - 160)

    # Bottom accent line
    draw.rectangle([80, H - 130, W - 80, H - 126], fill=(*accent, 180))

    return img


def render_insight(slide, img):
    """Tag badge + left-aligned body with optional AI background."""
    accent = hex_to_rgb(slide.get("accent_color", "#06B6D4"))
    draw = draw_dark_bg(img)

    # Optional AI background
    ai_prompt = slide.get("ai_background_prompt")
    if ai_prompt:
        bg_img = generate_ai_background(ai_prompt)
        if bg_img:
            bg_img = bg_img.resize((W, H), Image.LANCZOS)
            # Dark overlay at 70% for text readability
            dark_overlay = Image.new("RGBA", (W, H), (10, 8, 25, 180))
            img = Image.alpha_composite(bg_img, dark_overlay)
            draw = ImageDraw.Draw(img)

    # Left accent border
    draw.rectangle([60, 160, 66, H - 160], fill=(*accent, 220))

    # Tag badge (if present)
    tag = slide.get("tag", "")
    content_y = 180
    if tag:
        font_tag = load_font(18)
        tw, th = text_bbox_size(draw, tag, font_tag)
        badge_x, badge_y = 90, content_y
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + tw + 24, badge_y + th + 12],
            radius=6, fill=(*accent, 160),
        )
        draw.text((badge_x + 12, badge_y + 6), tag,
                  fill=(255, 255, 255), font=font_tag)
        content_y += th + 36

    # Title
    font_title = load_font(48)
    title = slide.get("title", "")
    title_h = draw_text_wrapped(draw, title, 90, content_y, W - 180,
                                 font_title, fill=(255, 255, 255))
    content_y += title_h + 24

    # Body
    font_body = load_font(28)
    body = slide.get("body", "")
    draw_text_wrapped(draw, body, 90, content_y, W - 180,
                       font_body, fill=(190, 195, 215))

    # Subtle particles
    draw_particles(draw, W, H, accent, count=20)

    return img


def render_stat(slide, img):
    """Huge centered number with description and radial accent glow."""
    accent = hex_to_rgb(slide.get("accent_color", "#F59E0B"))
    draw = draw_dark_bg(img)

    # Radial glow behind the stat
    img = add_glow(img, W // 2, H // 2 - 40, 300, accent, intensity=50)
    draw = ImageDraw.Draw(img)

    # Big stat value
    font_val = load_font(96)
    value = slide.get("title", "")
    vw, vh = text_bbox_size(draw, value, font_val)
    draw.text(((W - vw) // 2, H // 2 - vh - 30), value,
              fill=(255, 255, 255), font=font_val)

    # Description
    font_desc = load_font(30)
    body = slide.get("body", "")
    draw_text_centered_wrapped(draw, body, H // 2 + 40, W, font_desc,
                                fill=(190, 195, 215), max_width=W - 200)

    # Accent ring
    ring_r = 200
    for r in range(ring_r, ring_r - 4, -1):
        draw.ellipse(
            [W // 2 - r, H // 2 - 40 - r, W // 2 + r, H // 2 - 40 + r],
            outline=(*accent, 30),
        )

    # Particles
    draw_particles(draw, W, H, accent, count=25)

    return img


def render_product(slide, product_name, product_url, img):
    """Product name + tagline + feature pills + URL."""
    accent = hex_to_rgb(slide.get("accent_color", "#06B6D4"))
    draw = draw_dark_bg(img)

    # Glow behind product name
    img = add_glow(img, W // 2, 280, 250, accent, intensity=45)
    draw = ImageDraw.Draw(img)

    # Product name (use slide title or fallback to global product name)
    name = slide.get("title", product_name)
    font_name = load_font(64)
    draw_text_centered(draw, name, 220, W, font_name, fill=(255, 255, 255))

    # Tagline
    tagline = slide.get("tagline", "")
    font_tag = load_font(28)
    tag_h = draw_text_centered(draw, tagline, 310, W, font_tag,
                                fill=(180, 200, 220))

    # Feature pills — 2-column grid
    features = slide.get("features", [])
    font_feat = load_font(22)
    pill_y = 400
    col_w = (W - 200) // 2

    for i, feat in enumerate(features):
        col = i % 2
        row = i // 2
        px = 100 + col * col_w
        py = pill_y + row * 70

        fw, fh = text_bbox_size(draw, feat, font_feat)
        pill_w = min(fw + 40, col_w - 20)
        pill_h = fh + 24

        # Pill background
        draw.rounded_rectangle(
            [px, py, px + pill_w, py + pill_h],
            radius=12, fill=(30, 25, 55, 200),
            outline=(*accent, 120), width=2,
        )
        # Pill text
        draw.text((px + 20, py + 12), feat,
                  fill=(220, 225, 240), font=font_feat)

    # URL box at bottom
    url = slide.get("url", product_url)
    if url:
        font_url = load_font(26)
        uw, uh = text_bbox_size(draw, url, font_url)
        box_w = uw + 60
        box_h = uh + 28
        box_x = (W - box_w) // 2
        box_y = H - 200

        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=14, fill=(*accent, 200),
        )
        draw.text((box_x + 30, box_y + 14), url,
                  fill=(255, 255, 255), font=font_url)

    # Subtle particles
    draw_particles(draw, W, H, accent, count=20)

    return img


def render_cta(slide, product_url, img):
    """Title + body + prominent URL box with multiple glows."""
    accent = hex_to_rgb(slide.get("accent_color", "#7C3AED"))
    draw = draw_dark_bg(img)

    # Multiple overlapping glows for energy
    img = add_glow(img, W // 2, H // 2, 400, accent, intensity=30)
    img = add_glow(img, W // 3, H // 3, 250, hex_to_rgb("#06B6D4"), intensity=20)
    img = add_glow(img, 2 * W // 3, 2 * H // 3, 250, hex_to_rgb("#7C3AED"), intensity=20)
    draw = ImageDraw.Draw(img)

    # Title
    font_title = load_font(56)
    title = slide.get("title", "")
    title_h = draw_text_centered_wrapped(draw, title, 280, W, font_title,
                                          fill=(255, 255, 255), max_width=W - 160)

    # Body
    font_body = load_font(28)
    body = slide.get("body", "")
    body_y = 280 + title_h + 30
    body_h = draw_text_centered_wrapped(draw, body, body_y, W, font_body,
                                         fill=(200, 205, 225), max_width=W - 200)

    # URL box
    url = product_url
    if url:
        font_url = load_font(30)
        uw, uh = text_bbox_size(draw, url, font_url)
        box_w = uw + 80
        box_h = uh + 36
        box_x = (W - box_w) // 2
        box_y = body_y + body_h + 50

        # Glow behind the box
        img = add_glow(img, W // 2, box_y + box_h // 2, 120, accent, intensity=50)
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=16, fill=(*accent, 230),
        )
        draw.text((box_x + 40, box_y + 18), url,
                  fill=(255, 255, 255), font=font_url)

    # Branding line
    font_brand = load_font(20)
    draw_text_centered(draw, "Built by ZkAGI", H - 140, W, font_brand,
                        fill=(120, 110, 160))

    # Particles
    draw_particles(draw, W, H, accent, count=35, size_range=(1, 4))

    return img


# ---------------------------------------------------------------------------
# Main rendering pipeline
# ---------------------------------------------------------------------------

def render_slide(slide, index, total, product_name, product_url):
    """Render a single slide and return the PIL Image."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    slide_type = slide.get("type", "insight")

    print(f"  Rendering slide {index + 1}/{total}: {slide_type} — {slide.get('title', '')[:50]}")

    if slide_type == "hook":
        img = render_hook(slide, img)
    elif slide_type == "insight":
        img = render_insight(slide, img)
    elif slide_type == "stat":
        img = render_stat(slide, img)
    elif slide_type == "product":
        img = render_product(slide, product_name, product_url, img)
    elif slide_type == "cta":
        img = render_cta(slide, product_url, img)
    else:
        print(f"  WARNING: Unknown slide type '{slide_type}', rendering as insight")
        img = render_insight(slide, img)

    # Apply common overlays
    img = apply_overlays(img, index + 1, total)

    return img.convert("RGB")


def generate_carousel(data: dict):
    """Main entry point: parse JSON and render all slides."""
    date = data.get("date", time.strftime("%Y-%m-%d"))
    product_name = data.get("product", "ZkAGI")
    product_url = data.get("product_url", "")
    slides = data.get("slides", [])

    if not slides:
        print("ERROR: No slides defined in input JSON")
        sys.exit(1)

    # Create output directory
    out_dir = os.path.join(os.path.dirname(__file__), "output", f"carousel-{date}")
    os.makedirs(out_dir, exist_ok=True)

    print(f"Generating {len(slides)} carousel slides...")
    print(f"  Product: {product_name} ({product_url})")
    print(f"  Output:  {out_dir}/")

    output_files = []
    for i, slide in enumerate(slides):
        img = render_slide(slide, i, len(slides), product_name, product_url)
        filename = f"slide-{i + 1}.png"
        filepath = os.path.join(out_dir, filename)
        img.save(filepath, "PNG", quality=95)
        output_files.append(filepath)
        print(f"  Saved: {filepath}")

    print(f"\nDone! {len(output_files)} slides saved to {out_dir}/")
    return output_files


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    _ensure_font()

    parser = argparse.ArgumentParser(description="Generate LinkedIn carousel slides")
    parser.add_argument("--input", "-i", help="Path to JSON file with slide definitions")
    parser.add_argument("--json", "-j", help="JSON string with slide definitions")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r") as f:
            data = json.load(f)
    elif args.json:
        data = json.loads(args.json)
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        print("ERROR: Provide input via --input FILE, --json STRING, or stdin")
        sys.exit(1)

    generate_carousel(data)


if __name__ == "__main__":
    main()
