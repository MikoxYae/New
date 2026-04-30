import asyncio
import random
import re
import string
import time
from datetime import datetime
from io import BytesIO

import aiohttp
import qrcode
from motor.motor_asyncio import AsyncIOMotorClient
from pytz import timezone as _tz
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot import Bot
from config import DB_URI, DB_NAME, OWNER_ID, PREMIUM_PIC
from database.db_premium import add_premium, collection as _premium_col
from database.db_plans import (
    list_plans,
    get_plan,
    to_addpremium_unit,
    ALLOWED_UNITS,
    grant_gift,
)
from plugins.premium_system.premium_cdm import monitor_premium_expiry


# ═══════════════════════════════════════════════════════════════════════════════
#   Sellgram Paytm Status API + UPI configuration
# ═══════════════════════════════════════════════════════════════════════════════
SELLGRAM_API_BASE = "https://ptapi.sellgram.in"
SELLGRAM_API_KEY = "8Mv3zQgQZNVCdU4iBaAFvtu8"

UPI_ID = "paytm.s20gmbu@pty"
PAYEE_NAME = "MikoPremium"

SUPPORT_URL = "https://t.me/Iam_addictive"


# ═══════════════════════════════════════════════════════════════════════════════
#   Legacy fallback plans  ->  used ONLY when admin has not yet added any
#   plans via /psetting (i.e. the premium-plans collection is empty).
#   id : (label, amount_inr, time_value, time_unit, tier)
# ═══════════════════════════════════════════════════════════════════════════════
LEGACY_PLANS = {
    "1h":  ("1 ʜᴏᴜʀ (ᴛᴇsᴛ)", 1,   1,  "h",  "gold"),
    "1d":  ("1 ᴅᴀʏ",         10,  1,  "d",  "gold"),
    "7d":  ("7 ᴅᴀʏs",        50,  7,  "d",  "gold"),
    "30d": ("30 ᴅᴀʏs",       150, 30, "d",  "gold"),
}


# ═══════════════════════════════════════════════════════════════════════════════
#   Helpers for dynamic plans (loaded from db_plans.premium-plans)
# ═══════════════════════════════════════════════════════════════════════════════
def _parse_price_inr(price_str) -> int:
    """Extract integer rupee amount from a free-form price string.
       '₹150', '150', 'Rs. 150', '150 INR' -> 150"""
    if price_str is None:
        return 0
    m = re.search(r"\d+", str(price_str))
    return int(m.group()) if m else 0


def _short_unit(unit: str) -> str:
    """Short label for buttons: 1ʜ / 1ᴅ / 7ᴅ / 30ᴅ / 1ᴡ / 1ᴍᴏɴ ..."""
    return {
        "m":   "ᴍ",
        "h":   "ʜ",
        "d":   "ᴅ",
        "w":   "ᴡ",
        "mon": "ᴍᴏɴ",
        "y":   "ʏ",
    }.get(unit.lower(), unit)


def _full_unit_label(value: int, unit: str) -> str:
    base = ALLOWED_UNITS.get(unit.lower(), unit)
    if value == 1 and base.endswith("s"):
        base = base[:-1]
    return base.lower()


# ═══════════════════════════════════════════════════════════════════════════════
#   MongoDB collection for pending orders (survives restarts)
# ═══════════════════════════════════════════════════════════════════════════════
_mongo = AsyncIOMotorClient(DB_URI)
_db = _mongo[DB_NAME]
_orders_col = _db["pending_orders"]


# ═══════════════════════════════════════════════════════════════════════════════
#   Helpers
# ═══════════════════════════════════════════════════════════════════════════════
def _gen_order_id(amount: int, user_id: int) -> str:
    """Order ID format -> ZERO-{amount}-{user_id}-{timestamp}-{rand4_HEX}"""
    ts = int(time.time())
    rand = "".join(random.choices("0123456789ABCDEF", k=4))
    return f"ZERO-{amount}-{user_id}-{ts}-{rand}"


def _make_qr(amount: int, order_id: str) -> BytesIO:
    upi_url = (
        f"upi://pay?pa={UPI_ID}"
        f"&pn={PAYEE_NAME}"
        f"&am={amount}"
        f"&cu=INR"
        f"&tn={order_id}"
        f"&tr={order_id}"
    )
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    bio.name = "payment_qr.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio


async def _check_payment(order_id: str) -> dict:
    url = f"{SELLGRAM_API_BASE}/status/{order_id}?api_key={SELLGRAM_API_KEY}"
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            return await r.json(content_type=None)


def _legacy_menu_text(first_name: str) -> str:
    return (
        f"<b>💎 ʜᴇʟʟᴏ {first_name}, ᴜɴʟᴏᴄᴋ ᴘʀᴇᴍɪᴜᴍ</b>\n\n"
        f"<b>ᴘᴇʀᴋs:</b>\n"
        f"  ✅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ʟɪɴᴋs\n"
        f"  ✅ ɴᴏ ᴀᴅs / ɴᴏ sʜᴏʀᴛɴᴇʀ ᴛᴏᴋᴇɴ\n"
        f"  ✅ ғᴏʀᴄᴇ-sᴜʙ ʙʏᴘᴀss\n"
        f"  ✅ ᴘʀᴏᴛᴇᴄᴛ-ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss\n\n"
        f"<b>ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀɴs:</b>\n"
        f"  • 1 ʜᴏᴜʀ — <b>₹1</b> (ᴛᴇsᴛ)\n"
        f"  • 1 ᴅᴀʏ — <b>₹10</b>\n"
        f"  • 7 ᴅᴀʏs — <b>₹50</b>\n"
        f"  • 30 ᴅᴀʏs — <b>₹150</b>\n\n"
        f"<i>ᴘᴀʏᴍᴇɴᴛ ɪs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴠᴇʀɪғɪᴇᴅ — ɴᴏ ᴡᴀɪᴛɪɴɢ ғᴏʀ ᴏᴡɴᴇʀ.</i>"
    )


def _legacy_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1ʜ — ₹1 (ᴛᴇsᴛ)", callback_data="pa_plan_1h"),
            InlineKeyboardButton("1ᴅ — ₹10",       callback_data="pa_plan_1d"),
        ],
        [
            InlineKeyboardButton("7ᴅ — ₹50",  callback_data="pa_plan_7d"),
            InlineKeyboardButton("30ᴅ — ₹150", callback_data="pa_plan_30d"),
        ],
        [
            InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="pa_close"),
        ],
    ])


def _dynamic_menu_text(first_name: str, plans: list) -> str:
    lines = [
        f"<b>💎 ʜᴇʟʟᴏ {first_name}, ᴜɴʟᴏᴄᴋ ᴘʀᴇᴍɪᴜᴍ</b>\n",
        "<b>ᴘᴇʀᴋs:</b>",
        "  ✅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ʟɪɴᴋs",
        "  ✅ ɴᴏ ᴀᴅs / ɴᴏ sʜᴏʀᴛɴᴇʀ ᴛᴏᴋᴇɴ",
        "  ✅ ғᴏʀᴄᴇ-sᴜʙ ʙʏᴘᴀss",
        "  ✅ ᴘʀᴏᴛᴇᴄᴛ-ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss\n",
        "<b>ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀɴs:</b>",
    ]
    for p in plans:
        amount = _parse_price_inr(p.get("price"))
        unit_label = _full_unit_label(int(p.get("duration_value", 0)), p.get("duration_unit", ""))
        tier = (p.get("tier") or "gold").lower()
        emoji = "🥇" if tier == "gold" else "💎"
        lines.append(
            f"  {emoji} <b>{p.get('name', '—')}</b> — "
            f"<b>₹{amount}</b> · {p.get('duration_value', '?')} {unit_label}"
        )
    lines.append("\n<i>ᴘᴀʏᴍᴇɴᴛ ɪs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴠᴇʀɪғɪᴇᴅ — ɴᴏ ᴡᴀɪᴛɪɴɢ ғᴏʀ ᴏᴡɴᴇʀ.</i>")
    return "\n".join(lines)


def _dynamic_menu_kb(plans: list) -> InlineKeyboardMarkup:
    rows = []
    buf = []
    for p in plans:
        amount = _parse_price_inr(p.get("price"))
        short = f"{p.get('duration_value', '?')}{_short_unit(p.get('duration_unit', ''))}"
        label = f"{p.get('name', short)} — ₹{amount}"
        if len(label) > 32:
            label = f"{short} — ₹{amount}"
        buf.append(InlineKeyboardButton(
            label,
            callback_data=f"pa_plan_db_{p.get('_id')}",
        ))
        if len(buf) == 2:
            rows.append(buf)
            buf = []
    if buf:
        rows.append(buf)
    rows.append([InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="pa_close")])
    return InlineKeyboardMarkup(rows)


async def _build_menu(first_name: str):
    """Return (text, keyboard). Uses db plans if any exist, else legacy."""
    try:
        plans = await list_plans()
    except Exception:
        plans = []
    # Filter plans whose price parses to > 0
    plans = [p for p in plans if _parse_price_inr(p.get("price")) > 0]
    if plans:
        return _dynamic_menu_text(first_name, plans), _dynamic_menu_kb(plans)
    return _legacy_menu_text(first_name), _legacy_menu_kb()


# ═══════════════════════════════════════════════════════════════════════════════
#   Callback: open premium menu  (entry from "Buy Premium" button in start.py)
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^(premium|buy_premium)$"))
async def open_premium_menu(client: Bot, query: CallbackQuery):
    await query.answer()
    text, kb = await _build_menu(query.from_user.first_name)
    msg = query.message

    try:
        await msg.edit_caption(caption=text, reply_markup=kb)
    except Exception:
        try:
            await msg.edit_text(text=text, reply_markup=kb, disable_web_page_preview=True)
        except Exception:
            try:
                await msg.delete()
            except Exception:
                pass
            await client.send_photo(
                chat_id=msg.chat.id,
                photo=PREMIUM_PIC,
                caption=text,
                reply_markup=kb,
            )


# ═══════════════════════════════════════════════════════════════════════════════
#   Callback: user picks a plan  ->  generate QR + persist order
#
#   callback_data formats:
#     pa_plan_db_<ObjectId>   -> dynamic plan from premium-plans collection
#     pa_plan_<legacy_id>     -> legacy hardcoded plan (1h/1d/7d/30d)
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^pa_plan_(.+)$"))
async def pick_plan(client: Bot, query: CallbackQuery):
    raw = query.data.replace("pa_plan_", "", 1)

    if raw.startswith("db_"):
        # Dynamic plan from /psetting
        db_plan_id = raw[3:]
        plan_doc = await get_plan(db_plan_id)
        if not plan_doc:
            return await query.answer(
                "ᴛʜɪs ᴘʟᴀɴ ɴᴏ ʟᴏɴɢᴇʀ ᴇxɪsᴛs. ʀᴇᴏᴘᴇɴ ᴛʜᴇ ᴍᴇɴᴜ.",
                show_alert=True,
            )
        amount = _parse_price_inr(plan_doc.get("price"))
        if amount <= 0:
            return await query.answer(
                "ᴘʀɪᴄᴇ ɴᴏᴛ sᴇᴛ ᴄᴏʀʀᴇᴄᴛʟʏ ғᴏʀ ᴛʜɪs ᴘʟᴀɴ. ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.",
                show_alert=True,
            )
        try:
            time_value, time_unit = to_addpremium_unit(
                int(plan_doc.get("duration_value", 0)),
                plan_doc.get("duration_unit", "d"),
            )
        except Exception:
            return await query.answer("ɪɴᴠᴀʟɪᴅ ᴘʟᴀɴ ᴅᴜʀᴀᴛɪᴏɴ. ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.", show_alert=True)
        tier = (plan_doc.get("tier") or "gold").lower()
        unit_full = _full_unit_label(int(plan_doc.get("duration_value", 0)),
                                     plan_doc.get("duration_unit", ""))
        label = f"{plan_doc.get('name', '—')} — {plan_doc.get('duration_value','?')} {unit_full}"
        plan_id_for_order = f"db_{db_plan_id}"
        gift_channel_id    = plan_doc.get("gift_channel_id")
        gift_channel_title = plan_doc.get("gift_channel_title")
    else:
        # Legacy hardcoded fallback
        plan = LEGACY_PLANS.get(raw)
        if not plan:
            return await query.answer("ɪɴᴠᴀʟɪᴅ ᴘʟᴀɴ.", show_alert=True)
        label, amount, time_value, time_unit, tier = plan
        plan_id_for_order = raw
        gift_channel_id    = None
        gift_channel_title = None

    user_id = query.from_user.id
    order_id = _gen_order_id(amount, user_id)

    await query.answer("ɢᴇɴᴇʀᴀᴛɪɴɢ ǫʀ…")

    order_doc = {
        "order_id":   order_id,
        "user_id":    user_id,
        "amount":     amount,
        "plan_id":    plan_id_for_order,
        "plan_label": label,
        "time_value": time_value,
        "time_unit":  time_unit,
        "tier":       tier,
        "status":     "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    if gift_channel_id:
        order_doc["gift_channel_id"]    = int(gift_channel_id)
        order_doc["gift_channel_title"] = gift_channel_title or str(gift_channel_id)
    await _orders_col.insert_one(order_doc)

    qr_img = _make_qr(amount, order_id)

    gift_line = ""
    if gift_channel_id:
        gift_line = (
            f"<b>🎀 ɢɪғᴛ ᴀᴅᴅᴇᴅ:</b> <b>{gift_channel_title}</b>\n"
            f"<i>(ʏᴏᴜ ᴡɪʟʟ ʙᴇ ɪɴᴠɪᴛᴇᴅ ᴀғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ)</i>\n\n"
        )

    caption = (
        f"<b>💳 ᴄᴏᴍᴘʟᴇᴛᴇ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ</b>\n\n"
        f"<b>ᴘʟᴀɴ:</b> {label}\n"
        f"<b>ᴀᴍᴏᴜɴᴛ:</b> <b>₹{amount}</b>\n"
        f"<b>ᴏʀᴅᴇʀ ɪᴅ:</b> <code>{order_id}</code>\n\n"
        f"{gift_line}"
        f"<b>📱 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:</b>\n"
        f"<b>1.</b> ᴏᴘᴇɴ ᴀɴʏ ᴜᴘɪ ᴀᴘᴘ — ᴘᴀʏᴛᴍ / ɢᴘᴀʏ / ᴘʜᴏɴᴇᴘᴇ.\n"
        f"<b>2.</b> sᴄᴀɴ ᴛʜᴇ ǫʀ ᴄᴏᴅᴇ ᴀʙᴏᴠᴇ.\n"
        f"<b>3.</b> ᴘᴀʏ ᴛʜᴇ ᴇxᴀᴄᴛ ᴀᴍᴏᴜɴᴛ <b>₹{amount}</b>.\n"
        f"<b>4.</b> ᴀғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ, ᴄʟɪᴄᴋ <b>ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ</b>.\n"
        f"<b>5.</b> ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ.\n\n"
        f"⚠️ <b>ᴘᴀʏ ᴇxᴀᴄᴛ ᴀᴍᴏᴜɴᴛ ᴏɴʟʏ.</b> ᴏᴛʜᴇʀᴡɪsᴇ ᴀᴜᴛᴏ-ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ᴡɪʟʟ ғᴀɪʟ.\n"
        f"💬 ɴᴇᴇᴅ ʜᴇʟᴘ? ᴜsᴇ ᴛʜᴇ <b>sᴜᴘᴘᴏʀᴛ</b> ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ."
    )

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ", callback_data=f"pa_paid_{order_id}"),
            InlineKeyboardButton("🆘 sᴜᴘᴘᴏʀᴛ",     url=SUPPORT_URL),
        ],
        [
            InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="pa_close"),
        ],
    ])

    msg = query.message
    try:
        await msg.delete()
    except Exception:
        pass

    await client.send_photo(
        chat_id=msg.chat.id,
        photo=qr_img,
        caption=caption,
        reply_markup=kb,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#   Callback: "I have paid"  ->  query Sellgram, verify, activate premium
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^pa_paid_(.+)$"))
async def i_have_paid(client: Bot, query: CallbackQuery):
    order_id = query.data.replace("pa_paid_", "", 1)
    user_id = query.from_user.id

    order = await _orders_col.find_one({"order_id": order_id})
    if not order:
        return await query.answer("ᴏʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ. ɢᴇɴᴇʀᴀᴛᴇ ᴀ ɴᴇᴡ ᴏɴᴇ.", show_alert=True)

    if order["user_id"] != user_id:
        return await query.answer("ᴛʜɪs ᴏʀᴅᴇʀ ᴅᴏᴇs ɴᴏᴛ ʙᴇʟᴏɴɢ ᴛᴏ ʏᴏᴜ.", show_alert=True)

    if order.get("status") == "paid":
        return await query.answer("ᴘʀᴇᴍɪᴜᴍ ᴀʟʀᴇᴀᴅʏ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ғᴏʀ ᴛʜɪs ᴏʀᴅᴇʀ.", show_alert=True)

    await query.answer("🔍 ᴠᴇʀɪғʏɪɴɢ ᴘᴀʏᴍᴇɴᴛ…")

    try:
        resp = await _check_payment(order_id)
    except Exception as e:
        return await query.message.reply(
            f"<b>⚠️ ᴄᴏᴜʟᴅ ɴᴏᴛ ʀᴇᴀᴄʜ ᴘᴀʏᴍᴇɴᴛ ᴀᴘɪ.</b>\n\n"
            f"<i>ᴛʀʏ ᴀɢᴀɪɴ ɪɴ ᴀ ғᴇᴡ sᴇᴄᴏɴᴅs.</i>\n\n"
            f"<code>{e}</code>"
        )

    data = (resp or {}).get("data") or {}
    status = data.get("status", "")
    amount_str = data.get("amount") or ""

    paid_amount = 0
    try:
        if amount_str:
            paid_amount = int(float(amount_str))
    except (TypeError, ValueError):
        paid_amount = 0

    expected = int(order["amount"])

    # Not yet success
    if status != "TXN_SUCCESS":
        return await query.message.reply(
            f"<b>❌ ᴘᴀʏᴍᴇɴᴛ ɴᴏᴛ ᴅᴇᴛᴇᴄᴛᴇᴅ ʏᴇᴛ.</b>\n\n"
            f"<b>sᴛᴀᴛᴜs:</b> <code>{status or 'Unknown'}</code>\n"
            f"<b>ᴍᴇssᴀɢᴇ:</b> <i>{data.get('resp_msg', 'Wait a few seconds and try again.')}</i>\n\n"
            f"<b>ᴏʀᴅᴇʀ ɪᴅ:</b> <code>{order_id}</code>\n\n"
            f"<i>ɪғ ʏᴏᴜ ᴊᴜsᴛ ᴘᴀɪᴅ, ᴡᴀɪᴛ 10–30 sᴇᴄᴏɴᴅs ᴀɴᴅ ᴘʀᴇss <b>ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ</b> ᴀɢᴀɪɴ.</i>"
        )

    # Amount mismatch
    if paid_amount and paid_amount < expected:
        return await query.message.reply(
            f"<b>❌ ᴘᴀʏᴍᴇɴᴛ ᴀᴍᴏᴜɴᴛ ᴍɪsᴍᴀᴛᴄʜ.</b>\n\n"
            f"<b>ᴘᴀɪᴅ:</b> ₹{paid_amount}\n"
            f"<b>ᴇxᴘᴇᴄᴛᴇᴅ:</b> ₹{expected}\n\n"
            f"<i>ᴄᴏɴᴛᴀᴄᴛ <a href=\"{SUPPORT_URL}\">sᴜᴘᴘᴏʀᴛ</a> ɪғ ʏᴏᴜ ᴘᴀɪᴅ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ᴀᴍᴏᴜɴᴛ.</i>"
        )

    # ✅ All good — activate premium with the tier saved on the order
    tier = (order.get("tier") or "gold").lower()
    expiration_time = await add_premium(
        user_id,
        int(order["time_value"]),
        order["time_unit"],
        tier,
    )

    await _orders_col.update_one(
        {"order_id": order_id},
        {"$set": {
            "status":  "paid",
            "txn_id":  data.get("txn_id"),
            "paid_at": datetime.utcnow().isoformat(),
        }},
    )

    asyncio.create_task(monitor_premium_expiry(client, user_id))

    # ── DELETE THE QR / INSTRUCTIONS MESSAGE ─────────────────────
    # query.message is the photo message (QR + caption + buttons)
    # the user paid against. Once payment is confirmed we no longer
    # need it on the user's screen; replace it with the receipt.
    qr_chat_id = query.message.chat.id
    try:
        await query.message.delete()
    except Exception:
        pass

    # ── BUILD THE DETAILED RECEIPT ───────────────────────────────
    txn_id = data.get("txn_id") or "—"

    # Active date = right now, formatted in IST (matches expiry style).
    try:
        active_date = datetime.now(_tz("Asia/Kolkata")).strftime(
            "%Y-%m-%d %H:%M:%S %p IST"
        )
    except Exception:
        active_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build a readable user name (first + last + @username when present)
    u = query.from_user
    full_name = (u.first_name or "").strip()
    if getattr(u, "last_name", None):
        full_name = f"{full_name} {u.last_name}".strip()
    if not full_name:
        full_name = "—"
    if getattr(u, "username", None):
        full_name = f"{full_name} (@{u.username})"

    plan_label = (
        order.get("plan_label")
        or f"{order['time_value']}{order['time_unit']}"
    )
    tier_emoji = "🥇" if tier == "gold" else "💎"

    receipt = (
        f"<b>🧾 ᴘᴀʏᴍᴇɴᴛ ʀᴇᴄᴇɪᴘᴛ — ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!</b>\n"
        f"<code>━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
        f"👤 <b>ᴜsᴇʀ ɴᴀᴍᴇ:</b> {full_name}\n"
        f"🆔 <b>ᴜsᴇʀ ɪᴅ:</b> <code>{user_id}</code>\n"
        f"{tier_emoji} <b>ᴘʟᴀɴ ᴛʏᴘᴇ:</b> {plan_label}\n"
        f"💰 <b>ᴘʟᴀɴ ᴀᴍᴏᴜɴᴛ:</b> ₹{order['amount']}\n"
        f"📦 <b>ᴏʀᴅᴇʀ ɪᴅ:</b> <code>{order_id}</code>\n"
        f"🔖 <b>ᴛxɴ ɪᴅ:</b> <code>{txn_id}</code>\n"
        f"📅 <b>ᴀᴄᴛɪᴠᴇ ᴅᴀᴛᴇ:</b> <code>{active_date}</code>\n"
        f"⏳ <b>ᴇxᴘɪʀᴇ ᴅᴀᴛᴇ:</b> <code>{expiration_time}</code>\n\n"
        f"<code>━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"<i>✨ ᴇɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss! ᴋᴇᴇᴘ ᴛʜɪs ʀᴇᴄᴇɪᴘᴛ ғᴏʀ ʀᴇғᴇʀᴇɴᴄᴇ.</i>"
    )

    receipt_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆘 sᴜᴘᴘᴏʀᴛ", url=SUPPORT_URL)],
        [InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="pa_close")],
    ])

    # Send the receipt as a fresh message (the QR is now gone).
    try:
        await client.send_message(
            chat_id=qr_chat_id,
            text=receipt,
            reply_markup=receipt_kb,
            disable_web_page_preview=True,
        )
    except Exception:
        # Last-resort fallback: plain reply via the (possibly already-
        # deleted) query.message handle. Telegram will just send a new
        # message in that chat in this case.
        try:
            await query.message.reply(receipt, reply_markup=receipt_kb)
        except Exception:
            pass

    # ── GIFT CHANNEL DELIVERY ────────────────────────────────────
    if order.get("gift_channel_id"):
        await _deliver_gift(client, query, order, expiration_time)

    # Notify owner
    try:
        await client.send_message(
            chat_id=OWNER_ID,
            text=(
                f"<b>💰 ɴᴇᴡ ᴘʀᴇᴍɪᴜᴍ sᴀʟᴇ</b>\n\n"
                f"<b>ᴜsᴇʀ:</b> {query.from_user.mention} (<code>{user_id}</code>)\n"
                f"<b>ᴘʟᴀɴ:</b> {order['time_value']}{order['time_unit']} — ₹{order['amount']}\n"
                f"<b>ᴏʀᴅᴇʀ:</b> <code>{order_id}</code>\n"
                f"<b>ᴛxɴ:</b> <code>{data.get('txn_id', '?')}</code>\n"
                f"<b>ᴇxᴘɪʀᴇs:</b> {expiration_time}"
            ),
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#   GIFT CHANNEL  —  helpers + callback
# ═══════════════════════════════════════════════════════════════════════════════
async def _deliver_gift(client: Bot, query: CallbackQuery, order: dict, expiration_time):
    """
    After a successful payment, if the plan has a gift channel attached:
      1. Generate a one-time invite link that requires admin approval.
      2. Send the buyer an "Open Channel" + "Done" button pair.
      3. Record the grant so we can kick the user when their premium expires.
    """
    user_id    = order["user_id"]
    channel_id = int(order["gift_channel_id"])
    title      = order.get("gift_channel_title") or str(channel_id)
    order_id   = order["order_id"]

    # 1. Create invite link (require admin approval to give us full control)
    invite_url = None
    try:
        link = await client.create_chat_invite_link(
            chat_id=channel_id,
            name=f"PremiumGift-{order_id[-8:]}",
            creates_join_request=True,
        )
        invite_url = getattr(link, "invite_link", None) or str(link)
    except Exception as e:
        # fall back to a plain invite link if join-requests aren't available
        try:
            link = await client.create_chat_invite_link(
                chat_id=channel_id,
                name=f"PremiumGift-{order_id[-8:]}",
                member_limit=1,
            )
            invite_url = getattr(link, "invite_link", None) or str(link)
        except Exception:
            try:
                await query.message.reply(
                    "<b>⚠️ ᴄᴏᴜʟᴅ ɴᴏᴛ ɢᴇɴᴇʀᴀᴛᴇ ɢɪғᴛ ɪɴᴠɪᴛᴇ ʟɪɴᴋ.</b>\n"
                    f"<code>{e}</code>\n\n"
                    "ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ — ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ɪs sᴛɪʟʟ ᴀᴄᴛɪᴠᴇ."
                )
            except Exception:
                pass
            return

    # 2. Record the grant so /remove_premium and expiry can revoke it
    try:
        if isinstance(expiration_time, datetime):
            expires_iso = expiration_time.isoformat()
        else:
            expires_iso = str(expiration_time)
        # most reliable: pull from premium collection (already in IST iso)
        prem = await _premium_col.find_one({"user_id": int(user_id)})
        if prem and prem.get("expiration_timestamp"):
            expires_iso = prem["expiration_timestamp"]

        await grant_gift(
            user_id       = int(user_id),
            channel_id    = channel_id,
            channel_title = title,
            plan_id       = str(order.get("plan_id", "")),
            expires_at    = expires_iso,
            order_id      = order_id,
        )
    except Exception:
        pass

    # 3. Send the buyer their Open Channel + Done buttons
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📨 ᴏᴘᴇɴ ᴄʜᴀɴɴᴇʟ", url=invite_url)],
        [InlineKeyboardButton("✅ ᴅᴏɴᴇ — ᴀᴅᴅ ᴍᴇ", callback_data=f"pa_giftdone_{order_id}")],
    ])
    try:
        await query.message.reply(
            f"<b>🎀 ʏᴏᴜʀ ɢɪғᴛ ᴄʜᴀɴɴᴇʟ ɪs ʀᴇᴀᴅʏ</b>\n\n"
            f"<b>ᴄʜᴀɴɴᴇʟ:</b> <b>{title}</b>\n\n"
            f"<b>ʜᴏᴡ ᴛᴏ ᴊᴏɪɴ:</b>\n"
            f"<b>1.</b> ᴛᴀᴘ <b>ᴏᴘᴇɴ ᴄʜᴀɴɴᴇʟ</b> ʙᴇʟᴏᴡ.\n"
            f"<b>2.</b> ᴛᴀᴘ <b>ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ</b> ɪɴ ᴛᴇʟᴇɢʀᴀᴍ.\n"
            f"<b>3.</b> ᴄᴏᴍᴇ ʙᴀᴄᴋ ʜᴇʀᴇ ᴀɴᴅ ᴛᴀᴘ <b>ᴅᴏɴᴇ</b>.\n\n"
            f"ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ᴀᴘᴘʀᴏᴠᴇ ʏᴏᴜ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ.\n"
            f"<i>ᴀᴄᴄᴇss ᴇɴᴅs ᴡʜᴇɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀᴇs.</i>",
            reply_markup=kb,
        )
    except Exception:
        pass


@Bot.on_callback_query(filters.regex(r"^pa_giftdone_(.+)$"))
async def gift_done(client: Bot, query: CallbackQuery):
    order_id = query.data.replace("pa_giftdone_", "", 1)
    user_id  = query.from_user.id

    order = await _orders_col.find_one({"order_id": order_id})
    if not order:
        return await query.answer("ᴏʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ.", show_alert=True)
    if order["user_id"] != user_id:
        return await query.answer("ᴛʜɪs ɢɪғᴛ ɪs ɴᴏᴛ ғᴏʀ ʏᴏᴜ.", show_alert=True)
    ch_id = order.get("gift_channel_id")
    if not ch_id:
        return await query.answer("ɴᴏ ɢɪғᴛ ᴄʜᴀɴɴᴇʟ ᴀᴛᴛᴀᴄʜᴇᴅ ᴛᴏ ᴛʜɪs ᴏʀᴅᴇʀ.", show_alert=True)

    await query.answer("ᴀᴘᴘʀᴏᴠɪɴɢ ʏᴏᴜʀ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ…")

    try:
        await client.approve_chat_join_request(chat_id=int(ch_id), user_id=user_id)
    except Exception as e:
        emsg = str(e).lower()
        # Most common: user hasn't tapped "Request to Join" yet
        if "user_not_participant" in emsg or "hide_requester" in emsg or "not found" in emsg:
            return await query.answer(
                "ᴏᴘᴇɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴛᴀᴘ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ ғɪʀsᴛ, ᴛʜᴇɴ ᴘʀᴇss ᴅᴏɴᴇ.",
                show_alert=True,
            )
        try:
            await query.message.reply(
                f"<b>⚠️ ᴀᴘᴘʀᴏᴠᴀʟ ғᴀɪʟᴇᴅ.</b>\n<code>{str(e)[:200]}</code>\n\n"
                "ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ɪғ ᴛʜɪs ᴋᴇᴇᴘs ʜᴀᴘᴘᴇɴɪɴɢ."
            )
        except Exception:
            pass
        return

    title = order.get("gift_channel_title") or str(ch_id)
    try:
        await query.message.edit_text(
            f"<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ — ᴀᴅᴅᴇᴅ!</b>\n\n"
            f"✅ ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ ɪɴᴛᴏ <b>{title}</b>.\n\n"
            "<i>ᴀᴄᴄᴇss ᴇɴᴅs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴡʜᴇɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀᴇs.</i>",
        )
    except Exception:
        try:
            await query.message.reply(
                f"<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ — ᴀᴅᴅᴇᴅ!</b>\n\n"
                f"✅ ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ ɪɴᴛᴏ <b>{title}</b>."
            )
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#   Callback: close
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^pa_close$"))
async def pa_close(client: Bot, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception:
        pass
    try:
        await query.answer()
    except Exception:
        pass
