#!/usr/bin/env python3
"""Generate stylized scene images using Pillow when AI image servers are down."""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 768, 512
SCENE_DIR = "/home/aten/zkagi-video-engine/public/scenes"
os.makedirs(SCENE_DIR, exist_ok=True)

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def gradient(draw, w, h, c1, c2, direction="vertical"):
    for i in range(h if direction == "vertical" else w):
        t = i / (h if direction == "vertical" else w)
        c = lerp_color(c1, c2, t)
        if direction == "vertical":
            draw.line([(0, i), (w, i)], fill=c)
        else:
            draw.line([(i, 0), (i, h)], fill=c)

def radial_gradient(img, center, radius, c1, c2):
    draw = ImageDraw.Draw(img)
    cx, cy = center
    for r in range(radius, 0, -1):
        t = 1.0 - (r / radius)
        c = lerp_color(c1, c2, t)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)

def add_particles(draw, w, h, color, count=40, size_range=(1, 4)):
    for _ in range(count):
        x, y = random.randint(0, w), random.randint(0, h)
        s = random.randint(*size_range)
        alpha_color = (*color, random.randint(60, 200))
        draw.ellipse([x - s, y - s, x + s, y + s], fill=color)

def add_grid(draw, w, h, color, spacing=40):
    for x in range(0, w, spacing):
        draw.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=color, width=1)

def add_glow(img, x, y, radius, color):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -2):
        alpha = int(80 * (1 - r / radius))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*color, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay)

def draw_monitor(draw, x, y, w, h, screen_color, frame_color=(40, 40, 50)):
    # Monitor frame
    draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=frame_color)
    # Screen
    margin = 6
    draw.rectangle([x + margin, y + margin, x + w - margin, y + h - margin * 3], fill=screen_color)
    # Stand
    sw = w // 4
    draw.rectangle([x + w // 2 - sw // 2, y + h, x + w // 2 + sw // 2, y + h + 15], fill=frame_color)
    draw.rectangle([x + w // 2 - sw, y + h + 15, x + w // 2 + sw, y + h + 20], fill=frame_color)

def draw_coffee_cup(draw, x, y, color=(139, 90, 43)):
    draw.ellipse([x, y, x + 20, y + 8], fill=(160, 110, 60))
    draw.rectangle([x + 2, y + 4, x + 18, y + 25], fill=color)
    draw.arc([x + 18, y + 6, x + 28, y + 20], 270, 90, fill=color, width=2)

# ═══════════════════════════════════════════════
# SCENE 0: THE SITUATION — Solo founder, dark office
# ═══════════════════════════════════════════════
def scene_0_a():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (15, 12, 25), (8, 8, 18))
    # Desk
    draw.rectangle([100, 320, 668, 340], fill=(50, 40, 35))
    draw.rectangle([100, 340, 668, 512], fill=(40, 32, 28))
    # Laptop glow
    img = add_glow(img, 384, 280, 180, (50, 120, 200))
    draw = ImageDraw.Draw(img)
    # Laptop
    draw.polygon([(320, 320), (340, 240), (428, 240), (448, 320)], fill=(30, 30, 40))
    draw.polygon([(325, 315), (342, 245), (426, 245), (443, 315)], fill=(40, 80, 140))
    draw.rectangle([310, 320, 458, 330], fill=(45, 45, 55))
    # Coffee cups
    for cx in [180, 220, 540, 580]:
        draw_coffee_cup(draw, cx, 298)
    # Sticky notes
    for nx, nc in [(260, (255, 230, 100)), (500, (255, 150, 150)), (150, (150, 255, 150))]:
        draw.rectangle([nx, 260, nx + 30, 290], fill=nc)
    # Spotlight from above
    img = add_glow(img, 384, 100, 250, (80, 80, 100))
    # Particles (dust in light)
    draw = ImageDraw.Draw(img)
    add_particles(draw, W, H, (100, 100, 140), count=30, size_range=(1, 2))
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-0-a.png"))

def scene_0_b():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (20, 15, 30), (10, 10, 20))
    # Close-up face glow from laptop
    img = add_glow(img, 384, 256, 200, (40, 100, 180))
    draw = ImageDraw.Draw(img)
    # Silhouette of person
    draw.ellipse([334, 150, 434, 260], fill=(25, 25, 35))  # Head
    draw.rectangle([340, 260, 428, 400], fill=(25, 25, 35))  # Body
    # Invoices scattered
    for ix, iy in [(150, 350), (200, 380), (500, 340), (550, 370)]:
        draw.rectangle([ix, iy, ix + 50, iy + 35], fill=(200, 200, 210), outline=(150, 150, 160))
    # Coffee cups in foreground
    for cx in [100, 620]:
        draw_coffee_cup(draw, cx, 420)
    add_particles(draw, W, H, (80, 80, 120), count=20)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-0-b.png"))

def scene_0_c():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (35, 40, 50), (20, 22, 30))
    # Conference table
    draw.rectangle([100, 280, 668, 420], fill=(60, 50, 45))
    # Empty chairs
    for cx in [150, 250, 350, 450, 550]:
        draw.ellipse([cx - 15, 250, cx + 15, 280], fill=(45, 45, 50))
        draw.rectangle([cx - 12, 280, cx + 12, 310], fill=(45, 45, 50))
    # Single laptop on table
    draw.rectangle([350, 290, 420, 310], fill=(50, 50, 60))
    draw.polygon([(355, 290), (365, 260), (405, 260), (415, 290)], fill=(40, 80, 130))
    # Whiteboard (empty)
    draw.rectangle([200, 60, 568, 200], fill=(230, 230, 235))
    draw.rectangle([200, 60, 568, 200], outline=(180, 180, 185), width=3)
    # Fluorescent lights
    for lx in [200, 400]:
        draw.rectangle([lx, 10, lx + 100, 18], fill=(200, 200, 220))
        img = add_glow(img, lx + 50, 14, 60, (150, 150, 170))
        draw = ImageDraw.Draw(img)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-0-c.png"))

# ═══════════════════════════════════════════════
# SCENE 1: THE TWIST — Content flying out of terminal
# ═══════════════════════════════════════════════
def scene_1_a():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (10, 15, 30), (5, 8, 20))
    # Central terminal glow
    img = add_glow(img, 384, 280, 250, (200, 160, 50))
    draw = ImageDraw.Draw(img)
    # Terminal screen
    draw.rounded_rectangle([280, 200, 488, 370], radius=10, fill=(20, 25, 40))
    draw.rounded_rectangle([286, 206, 482, 360], radius=8, fill=(10, 30, 50))
    # Terminal text lines
    for ty in range(215, 350, 12):
        tw = random.randint(60, 180)
        draw.rectangle([294, ty, 294 + tw, ty + 6], fill=(50, 200, 100))
    # Flying content pieces - images
    for fx, fy, fc in [(150, 130, (200, 80, 80)), (550, 100, (80, 150, 200)), (120, 350, (200, 180, 50)),
                        (600, 320, (100, 200, 100)), (200, 80, (180, 100, 200))]:
        draw.rounded_rectangle([fx, fy, fx + 60, fy + 40], radius=4, fill=fc)
    # Investors silhouettes in back
    for sx in [100, 160, 580, 640]:
        draw.ellipse([sx - 12, 380, sx + 12, 408], fill=(35, 35, 45))
        draw.rectangle([sx - 15, 408, sx + 15, 480], fill=(35, 40, 50))
    add_particles(draw, W, H, (200, 180, 80), count=50, size_range=(1, 3))
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-1-a.png"))

def scene_1_b():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (25, 20, 35), (15, 15, 25))
    # Boardroom table
    draw.rectangle([100, 300, 668, 420], fill=(55, 45, 40))
    # Three confused investors
    for sx, suit_c in [(200, (40, 40, 60)), (384, (50, 40, 40)), (560, (35, 45, 50))]:
        draw.ellipse([sx - 18, 220, sx + 18, 260], fill=(180, 150, 130))  # Face
        draw.rectangle([sx - 25, 260, sx + 25, 380], fill=suit_c)  # Suit
        # Question mark above head
        draw.text((sx - 5, 195), "?", fill=(200, 200, 50))
    # Laptop on table
    draw.rectangle([350, 310, 420, 325], fill=(50, 50, 60))
    img = add_glow(img, 385, 310, 60, (50, 120, 200))
    draw = ImageDraw.Draw(img)
    add_particles(draw, W, H, (60, 60, 80), count=15)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-1-b.png"))

def scene_1_c():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (10, 5, 25), (20, 8, 35))
    add_grid(draw, W, H, (30, 15, 50), spacing=50)
    # Central terminal
    draw.rounded_rectangle([334, 200, 434, 320], radius=6, fill=(15, 20, 35))
    draw.rounded_rectangle([338, 204, 430, 316], radius=4, fill=(10, 30, 50))
    img = add_glow(img, 384, 260, 120, (0, 200, 200))
    draw = ImageDraw.Draw(img)
    # Content pieces connected by glowing lines
    content_pos = [(80, 80), (180, 400), (600, 100), (550, 380), (100, 250)]
    for px, py in content_pos:
        draw.line([(384, 260), (px + 30, py + 20)], fill=(0, 150, 180), width=1)
        draw.rounded_rectangle([px, py, px + 60, py + 40], radius=4, fill=(40, 30, 60))
    add_particles(draw, W, H, (100, 200, 220), count=40, size_range=(1, 3))
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-1-c.png"))

def scene_1_d():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (15, 10, 25), (25, 15, 35))
    # Person leaning back (low angle hero)
    draw.rectangle([320, 250, 448, 480], fill=(35, 35, 50))  # Body
    draw.ellipse([348, 180, 420, 260], fill=(180, 150, 130))  # Head
    # Screens behind
    for mx, my in [(100, 100), (250, 80), (500, 90), (620, 110)]:
        draw.rounded_rectangle([mx, my, mx + 90, my + 65], radius=4, fill=(15, 25, 40))
        draw.rounded_rectangle([mx + 3, my + 3, mx + 87, my + 58], radius=3, fill=(20, 60, 100))
    # Dashboard glow
    img = add_glow(img, 384, 200, 300, (50, 80, 150))
    draw = ImageDraw.Draw(img)
    add_particles(draw, W, H, (80, 120, 180), count=30)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-1-d.png"))

# ═══════════════════════════════════════════════
# SCENE 2: THE KNOWLEDGE DROP — Terminal interface
# ═══════════════════════════════════════════════
def scene_2_a():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (5, 5, 20), (15, 5, 30))
    add_grid(draw, W, H, (20, 10, 40), spacing=40)
    # Multiple floating panels
    panels = [
        (80, 80, 280, 220, (20, 50, 80), "IMAGE"),
        (300, 100, 468, 230, (50, 20, 70), "VIDEO"),
        (488, 80, 688, 220, (20, 60, 50), "AUDIO"),
    ]
    for x1, y1, x2, y2, c, label in panels:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=c)
        draw.rounded_rectangle([x1 + 4, y1 + 4, x2 - 4, y2 - 4], radius=6, fill=(c[0] + 10, c[1] + 10, c[2] + 10))
        # Simulate content
        for ty in range(y1 + 25, y2 - 15, 10):
            tw = random.randint(40, (x2 - x1) - 30)
            draw.rectangle([x1 + 12, ty, x1 + 12 + tw, ty + 5], fill=(c[0] + 40, c[1] + 40, c[2] + 40))
    # Central command line
    draw.rounded_rectangle([200, 280, 568, 420], radius=10, fill=(10, 12, 20))
    draw.rounded_rectangle([206, 286, 562, 414], radius=8, fill=(5, 15, 25))
    for ty in range(295, 405, 12):
        tw = random.randint(80, 340)
        draw.rectangle([214, ty, 214 + tw, ty + 6], fill=(0, 180, 120))
    # Neon glows
    img = add_glow(img, 180, 150, 100, (0, 150, 200))
    img = add_glow(img, 384, 165, 80, (150, 50, 200))
    img = add_glow(img, 588, 150, 100, (0, 200, 150))
    draw = ImageDraw.Draw(img)
    add_particles(draw, W, H, (100, 200, 220), count=50)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-2-a.png"))

def scene_2_b():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (8, 5, 18), (18, 8, 30))
    # Terminal on left
    draw.rounded_rectangle([50, 150, 350, 400], radius=8, fill=(10, 15, 25))
    for ty in range(165, 390, 12):
        tw = random.randint(40, 280)
        draw.rectangle([62, ty, 62 + tw, ty + 6], fill=(50, 200, 100))
    # Arrow pointing right
    draw.polygon([(380, 260), (420, 280), (380, 300)], fill=(200, 150, 50))
    # Generated image appearing
    draw.rounded_rectangle([450, 120, 718, 400], radius=10, fill=(40, 30, 60))
    # Colorful image content
    for iy in range(130, 390, 8):
        for ix in range(460, 708, 8):
            c = (random.randint(80, 220), random.randint(50, 180), random.randint(100, 230))
            draw.rectangle([ix, iy, ix + 7, iy + 7], fill=c)
    img = add_glow(img, 584, 260, 150, (180, 100, 220))
    draw = ImageDraw.Draw(img)
    add_particles(draw, W, H, (150, 100, 200), count=30)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-2-b.png"))

def scene_2_c():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (10, 5, 25), (5, 10, 30))
    # Video play button center
    img = add_glow(img, 384, 256, 180, (100, 50, 180))
    draw = ImageDraw.Draw(img)
    draw.ellipse([334, 206, 434, 306], fill=(60, 30, 100))
    draw.polygon([(370, 230), (410, 256), (370, 282)], fill=(200, 200, 220))
    # Orbiting thumbnails
    for angle_deg in range(0, 360, 60):
        a = math.radians(angle_deg)
        tx = int(384 + 200 * math.cos(a))
        ty = int(256 + 130 * math.sin(a))
        c = (random.randint(40, 80), random.randint(40, 80), random.randint(60, 120))
        draw.rounded_rectangle([tx - 30, ty - 20, tx + 30, ty + 20], radius=4, fill=c)
    # Timeline bar at bottom
    draw.rectangle([100, 430, 668, 445], fill=(30, 30, 50))
    draw.rectangle([100, 430, 400, 445], fill=(100, 50, 180))
    add_particles(draw, W, H, (130, 80, 200), count=35)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-2-c.png"))

def scene_2_d():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (8, 10, 22), (15, 8, 28))
    # Audio waveform
    center_y = 256
    for x in range(50, 718):
        h = int(30 + 80 * abs(math.sin(x * 0.05)) * abs(math.cos(x * 0.02)))
        c = lerp_color((0, 180, 200), (150, 50, 200), x / 718)
        draw.line([(x, center_y - h), (x, center_y + h)], fill=c, width=2)
    # Microphone icon center
    draw.rounded_rectangle([364, 120, 404, 200], radius=20, fill=(80, 80, 100))
    draw.rectangle([374, 200, 394, 230], fill=(70, 70, 90))
    draw.arc([354, 170, 414, 240], 0, 180, fill=(70, 70, 90), width=3)
    img = add_glow(img, 384, 180, 100, (0, 180, 220))
    draw = ImageDraw.Draw(img)
    add_particles(draw, W, H, (0, 200, 220), count=40)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-2-d.png"))

# ═══════════════════════════════════════════════
# SCENE 3: THE PAYOFF — Split scene empty office vs solo laptop
# ═══════════════════════════════════════════════
def scene_3_a():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    # Left side: cold corporate
    for y in range(H):
        t = y / H
        c = lerp_color((40, 45, 55), (25, 28, 35), t)
        draw.line([(0, y), (W // 2, y)], fill=c)
    # Right side: warm cozy
    for y in range(H):
        t = y / H
        c = lerp_color((30, 20, 15), (15, 12, 10), t)
        draw.line([(W // 2, y), (W, y)], fill=c)
    # Divider
    draw.line([(W // 2, 0), (W // 2, H)], fill=(80, 80, 90), width=2)
    # Left: empty desks
    for row in range(3):
        for col in range(3):
            dx = 50 + col * 120
            dy = 180 + row * 100
            draw.rectangle([dx, dy, dx + 80, dy + 15], fill=(50, 50, 60))
            draw.rectangle([dx + 20, dy - 40, dx + 60, dy], fill=(35, 35, 45))
    # Right: person with laptop + charts
    img = add_glow(img, 580, 280, 150, (200, 150, 50))
    draw = ImageDraw.Draw(img)
    draw.ellipse([560, 200, 600, 240], fill=(180, 150, 130))  # Head
    draw.rectangle([555, 240, 605, 350], fill=(40, 35, 50))  # Body
    # Laptop
    draw.rectangle([520, 330, 600, 345], fill=(50, 50, 60))
    draw.polygon([(525, 330), (535, 300), (585, 300), (595, 330)], fill=(30, 80, 130))
    # Green charts floating
    for cx, cy in [(650, 180), (680, 250), (640, 320)]:
        draw.rectangle([cx, cy, cx + 60, cy + 30], fill=(20, 40, 25))
        # Rising line
        for x in range(cx + 5, cx + 55, 3):
            hy = cy + 25 - int(15 * (x - cx) / 60)
            draw.rectangle([x, hy, x + 2, cy + 28], fill=(50, 200, 100))
    add_particles(draw, W, H, (150, 130, 50), count=25)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-3-a.png"))

def scene_3_b():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (10, 12, 25), (8, 8, 18))
    # Giant browser tab
    draw.rounded_rectangle([50, 30, 718, 480], radius=12, fill=(20, 22, 35), outline=(50, 50, 70), width=2)
    # Tab bar
    draw.rectangle([50, 30, 718, 65], fill=(30, 32, 45))
    draw.rounded_rectangle([60, 35, 200, 60], radius=5, fill=(40, 42, 55))
    # Sections grid
    sections = [
        (70, 80, 370, 260, "IMG GEN", (20, 60, 50)),
        (380, 80, 700, 260, "VIDEO GEN", (50, 20, 60)),
        (70, 270, 370, 460, "AUDIO GEN", (20, 40, 60)),
        (380, 270, 700, 460, "PREDICTIONS", (50, 40, 20)),
    ]
    for x1, y1, x2, y2, label, c in sections:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=6, fill=c)
        # Chart lines
        for ty in range(y1 + 30, y2 - 10, 10):
            tw = random.randint(40, (x2 - x1) - 30)
            draw.rectangle([x1 + 12, ty, x1 + 12 + tw, ty + 5], fill=(c[0] + 30, c[1] + 30, c[2] + 30))
    add_particles(draw, W, H, (80, 100, 150), count=20)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-3-b.png"))

def scene_3_c():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    # Warm sunset gradient
    gradient(draw, W, H, (200, 120, 50), (40, 20, 60))
    # Person on top of browser tab (tiny, triumphant)
    # Giant browser tab
    draw.rounded_rectangle([150, 200, 618, 500], radius=15, fill=(25, 28, 40), outline=(60, 60, 80), width=3)
    # Person standing on top
    draw.ellipse([370, 155, 398, 185], fill=(180, 150, 130))
    draw.rectangle([372, 185, 396, 230], fill=(40, 40, 60))
    # Arms raised
    draw.line([(372, 195), (350, 170)], fill=(40, 40, 60), width=4)
    draw.line([(396, 195), (418, 170)], fill=(40, 40, 60), width=4)
    # Glow behind person
    img = add_glow(img, 384, 180, 100, (250, 200, 80))
    draw = ImageDraw.Draw(img)
    # Empty office building below
    draw.rectangle([50, 420, 150, 510], fill=(30, 30, 40))
    for wy in range(425, 505, 15):
        for wx in range(55, 145, 15):
            draw.rectangle([wx, wy, wx + 8, wy + 8], fill=(20, 25, 35))
    add_particles(draw, W, H, (250, 200, 80), count=40, size_range=(1, 4))
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-3-c.png"))

# ═══════════════════════════════════════════════
# SCENE 4: MIC DROP — URL reveal with energy burst
# ═══════════════════════════════════════════════
def scene_4_a():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (5, 8, 20), (10, 5, 25))
    add_grid(draw, W, H, (15, 10, 30), spacing=50)
    # Central glow burst
    img = add_glow(img, 384, 256, 300, (0, 180, 200))
    img = add_glow(img, 384, 256, 180, (200, 180, 50))
    draw = ImageDraw.Draw(img)
    # Terminal screen
    draw.rounded_rectangle([180, 160, 588, 360], radius=15, fill=(10, 15, 25), outline=(0, 180, 200), width=2)
    draw.rounded_rectangle([190, 170, 578, 350], radius=12, fill=(5, 10, 20))
    # URL text area (centered)
    draw.rounded_rectangle([220, 235, 548, 285], radius=8, fill=(0, 40, 50))
    # Energy rays
    for angle_deg in range(0, 360, 15):
        a = math.radians(angle_deg)
        x1 = int(384 + 200 * math.cos(a))
        y1 = int(256 + 150 * math.sin(a))
        x2 = int(384 + 350 * math.cos(a))
        y2 = int(256 + 250 * math.sin(a))
        draw.line([(x1, y1), (x2, y2)], fill=(0, 100, 120), width=1)
    add_particles(draw, W, H, (0, 200, 220), count=60, size_range=(1, 5))
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-4-a.png"))

def scene_4_b():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (8, 5, 20), (15, 10, 30))
    add_grid(draw, W, H, (20, 12, 35), spacing=60)
    # Corridor perspective
    for d in range(8, 0, -1):
        x = 384 - d * 40
        y = 256 - d * 25
        w = d * 80
        h = d * 50
        c = lerp_color((10, 15, 25), (30, 20, 45), d / 8)
        draw.rectangle([x, y, x + w, y + h], fill=c)
    # Person walking away
    draw.ellipse([374, 200, 394, 220], fill=(160, 140, 120))
    draw.rectangle([376, 220, 392, 280], fill=(40, 40, 55))
    # Laptop under arm
    draw.rectangle([392, 235, 408, 245], fill=(50, 50, 65))
    # Holographic screens on walls
    for sx, sy in [(150, 150), (150, 300), (550, 150), (550, 300)]:
        draw.rounded_rectangle([sx, sy, sx + 80, sy + 55], radius=4, fill=(20, 40, 60))
        img = add_glow(img, sx + 40, sy + 27, 50, (0, 150, 180))
        draw = ImageDraw.Draw(img)
    add_particles(draw, W, H, (100, 180, 220), count=40)
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-4-b.png"))

def scene_4_c():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient(draw, W, H, (10, 8, 25), (5, 12, 30))
    # Glowing terminal cursor on dark background
    img = add_glow(img, 384, 256, 250, (10, 180, 150))
    draw = ImageDraw.Draw(img)
    # Art Deco frame
    draw.rounded_rectangle([120, 100, 648, 412], radius=20, fill=(12, 15, 25), outline=(200, 170, 50), width=3)
    # Inner frame
    draw.rounded_rectangle([140, 120, 628, 392], radius=15, fill=(8, 10, 18), outline=(180, 150, 40), width=1)
    # Blinking cursor bar
    draw.rectangle([360, 240, 370, 275], fill=(0, 220, 180))
    img = add_glow(img, 365, 257, 40, (0, 220, 180))
    draw = ImageDraw.Draw(img)
    # Geometric Art Deco patterns in corners
    for cx, cy in [(160, 140), (608, 140), (160, 372), (608, 372)]:
        draw.polygon([(cx, cy), (cx + 15, cy - 15), (cx + 30, cy)], fill=(200, 170, 50))
    # Gold sparkle particles
    add_particles(draw, W, H, (200, 180, 60), count=50, size_range=(1, 3))
    img.convert("RGB").save(os.path.join(SCENE_DIR, "scene-4-c.png"))

# Generate all images
print("Generating fallback scene images...")
generators = [
    ("scene-0-a", scene_0_a), ("scene-0-b", scene_0_b), ("scene-0-c", scene_0_c),
    ("scene-1-a", scene_1_a), ("scene-1-b", scene_1_b), ("scene-1-c", scene_1_c), ("scene-1-d", scene_1_d),
    ("scene-2-a", scene_2_a), ("scene-2-b", scene_2_b), ("scene-2-c", scene_2_c), ("scene-2-d", scene_2_d),
    ("scene-3-a", scene_3_a), ("scene-3-b", scene_3_b), ("scene-3-c", scene_3_c),
    ("scene-4-a", scene_4_a), ("scene-4-b", scene_4_b), ("scene-4-c", scene_4_c),
]

for name, gen_fn in generators:
    gen_fn()
    size = os.path.getsize(os.path.join(SCENE_DIR, f"{name}.png"))
    print(f"  [{name}] OK ({size} bytes)")

print(f"\n=== All {len(generators)} images generated ===")
