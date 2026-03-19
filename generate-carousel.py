#!/usr/bin/env python3
"""
Generate LinkedIn carousel slides (1080x1080 PNG) from a JSON definition.

Usage:
  python3 generate-carousel.py --input slides.json
  python3 generate-carousel.py --json '{"date":"2026-03-14","slides":[...]}'
  cat slides.json | python3 generate-carousel.py

Each slide is rendered as a 1080x1080 PNG with professional dark-theme design
and ZkAGI tiger mascot characters.
"""

import argparse
import io
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

W, H = 1080, 1080
PAD = 60  # outer padding

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(SCRIPT_DIR, "assets", "fonts")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "Inter-Bold.ttf")
CHAR_DIR = os.path.join(SCRIPT_DIR, "assets", "characters")
LOGO_PATH = os.path.join(SCRIPT_DIR, "assets", "branding", "logo_transparent.png")

# Logo cache
_logo_cache: Image.Image | None = None

# Dark gradient colors
BG_TOP = (18, 14, 40)
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

# Character image cache
_char_cache: dict[str, Image.Image] = {}

def get_logo(size: int = 48) -> Image.Image | None:
    """Load and cache the ZkAGI transparent logo, resized to given height."""
    global _logo_cache
    if _logo_cache is not None:
        if _logo_cache.height != size:
            ratio = size / _logo_cache.height
            return _logo_cache.resize((int(_logo_cache.width * ratio), size), Image.LANCZOS)
        return _logo_cache.copy()
    if not os.path.isfile(LOGO_PATH):
        return None
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        _logo_cache = logo
        ratio = size / logo.height
        return logo.resize((int(logo.width * ratio), size), Image.LANCZOS)
    except Exception:
        return None


# Style constants for prompt crafting (from image-prompt-craft skill)
# Professional, sophisticated visual language — LinkedIn-safe, no alarming words
CAROUSEL_ART_STYLE = (
    "premium cinematic 3D render, ray tracing, subsurface scattering, "
    "volumetric lighting, soft ambient occlusion, photorealistic stylized characters, "
    "polished finish, depth of field"
)
CAROUSEL_QUALITY = (
    "ultra detailed, 8K resolution, sharp focus, cinematic composition, "
    "refined color palette, professional illustration quality, artstation trending, "
    "unreal engine 5, octane render quality"
)

# ---------------------------------------------------------------------------
# Font helpers
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


def load_font(size: int) -> ImageFont.FreeTypeFont:
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


def draw_rich_bg(img, accent, slide_type="hook", seed=0):
    """Rich fallback background with mesh gradients, orbs, and abstract shapes.
    Used when AI image servers are unavailable."""
    import random
    rng = random.Random(seed)

    draw = ImageDraw.Draw(img)
    draw_gradient(draw, W, H, BG_TOP, BG_BOTTOM)

    # --- Large blurred accent orbs (mesh gradient effect) ---
    orb_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    orb_positions = {
        "hook":    [(-100, -100, 500), (W + 100, H + 100, 450), (W // 2, H // 2, 300)],
        "insight": [(W, 0, 400), (0, H, 350), (W // 3, H // 3, 250)],
        "stat":    [(W // 2, H // 3, 450), (-50, H, 300), (W, 0, 350)],
        "product": [(0, 0, 400), (W, H // 2, 350), (W // 2, H, 300)],
        "cta":     [(W // 2, 0, 400), (0, H, 350), (W, H // 2, 300)],
    }
    positions = orb_positions.get(slide_type, orb_positions["hook"])

    # Primary accent orb
    accent_dark = tuple(max(0, c // 3) for c in accent)
    accent_mid = tuple(max(0, c // 2) for c in accent)
    # Secondary color (complementary shift)
    secondary = (accent[2], accent[0], accent[1])

    orb_colors = [accent_dark, accent_mid, tuple(c // 4 for c in secondary)]
    od = ImageDraw.Draw(orb_layer)
    for (ox, oy, orad), color in zip(positions, orb_colors):
        # Offset slightly randomly
        ox += rng.randint(-50, 50)
        oy += rng.randint(-50, 50)
        for r in range(orad, 0, -3):
            alpha = int(45 * (1 - r / orad) ** 0.6)
            od.ellipse([ox - r, oy - r, ox + r, oy + r], fill=(*color, alpha))

    # Blur the orb layer for soft mesh effect
    orb_layer = orb_layer.filter(ImageFilter.GaussianBlur(radius=40))
    img = Image.alpha_composite(img, orb_layer)

    # --- Abstract geometric shapes (glassmorphism style) ---
    shapes_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shapes_layer)

    num_shapes = rng.randint(3, 6)
    for _ in range(num_shapes):
        shape_type = rng.choice(["rect", "circle", "line"])
        alpha = rng.randint(8, 25)
        sx = rng.randint(-100, W)
        sy = rng.randint(-100, H)

        if shape_type == "rect":
            sw = rng.randint(80, 300)
            sh = rng.randint(80, 300)
            sd.rounded_rectangle(
                [sx, sy, sx + sw, sy + sh],
                radius=rng.randint(8, 30),
                fill=(*accent, alpha),
                outline=(*accent, alpha + 10),
                width=1,
            )
        elif shape_type == "circle":
            sr = rng.randint(60, 200)
            sd.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                       fill=(*accent, alpha))
        else:  # line
            ex = sx + rng.randint(100, 500)
            ey = sy + rng.randint(-200, 200)
            sd.line([(sx, sy), (ex, ey)], fill=(*accent, alpha + 15), width=2)

    shapes_layer = shapes_layer.filter(ImageFilter.GaussianBlur(radius=8))
    img = Image.alpha_composite(img, shapes_layer)

    # --- Subtle noise grain texture ---
    noise_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(noise_layer)
    for _ in range(800):
        nx = rng.randint(0, W - 1)
        ny = rng.randint(0, H - 1)
        na = rng.randint(5, 20)
        nd.point((nx, ny), fill=(255, 255, 255, na))

    img = Image.alpha_composite(img, noise_layer)

    return img


def add_glow(img, x, y, radius, color, intensity=40):
    """Soft radial glow at (x, y)."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -4):
        alpha = int(intensity * (1 - r / radius))
        od.ellipse([x - r, y - r, x + r, y + r], fill=(*color, alpha))
    return Image.alpha_composite(img, overlay)


def text_bbox_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text_wrapped(draw, text, x, y, max_width, font, fill=(255, 255, 255),
                      line_spacing=10, shadow=True):
    """Draw text with line wrapping and optional drop shadow. Returns total height drawn."""
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
        _, lh = text_bbox_size(draw, line or " ", font)
        if shadow:
            # Multi-layer shadow for depth and readability against vivid backgrounds
            draw.text((x + 4, y + total_h + 5), line, fill=(0, 0, 0, 160), font=font)
            draw.text((x + 2, y + total_h + 3), line, fill=(0, 0, 0, 120), font=font)
            draw.text((x + 1, y + total_h + 2), line, fill=(0, 0, 0, 80), font=font)
        draw.text((x, y + total_h), line, fill=fill, font=font)
        total_h += lh + line_spacing
    return total_h


def draw_text_centered(draw, text, y, w, font, fill=(255, 255, 255), shadow=True):
    tw, th = text_bbox_size(draw, text, font)
    tx = (w - tw) // 2
    if shadow:
        draw.text((tx + 2, y + 3), text, fill=(0, 0, 0, 120), font=font)
        draw.text((tx + 1, y + 2), text, fill=(0, 0, 0, 80), font=font)
    draw.text((tx, y), text, fill=fill, font=font)
    return th


def draw_text_centered_wrapped(draw, text, y, w, font, fill=(255, 255, 255),
                                line_spacing=10, max_width=None, shadow=True):
    if max_width is None:
        max_width = w - 160
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
        tx = (w - lw) // 2
        if shadow:
            draw.text((tx + 4, y + total_h + 5), line, fill=(0, 0, 0, 160), font=font)
            draw.text((tx + 2, y + total_h + 3), line, fill=(0, 0, 0, 120), font=font)
            draw.text((tx + 1, y + total_h + 2), line, fill=(0, 0, 0, 80), font=font)
        draw.text((tx, y + total_h), line, fill=fill, font=font)
        total_h += lh + line_spacing
    return total_h


def measure_text_wrapped(draw, text, max_width, font, line_spacing=10):
    """Measure total height of wrapped text without drawing."""
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
        _, lh = text_bbox_size(draw, line or " ", font)
        total_h += lh + line_spacing
    return total_h


# ---------------------------------------------------------------------------
# Tiger character drawing (PIL-rendered mascot)
# ---------------------------------------------------------------------------

def _draw_tiger_avatar(size: int, theme_color: tuple, character: str = "paw") -> Image.Image:
    """Draw a stylized cartoon tiger avatar on transparent background.
    character: 'paw' (host, energetic) or 'pad' (explainer, thoughtful)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    s = size / 400  # scale factor (designed at 400px)

    # --- Body circle (torso hint) ---
    body_r = int(120 * s)
    body_cy = cy + int(100 * s)
    d.ellipse([cx - body_r, body_cy - int(60 * s), cx + body_r, body_cy + body_r],
              fill=(240, 160, 50, 200))

    # --- Head ---
    head_r = int(130 * s)
    head_cy = cy - int(20 * s)
    # Ears (behind head)
    ear_r = int(55 * s)
    ear_offset_x = int(90 * s)
    ear_offset_y = int(85 * s)
    for ex in [-1, 1]:
        ear_cx = cx + ex * ear_offset_x
        ear_cy = head_cy - ear_offset_y
        d.ellipse([ear_cx - ear_r, ear_cy - ear_r, ear_cx + ear_r, ear_cy + ear_r],
                  fill=(240, 160, 50))
        # Inner ear
        inner_r = int(35 * s)
        d.ellipse([ear_cx - inner_r, ear_cy - inner_r, ear_cx + inner_r, ear_cy + inner_r],
                  fill=(255, 200, 160))

    # Head circle
    d.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
              fill=(245, 170, 55))

    # --- Tiger stripes on forehead ---
    stripe_color = (80, 40, 10)
    stripe_w = int(8 * s)
    for i, offset in enumerate([-30, 0, 30]):
        sx = cx + int(offset * s)
        sy1 = head_cy - int(90 * s)
        sy2 = head_cy - int(45 * s)
        d.rounded_rectangle([sx - stripe_w, sy1, sx + stripe_w, sy2],
                            radius=int(4 * s), fill=stripe_color)

    # --- White muzzle area ---
    muzzle_w = int(90 * s)
    muzzle_h = int(70 * s)
    muzzle_y = head_cy + int(15 * s)
    d.ellipse([cx - muzzle_w, muzzle_y - int(10 * s),
               cx + muzzle_w, muzzle_y + muzzle_h],
              fill=(255, 245, 235))

    # --- Eyes ---
    eye_y = head_cy - int(15 * s)
    eye_spacing = int(50 * s)
    eye_r = int(22 * s)
    pupil_r = int(12 * s)
    shine_r = int(6 * s)
    for ex in [-1, 1]:
        eye_cx = cx + ex * eye_spacing
        # White
        d.ellipse([eye_cx - eye_r, eye_y - eye_r, eye_cx + eye_r, eye_y + eye_r],
                  fill=(255, 255, 255))
        # Pupil
        d.ellipse([eye_cx - pupil_r, eye_y - pupil_r + int(2 * s),
                   eye_cx + pupil_r, eye_y + pupil_r + int(2 * s)],
                  fill=(40, 30, 20))
        # Shine
        d.ellipse([eye_cx - shine_r - int(4 * s), eye_y - shine_r - int(4 * s),
                   eye_cx + shine_r - int(4 * s), eye_y + shine_r - int(4 * s)],
                  fill=(255, 255, 255))

    # --- Nose ---
    nose_y = muzzle_y + int(10 * s)
    nose_r = int(14 * s)
    d.ellipse([cx - nose_r, nose_y - int(8 * s), cx + nose_r, nose_y + int(8 * s)],
              fill=(220, 120, 120))

    # --- Mouth ---
    mouth_y = nose_y + int(16 * s)
    d.arc([cx - int(15 * s), mouth_y - int(8 * s), cx, mouth_y + int(8 * s)],
          start=0, end=180, fill=(120, 60, 60), width=int(3 * s))
    d.arc([cx, mouth_y - int(8 * s), cx + int(15 * s), mouth_y + int(8 * s)],
          start=0, end=180, fill=(120, 60, 60), width=int(3 * s))

    # --- Whiskers ---
    whisker_y = muzzle_y + int(20 * s)
    whisker_len = int(60 * s)
    for ex in [-1, 1]:
        base_x = cx + ex * int(55 * s)
        for wy_off in [-int(8 * s), int(4 * s), int(16 * s)]:
            end_x = base_x + ex * whisker_len
            d.line([(base_x, whisker_y + wy_off), (end_x, whisker_y + wy_off - int(3 * s))],
                   fill=(120, 80, 40, 180), width=max(1, int(2 * s)))

    # --- Character-specific accessory ---
    if character == "paw":
        # Headset — arc over head + ear cups
        hs_color = theme_color
        hs_w = int(6 * s)
        # Headband arc
        d.arc([cx - int(105 * s), head_cy - int(140 * s),
               cx + int(105 * s), head_cy - int(30 * s)],
              start=200, end=340, fill=hs_color, width=int(8 * s))
        # Ear cups
        cup_r = int(22 * s)
        for ex in [-1, 1]:
            cup_cx = cx + ex * int(100 * s)
            cup_cy = head_cy - int(40 * s)
            d.ellipse([cup_cx - cup_r, cup_cy - cup_r, cup_cx + cup_r, cup_cy + cup_r],
                      fill=hs_color)
            d.ellipse([cup_cx - int(14 * s), cup_cy - int(14 * s),
                       cup_cx + int(14 * s), cup_cy + int(14 * s)],
                      fill=(min(hs_color[0] + 40, 255), min(hs_color[1] + 40, 255),
                            min(hs_color[2] + 40, 255)))
        # Mic boom (left side)
        mic_start = (cx - int(100 * s), head_cy - int(20 * s))
        mic_end = (cx - int(80 * s), head_cy + int(55 * s))
        d.line([mic_start, mic_end], fill=hs_color, width=int(4 * s))
        mic_r = int(10 * s)
        d.ellipse([mic_end[0] - mic_r, mic_end[1] - mic_r,
                   mic_end[0] + mic_r, mic_end[1] + mic_r], fill=hs_color)
    else:
        # Pad — small glasses
        glass_y = eye_y
        glass_r = int(28 * s)
        glass_w = int(3 * s)
        for ex in [-1, 1]:
            glass_cx = cx + ex * int(50 * s)
            d.ellipse([glass_cx - glass_r, glass_y - glass_r,
                       glass_cx + glass_r, glass_y + glass_r],
                      outline=theme_color, width=glass_w)
        # Bridge
        d.line([(cx - int(22 * s), glass_y), (cx + int(22 * s), glass_y)],
               fill=theme_color, width=glass_w)
        # Temple arms
        for ex in [-1, 1]:
            arm_x = cx + ex * int(78 * s)
            d.line([(arm_x, glass_y - int(5 * s)),
                    (arm_x + ex * int(25 * s), glass_y - int(20 * s))],
                   fill=theme_color, width=glass_w)

    # --- Accent color ring/glow behind character ---
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    ring_r = int(160 * s)
    for r in range(ring_r, ring_r - int(30 * s), -2):
        alpha = int(25 * (1 - (ring_r - r) / (30 * s)))
        rd.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=(*theme_color, alpha))
    result = Image.alpha_composite(ring, img)

    return result


def get_character_image(character: str, size: int) -> Image.Image:
    """Get tiger character image. Tries cached AI-generated, falls back to PIL-drawn."""
    cache_key = f"{character}-{size}"
    if cache_key in _char_cache:
        return _char_cache[cache_key].copy()

    # Check for AI-generated character file
    ai_path = os.path.join(CHAR_DIR, f"{character}.png")
    if os.path.isfile(ai_path):
        fsize = os.path.getsize(ai_path)
        if fsize > 1000:  # valid image, not an error response
            try:
                img = Image.open(ai_path).convert("RGBA")
                img = img.resize((size, size), Image.LANCZOS)
                _char_cache[cache_key] = img.copy()
                return img
            except Exception:
                pass

    # Fall back to PIL-drawn tiger
    theme = (124, 58, 237) if character == "paw" else (6, 182, 212)
    img = _draw_tiger_avatar(size, theme, character)
    _char_cache[cache_key] = img.copy()
    return img


def try_generate_character(character: str):
    """Try to generate a character image via AI servers using image-prompt-craft skill."""
    os.makedirs(CHAR_DIR, exist_ok=True)
    out_path = os.path.join(CHAR_DIR, f"{character}.png")
    if os.path.isfile(out_path) and os.path.getsize(out_path) > 1000:
        return  # already cached

    # Prompts crafted using image-prompt-craft skill:
    # [SUBJECT] + [ACTION/POSE] + [SETTING] + [ART STYLE] + [LIGHTING] + [CAMERA] + [QUALITY]
    if character == "paw":
        prompt = (
            "A majestic photorealistic tiger mascot character with dark purple-tinted fur and bold stripes, "
            "wearing a stylish glowing purple gaming headset with a microphone, standing confidently "
            "with powerful posture, full body centered in frame, "
            f"{CAROUSEL_ART_STYLE}, dramatic purple rim lighting with volumetric purple glow, "
            f"front-facing hero composition, solid pure black background, "
            f"{CAROUSEL_QUALITY}, dark moody atmosphere, no text no watermark"
        )
    else:
        prompt = (
            "A wise photorealistic tiger mascot character with dark teal-tinted fur and bold stripes, "
            "wearing round glowing teal-colored glasses, standing in a thoughtful pose, "
            "full body centered in frame, "
            f"{CAROUSEL_ART_STYLE}, cool teal ambient lighting with dramatic volumetric glow, "
            f"front-facing editorial composition, solid pure black background, "
            f"{CAROUSEL_QUALITY}, dark moody atmosphere, no text no watermark"
        )

    for server_fn in [_try_primary_server, _try_zynapse_server]:
        img = server_fn(prompt)
        if img:
            img = img.resize((800, 800), Image.LANCZOS)
            img = _remove_dark_bg(img)
            img.save(out_path, "PNG")
            print(f"  Saved AI character: {out_path}")
            return
    print(f"  AI servers unavailable — using drawn {character} avatar")


def craft_slide_prompt(slide: dict, slide_type: str, product_name: str = "") -> str:
    """Craft an AI image prompt for a slide using image-prompt-craft skill principles.

    Uses: [SUBJECT] + [ACTION/POSE] + [SETTING] + [ART STYLE] + [LIGHTING] + [CAMERA] + [QUALITY]
    Language: Professional, sophisticated, LinkedIn-appropriate. No alarming or negative words.
    """
    title = slide.get("title", "")
    body = slide.get("body", "")
    # Use explicit prompt if provided
    if slide.get("ai_background_prompt"):
        base = slide["ai_background_prompt"]
        return (
            f"{base}, {CAROUSEL_ART_STYLE}, refined cinematic lighting, "
            f"elegant composition, {CAROUSEL_QUALITY}, sophisticated dark atmosphere"
        )

    accent = slide.get("accent_color", "#7C3AED")
    accent_name = {
        "#7C3AED": "regal purple", "#06B6D4": "luminous teal", "#EF4444": "vibrant crimson",
        "#F59E0B": "warm amber", "#10B981": "emerald green",
    }.get(accent, "regal purple")

    if slide_type == "hook":
        return (
            f"A majestic dark {accent_name}-toned photorealistic tiger standing in a futuristic server room corridor, "
            f"the tiger's fur is dark with {accent_name} undertones matching the environment, "
            f"towering server racks on both sides with glowing {accent_name} circuit board patterns on the ceiling, "
            f"holographic data streams, dramatic {accent_name} monochromatic neon atmosphere, "
            f"the entire scene is bathed in deep {accent_name} tones creating a unified color palette, "
            f"{CAROUSEL_ART_STYLE}, cinematic wide establishing shot with {accent_name} volumetric fog and rim lighting, "
            f"{CAROUSEL_QUALITY}, moody dark cyberpunk atmosphere, dark color-matched tiger"
        )

    elif slide_type == "insight":
        return (
            f"A photorealistic dark-furred tiger with glowing {accent_name} spectacles in a high-tech lab, "
            f"the tiger's fur has {accent_name} undertones blending with the environment, "
            f"surrounded by floating holographic screens showing data visualizations about '{title}', "
            f"sophisticated dark tech laboratory with {accent_name} accent lighting and glass surfaces, "
            f"unified {accent_name} monochromatic color palette throughout the entire scene, "
            f"{CAROUSEL_ART_STYLE}, atmospheric {accent_name} volumetric lighting with cinematic depth of field, "
            f"medium wide editorial composition, {CAROUSEL_QUALITY}, dark moody unified color scheme"
        )

    elif slide_type == "stat":
        return (
            f"A dramatic data visualization scene with massive luminous {accent_name} holographic numbers "
            f"floating in a dark void, crystalline geometric structures refracting {accent_name} light, "
            f"a dark-furred photorealistic tiger with {accent_name}-tinted fur standing on a reflective platform, "
            f"surrounded by orbiting data particles and {accent_name} light trails, "
            f"unified monochromatic {accent_name} color palette, "
            f"{CAROUSEL_ART_STYLE}, {accent_name} volumetric glow with dramatic low-angle composition, "
            f"{CAROUSEL_QUALITY}, premium dark cinematic atmosphere"
        )

    elif slide_type == "product":
        return (
            f"A powerful dark-furred photorealistic tiger with {accent_name}-tinted coat showcasing "
            f"a glowing holographic product interface, sleek futuristic showroom bathed entirely in {accent_name} lighting, "
            f"polished dark reflective surfaces, floating UI panels with {accent_name} accents, "
            f"the tiger blends seamlessly into the monochromatic {accent_name} environment, "
            f"{CAROUSEL_ART_STYLE}, clean professional {accent_name} neon illumination with reflective floor, "
            f"hero product composition, {CAROUSEL_QUALITY}, premium dark elegant atmosphere"
        )

    elif slide_type == "cta":
        return (
            f"A charismatic dark-furred photorealistic tiger with {accent_name}-tinted coat, "
            f"extending a welcoming paw toward the viewer, standing before a radiant {accent_name} portal "
            f"of light with floating luminous particles and energy wisps, "
            f"the tiger matches the {accent_name} monochromatic atmosphere perfectly, "
            f"dramatic {accent_name} backlighting with cinematic bokeh, "
            f"{CAROUSEL_ART_STYLE}, warm {accent_name} rim lighting, "
            f"medium close-up editorial composition, {CAROUSEL_QUALITY}, unified dark {accent_name} atmosphere"
        )

    # fallback
    return (
        f"An elegant scene representing '{title}', refined dark technological environment, "
        f"{CAROUSEL_ART_STYLE}, {accent_name} accent lighting, "
        f"editorial composition, {CAROUSEL_QUALITY}"
    )


def _remove_dark_bg(img: Image.Image, threshold=40) -> Image.Image:
    """Make very dark pixels transparent."""
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    for r, g, b, a in data:
        if r < threshold and g < threshold and b < threshold:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img


# ---------------------------------------------------------------------------
# AI background generation
# ---------------------------------------------------------------------------

def generate_ai_background(prompt: str) -> Image.Image | None:
    bg = _try_primary_server(prompt)
    if bg:
        return bg
    bg = _try_zynapse_server(prompt)
    if bg:
        return bg
    return None


def _try_primary_server(prompt: str) -> Image.Image | None:
    try:
        payload = json.dumps({
            "prompt": prompt, "width": 1080, "height": 1080,
            "num_steps": 28, "guidance": 4.0,
        }).encode()
        req = urllib.request.Request(
            PRIMARY_IMG_SERVER, data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=60)
        data = resp.read()
        if len(data) < 1000:
            return None
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        return None


def _try_zynapse_server(prompt: str) -> Image.Image | None:
    try:
        payload = json.dumps({
            "prompt": prompt, "width": 1080, "height": 1080,
            "num_steps": 30, "guidance": 4.0, "strength": 1,
        }).encode()
        req = urllib.request.Request(
            ZYNAPSE_IMG_SERVER, data=payload,
            headers={"Content-Type": "application/json", "X-API-Key": ZYNAPSE_API_KEY},
        )
        resp = urllib.request.urlopen(req, timeout=120)
        data = resp.read()
        if len(data) < 1000:
            return None
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Common overlays (applied to every slide)
# ---------------------------------------------------------------------------

def apply_overlays(img, slide_num, total_slides, accent):
    """Slide border, branding, progress indicator."""
    draw = ImageDraw.Draw(img)

    # --- Accent border with glow ---
    # Outer glow border (wider, softer)
    border_glow_w = 6
    draw.rounded_rectangle(
        [2, 2, W - 2, H - 2],
        radius=22, outline=(*accent, 35), width=border_glow_w,
    )
    # Inner crisp border
    border_w = 2
    draw.rounded_rectangle(
        [8, 8, W - 8, H - 8],
        radius=18, outline=(*accent, 120), width=border_w,
    )

    # --- Top-left ZkAGI logo ---
    logo = get_logo(48)
    if logo:
        logo_x, logo_y = PAD - 4, 18
        img.paste(logo, (logo_x, logo_y), logo)
        draw = ImageDraw.Draw(img)
    else:
        # Fallback text if logo file missing
        font_brand = load_font(22)
        draw.text((PAD, 28), "ZkAGI",
                  fill=(255, 255, 255, 160), font=font_brand)

    # --- Bottom bar ---
    bar_y = H - 55

    # Slide number — bottom right
    font_num = load_font(20)
    num_text = f"{slide_num}/{total_slides}"
    nw, nh = text_bbox_size(draw, num_text, font_num)
    draw.text((W - nw - PAD, bar_y), num_text,
              fill=(255, 255, 255, 120), font=font_num)

    # Progress bar — bottom center (wider, more prominent)
    bar_total_w = 260
    bar_h = 5
    bar_x = (W - bar_total_w) // 2
    # Background track
    draw.rounded_rectangle(
        [bar_x, bar_y + 8, bar_x + bar_total_w, bar_y + 8 + bar_h],
        radius=3, fill=(255, 255, 255, 50),
    )
    # Filled portion with glow
    fill_w = int(bar_total_w * slide_num / total_slides)
    if fill_w > 0:
        # Glow behind fill
        draw.rounded_rectangle(
            [bar_x - 1, bar_y + 6, bar_x + fill_w + 1, bar_y + 10 + bar_h],
            radius=4, fill=(*accent, 50),
        )
        draw.rounded_rectangle(
            [bar_x, bar_y + 8, bar_x + fill_w, bar_y + 8 + bar_h],
            radius=3, fill=(*accent, 230),
        )

    return img


# ---------------------------------------------------------------------------
# Subtle decorative elements (replacing particles)
# ---------------------------------------------------------------------------

def draw_corner_accents(draw, accent, opacity=30):
    """Bold corner bracket frames for a premium editorial look."""
    # Stronger opacity for visible framing
    a_strong = (*accent, min(opacity + 60, 180))
    a_glow = (*accent, min(opacity + 20, 80))
    line_len = 120
    line_w = 3
    glow_w = 6

    # Top-right corner bracket
    # Glow layer (wider, softer)
    draw.line([(W - PAD + 8, PAD + 40), (W - PAD + 8, PAD + 40 + line_len)],
              fill=a_glow, width=glow_w)
    draw.line([(W - PAD + 8 - line_len, PAD + 40), (W - PAD + 8, PAD + 40)],
              fill=a_glow, width=glow_w)
    # Core line
    draw.line([(W - PAD + 8, PAD + 40), (W - PAD + 8, PAD + 40 + line_len)],
              fill=a_strong, width=line_w)
    draw.line([(W - PAD + 8 - line_len, PAD + 40), (W - PAD + 8, PAD + 40)],
              fill=a_strong, width=line_w)

    # Bottom-left corner bracket
    draw.line([(PAD - 8, H - PAD - 50 - line_len), (PAD - 8, H - PAD - 50)],
              fill=a_glow, width=glow_w)
    draw.line([(PAD - 8, H - PAD - 50), (PAD - 8 + line_len, H - PAD - 50)],
              fill=a_glow, width=glow_w)
    draw.line([(PAD - 8, H - PAD - 50 - line_len), (PAD - 8, H - PAD - 50)],
              fill=a_strong, width=line_w)
    draw.line([(PAD - 8, H - PAD - 50), (PAD - 8 + line_len, H - PAD - 50)],
              fill=a_strong, width=line_w)

    # Top-left small accent (subtle, near logo)
    a_subtle = (*accent, min(opacity + 10, 60))
    draw.line([(PAD - 8, PAD + 40), (PAD - 8, PAD + 40 + 60)],
              fill=a_subtle, width=2)

    # Bottom-right small accent
    draw.line([(W - PAD + 8, H - PAD - 50), (W - PAD + 8, H - PAD - 50 - 60)],
              fill=a_subtle, width=2)


def draw_accent_line(draw, y, accent, full_width=False):
    """Thin horizontal accent line."""
    x1 = PAD if full_width else PAD + 20
    x2 = W - PAD if full_width else W - PAD - 20
    draw.line([(x1, y), (x2, y)], fill=(*accent, 60), width=1)


def draw_dot_grid(draw, accent, spacing=60, dot_r=1, opacity=20):
    """Subtle dot grid pattern across the slide."""
    a = (*accent, opacity)
    for x in range(PAD + 30, W - PAD, spacing):
        for y in range(80, H - 70, spacing):
            draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=a)


# ---------------------------------------------------------------------------
# Slide renderers
# ---------------------------------------------------------------------------

def render_hook(slide, img, ai_bg=None):
    """Opening slide — bold title, body, tiger character on right."""
    accent = hex_to_rgb(slide.get("accent_color", "#7C3AED"))

    # Use AI background or rich gradient fallback
    img = apply_ai_background(img, ai_bg, overlay_alpha=100)
    if ai_bg is None:
        img = draw_rich_bg(img, accent, "hook", seed=hash(slide.get("title", "")) & 0xFFFF)
        img = add_glow(img, W // 2, H // 2, 400, accent, intensity=25)
    draw = ImageDraw.Draw(img)

    # Subtle dot grid adds polish
    draw_dot_grid(draw, accent, spacing=50, dot_r=1, opacity=15)
    draw_corner_accents(draw, accent, opacity=50)

    # --- Layout: text on left (55%), character on right (45%) ---
    text_area_w = int(W * 0.55)
    char_size = 400

    # Measure text to vertically center — bold, impactful sizes
    font_title = load_font(72)
    font_body = load_font(28)
    title = slide.get("title", "")
    body = slide.get("body", "")

    title_h = measure_text_wrapped(draw, title, text_area_w - PAD - 20, font_title)
    body_h = measure_text_wrapped(draw, body, text_area_w - PAD - 20, font_body)
    total_text_h = title_h + 30 + body_h

    # Vertical center in usable area (80 to H-80)
    usable_top = 80
    usable_bottom = H - 80
    text_start_y = usable_top + (usable_bottom - usable_top - total_text_h) // 2

    # Bold accent bar left of text (with strong glow)
    bar_x = PAD
    # Glow behind bar (wider, more visible)
    draw.rounded_rectangle(
        [bar_x - 8, text_start_y - 20, bar_x + 18, text_start_y + total_text_h + 20],
        radius=8, fill=(*accent, 50),
    )
    # Core bar — thicker for visual impact
    draw.rounded_rectangle(
        [bar_x, text_start_y - 10, bar_x + 10, text_start_y + total_text_h + 10],
        radius=5, fill=(*accent, 255),
    )

    # Title
    draw_text_wrapped(draw, title, PAD + 20, text_start_y,
                      text_area_w - PAD - 40, font_title, fill=(255, 255, 255))

    # Body
    draw_text_wrapped(draw, body, PAD + 20, text_start_y + title_h + 30,
                      text_area_w - PAD - 40, font_body, fill=(190, 195, 220))

    # Tiger character — right side (only when no AI background, which already has characters)
    if ai_bg is None:
        char_img = get_character_image("paw", char_size)
        char_x = W - char_size - PAD + 20
        char_y = (H - char_size) // 2 + 20
        img.paste(char_img, (char_x, char_y), char_img)
        draw = ImageDraw.Draw(img)
        draw_accent_line(draw, char_y + char_size + 15, accent)

    return img


def render_insight(slide, img, ai_bg=None):
    """News/analysis slide — tag, title, body, character on right."""
    accent = hex_to_rgb(slide.get("accent_color", "#06B6D4"))

    img = apply_ai_background(img, ai_bg, overlay_alpha=110)
    if ai_bg is None:
        img = draw_rich_bg(img, accent, "insight", seed=hash(slide.get("title", "")) & 0xFFFF)
    draw = ImageDraw.Draw(img)

    draw_dot_grid(draw, accent, spacing=50, dot_r=1, opacity=12)
    draw_corner_accents(draw, accent, opacity=45)

    # --- Measure content to vertically center ---
    content_x = PAD + 20
    text_area_w = int(W * 0.60)
    char_size = 300

    font_tag_f = load_font(18)
    font_title = load_font(52)
    font_body = load_font(26)
    tag = slide.get("tag", "")
    title = slide.get("title", "")
    body = slide.get("body", "")

    tag_h = 0
    if tag:
        _, th = text_bbox_size(draw, tag, font_tag_f)
        tag_h = th + 30
    title_h = measure_text_wrapped(draw, title, text_area_w - 40, font_title)
    body_h = measure_text_wrapped(draw, body, text_area_w - 40, font_body)
    total_h = tag_h + title_h + 24 + body_h

    usable_top = 80
    usable_bottom = H - 80
    # Use 45% position (optical center — slightly above mathematical center)
    content_y = usable_top + int((usable_bottom - usable_top - total_h) * 0.42)

    # Tag badge
    if tag:
        tw, th = text_bbox_size(draw, tag, font_tag_f)
        draw.rounded_rectangle(
            [content_x, content_y, content_x + tw + 20, content_y + th + 10],
            radius=4, fill=(*accent, 180),
        )
        draw.text((content_x + 10, content_y + 5), tag,
                  fill=(255, 255, 255), font=font_tag_f)
        content_y += tag_h

    # Left accent bar (spans title + body) with strong glow
    draw.rounded_rectangle(
        [PAD - 8, content_y - 15, PAD + 18, content_y + title_h + 24 + body_h + 15],
        radius=8, fill=(*accent, 45),
    )
    draw.rounded_rectangle(
        [PAD, content_y - 5, PAD + 10, content_y + title_h + 24 + body_h + 5],
        radius=5, fill=(*accent, 255),
    )

    # Title
    draw_text_wrapped(draw, title, content_x, content_y,
                       text_area_w - 40, font_title, fill=(255, 255, 255))
    content_y += title_h + 12

    # Accent separator (only within text area, not crossing into character)
    sep_x2 = min(text_area_w, W - char_size - PAD - 20)
    draw.line([(PAD + 20, content_y), (sep_x2, content_y)],
              fill=(*accent, 60), width=1)
    content_y += 12

    # Body (keep within text area, don't overlap character)
    draw_text_wrapped(draw, body, content_x, content_y,
                       text_area_w - 40, font_body, fill=(185, 190, 215))

    # Tiger character — right side (only when no AI background)
    if ai_bg is None:
        char_img = get_character_image("pad", char_size)
        char_x = W - char_size - PAD + 20
        char_y = (H - char_size) // 2 + 20
        img.paste(char_img, (char_x, char_y), char_img)

    return img


def render_stat(slide, img, ai_bg=None):
    """Big number/statistic — centered, clean."""
    accent = hex_to_rgb(slide.get("accent_color", "#F59E0B"))

    img = apply_ai_background(img, ai_bg, overlay_alpha=110)
    if ai_bg is None:
        img = draw_rich_bg(img, accent, "stat", seed=hash(slide.get("title", "")) & 0xFFFF)
        img = add_glow(img, W // 2, H // 2 - 40, 350, accent, intensity=35)
    draw = ImageDraw.Draw(img)

    draw_dot_grid(draw, accent, spacing=50, dot_r=1, opacity=12)
    draw_corner_accents(draw, accent, opacity=45)

    # --- Centered stat ---
    font_val = load_font(100)
    font_desc = load_font(28)
    value = slide.get("title", "")
    body = slide.get("body", "")

    vw, vh = text_bbox_size(draw, value, font_val)
    body_h = measure_text_wrapped(draw, body, W - 200, font_desc)

    total_h = vh + 40 + body_h
    start_y = (H - total_h) // 2 - 20

    # Accent line above stat
    line_w = min(vw + 60, W - 2 * PAD)
    draw.rounded_rectangle(
        [(W - line_w) // 2, start_y - 25, (W + line_w) // 2, start_y - 22],
        radius=2, fill=(*accent, 140),
    )

    # Stat value
    draw.text(((W - vw) // 2, start_y), value,
              fill=(*accent, 255), font=font_val)

    # Description
    desc_y = start_y + vh + 40
    draw_text_centered_wrapped(draw, body, desc_y, W, font_desc,
                                fill=(200, 205, 225), max_width=W - 200)

    # Accent line below description
    draw.rounded_rectangle(
        [(W - line_w) // 2, desc_y + body_h + 15,
         (W + line_w) // 2, desc_y + body_h + 18],
        radius=2, fill=(*accent, 140),
    )

    # Tiger in corner (only when no AI background) — larger for visual weight
    if ai_bg is None:
        char_size = 220
        char_img = get_character_image("pad", char_size)
        img.paste(char_img, (W - char_size - PAD + 10, H - char_size - 70), char_img)

    return img


def render_product(slide, product_name, product_url, img, ai_bg=None):
    """Product showcase — character on left, info on right."""
    accent = hex_to_rgb(slide.get("accent_color", "#06B6D4"))

    img = apply_ai_background(img, ai_bg, overlay_alpha=105)
    if ai_bg is None:
        img = draw_rich_bg(img, accent, "product", seed=hash(product_name) & 0xFFFF)
        img = add_glow(img, W // 3, H // 2, 300, accent, intensity=30)
    draw = ImageDraw.Draw(img)

    draw_dot_grid(draw, accent, spacing=50, dot_r=1, opacity=12)
    draw_corner_accents(draw, accent, opacity=45)

    # --- Tiger character on left (only when no AI background) ---
    char_size = 300
    if ai_bg is None:
        char_img = get_character_image("paw", char_size)
        char_x = PAD - 10
        char_y = (H - char_size) // 2
        img.paste(char_img, (char_x, char_y), char_img)
    draw = ImageDraw.Draw(img)

    # --- Product info ---
    if ai_bg is None:
        info_x = PAD - 10 + char_size + 10
    else:
        info_x = PAD + 40  # full width when AI background provides character
    info_w = W - info_x - PAD

    # Product name — bold and impactful
    name = slide.get("title", product_name)
    font_name = load_font(56)
    nw, nh = text_bbox_size(draw, name, font_name)
    name_y = 150
    draw.text((info_x, name_y), name, fill=(255, 255, 255), font=font_name)

    # Accent line under name
    draw.rounded_rectangle(
        [info_x, name_y + nh + 12, info_x + min(nw, info_w), name_y + nh + 15],
        radius=2, fill=(*accent, 180),
    )

    # Tagline
    tagline = slide.get("tagline", "")
    font_tag = load_font(24)
    tag_y = name_y + nh + 30
    draw_text_wrapped(draw, tagline, info_x, tag_y, info_w,
                       font_tag, fill=(180, 190, 220))

    # Feature list with accent bullets
    features = slide.get("features", [])
    font_feat = load_font(22)
    feat_y = tag_y + 60
    for feat in features:
        # Accent bullet
        bullet_r = 5
        draw.ellipse([info_x + 2, feat_y + 10 - bullet_r,
                      info_x + 2 + bullet_r * 2, feat_y + 10 + bullet_r],
                     fill=(*accent, 220))
        draw.text((info_x + 22, feat_y), feat,
                  fill=(210, 215, 235), font=font_feat)
        feat_y += 46

    # URL box at bottom center
    url = slide.get("url", product_url)
    if url:
        font_url = load_font(24)
        uw, uh = text_bbox_size(draw, url, font_url)
        box_w = uw + 50
        box_h = uh + 22
        box_x = (W - box_w) // 2
        box_y = H - 120

        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=12, fill=(*accent, 200),
        )
        draw.text((box_x + 25, box_y + 11), url,
                  fill=(255, 255, 255), font=font_url)

    return img


def render_cta(slide, product_url, img, ai_bg=None):
    """Call-to-action closing slide — character on left, CTA content centered."""
    accent = hex_to_rgb(slide.get("accent_color", "#7C3AED"))

    img = apply_ai_background(img, ai_bg, overlay_alpha=100)
    if ai_bg is None:
        img = draw_rich_bg(img, accent, "cta", seed=hash(slide.get("title", "")) & 0xFFFF)
        img = add_glow(img, W // 2, H // 2, 350, accent, intensity=30)
        img = add_glow(img, W // 3, H // 3, 200, accent, intensity=20)
    draw = ImageDraw.Draw(img)

    draw_dot_grid(draw, accent, spacing=50, dot_r=1, opacity=12)
    draw_corner_accents(draw, accent, opacity=50)

    # --- Measure to vertically center everything ---
    font_title = load_font(60)
    font_body = load_font(26)
    font_url = load_font(28)
    title = slide.get("title", "")
    body = slide.get("body", "")
    url = product_url

    char_size = 260
    title_h = measure_text_wrapped(draw, title, W - 160, font_title)
    body_h = measure_text_wrapped(draw, body, W - 200, font_body)
    url_h = 0
    if url:
        _, uh = text_bbox_size(draw, url, font_url)
        url_h = uh + 32 + 35  # button height + spacing

    total_h = char_size + 20 + title_h + 20 + body_h + url_h
    start_y = (H - total_h) // 2

    # --- Tiger character centered (only when no AI background) ---
    if ai_bg is None:
        char_img = get_character_image("paw", char_size)
        char_x = (W - char_size) // 2
        img.paste(char_img, (char_x, start_y), char_img)
    draw = ImageDraw.Draw(img)

    # --- Title ---
    title_y = start_y + char_size + 20
    title_h_actual = draw_text_centered_wrapped(draw, title, title_y, W, font_title,
                                                 fill=(255, 255, 255), max_width=W - 160)

    # --- Body ---
    body_y = title_y + title_h_actual + 20
    body_h_actual = draw_text_centered_wrapped(draw, body, body_y, W, font_body,
                                                fill=(200, 205, 225), max_width=W - 200)

    # --- Prominent URL button ---
    if url:
        uw, uh = text_bbox_size(draw, url, font_url)
        box_w = uw + 70
        box_h = uh + 32
        box_x = (W - box_w) // 2
        box_y = body_y + body_h_actual + 35

        img = add_glow(img, W // 2, box_y + box_h // 2, 100, accent, intensity=40)
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=16, fill=(*accent, 240),
        )
        draw.text((box_x + 35, box_y + 16), url,
                  fill=(255, 255, 255), font=font_url)

    # "Built by ZkAGI" subtle at very bottom
    font_small = load_font(18)
    draw_text_centered(draw, "Built by ZkAGI", H - 90, W, font_small,
                        fill=(100, 95, 140))

    return img


# ---------------------------------------------------------------------------
# Main rendering pipeline
# ---------------------------------------------------------------------------

def generate_slide_background(slide: dict, slide_type: str,
                               product_name: str) -> Image.Image | None:
    """Generate an AI background for a slide using crafted prompts."""
    prompt = craft_slide_prompt(slide, slide_type, product_name)
    print(f"    Generating AI background...")
    bg = generate_ai_background(prompt)
    if bg:
        bg = bg.resize((W, H), Image.LANCZOS)
        print(f"    AI background OK")
    else:
        print(f"    AI background unavailable — using gradient fallback")
    return bg


def apply_ai_background(img: Image.Image, bg: Image.Image | None,
                         overlay_alpha: int = 180) -> Image.Image:
    """Apply an AI-generated background with minimal overlay to preserve quality.

    Uses a light vignette so AI art remains vivid and cinematic while
    keeping text readable through contrast rather than heavy overlays.
    """
    if bg is None:
        return img

    # --- Layer 1: Very light base tint — let AI art dominate ---
    base_alpha = max(overlay_alpha - 120, 30)  # much lighter to preserve AI art
    base = Image.new("RGBA", (W, H), (12, 10, 28, base_alpha))
    result = Image.alpha_composite(bg, base)

    # --- Layer 2: Subtle edge vignette only (corners/edges darken, center stays vivid) ---
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    cx, cy = W // 2, H // 2
    max_r = int(math.hypot(cx, cy))
    # Start darkening from 70% out — keeps much more of center vivid
    inner_r = int(max_r * 0.70)
    for r in range(max_r, 0, -4):
        if r > inner_r:
            t = (r - inner_r) / (max_r - inner_r)
            alpha = int(t * t * overlay_alpha * 0.45)  # gentler falloff
        else:
            alpha = 0
        vd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(8, 6, 22, alpha))
    result = Image.alpha_composite(result, vignette)

    # --- Layer 3: Left-side text readability gradient (only where text sits) ---
    text_band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(text_band)
    # Horizontal gradient: dark on left, transparent on right
    band_end = int(W * 0.55)
    for x in range(0, band_end):
        t = 1.0 - (x / band_end)
        a = int(t * t * 90)  # quadratic — strong near edge, fades quickly
        td.line([(x, 0), (x, H)], fill=(8, 6, 22, a))
    result = Image.alpha_composite(result, text_band)

    # --- Layer 4: Subtle bottom strip for UI elements ---
    bottom_band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bottom_band)
    band_start = int(H * 0.85)
    for y in range(band_start, H):
        t = (y - band_start) / (H - band_start)
        a = int(t * 70)
        bd.line([(0, y), (W, y)], fill=(8, 6, 22, a))
    result = Image.alpha_composite(result, bottom_band)

    return result


def render_slide(slide, index, total, product_name, product_url):
    """Render a single slide and return the PIL Image."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    slide_type = slide.get("type", "insight")
    accent = hex_to_rgb(slide.get("accent_color", "#7C3AED"))

    print(f"  Rendering slide {index + 1}/{total}: {slide_type} — "
          f"{slide.get('title', '')[:50]}")

    # Generate AI background for this slide
    ai_bg = generate_slide_background(slide, slide_type, product_name)

    if slide_type == "hook":
        img = render_hook(slide, img, ai_bg)
    elif slide_type == "insight":
        img = render_insight(slide, img, ai_bg)
    elif slide_type == "stat":
        img = render_stat(slide, img, ai_bg)
    elif slide_type == "product":
        img = render_product(slide, product_name, product_url, img, ai_bg)
    elif slide_type == "cta":
        img = render_cta(slide, product_url, img, ai_bg)
    else:
        print(f"  WARNING: Unknown slide type '{slide_type}', rendering as insight")
        img = render_insight(slide, img, ai_bg)

    img = apply_overlays(img, index + 1, total, accent)
    return img.convert("RGB")


def generate_carousel(data: dict):
    """Main entry point: parse JSON and render all slides."""
    carousel_date = data.get("date", time.strftime("%Y-%m-%d"))
    product_name = data.get("product", "ZkAGI")
    product_url = data.get("product_url", "")
    slides = data.get("slides", [])

    if not slides:
        print("ERROR: No slides defined in input JSON")
        sys.exit(1)

    out_dir = os.path.join(SCRIPT_DIR, "output", f"carousel-{carousel_date}")
    os.makedirs(out_dir, exist_ok=True)

    # Try to generate AI character images (cached after first success)
    print("Preparing character assets...")
    try_generate_character("paw")
    try_generate_character("pad")

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
