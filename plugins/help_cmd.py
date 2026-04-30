# ──────────────────────────────────────────────────────────────────────────────
#  /help  —  paginated, button-driven help menu
#
#  Built as a NEW plugin so the existing `cb_handler` regex in cbb.py keeps
#  working untouched. This file owns:
#
#     • /help       command (anyone in private chat)
#     • hlp_*       callback prefix for navigation
#
#  Why buttons? Telegram has a 4096-char text limit per message AND inline
#  callback markup is much nicer to read than one giant wall of text. Each
#  page is well under 4096 chars so we never truncate.
#
#  Owner-only pages are gated TWICE:
#     1. The OWNER COMMANDS button is only shown when the viewer is owner /
#        admin (so users don't even see it).
#     2. Every owner-prefixed callback re-checks ownership before rendering,
#        so a curious user can't craft a callback by hand to peek.
# ──────────────────────────────────────────────────────────────────────────────

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot import Bot
from config import OWNER, OWNER_ID
from database.database import db
from helper_func import get_support_url


# ═════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═════════════════════════════════════════════════════════════════════════════
async def _is_owner_or_admin(uid: int) -> bool:
    """True when user is the configured OWNER or a DB-registered admin."""
    if uid == OWNER_ID:
        return True
    try:
        return bool(await db.admin_exist(uid))
    except Exception:
        return False


def _owner_fallback_url() -> str:
    """t.me/{OWNER} — fallback used when the admin hasn't set a support link."""
    user = (OWNER or "").lstrip("@").strip()
    if not user:
        return "https://t.me/"
    return f"https://t.me/{user}"


async def _support_url() -> str:
    """
    Resolve the live support URL for the SUPPORT button.

    Prefers the admin-configured link saved via /settings → Support,
    and falls back to the OWNER's t.me profile when nothing is set.
    """
    return await get_support_url(_owner_fallback_url())


def _close_row():
    return [InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="hlp_close")]


def _back_close_row(back_cb: str = "hlp_main"):
    return [
        InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=back_cb),
        InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="hlp_close"),
    ]


# ═════════════════════════════════════════════════════════════════════════════
#  Page text  (kept as plain strings so they're easy to edit)
# ═════════════════════════════════════════════════════════════════════════════

MAIN_TXT = (
    "<b>📖 ʜᴇʟᴘ ᴍᴇɴᴜ</b>\n\n"
    "ᴄʜᴏᴏsᴇ ᴀ sᴇᴄᴛɪᴏɴ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴇ ᴀʟʟ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs.\n\n"
    "👤 <b>ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs</b> — sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ, ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ, ᴠᴇʀɪғʏ ᴀ ᴘᴀʏᴍᴇɴᴛ.\n"
    "⚙️ <b>ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs</b> — ᴀᴅᴍɪɴ, ʀᴇᴘᴏʀᴛs, ʙʀᴏᴀᴅᴄᴀsᴛ, ʀᴇᴄᴏᴠᴇʀʏ.\n\n"
    "<i>ᴏᴡɴᴇʀ sᴇᴄᴛɪᴏɴ ɪs ᴠɪsɪʙʟᴇ ᴏɴʟʏ ᴛᴏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ.</i>"
)

USER_TXT = (
    "<b>👤 ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs</b>\n\n"
    "🔹 <b>/sᴛᴀʀᴛ</b>\n"
    "ᴏᴘᴇɴ ᴛʜᴇ ʙᴏᴛ. ᴀʟsᴏ ᴜsᴇᴅ ɪɴᴛᴇʀɴᴀʟʟʏ ʙʏ sʜᴀʀᴇ-ʟɪɴᴋs ᴛᴏ ᴅᴇʟɪᴠᴇʀ ғɪʟᴇs.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/start</code>\n\n"
    "🔹 <b>/ʜᴇʟᴘ</b>\n"
    "sʜᴏᴡs ᴛʜɪs ʜᴇʟᴘ ᴍᴇɴᴜ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/help</code>\n\n"
    "🔹 <b>/ᴍʏᴘʟᴀɴ</b>\n"
    "sʜᴏᴡs ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ, ᴇxᴘɪʀʏ ᴀɴᴅ ʀᴇᴍᴀɪɴɪɴɢ ᴛɪᴍᴇ. "
    "ʀᴇᴛᴜʀɴs <code>ɴᴏ ᴀᴄᴛɪᴠᴇ ᴘʟᴀɴ</code> ɪғ ʏᴏᴜ ᴀʀᴇɴ'ᴛ ᴘʀᴇᴍɪᴜᴍ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/myplan</code>\n\n"
    "🔹 <b>ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ</b>\n"
    "ᴏᴘᴇɴ /sᴛᴀʀᴛ → <code>ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ</code>. ᴘɪᴄᴋ ᴀ ᴘʟᴀɴ "
    "(<code>1ʜ ₹1</code>, <code>1ᴅ ₹10</code>, <code>7ᴅ ₹50</code>, "
    "<code>30ᴅ ₹150</code>) → sᴄᴀɴ ᴜᴘɪ ǫʀ → ᴘᴀʏ ᴛʜᴇ ᴇxᴀᴄᴛ ᴀᴍᴏᴜɴᴛ → "
    "ᴛᴀᴘ <code>✅ ɪ ᴘᴀɪᴅ</code>. ᴀᴜᴛᴏ-ᴠᴇʀɪғɪᴇᴅ ᴠɪᴀ sᴇʟʟɢʀᴀᴍ ᴀᴘɪ.\n"
    "<i>ᴏʀᴅᴇʀ-ɪᴅ ғᴏʀᴍᴀᴛ:</i> <code>ZERO-{amount}-{user_id}-{ts}-{HEX4}</code>\n\n"
    "🔹 <b>🧾 ᴘᴀʏᴍᴇɴᴛ ʀᴇᴄᴇɪᴘᴛ</b> <i>(ᴜᴘᴅᴀᴛᴇᴅ — ᴠ1.12)</i>\n"
    "ᴀs sᴏᴏɴ ᴀs ᴛʜᴇ ᴘᴀʏᴍᴇɴᴛ ɪs ᴠᴇʀɪғɪᴇᴅ, ᴛʜᴇ ǫʀ + ɪɴsᴛʀᴜᴄᴛɪᴏɴs ᴍᴇssᴀɢᴇ "
    "ɪs <b>ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ</b> ᴀɴᴅ ʏᴏᴜ ɢᴇᴛ ᴀ <b>ᴘɴɢ ʀᴇᴄᴇɪᴘᴛ ɪᴍᴀɢᴇ</b> ᴅᴇʟɪᴠᴇʀᴇᴅ "
    "ᴀs ᴀ ᴅᴏᴄᴜᴍᴇɴᴛ (ᴅᴏᴡɴʟᴏᴀᴅᴀʙʟᴇ <code>receipt_&lt;order_id&gt;.png</code>) "
    "ᴄᴏɴᴛᴀɪɴɪɴɢ:\n"
    "  • 👤 ᴜsᴇʀ ɴᴀᴍᴇ\n"
    "  • 🆔 ᴜsᴇʀ ɪᴅ\n"
    "  • 💎 ᴘʟᴀɴ ᴛʏᴘᴇ\n"
    "  • 💰 ᴘʟᴀɴ ᴀᴍᴏᴜɴᴛ\n"
    "  • 📦 ᴏʀᴅᴇʀ ɪᴅ\n"
    "  • 🔖 ᴛxɴ ɪᴅ\n"
    "  • 📅 ᴀᴄᴛɪᴠᴇ ᴅᴀᴛᴇ (ɪsᴛ)\n"
    "  • ⏳ ᴇxᴘɪʀᴇ ᴅᴀᴛᴇ (ɪsᴛ)\n"
    "<i>sᴀᴠᴇ ᴛʜᴇ ɪᴍᴀɢᴇ ғᴏʀ ʏᴏᴜʀ ʀᴇᴄᴏʀᴅs — sᴜᴘᴘᴏʀᴛ ᴄᴀɴ ᴜsᴇ ᴛʜᴇ ᴏʀᴅᴇʀ-ɪᴅ "
    "ᴏʀ ᴛxɴ-ɪᴅ ғᴏʀ ʟᴏᴏᴋᴜᴘ.</i>"
)

OWNER_MAIN_TXT = (
    "<b>⚙️ ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs</b>\n\n"
    "ᴘɪᴄᴋ ᴀ ᴄᴀᴛᴇɢᴏʀʏ:\n\n"
    "📋 <b>ᴀᴅᴍɪɴ ᴏʀᴅᴇʀs</b> — ɪɴsᴘᴇᴄᴛ ᴀɴᴅ ʀᴇᴄᴏᴠᴇʀ ᴘʀᴇᴍɪᴜᴍ ᴏʀᴅᴇʀs\n"
    "💎 <b>ᴘʀᴇᴍɪᴜᴍ ᴍɢᴍᴛ</b> — ɢʀᴀɴᴛ / ʀᴇᴠᴏᴋᴇ ᴘʀᴇᴍɪᴜᴍ\n"
    "🔗 <b>ʟɪɴᴋ ɢᴇɴ</b> — ʙᴀᴛᴄʜ, ɢᴇɴʟɪɴᴋ, ᴄᴜsᴛᴏᴍ_ʙᴀᴛᴄʜ\n"
    "📢 <b>ʙʀᴏᴀᴅᴄᴀsᴛs</b> — ᴀʟʟ ʙʀᴏᴀᴅᴄᴀsᴛ ᴠᴀʀɪᴀɴᴛs\n"
    "🔐 <b>ᴄʀᴇᴅᴇɴᴛɪᴀʟs</b> — ʟɪᴠᴇ ʀᴏᴛᴀᴛᴇ ᴜᴘɪ + sᴇʟʟɢʀᴀᴍ ᴋᴇʏ\n"
    "📊 <b>sᴛᴀᴛs & sᴇᴛᴛɪɴɢs</b> — ᴀɴᴀʟʏᴛɪᴄs + ʙᴏᴛ ᴄᴏɴғɪɢ"
)

OWNER_CREDS_TXT = (
    "<b>🔐 ᴄʀᴇᴅᴇɴᴛɪᴀʟs ʀᴏᴛᴀᴛɪᴏɴ</b>  <i>(ᴏᴡɴᴇʀ-ᴏɴʟʏ)</i>\n\n"
    "🔸 <b>/ʀᴏᴛᴀᴛᴇ_ᴜᴘɪ</b> <code>&lt;new_upi&gt;</code> <code>&lt;new_api_key&gt;</code>\n"
    "ʟɪᴠᴇ-sᴡᴀᴘ ᴛʜᴇ ᴜᴘɪ ʀᴇᴄᴇɪᴠᴇʀ ᴀɴᴅ sᴇʟʟɢʀᴀᴍ ᴀᴘɪ ᴋᴇʏ ᴡɪᴛʜᴏᴜᴛ ʀᴇsᴛᴀʀᴛɪɴɢ "
    "ᴛʜᴇ ʙᴏᴛ. ᴄʜᴀɴɢᴇs ᴀʀᴇ ᴡʀɪᴛᴛᴇɴ ᴛᴏ <code>plugins/premium_system/premium_auto.py</code> "
    "ᴀɴᴅ <code>plugins/premium_system/admin_orders.py</code> sᴏ ᴛʜᴇʏ sᴜʀᴠɪᴠᴇ ᴀ ʀᴇsᴛᴀʀᴛ "
    "ᴛᴏᴏ.\n"
    "ᴠᴀʟɪᴅᴀᴛɪᴏɴ:\n"
    "  • ᴜᴘɪ ᴍᴜsᴛ ᴍᴀᴛᴄʜ <code>name@handle</code>\n"
    "  • ᴀᴘɪ ᴋᴇʏ ᴍᴜsᴛ ʙᴇ 16-128 ᴜʀʟ-sᴀғᴇ ᴀʟᴘʜᴀɴᴜᴍᴇʀɪᴄ\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i>\n"
    "<code>/rotate_upi paytm.s20gmbu@pty 8Mv3zQgQZNVCdU4iBaAFvtu8</code>\n\n"
    "🔸 <b>/sʜᴏᴡ_ᴄʀᴇᴅs</b>\n"
    "sʜᴏᴡ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛʟʏ-ᴀᴄᴛɪᴠᴇ ᴜᴘɪ + ᴍᴀsᴋᴇᴅ ᴀᴘɪ ᴋᴇʏ. ᴜsᴇғᴜʟ ʀɪɢʜᴛ "
    "ᴀғᴛᴇʀ <code>/rotate_upi</code> ᴛᴏ ᴠᴇʀɪғʏ ᴛʜᴇ sᴡᴀᴘ ʟᴀɴᴅᴇᴅ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/show_creds</code>\n\n"
    "<i>ʙᴏᴛʜ ᴄᴏᴍᴍᴀɴᴅs ᴀʀᴇ ʟᴏᴄᴋᴇᴅ ᴛᴏ <code>OWNER_ID</code> — ᴇᴠᴇɴ ᴅʙ-"
    "ʀᴇɢɪsᴛᴇʀᴇᴅ ᴀᴅᴍɪɴs ᴄᴀɴɴᴏᴛ ʀᴜɴ ᴛʜᴇᴍ.</i>"
)

OWNER_ORDERS_TXT = (
    "<b>📋 ᴀᴅᴍɪɴ ᴏʀᴅᴇʀs ᴘᴀɴᴇʟ</b>  <i>(ᴏᴡɴᴇʀ-ᴏɴʟʏ)</i>\n\n"
    "🔸 <b>/ɪᴅ</b> [<code>today</code>|<code>yesterday</code>|<code>DD-MM-YYYY</code>]\n"
    "ʟɪsᴛ ᴀʟʟ ᴜsᴇʀ-ɪᴅs ᴡʜᴏ ᴘᴀɪᴅ ᴏɴ ᴀ ɢɪᴠᴇɴ ᴅᴀᴛᴇ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇs:</i>\n"
    "<code>/id</code>\n"
    "<code>/id today</code>\n"
    "<code>/id yesterday</code>\n"
    "<code>/id 26-04-2026</code>\n\n"
    "🔸 <b>/ᴏʀᴅ</b> <code>&lt;user_id&gt;</code>\n"
    "sʜᴏᴡ ᴀʟʟ ᴏʀᴅᴇʀs ᴏғ ᴀ sᴘᴇᴄɪғɪᴄ ᴜsᴇʀ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/ord 7137144805</code>\n\n"
    "🔸 <b>/ᴀᴍᴏᴜɴᴛ</b> [<code>today</code>|<code>yesterday</code>|<code>DD-MM-YYYY</code>]\n"
    "sʜᴏᴡ ᴛᴏᴛᴀʟ ʀᴇᴠᴇɴᴜᴇ ᴄᴏʟʟᴇᴄᴛᴇᴅ ᴏɴ ᴀ ᴅᴀᴛᴇ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/amount today</code>\n\n"
    "🔸 <b>/sᴛᴀᴛs</b>\n"
    "ᴏᴠᴇʀᴀʟʟ ʙᴏᴛ + ᴏʀᴅᴇʀs sᴛᴀᴛs (ᴛᴏᴛᴀʟ ᴜsᴇʀs, ᴘᴀɪᴅ ᴜsᴇʀs, ʟɪғᴇᴛɪᴍᴇ ʀᴇᴠᴇɴᴜᴇ).\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/stats</code>\n\n"
    "🔸 <b>/ᴄʜᴇᴄᴋᴏʀᴅᴇʀ</b> <code>&lt;order_id&gt;</code>\n"
    "ʟᴏᴏᴋ ᴜᴘ ᴀɴ ᴏʀᴅᴇʀ ᴀɢᴀɪɴsᴛ sᴇʟʟɢʀᴀᴍ ᴀᴘɪ + ᴅʙ. <i>ʀᴇᴀᴅ-ᴏɴʟʏ ᴅᴇʙᴜɢ.</i>\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/checkorder ZERO-1-7137144805-1777510697-A1F4</code>\n\n"
    "🔸 <b>/ғᴏʀᴄᴇᴠᴇʀɪғʏ</b> <code>&lt;order_id&gt;</code>\n"
    "ʀᴇᴄᴏᴠᴇʀʏ ᴄᴏᴍᴍᴀɴᴅ. ᴡʜᴇɴ sᴇʟʟɢʀᴀᴍ sᴀʏs sᴜᴄᴄᴇss ʙᴜᴛ ᴅʙ sᴀʏs <code>failed</code>, "
    "ᴛʜɪs ʀᴇ-ᴄʜᴇᴄᴋs, ᴘʀᴏᴍᴏᴛᴇs ᴛᴏ <code>paid</code>, ᴀᴄᴛɪᴠᴀᴛᴇs ᴘʀᴇᴍɪᴜᴍ, ᴀɴᴅ "
    "sᴇɴᴅs ᴛʜᴇ ᴜsᴇʀ ʀᴇᴄᴇɪᴘᴛ + ɪɴᴠɪᴛᴇ ʟɪɴᴋ. ᴀʟsᴏ ғɪxᴇs <code>/id</code>, "
    "<code>/ord</code>, <code>/amount</code>. 💪\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/forceverify ZERO-1-7137144805-1777510697-A1F4</code>"
)

OWNER_PREMIUM_TXT = (
    "<b>💎 ᴘʀᴇᴍɪᴜᴍ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ</b>\n\n"
    "🔸 <b>/ᴀᴅᴅᴘʀᴇᴍɪᴜᴍ</b> <code>&lt;user_id&gt;</code> <code>&lt;duration&gt;</code>\n"
    "ɢʀᴀɴᴛ ᴘʀᴇᴍɪᴜᴍ ᴍᴀɴᴜᴀʟʟʏ. ᴅᴜʀᴀᴛɪᴏɴ: <code>1h</code>, <code>1d</code>, "
    "<code>7d</code>, <code>30d</code>, ᴇᴛᴄ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/addpremium 7137144805 30d</code>\n\n"
    "🔸 <b>/ʀᴇᴍᴏᴠᴇ_ᴘʀᴇᴍɪᴜᴍ</b> <code>&lt;user_id&gt;</code>\n"
    "ʀᴇᴠᴏᴋᴇ ᴀ ᴜsᴇʀ's ᴘʀᴇᴍɪᴜᴍ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/remove_premium 7137144805</code>\n\n"
    "🔸 <b>/ᴘʀᴇᴍɪᴜᴍ_ᴜsᴇʀs</b>\n"
    "ʟɪsᴛ ᴀʟʟ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴡɪᴛʜ ᴇxᴘɪʀʏ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/premium_users</code>\n\n"
    "🔸 <b>/sᴛᴀʀᴛ_ᴘʀᴇᴍɪᴜᴍ_ᴍᴏɴɪᴛᴏʀɪɴɢ</b>\n"
    "(ʀᴇ-)sᴛᴀʀᴛ ᴛʜᴇ ʙᴀᴄᴋɢʀᴏᴜɴᴅ ᴊᴏʙ ᴛʜᴀᴛ ᴇxᴘɪʀᴇs ᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ sᴇssɪᴏɴs.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/start_premium_monitoring</code>"
)

OWNER_LINK_TXT = (
    "<b>🔗 ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴏʀs</b>\n\n"
    "🔸 <b>/ɢᴇɴʟɪɴᴋ</b>\n"
    "ɢᴇɴᴇʀᴀᴛᴇ ᴀ sʜᴀʀᴇ-ʟɪɴᴋ ғᴏʀ ᴀ <i>sɪɴɢʟᴇ</i> ᴅʙ-ᴄʜᴀɴɴᴇʟ ᴍᴇssᴀɢᴇ. ʙᴏᴛ "
    "ᴡɪʟʟ ᴀsᴋ ʏᴏᴜ ᴛᴏ ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/genlink</code>\n\n"
    "🔸 <b>/ʙᴀᴛᴄʜ</b>\n"
    "ɢᴇɴᴇʀᴀᴛᴇ ᴀ ʀᴀɴɢᴇ ʟɪɴᴋ ʙᴇᴛᴡᴇᴇɴ ᴛᴡᴏ ᴅʙ-ᴄʜᴀɴɴᴇʟ ᴍᴇssᴀɢᴇs (ɪɴᴄʟᴜsɪᴠᴇ). "
    "ʙᴏᴛ ᴀsᴋs ғᴏʀ ɢɪʀsᴛ + ʟᴀsᴛ ғᴏʀᴡᴀʀᴅ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/batch</code>\n\n"
    "🔸 <b>/ᴄᴜsᴛᴏᴍ_ʙᴀᴛᴄʜ</b>\n"
    "ɪɴᴛᴇʀᴀᴄᴛɪᴠᴇ ᴄᴏʟʟᴇᴄᴛɪᴏɴ. sᴇɴᴅ ᴀʟʟ ᴍᴇᴅɪᴀ/ғɪʟᴇs ʏᴏᴜ ᴡᴀɴᴛ → ᴘʀᴇss "
    "<code>STOP</code> → ʙᴏᴛ ʀᴇᴛᴜʀɴs ᴀ sɪɴɢʟᴇ ʙᴀᴛᴄʜ ʟɪɴᴋ.\n"
    "ᴄᴏᴘɪᴇs ᴇxᴀᴄᴛʟʏ ᴏɴᴄᴇ (ᴠ1.5 ғɪx) — ɴᴏ ᴅᴜᴘᴇs, ɴᴏ sᴛᴏᴘ-ᴊᴜɴᴋ-ʟɪɴᴋ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/custom_batch</code>\n\n"
    "<i>ᴀʟʟ ᴛʜʀᴇᴇ ᴀʟsᴏ ᴀᴄᴄᴇᴘᴛ ᴀ ᴅʙ-ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ʟɪɴᴋ ɪɴsᴛᴇᴀᴅ ᴏғ ᴀ ғᴏʀᴡᴀʀᴅ.</i>\n\n"
    "🔸 <b>ᴅɪʀᴇᴄᴛ ᴜᴘʟᴏᴀᴅ</b>\n"
    "sᴇɴᴅ ᴀɴʏ ᴍᴇᴅɪᴀ/ғɪʟᴇ ᴅɪʀᴇᴄᴛʟʏ ᴛᴏ ᴛʜᴇ ʙᴏᴛ — ɪᴛ ᴀᴜᴛᴏ-sᴛᴏʀᴇs ɪɴ ᴅʙ "
    "ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ʀᴇᴘʟɪᴇs ᴡɪᴛʜ ᴀ sʜᴀʀᴇ-ʟɪɴᴋ. ɴᴏ ᴄᴏᴍᴍᴀɴᴅ ɴᴇᴇᴅᴇᴅ."
)

OWNER_BC_TXT = (
    "<b>📢 ʙʀᴏᴀᴅᴄᴀsᴛs</b>\n\n"
    "🔸 <b>/ʙʀᴏᴀᴅᴄᴀsᴛ</b>  <i>(ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ)</i>\n"
    "sᴇɴᴅ ᴛʜᴀᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs. ᴜsᴇs ɴᴏʀᴍᴀʟ <code>send_message</code>, "
    "sᴏ ᴜsᴇʀs sᴇᴇ ɪᴛ ᴀs ᴀ ᴘʟᴀɪɴ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴛʜᴇ ʙᴏᴛ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ᴍᴇssᴀɢᴇ → <code>/broadcast</code>\n\n"
    "🔸 <b>/ᴘʙʀᴏᴀᴅᴄᴀsᴛ</b>  <i>(ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ)</i>\n"
    "ᴘɪɴɴᴇᴅ ʙʀᴏᴀᴅᴄᴀsᴛ — sᴀᴍᴇ ᴀs <code>/broadcast</code> ʙᴜᴛ ᴀʟsᴏ ᴘɪɴs ᴛʜᴇ "
    "ᴍᴇssᴀɢᴇ ɪɴ ᴇᴀᴄʜ ᴜsᴇʀ's ᴘᴍ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> ʀᴇᴘʟʏ → <code>/pbroadcast</code>\n\n"
    "🔸 <b>/ᴅʙʀᴏᴀᴅᴄᴀsᴛ</b> <code>&lt;seconds&gt;</code>  <i>(ʀᴇᴘʟʏ)</i>\n"
    "ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ. ᴍᴇssᴀɢᴇ ᴅᴇʟᴇᴛᴇs ᴀғᴛᴇʀ <code>seconds</code> "
    "ɪɴ ᴇᴠᴇʀʏ ᴜsᴇʀ's ᴘᴍ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> ʀᴇᴘʟʏ → <code>/dbroadcast 60</code>"
)

OWNER_STATS_TXT = (
    "<b>📊 sᴛᴀᴛs & sᴇᴛᴛɪɴɢs</b>\n\n"
    "🔸 <b>/sᴇᴛᴛɪɴɢs</b>\n"
    "ᴏᴘᴇɴ ᴛʜᴇ ɪɴʟɪɴᴇ sᴇᴛᴛɪɴɢs ᴘᴀɴᴇʟ — ᴀᴅᴍɪɴs, ʙᴀɴ, ғᴏʀᴄᴇ-sᴜʙ, "
    "ʀᴇǫᴜᴇsᴛ ᴍᴏᴅᴇ, ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ, sʜᴏʀᴛᴇɴᴇʀ, ᴄᴀᴘᴛɪᴏɴ, "
    "ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, ᴇᴛᴄ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/settings</code>\n\n"
    "🔸 <b>🆘 sᴜᴘᴘᴏʀᴛ ʟɪɴᴋ</b>  <i>(ɴᴇᴡ — ᴠ1.12)</i>\n"
    "ɪɴ <code>/settings</code> → tap <b>🆘 sᴜᴘᴘᴏʀᴛ</b> ᴛᴏ sᴇᴛ ᴛʜᴇ sᴜᴘᴘᴏʀᴛ "
    "ʟɪɴᴋ ᴛʜᴀᴛ ᴀᴘᴘᴇᴀʀs ᴀᴄʀᴏss ᴛʜᴇ ʙᴏᴛ (ʀᴇᴄᴇɪᴘᴛs, ǫʀ-ᴇʀʀᴏʀs, "
    "ᴀᴍᴏᴜɴᴛ-ᴍɪsᴍᴀᴛᴄʜ, ʙᴀɴ ɴᴏᴛɪᴄᴇ, /help). ᴀᴄᴄᴇᴘᴛs ᴀɴʏ ᴏғ:\n"
    "  • <code>https://t.me/Iam_addictive</code>\n"
    "  • <code>t.me/Iam_addictive</code>\n"
    "  • <code>@Iam_addictive</code>\n"
    "  • <code>Iam_addictive</code>\n"
    "ᴀᴜᴛᴏ-ɴᴏʀᴍᴀʟɪᴢᴇᴅ ᴀɴᴅ sᴀᴠᴇᴅ ᴛᴏ ᴅʙ. ᴜsᴇ ᴄʟᴇᴀʀ ᴛᴏ ʀᴇᴠᴇʀᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛ.\n\n"
    "🔸 <b>/ᴘᴇᴀᴋʜᴏᴜʀs</b>\n"
    "sʜᴏᴡ ʜᴏᴜʀʟʏ ᴀᴄᴛɪᴠɪᴛʏ ʜɪsᴛᴏɢʀᴀᴍ — ᴡʜᴇɴ ᴜsᴇʀs ᴀʀᴇ ᴍᴏsᴛ ᴀᴄᴛɪᴠᴇ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/peakhours</code>\n\n"
    "🔸 <b>/ᴡᴇᴇᴋʟʏʀᴇᴘᴏʀᴛ</b>\n"
    "7-ᴅᴀʏ ᴀɴᴀʟʏᴛɪᴄs ʀᴏʟʟ-ᴜᴘ.\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/weeklyreport</code>\n\n"
    "🔸 <b>/ᴄʟᴇᴀɴsᴛᴀᴛs</b>\n"
    "ᴡɪᴘᴇ sᴛᴏʀᴇᴅ ᴀᴄᴛɪᴠɪᴛʏ ᴄᴏᴜɴᴛᴇʀs (sᴛᴀʀᴛs ғʀᴇsʜ).\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/cleanstats</code>\n\n"
    "🔸 <b>/ᴄᴏᴍᴍᴀɴᴅs</b>\n"
    "ʟᴇɢᴀᴄʏ sʜᴏʀᴛ ᴀᴅᴍɪɴ-ᴄᴍᴅs ʟɪsᴛ (ᴋᴇᴘᴛ ғᴏʀ ʙᴀᴄᴋᴡᴀʀᴅ ᴄᴏᴍᴘᴀᴛ).\n"
    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>/commands</code>"
)


# ═════════════════════════════════════════════════════════════════════════════
#  Keyboards
# ═════════════════════════════════════════════════════════════════════════════
def _main_kb(is_owner: bool, support_url: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton("👤 ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs", callback_data="hlp_user")]]
    if is_owner:
        rows.append(
            [InlineKeyboardButton("⚙️ ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs", callback_data="hlp_owner")]
        )
    rows.append(
        [
            InlineKeyboardButton("📞 sᴜᴘᴘᴏʀᴛ", url=support_url),
            InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="hlp_close"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def _user_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([_back_close_row("hlp_main")])


def _owner_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 ᴀᴅᴍɪɴ ᴏʀᴅᴇʀs", callback_data="hlp_o_orders")],
            [InlineKeyboardButton("💎 ᴘʀᴇᴍɪᴜᴍ ᴍɢᴍᴛ", callback_data="hlp_o_prem")],
            [InlineKeyboardButton("🔗 ʟɪɴᴋ ɢᴇɴ", callback_data="hlp_o_link")],
            [InlineKeyboardButton("📢 ʙʀᴏᴀᴅᴄᴀsᴛs", callback_data="hlp_o_bc")],
            [InlineKeyboardButton("🔐 ᴄʀᴇᴅᴇɴᴛɪᴀʟs", callback_data="hlp_o_creds")],
            [InlineKeyboardButton("📊 sᴛᴀᴛs & sᴇᴛᴛɪɴɢs", callback_data="hlp_o_stat")],
            _back_close_row("hlp_main"),
        ]
    )


def _owner_sub_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([_back_close_row("hlp_owner")])


# ═════════════════════════════════════════════════════════════════════════════
#  /help command
# ═════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    is_owner = await _is_owner_or_admin(message.from_user.id)
    support_url = await _support_url()
    await message.reply_text(
        MAIN_TXT,
        reply_markup=_main_kb(is_owner, support_url),
        disable_web_page_preview=True,
        quote=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
#  Callback router  —  prefix "hlp_"
# ═════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^hlp_"))
async def help_cb(client: Client, query: CallbackQuery):
    data = query.data
    uid = query.from_user.id
    is_owner = await _is_owner_or_admin(uid)

    # gate every owner-prefixed page
    if data.startswith("hlp_o") and not is_owner:
        try:
            await query.answer("ᴏᴡɴᴇʀ-ᴏɴʟʏ.", show_alert=True)
        except Exception:
            pass
        return

    # ── close ────────────────────────────────────────────────────────────
    if data == "hlp_close":
        try:
            await query.message.delete()
        except Exception:
            pass
        try:
            await query.answer()
        except Exception:
            pass
        return

    # ── main ─────────────────────────────────────────────────────────────
    if data == "hlp_main":
        support_url = await _support_url()
        await _safe_edit(query, MAIN_TXT, _main_kb(is_owner, support_url))
        return

    # ── user commands ────────────────────────────────────────────────────
    if data == "hlp_user":
        await _safe_edit(query, USER_TXT, _user_kb())
        return

    # ── owner: main category list ────────────────────────────────────────
    if data == "hlp_owner":
        await _safe_edit(query, OWNER_MAIN_TXT, _owner_main_kb())
        return

    # ── owner: subpages ─────────────────────────────────────────────────
    sub_pages = {
        "hlp_o_orders": OWNER_ORDERS_TXT,
        "hlp_o_prem":   OWNER_PREMIUM_TXT,
        "hlp_o_link":   OWNER_LINK_TXT,
        "hlp_o_bc":     OWNER_BC_TXT,
        "hlp_o_creds":  OWNER_CREDS_TXT,
        "hlp_o_stat":   OWNER_STATS_TXT,
    }
    if data in sub_pages:
        await _safe_edit(query, sub_pages[data], _owner_sub_kb())
        return

    # unknown -> just ack
    try:
        await query.answer()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: edit message text gracefully even if the message is a photo/etc.
# ─────────────────────────────────────────────────────────────────────────────
async def _safe_edit(query: CallbackQuery, text: str, kb: InlineKeyboardMarkup):
    try:
        await query.message.edit_text(
            text, reply_markup=kb, disable_web_page_preview=True
        )
    except Exception:
        # if the message is a photo (caption only) or already same text, fall
        # back to deleting + sending fresh.
        try:
            await query.message.delete()
        except Exception:
            pass
        try:
            await query.message.chat.send_message(
                text, reply_markup=kb, disable_web_page_preview=True
            )
        except Exception:
            pass
    try:
        await query.answer()
    except Exception:
        pass
