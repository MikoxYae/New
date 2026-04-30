import asyncio
import random
import string
import time
from datetime import datetime
from io import BytesIO

import aiohttp
import qrcode
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot import Bot
from config import DB_URI, DB_NAME, OWNER_ID, PREMIUM_PIC
from database.db_premium import add_premium
from plugins.premium_cdm import monitor_premium_expiry


# ═══════════════════════════════════════════════════════════════════════════════
#   Sellgram Paytm Status API + UPI configuration
# ═══════════════════════════════════════════════════════════════════════════════
SELLGRAM_API_BASE = "https://ptapi.sellgram.in"
SELLGRAM_API_KEY = "8Mv3zQgQZNVCdU4iBaAFvtu8"

UPI_ID = "paytm.s20gmbu@pty"
PAYEE_NAME = "MikoPremium"

SUPPORT_URL = "https://t.me/Iam_addictive"


# ═══════════════════════════════════════════════════════════════════════════════
#   Plans  ->  id : (label, amount_inr, time_value, time_unit)
# ═══════════════════════════════════════════════════════════════════════════════
PLANS = {
    "1h":  ("1 ʜᴏᴜʀ (ᴛᴇsᴛ)", 1,   1,  "h"),
    "1d":  ("1 ᴅᴀʏ",         10,  1,  "d"),
    "7d":  ("7 ᴅᴀʏs",        50,  7,  "d"),
    "30d": ("30 ᴅᴀʏs",       150, 30, "d"),
}


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


def _plan_menu_text(first_name: str) -> str:
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


def _plan_menu_kb() -> InlineKeyboardMarkup:
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


# ═══════════════════════════════════════════════════════════════════════════════
#   Callback: open premium menu  (entry from "Buy Premium" button in start.py)
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^(premium|buy_premium)$"))
async def open_premium_menu(client: Bot, query: CallbackQuery):
    await query.answer()
    text = _plan_menu_text(query.from_user.first_name)
    kb = _plan_menu_kb()
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
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^pa_plan_(\w+)$"))
async def pick_plan(client: Bot, query: CallbackQuery):
    plan_id = query.data.replace("pa_plan_", "", 1)
    plan = PLANS.get(plan_id)
    if not plan:
        return await query.answer("ɪɴᴠᴀʟɪᴅ ᴘʟᴀɴ.", show_alert=True)

    label, amount, time_value, time_unit = plan
    user_id = query.from_user.id
    order_id = _gen_order_id(amount, user_id)

    await query.answer("ɢᴇɴᴇʀᴀᴛɪɴɢ ǫʀ…")

    await _orders_col.insert_one({
        "order_id":   order_id,
        "user_id":    user_id,
        "amount":     amount,
        "plan_id":    plan_id,
        "time_value": time_value,
        "time_unit":  time_unit,
        "status":     "pending",
        "created_at": datetime.utcnow().isoformat(),
    })

    qr_img = _make_qr(amount, order_id)

    caption = (
        f"<b>💳 ᴄᴏᴍᴘʟᴇᴛᴇ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ</b>\n\n"
        f"<b>ᴘʟᴀɴ:</b> {label}\n"
        f"<b>ᴀᴍᴏᴜɴᴛ:</b> <b>₹{amount}</b>\n"
        f"<b>ᴏʀᴅᴇʀ ɪᴅ:</b> <code>{order_id}</code>\n\n"
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

    # ✅ All good — activate premium (gold tier so they get token + protect bypass)
    expiration_time = await add_premium(
        user_id,
        int(order["time_value"]),
        order["time_unit"],
        "gold",
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

    await query.message.reply(
        f"<b>✅ ᴘᴀʏᴍᴇɴᴛ ᴠᴇʀɪғɪᴇᴅ — ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!</b>\n\n"
        f"<b>ᴏʀᴅᴇʀ ɪᴅ:</b> <code>{order_id}</code>\n"
        f"<b>ᴀᴍᴏᴜɴᴛ:</b> ₹{order['amount']}\n"
        f"<b>ᴅᴜʀᴀᴛɪᴏɴ:</b> {order['time_value']}{order['time_unit']}\n"
        f"<b>ᴇxᴘɪʀᴇs ᴏɴ:</b> {expiration_time}\n\n"
        f"<i>ᴇɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss! 🎉</i>"
    )

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
