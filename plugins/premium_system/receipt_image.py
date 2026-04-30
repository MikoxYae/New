"""
Receipt image generator (Pillow).

Renders the premium-receipt as a polished PNG so the bot can deliver it as
a downloadable document instead of a plain HTML message.

Usage:
    from .receipt_image import build_receipt_image
    buf = build_receipt_image(
        user_name="John Doe",
        user_id=123456789,
        plan_type="GOLD - 30 Days",
        plan_amount="₹49",
        order_id="ORD-XYZ",
        txn_id="TXNABC123",
        active_date="01 Jan 2026, 10:30 PM",
        expire_date="31 Jan 2026, 10:30 PM",
    )
    await client.send_document(uid, document=buf, file_name=buf.name, caption="...")
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


# ── Font discovery ─────────────────────────────────────────────────────
_BOLD_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
]
_REG_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
]
_MONO_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
]


def _load_font(size: int, bold: bool = False, mono: bool = False):
    candidates = (
        _MONO_FONT_CANDIDATES
        if mono
        else (_BOLD_FONT_CANDIDATES if bold else _REG_FONT_CANDIDATES)
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ── Palette ────────────────────────────────────────────────────────────
GOLD       = (255, 200, 60)
GOLD_DIM   = (200, 156, 47)
WHITE      = (245, 245, 248)
GREY       = (170, 170, 185)
BG_TOP     = (15, 18, 32)
BG_BOTTOM  = (30, 22, 12)
BAND       = (34, 28, 14)
DIVIDER    = (110, 90, 35)


def _measure(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    try:
        return int(draw.textlength(text, font=font))
    except Exception:
        # Pillow < 9 fallback
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]


def _wrap_lines(draw, text: str, font, max_width: int):
    words, lines, line = text.split(), [], ""
    for w in words:
        candidate = (line + " " + w).strip()
        if _measure(draw, candidate, font) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def build_receipt_image(
    *,
    title: str = "PAYMENT RECEIPT",
    subtitle: str = "PREMIUM ACTIVATED",
    user_name: str = "—",
    user_id: object = "—",
    plan_type: str = "—",
    plan_amount: Optional[str] = None,
    order_id: Optional[str] = None,
    txn_id: Optional[str] = None,
    active_date: str = "—",
    expire_date: str = "—",
    granted_by: Optional[str] = None,
    footer: str = "Enjoy your Premium Access. Keep this receipt for your records.",
    brand: str = "MIKO PREMIUM",
) -> BytesIO:
    """Render a receipt PNG and return it as a named BytesIO."""

    # Build the field list first so we can size the canvas dynamically.
    fields: list[tuple[str, str]] = [
        ("USER NAME", str(user_name)),
        ("USER ID",   str(user_id)),
        ("PLAN TYPE", str(plan_type)),
    ]
    if plan_amount:
        fields.append(("PLAN AMOUNT", str(plan_amount)))
    if order_id:
        fields.append(("ORDER ID", str(order_id)))
    if txn_id:
        fields.append(("TXN ID", str(txn_id)))
    fields += [
        ("ACTIVE DATE", str(active_date)),
        ("EXPIRE DATE", str(expire_date)),
    ]
    if granted_by:
        fields.append(("GRANTED BY", str(granted_by)))

    W = 980
    pad = 22
    band_h = 150
    row_h = 78
    fields_block_h = row_h * len(fields) + 30
    footer_block_h = 150
    H = pad + 12 + band_h + 50 + fields_block_h + footer_block_h + pad

    # Canvas + gradient background
    img = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Outer borders
    draw.rectangle([pad, pad, W - pad, H - pad], outline=GOLD_DIM, width=3)
    draw.rectangle([pad + 8, pad + 8, W - pad - 8, H - pad - 8], outline=GOLD, width=1)

    # Fonts
    f_title = _load_font(58, bold=True)
    f_sub   = _load_font(28, bold=True)
    f_label = _load_font(20, bold=True)
    f_value = _load_font(30, bold=True)
    f_small = _load_font(20, bold=False)
    f_brand = _load_font(34, bold=True)

    # Header band
    band_top = pad + 12
    band_bot = band_top + band_h
    draw.rectangle([pad + 12, band_top, W - pad - 12, band_bot], fill=BAND)

    tw = _measure(draw, title, f_title)
    draw.text(((W - tw) / 2, band_top + 22), title, font=f_title, fill=GOLD)
    sw = _measure(draw, subtitle, f_sub)
    draw.text(((W - sw) / 2, band_top + 95), subtitle, font=f_sub, fill=WHITE)

    # Divider under header
    y = band_bot + 32
    draw.line([(pad + 40, y), (W - pad - 40, y)], fill=DIVIDER, width=2)
    y += 28

    # Field rows
    label_x = pad + 60
    value_x = pad + 60
    for label, value in fields:
        draw.text((label_x, y), label, font=f_label, fill=GOLD)
        # Truncate very long values so the layout never overflows.
        v = value
        if _measure(draw, v, f_value) > W - 2 * pad - 100:
            while v and _measure(draw, v + "…", f_value) > W - 2 * pad - 100:
                v = v[:-1]
            v = v + "…"
        draw.text((value_x, y + 26), v, font=f_value, fill=WHITE)
        y += row_h

    # Footer divider
    y += 6
    draw.line([(pad + 40, y), (W - pad - 40, y)], fill=DIVIDER, width=2)
    y += 22

    # Footer message (centered, wrapped if needed)
    lines = _wrap_lines(draw, footer, f_small, W - 2 * pad - 100)
    for ln in lines:
        lw = _measure(draw, ln, f_small)
        draw.text(((W - lw) / 2, y), ln, font=f_small, fill=GREY)
        y += 28

    # Brand bottom-right
    bw = _measure(draw, brand, f_brand)
    draw.text((W - bw - pad - 40, H - pad - 60), brand, font=f_brand, fill=GOLD_DIM)

    out = BytesIO()
    out.name = "receipt.png"
    img.save(out, format="PNG", optimize=True)
    out.seek(0)
    return out
