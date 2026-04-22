"""
Payment receipt PNG generator for the Angle bot.
Drop this file into your bot's `plugins/` folder.

Requires: Pillow (already pulled in via the `qrcode` dependency).
"""

import io
import random
import string
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pytz import timezone

# ── Config ───────────────────────────────────────────────────────────────────
WIDTH = 640
PADDING = 20
RADIUS = 18

BG_OUTER   = (0, 0, 0)
BG_CARD    = (20, 23, 29)
BG_HEADER  = (226, 59, 59)
COL_TEXT   = (255, 255, 255)
COL_MUTED  = (138, 147, 166)
COL_LINE   = (42, 47, 56)
COL_FOOTER = (255, 91, 91)

STATUS_COLORS = {
    "PAID":    (37, 194, 107),
    "PENDING": (243, 178, 26),
    "FAILED":  (226, 59, 59),
}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load DejaVuSans which ships with Pillow on every platform."""
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def _rounded_card(size, radius, fill):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=fill)
    return img


def _text_w(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def random_receipt_id() -> str:
    s = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"RCP-{s}"


def format_ist(dt: datetime) -> str:
    ist = timezone("Asia/Kolkata")
    if dt.tzinfo is None:
        dt = ist.localize(dt)
    else:
        dt = dt.astimezone(ist)
    return dt.strftime("%d %b %Y, %I:%M %p IST")


def generate_receipt(
    name: str,
    user_id: int | str,
    premium: str,
    plan: str,
    expires: str,
    issued_at: datetime | None = None,
    receipt_id: str | None = None,
    status: str = "PAID",
    brand: str = "Angle Baby",
) -> io.BytesIO:
    """
    Returns a BytesIO containing a PNG receipt that you can send via Pyrogram:
        await client.send_photo(chat_id, generate_receipt(...))
    """
    if issued_at is None:
        issued_at = datetime.now(timezone("Asia/Kolkata"))
    if receipt_id is None:
        receipt_id = random_receipt_id()

    status = status.upper()
    status_color = STATUS_COLORS.get(status, STATUS_COLORS["PAID"])

    # Fonts
    f_header = _font(24, bold=True)
    f_meta   = _font(15)
    f_label  = _font(16)
    f_value  = _font(17, bold=True)
    f_badge  = _font(17, bold=True)
    f_thanks = _font(15)
    f_powered = _font(14)
    f_id_mono = _font(14)

    # Layout calc
    header_h = 56
    meta_h   = 44
    row_h    = 42
    rows     = 5
    divider_pad = 14
    badge_h  = 70
    footer_h = 60

    inner_h = header_h + meta_h + (row_h * rows) + divider_pad + badge_h + footer_h
    total_h = inner_h + PADDING * 2

    # Outer canvas
    img = Image.new("RGB", (WIDTH, total_h), BG_OUTER)

    # Card
    card_w = WIDTH - PADDING * 2
    card = _rounded_card((card_w, inner_h), RADIUS, BG_CARD)
    img.paste(card, (PADDING, PADDING), card)

    draw = ImageDraw.Draw(img)
    x0 = PADDING
    y  = PADDING

    # Header (red bar, rounded only on top — emulate by drawing a rounded rect then masking bottom)
    header = Image.new("RGBA", (card_w, header_h * 2), (0, 0, 0, 0))
    hd = ImageDraw.Draw(header)
    hd.rounded_rectangle((0, 0, card_w - 1, header_h * 2 - 1), radius=RADIUS, fill=BG_HEADER)
    header = header.crop((0, 0, card_w, header_h))
    img.paste(header, (x0, y), header)

    # Header text
    title = "PAYMENT RECEIPT"
    tw = _text_w(draw, title, f_header)
    draw.text((x0 + (card_w - tw) // 2, y + (header_h - 26) // 2), title, font=f_header, fill=COL_TEXT)
    y += header_h

    # Meta row (receipt id  •  date)
    pad_x = 22
    draw.text((x0 + pad_x, y + 14), receipt_id, font=f_id_mono, fill=COL_MUTED)
    date_str = format_ist(issued_at)
    dw = _text_w(draw, date_str, f_meta)
    draw.text((x0 + card_w - pad_x - dw, y + 13), date_str, font=f_meta, fill=COL_MUTED)
    # Bottom border under meta
    draw.line((x0 + pad_x, y + meta_h - 1, x0 + card_w - pad_x, y + meta_h - 1), fill=COL_LINE, width=1)
    y += meta_h

    # Detail rows
    rows_data = [
        ("Name",    str(name)),
        ("User ID", str(user_id)),
        ("Premium", str(premium)),
        ("Plan",    str(plan)),
        ("Expires", str(expires)),
    ]
    for label, value in rows_data:
        draw.text((x0 + pad_x, y + 11), label, font=f_label, fill=COL_MUTED)
        vw = _text_w(draw, value, f_value)
        draw.text((x0 + card_w - pad_x - vw, y + 10), value, font=f_value, fill=COL_TEXT)
        y += row_h

    # Divider above status
    y += divider_pad // 2
    draw.line((x0 + pad_x, y, x0 + card_w - pad_x, y), fill=COL_LINE, width=1)
    y += divider_pad // 2

    # Status badge (rounded outline pill, centered)
    # Draw the checkmark with line segments so we don't depend on font glyphs.
    badge_text = status
    text_only_w = _text_w(draw, badge_text, f_badge)
    check_w = 18 if status == "PAID" else 0
    bw = text_only_w + check_w + 48
    bh = 36
    bx = x0 + (card_w - bw) // 2
    by = y + (badge_h - bh) // 2
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=bh // 2, outline=status_color, width=2)
    inner_x = bx + (bw - text_only_w - check_w) // 2
    if status == "PAID":
        cy = by + bh // 2
        # Two-segment check: down-right then up-right
        draw.line([(inner_x, cy + 2), (inner_x + 6, cy + 8), (inner_x + 14, cy - 6)],
                  fill=status_color, width=3, joint="curve")
        inner_x += check_w
    draw.text((inner_x, by + (bh - 22) // 2), badge_text, font=f_badge, fill=status_color)
    y += badge_h

    # Footer
    thanks = "Thank you for your purchase!"
    tw = _text_w(draw, thanks, f_thanks)
    draw.text((x0 + (card_w - tw) // 2, y + 8), thanks, font=f_thanks, fill=(201, 205, 214))
    powered = f"Powered By {brand}"
    pw = _text_w(draw, powered, f_powered)
    draw.text((x0 + (card_w - pw) // 2, y + 30), powered, font=f_powered, fill=COL_FOOTER)

    # Output
    bio = io.BytesIO()
    bio.name = "receipt.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio
