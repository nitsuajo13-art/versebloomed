# generate_image.py — Generate VerseBloomed slide images

from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from config import CANVAS_SIZE, OUTPUT_DIR, FONTS, THEMES, LANGUAGE_ORDER


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ── BACKGROUND BUILDERS ───────────────────────────────────────────────────────

def draw_golden_bg(img, W, H):
    """Ivory to warm gold gradient — English slide."""
    draw = ImageDraw.Draw(img)
    colors = [
        (0.00, (253, 248, 236)),
        (0.35, (245, 232, 192)),
        (0.65, (232, 204, 128)),
        (1.00, (201, 164,  74)),
    ]
    for y in range(H):
        t = y / H
        # Find surrounding stops
        c1 = hex_to_rgb("#FDF8EC")
        c2 = hex_to_rgb("#C9A44A")
        for i in range(len(colors) - 1):
            if colors[i][0] <= t <= colors[i+1][0]:
                span = colors[i+1][0] - colors[i][0]
                local_t = (t - colors[i][0]) / span if span > 0 else 0
                c1 = colors[i][1]
                c2 = colors[i+1][1]
                r = int(c1[0] + (c2[0]-c1[0]) * local_t)
                g = int(c1[1] + (c2[1]-c1[1]) * local_t)
                b = int(c1[2] + (c2[2]-c1[2]) * local_t)
                draw.line([(0, y), (W, y)], fill=(r, g, b))
                break

    # Soft center bloom
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    cx, cy = W // 2, int(H * 0.42)
    for r in range(int(W * 0.65), 0, -3):
        ratio = r / (W * 0.65)
        alpha = int(140 * (1 - ratio))
        od.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255, 252, 240, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    return img.convert("RGB")


def draw_vertical_bg(img, W, H, theme):
    """Vertical gradient — Hindi slide."""
    draw = ImageDraw.Draw(img)
    s = theme["gradient_start"]
    e = theme["gradient_end"]
    for y in range(H):
        t = y / H
        r = int(s[0] + (e[0]-s[0]) * t)
        g = int(s[1] + (e[1]-s[1]) * t)
        b = int(s[2] + (e[2]-s[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def draw_diagonal_bg(img, W, H, theme):
    """Diagonal stripe gradient — Marathi & Kannada slides."""
    stops  = theme["stripe_stops"]
    colors = [hex_to_rgb(c) for c in theme["stripe_colors"]]
    pixels = img.load()
    for y in range(H):
        for x in range(W):
            t = (x + y) / (W + H)
            c1, c2, local_t = colors[0], colors[-1], 0
            for i in range(len(stops) - 1):
                if stops[i] <= t <= stops[i+1]:
                    span = stops[i+1] - stops[i]
                    local_t = (t - stops[i]) / span if span > 0 else 0
                    c1, c2 = colors[i], colors[i+1]
                    break
            r = int(c1[0] + (c2[0]-c1[0]) * local_t)
            g = int(c1[1] + (c2[1]-c1[1]) * local_t)
            b = int(c1[2] + (c2[2]-c1[2]) * local_t)
            pixels[x, y] = (r, g, b)
    return img


def add_vignette(img, W, H, is_light):
    """Add subtle vignette overlay."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    max_r = int(W * 0.8)
    for r in range(max_r, 0, -4):
        ratio = 1 - (r / max_r)
        alpha = int((18 if is_light else 30) * ratio)
        od.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


# ── CORNER BRACKETS ───────────────────────────────────────────────────────────

def draw_frame(draw, W, H, color):
    m, l = 52, 65
    lw = 2
    draw.line([(m, m+l), (m, m), (m+l, m)], fill=color, width=lw)
    draw.line([(W-m-l, m), (W-m, m), (W-m, m+l)], fill=color, width=lw)
    draw.line([(m, H-m-l), (m, H-m), (m+l, H-m)], fill=color, width=lw)
    draw.line([(W-m-l, H-m), (W-m, H-m), (W-m, H-m-l)], fill=color, width=lw)


# ── TEXT WRAP ─────────────────────────────────────────────────────────────────

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines


# ── BLOOD RED FLOWER ──────────────────────────────────────────────────────────

def draw_flower(draw, cx, cy, size):
    """Draw a 5-petal blood red flower."""
    import math
    petal_r      = int(size * 0.42)
    petal_offset = int(size * 0.32)
    blood_red    = (139, 0, 0)
    crimson      = (176, 0, 0)

    for i in range(5):
        angle = (i * 2 * math.pi / 5) - math.pi / 2
        px = int(cx + petal_offset * math.cos(angle))
        py = int(cy + petal_offset * math.sin(angle))
        draw.ellipse([px-petal_r, py-petal_r, px+petal_r, py+petal_r], fill=crimson)

    # Gold center
    cr = int(size * 0.22)
    draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill=(255, 215, 0))
    # Center dot
    sr = int(size * 0.08)
    draw.ellipse([cx-sr, cy-sr, cx+sr, cy+sr], fill=blood_red)


# ── WATERMARK ─────────────────────────────────────────────────────────────────

def draw_watermark(draw, img, W, H, theme):
    """Draw ❀ VerseBloomed ❀ with blood red flowers and underline."""
    wm_text = "VerseBloomed"
    wm_size = 32
    fl_size = 18
    r_pad   = 55
    b_pad   = 108

    try:
        wm_font = ImageFont.truetype(FONTS["playfair_bold"], wm_size)
    except:
        wm_font = ImageFont.load_default()

    text_w = draw.textlength(wm_text, font=wm_font)
    gap    = 10
    fl_d   = fl_size * 2
    total_w = fl_d + gap + text_w + gap + fl_d

    start_x = W - r_pad - total_w
    base_y  = H - b_pad
    fl_y    = base_y - wm_size // 2

    # Left flower
    draw_flower(draw, int(start_x + fl_size), int(fl_y), fl_size)

    # Watermark text
    text_x = int(start_x + fl_d + gap)
    draw.text((text_x, base_y - wm_size), wm_text,
              font=wm_font, fill=theme["wm_color"])

    # Underline
    ul_y = base_y + 4
    draw.line([(text_x, ul_y), (int(text_x + text_w), ul_y)],
              fill=theme["wm_ul_color"], width=2)

    # Right flower
    draw_flower(draw, int(text_x + text_w + gap + fl_size), int(fl_y), fl_size)


# ── MAIN SLIDE GENERATOR ──────────────────────────────────────────────────────

def generate_slide(language, verse_text, reference, session, date_str):
    """Generate one 1080×1080 slide image."""
    theme = THEMES[language]
    W, H  = CANVAS_SIZE

    # Background
    img  = Image.new("RGB", (W, H), (255, 255, 255))
    gtype = theme["gradient_type"]

    if gtype == "golden":
        img = draw_golden_bg(img, W, H)
    elif gtype == "vertical":
        img = draw_vertical_bg(img, W, H, theme)
    elif gtype == "diagonal":
        img = draw_diagonal_bg(img, W, H, theme)

    img  = add_vignette(img, W, H, theme["is_light"])
    draw = ImageDraw.Draw(img, "RGBA")

    # Corner brackets
    draw_frame(draw, W, H, theme["frame_color"])

    # Fonts
    PAD   = 110
    max_w = W - PAD * 2
    font_key = theme["font_verse"]
    ref_key  = theme["font_ref"]

    font_size = 58
    try:
        font_obj = ImageFont.truetype(FONTS[font_key], font_size)
    except Exception as e:
        print(f"❌ Font error: {e}")
        font_obj = ImageFont.load_default()

    lines = wrap_text(draw, verse_text, font_obj, max_w)

    # Auto-shrink if too many lines
    while len(lines) > 7 and font_size > 30:
        font_size -= 3
        font_obj  = ImageFont.truetype(FONTS[font_key], font_size)
        lines     = wrap_text(draw, verse_text, font_obj, max_w)

    ref_size  = max(20, int(font_size * 0.54))
    try:
        ref_font = ImageFont.truetype(FONTS[ref_key], ref_size)
    except:
        ref_font = ImageFont.load_default()

    line_h  = int(font_size * 1.72)
    total_h = len(lines) * line_h
    block_h = total_h + 50 + ref_size
    start_y = (H - block_h) // 2 - 10

    # Big background quote mark
    try:
        q_font = ImageFont.truetype(FONTS[font_key], font_size * 3)
        draw.text((PAD - 10, start_y + font_size * 2),
                  "\u201C", font=q_font, fill=theme["quote_color"])
    except:
        pass

    # Verse lines
    tc = theme["text_color"]
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_obj)
        lw   = bbox[2] - bbox[0]
        x    = (W - lw) // 2
        y    = start_y + i * line_h
        draw.text((x, y), line, font=font_obj, fill=(*tc, 255))

    # Reference — text only, NO decorative lines
    ref_text = f"\u2014 {reference} \u2014"
    ref_y    = start_y + total_h + 48
    bbox_r   = draw.textbbox((0, 0), ref_text, font=ref_font)
    ref_x    = (W - (bbox_r[2] - bbox_r[0])) // 2
    draw.text((ref_x, ref_y), ref_text,
              font=ref_font, fill=theme["ref_color"])

    # Watermark
    draw_watermark(draw, img, W, H, theme)

    # Save
    folder = os.path.join(OUTPUT_DIR, f"{date_str}_{session}")
    os.makedirs(folder, exist_ok=True)
    out_path = os.path.join(folder, f"slide_{language}.png")
    img.save(out_path, "PNG")
    print(f"  ✅ Saved: {out_path}")
    return out_path


def generate_carousel(verse_texts, references, session):
    """Generate all 4 slides for one carousel."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    paths    = []
    for lang in LANGUAGE_ORDER:
        path = generate_slide(
            lang,
            verse_texts[lang],
            references[lang],
            session,
            date_str
        )
        paths.append(path)
    return paths
