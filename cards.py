"""Rank card rendering. Drawn procedurally (no background asset). Synchronous
Pillow work is meant to be called via run_in_executor so it never blocks the loop.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFont

import config

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font(size: int):
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _hex_to_rgb(h: str, default=(139, 0, 0)):
    if not h:
        return default
    h = h.lstrip("#")
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return default


def render_card(
    *, username: str, avatar_bytes: bytes | None, level: int, rank_title: str,
    xp_into: int, xp_need: int, position: int, souls: int, accent_hex: str | None,
    has_mark: bool,
) -> io.BytesIO:
    W, H = 900, 280
    accent = _hex_to_rgb(accent_hex)

    img = Image.new("RGB", (W, H), (18, 16, 18))
    d = ImageDraw.Draw(img)

    # vertical velvet gradient
    top, bot = (28, 10, 22), (12, 10, 12)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))

    # accent spine + frame
    d.rectangle([0, 0, 10, H], fill=accent)
    d.rectangle([0, 0, W - 1, H - 1], outline=(40, 36, 40))

    # avatar
    ax, ay, asz = 40, 60, 160
    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGB").resize((asz, asz))
            mask = Image.new("L", (asz, asz), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, asz, asz], fill=255)
            img.paste(av, (ax, ay), mask)
        except Exception:
            d.ellipse([ax, ay, ax + asz, ay + asz], fill=(40, 30, 36))
    else:
        d.ellipse([ax, ay, ax + asz, ay + asz], fill=(40, 30, 36))
    d.ellipse([ax, ay, ax + asz, ay + asz], outline=accent, width=4)

    tx = ax + asz + 36
    bone = (232, 224, 213)
    ash = (150, 140, 145)

    name = (username[:22] + "…") if len(username) > 23 else username
    d.text((tx, 50), name, font=_font(40), fill=bone)
    if has_mark:
        nw = d.textlength(name, font=_font(40))
        cx, cy = tx + nw + 22, 72
        d.polygon([(cx, cy - 12), (cx - 9, cy + 8), (cx + 9, cy + 8)], fill=accent)  # blood drop
    d.text((tx, 100), f"{rank_title}", font=_font(26), fill=accent)

    d.text((tx, 150), f"LEVEL {level}", font=_font(28), fill=bone)
    d.text((W - 250, 150), f"RANK #{position}", font=_font(28), fill=ash)

    # xp bar
    bx, by, bw, bh = tx, 200, W - tx - 40, 26
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=13, fill=(40, 36, 40))
    frac = 0 if xp_need <= 0 else max(0.0, min(1.0, xp_into / xp_need))
    if frac > 0:
        d.rounded_rectangle([bx, by, bx + int(bw * frac), by + bh], radius=13, fill=accent)
    d.text((bx, by + bh + 8), f"{xp_into:,} / {xp_need:,} XP", font=_font(20), fill=ash)
    # souls: drawn diamond + count (no emoji glyph, which DejaVu lacks)
    sx, sy = W - 250, by + bh + 12
    d.polygon([(sx, sy + 9), (sx + 9, sy), (sx + 18, sy + 9), (sx + 9, sy + 18)], fill=accent)
    d.text((sx + 28, by + bh + 8), f"{souls:,}", font=_font(22), fill=bone)

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf
