#  ─────────────────────────────────────────────
#   /psetting  —  Premium Plan manager (admin)
#   /plans     —  Show available plans (any user)
#
#   By Yae X Miko
#  ─────────────────────────────────────────────

from pyrogram import Client, filters, StopPropagation
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from datetime import datetime
from pytz import timezone

from bot import Bot
from helper_func import admin
from database.db_plans import (
    add_plan, list_plans, delete_plan, get_plan,
    format_plan_line, format_plans_block,
    ALLOWED_UNITS, to_addpremium_unit,
    set_gift_channel, clear_gift_channel,
)
from database.db_premium import add_premium

# Pretty unit labels for the manual-grant receipt
_UNIT_LABELS_SMALLCAPS = {
    "s": "sᴇᴄᴏɴᴅs", "m": "ᴍɪɴᴜᴛᴇs", "h": "ʜᴏᴜʀs",
    "d": "ᴅᴀʏs", "w": "ᴡᴇᴇᴋs", "mon": "ᴍᴏɴᴛʜs", "y": "ʏᴇᴀʀs",
}

PSETTING_PIC = "https://graph.org/file/d18515f99d522b3ee4e6f-876aedcb4f5dde2d4e.jpg"

# user_id -> { step, draft, msg_id, chat_id }
_pending: dict = {}


# ═══════════════════════════════════════════════════════════════
#  MARKUP HELPERS
# ═══════════════════════════════════════════════════════════════

def _main_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 ʟɪsᴛ ᴘʟᴀɴs",  callback_data="pst_list"),
            InlineKeyboardButton("➕ ᴀᴅᴅ ᴘʟᴀɴ",    callback_data="pst_add"),
        ],
        [
            InlineKeyboardButton("🗑 ᴅᴇʟᴇᴛᴇ ᴘʟᴀɴ", callback_data="pst_del_menu"),
            InlineKeyboardButton("🎁 ɢʀᴀɴᴛ",       callback_data="pst_grant_menu"),
        ],
        [
            InlineKeyboardButton("🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ", callback_data="pst_gift_menu"),
        ],
        [InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="pst_close")],
    ])


def _back_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="pst_back")]])


def _unit_markup():
    rows = []
    units = list(ALLOWED_UNITS.items())
    for i in range(0, len(units), 3):
        rows.append([
            InlineKeyboardButton(label, callback_data=f"pst_unit_{code}")
            for code, label in units[i:i + 3]
        ])
    rows.append([InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")])
    return InlineKeyboardMarkup(rows)


async def _edit(query: CallbackQuery, caption: str, markup):
    """Edit caption when message has photo, else edit text."""
    try:
        await query.message.edit_caption(caption=caption, reply_markup=markup)
    except Exception:
        try:
            await query.message.edit_text(caption, reply_markup=markup)
        except Exception:
            pass


async def _patch(client: Client, chat_id: int, msg_id: int, caption: str, markup):
    try:
        await client.edit_message_caption(chat_id, msg_id, caption=caption, reply_markup=markup)
    except Exception:
        try:
            await client.edit_message_text(chat_id, msg_id, caption, reply_markup=markup)
        except Exception:
            pass


def _main_caption() -> str:
    return (
        "<b>🥇 ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ ᴍᴀɴᴀɢᴇʀ</b>\n"
        "─────────────────────\n\n"
        "<b>📋 ʟɪsᴛ ᴘʟᴀɴs</b> — sᴇᴇ ᴀʟʟ ᴄᴏɴғɪɢᴜʀᴇᴅ ᴘʟᴀɴs\n"
        "<b>➕ ᴀᴅᴅ ᴘʟᴀɴ</b> — ᴄʀᴇᴀᴛᴇ ᴀ ɴᴇᴡ ᴘʟᴀɴ (ɴᴀᴍᴇ, ᴅᴜʀᴀᴛɪᴏɴ, ᴘʀɪᴄᴇ)\n"
        "<b>🗑 ᴅᴇʟᴇᴛᴇ ᴘʟᴀɴ</b> — ʀᴇᴍᴏᴠᴇ ᴀɴ ᴇxɪsᴛɪɴɢ ᴘʟᴀɴ\n"
        "<b>🎁 ɢʀᴀɴᴛ</b> — ᴀᴘᴘʟʏ ᴀ ᴘʟᴀɴ ᴛᴏ ᴀ sᴘᴇᴄɪғɪᴄ ᴜsᴇʀ\n"
        "<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ</b> — ʟɪɴᴋ ᴀ ᴛᴇʟᴇɢʀᴀᴍ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀ ᴘʟᴀɴ;\n"
        "    ʙᴜʏᴇʀs ᴀʀᴇ ᴀᴜᴛᴏ-ᴀᴅᴅᴇᴅ ᴏɴ ᴘᴀʏᴍᴇɴᴛ, ʀᴇᴍᴏᴠᴇᴅ ᴏɴ ᴇxᴘɪʀʏ\n\n"
        "<i>ᴛɪᴘ: ᴜsᴇʀs ᴄᴀɴ ʀᴜɴ /plans ᴛᴏ sᴇᴇ ʏᴏᴜʀ ᴀᴠᴀɪʟᴀʙʟᴇ ᴏғғᴇʀs.</i>"
    )


# ═══════════════════════════════════════════════════════════════
#  /psetting  COMMAND
# ═══════════════════════════════════════════════════════════════

@Bot.on_message(filters.command("psetting") & filters.private & admin)
async def psetting_cmd(client: Client, message: Message):
    _pending.pop(message.from_user.id, None)
    await message.reply_photo(
        photo=PSETTING_PIC,
        caption=_main_caption(),
        reply_markup=_main_markup(),
    )


# ═══════════════════════════════════════════════════════════════
#  /plans  COMMAND  (visible to ALL users)
# ═══════════════════════════════════════════════════════════════

@Bot.on_message(filters.command("plans") & filters.private)
async def plans_cmd(client: Client, message: Message):
    plans = await list_plans()
    text = (
        "<b>🥇 ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs</b>\n"
        "─────────────────────\n\n"
        + format_plans_block(plans, with_id=False)
    )
    if plans:
        text += (
            "\n\n<i>ᴄᴏɴᴛᴀᴄᴛ ᴛʜᴇ ᴏᴡɴᴇʀ ᴛᴏ ᴘᴜʀᴄʜᴀsᴇ ᴀ ᴘʟᴀɴ.</i>"
        )
    await message.reply_text(text, disable_web_page_preview=True)


# ═══════════════════════════════════════════════════════════════
#  CALLBACK ROUTER  (admin only)
# ═══════════════════════════════════════════════════════════════

@Bot.on_callback_query(filters.regex(r"^pst_"))
async def psetting_cb(client: Bot, query: CallbackQuery):
    # admin gate
    from helper_func import check_admin
    if not await check_admin(None, client, query):
        return await query.answer("Admins only.", show_alert=True)

    await query.answer()
    data = query.data
    uid  = query.from_user.id

    # ── BACK / CLOSE ─────────────────────────────────────────
    if data == "pst_back":
        _pending.pop(uid, None)
        return await _edit(query, _main_caption(), _main_markup())

    if data == "pst_close":
        _pending.pop(uid, None)
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ── LIST PLANS ───────────────────────────────────────────
    if data == "pst_list":
        plans = await list_plans()
        body = format_plans_block(plans, with_id=True)
        cap  = (
            "<b>📋 All Premium Plans</b>\n"
            "─────────────────────\n\n"
            + body
        )
        return await _edit(query, cap, _back_main())

    # ── ADD PLAN — START ─────────────────────────────────────
    if data == "pst_add":
        _pending[uid] = {
            "step": "name",
            "draft": {"tier": "gold"},
            "msg_id":  query.message.id,
            "chat_id": query.message.chat.id,
        }
        return await _edit(
            query,
            "<b>➕ ᴀᴅᴅ ɴᴇᴡ ᴘʟᴀɴ — sᴛᴇᴘ 1 / 3</b>\n\n"
            "sᴇɴᴅ ᴛʜᴇ <b>ᴘʟᴀɴ ɴᴀᴍᴇ</b> ᴀs ᴀ ᴍᴇssᴀɢᴇ.\n"
            "<i>ᴇxᴀᴍᴘʟᴇ:  Gold 1 Month</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
        )

    # ── ADD PLAN — UNIT PICK ─────────────────────────────────
    if data.startswith("pst_unit_"):
        st = _pending.get(uid)
        if not st or st.get("step") != "unit":
            return
        unit = data.split("_", 2)[2]
        if unit not in ALLOWED_UNITS:
            return
        st["draft"]["duration_unit"] = unit
        st["step"] = "price"
        return await _edit(
            query,
            f"<b>➕ ᴀᴅᴅ ɴᴇᴡ ᴘʟᴀɴ — sᴛᴇᴘ 3 / 3</b>\n\n"
            f"ᴘʟᴀɴ: <b>{st['draft']['name']}</b>\n"
            f"ᴅᴜʀᴀᴛɪᴏɴ: <b>{st['draft']['duration_value']} "
            f"{ALLOWED_UNITS[unit]}</b>\n\n"
            f"sᴇɴᴅ ᴛʜᴇ <b>ᴘʀɪᴄᴇ</b> ᴀs ᴀ ᴍᴇssᴀɢᴇ.\n"
            f"<i>ᴇxᴀᴍᴘʟᴇ:  ₹49   |   $5   |   Free</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
        )

    # ── DELETE MENU ──────────────────────────────────────────
    if data == "pst_del_menu":
        plans = await list_plans()
        if not plans:
            return await _edit(
                query,
                "<b>🗑 ᴅᴇʟᴇᴛᴇ ᴘʟᴀɴ</b>\n\nɴᴏ ᴘʟᴀɴs ᴛᴏ ᴅᴇʟᴇᴛᴇ.",
                _back_main(),
            )
        rows = []
        for p in plans:
            label = f"❌ {p.get('name','—')}"
            rows.append([InlineKeyboardButton(label, callback_data=f"pst_del_{p['_id']}")])
        rows.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="pst_back")])
        return await _edit(
            query,
            "<b>🗑 ᴅᴇʟᴇᴛᴇ ᴘʟᴀɴ</b>\n\nᴛᴀᴘ ᴀ ᴘʟᴀɴ ᴛᴏ ᴅᴇʟᴇᴛᴇ ɪᴛ.",
            InlineKeyboardMarkup(rows),
        )

    if data.startswith("pst_del_"):
        plan_id = data.split("_", 2)[2]
        ok = await delete_plan(plan_id)
        msg = "✅ ᴘʟᴀɴ ᴅᴇʟᴇᴛᴇᴅ." if ok else "❌ ᴘʟᴀɴ ɴᴏᴛ ғᴏᴜɴᴅ."
        plans = await list_plans()
        rows = []
        for p in plans:
            label = f"❌ {p.get('name','—')}"
            rows.append([InlineKeyboardButton(label, callback_data=f"pst_del_{p['_id']}")])
        rows.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="pst_back")])
        return await _edit(
            query,
            f"<b>🗑 ᴅᴇʟᴇᴛᴇ ᴘʟᴀɴ</b>\n\n{msg}",
            InlineKeyboardMarkup(rows) if plans else _back_main(),
        )

    # ── GRANT MENU ───────────────────────────────────────────
    if data == "pst_grant_menu":
        plans = await list_plans()
        if not plans:
            return await _edit(
                query,
                "<b>🎁 ɢʀᴀɴᴛ ᴘʟᴀɴ</b>\n\nɴᴏ ᴘʟᴀɴs ᴄᴏɴғɪɢᴜʀᴇᴅ. ᴀᴅᴅ ᴏɴᴇ ғɪʀsᴛ.",
                _back_main(),
            )
        rows = []
        for p in plans:
            label = f"🎁 {p.get('name','—')}"
            rows.append([InlineKeyboardButton(label, callback_data=f"pst_grant_{p['_id']}")])
        rows.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="pst_back")])
        return await _edit(
            query,
            "<b>🎁 ɢʀᴀɴᴛ ᴘʟᴀɴ</b>\n\nᴘɪᴄᴋ ᴀ ᴘʟᴀɴ ᴛᴏ ɢʀᴀɴᴛ ᴛᴏ ᴀ ᴜsᴇʀ.",
            InlineKeyboardMarkup(rows),
        )

    if data.startswith("pst_grant_"):
        plan_id = data.split("_", 2)[2]
        plan = await get_plan(plan_id)
        if not plan:
            return await _edit(query, "<b>❌ ᴘʟᴀɴ ɴᴏᴛ ғᴏᴜɴᴅ.</b>", _back_main())
        _pending[uid] = {
            "step":   "grant_uid",
            "draft":  {"plan_id": plan_id},
            "msg_id":  query.message.id,
            "chat_id": query.message.chat.id,
        }
        return await _edit(
            query,
            "<b>🎁 ɢʀᴀɴᴛ ᴘʟᴀɴ</b>\n\n"
            f"ᴘʟᴀɴ: {format_plan_line(plan)}\n\n"
            "sᴇɴᴅ ᴛʜᴇ <b>ᴜsᴇʀ_ɪᴅ</b> ᴛᴏ ɢʀᴀɴᴛ ᴛʜɪs ᴘʟᴀɴ ᴛᴏ.",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
        )

    # ── GIFT CHANNEL — pick a plan ───────────────────────────
    if data == "pst_gift_menu":
        plans = await list_plans()
        if not plans:
            return await _edit(
                query,
                "<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ</b>\n\nɴᴏ ᴘʟᴀɴs ᴄᴏɴғɪɢᴜʀᴇᴅ. ᴀᴅᴅ ᴀ ᴘʟᴀɴ ғɪʀsᴛ.",
                _back_main(),
            )
        rows = []
        for p in plans:
            label = f"🎀 {p.get('name','—')}"
            if p.get("gift_channel_id"):
                label += "  ✓"
            rows.append([InlineKeyboardButton(label, callback_data=f"pst_gift_{p['_id']}")])
        rows.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="pst_back")])
        return await _edit(
            query,
            "<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ</b>\n\n"
            "ᴘɪᴄᴋ ᴀ ᴘʟᴀɴ ᴛᴏ ᴀᴛᴛᴀᴄʜ ᴀ ɢɪғᴛ ᴄʜᴀɴɴᴇʟ ᴛᴏ.\n"
            "ᴘʟᴀɴs ᴀʟʀᴇᴀᴅʏ ʟɪɴᴋᴇᴅ ᴀʀᴇ ᴍᴀʀᴋᴇᴅ ᴡɪᴛʜ <b>✓</b>.",
            InlineKeyboardMarkup(rows),
        )

    # ── GIFT CHANNEL — clear an existing link ────────────────
    if data.startswith("pst_giftclr_"):
        plan_id = data.split("_", 2)[2]
        await clear_gift_channel(plan_id)
        plan = await get_plan(plan_id)
        return await _edit(
            query,
            "<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ</b>\n\n"
            "✅ ɢɪғᴛ ᴄʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴛʜɪs ᴘʟᴀɴ.\n\n"
            f"ᴘʟᴀɴ: {format_plan_line(plan) if plan else '—'}",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ ᴛᴏ ɢɪғᴛ ᴍᴇɴᴜ", callback_data="pst_gift_menu")],
            ]),
        )

    # ── GIFT CHANNEL — selected a specific plan ──────────────
    if data.startswith("pst_gift_"):
        plan_id = data.split("_", 2)[2]
        plan = await get_plan(plan_id)
        if not plan:
            return await _edit(query, "<b>❌ ᴘʟᴀɴ ɴᴏᴛ ғᴏᴜɴᴅ.</b>", _back_main())

        existing = ""
        if plan.get("gift_channel_id"):
            existing = (
                f"\n\n<b>ᴄᴜʀʀᴇɴᴛʟʏ ʟɪɴᴋᴇᴅ:</b> "
                f"{plan.get('gift_channel_title','—')} "
                f"(<code>{plan['gift_channel_id']}</code>)"
            )

        _pending[uid] = {
            "step":    "gift_channel",
            "draft":   {"plan_id": plan_id},
            "msg_id":   query.message.id,
            "chat_id":  query.message.chat.id,
        }

        rows = [[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]
        if plan.get("gift_channel_id"):
            rows.insert(0, [InlineKeyboardButton(
                "🗑 ʀᴇᴍᴏᴠᴇ ᴇxɪsᴛɪɴɢ ʟɪɴᴋ",
                callback_data=f"pst_giftclr_{plan_id}",
            )])

        return await _edit(
            query,
            "<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ — sᴇᴛᴜᴘ</b>\n\n"
            f"ᴘʟᴀɴ: {format_plan_line(plan)}{existing}\n\n"
            "<b>sᴛᴇᴘs:</b>\n"
            "1. ᴀᴅᴅ ᴛʜɪs ʙᴏᴛ ᴀs <b>ᴀᴅᴍɪɴ</b> ɪɴ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ.\n"
            "2. ɢɪᴠᴇ ɪᴛ ᴛʜᴇ <b>ɪɴᴠɪᴛᴇ ᴜsᴇʀs ᴠɪᴀ ʟɪɴᴋ</b> ᴘᴇʀᴍɪssɪᴏɴ "
            "(ᴀɴᴅ <b>ʙᴀɴ ᴜsᴇʀs</b> sᴏ ɪᴛ ᴄᴀɴ ʀᴇᴍᴏᴠᴇ ᴏɴ ᴇxᴘɪʀʏ).\n"
            "3. sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ʙᴇʟᴏᴡ — ɪᴛ ᴍᴜsᴛ sᴛᴀʀᴛ ᴡɪᴛʜ "
            "<code>-100</code>.\n\n"
            "<i>ᴇxᴀᴍᴘʟᴇ: <code>-1001234567890</code></i>",
            InlineKeyboardMarkup(rows),
        )


# ═══════════════════════════════════════════════════════════════
#  TEXT INPUT HANDLER  (multi-step add wizard + grant flow)
# ═══════════════════════════════════════════════════════════════

@Bot.on_message(
    filters.private & filters.text &
    filters.create(lambda _, __, m: m.from_user and m.from_user.id in _pending),
    group=-2,
)
async def psetting_input(client: Bot, message: Message):
    uid   = message.from_user.id
    state = _pending.get(uid)
    if not state:
        return

    raw     = (message.text or "").strip()
    chat_id = state["chat_id"]
    msg_id  = state["msg_id"]
    step    = state["step"]
    draft   = state["draft"]

    try:
        await message.delete()
    except Exception:
        pass

    # ── STEP: NAME → VALUE ───────────────────────────────────
    if step == "name":
        if not raw:
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ ɴᴀᴍᴇ ᴄᴀɴɴᴏᴛ ʙᴇ ᴇᴍᴘᴛʏ. ᴛʀʏ ᴀɢᴀɪɴ.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
            )
            raise StopPropagation
        if len(raw) > 64:
            raw = raw[:64]
        draft["name"] = raw
        state["step"] = "value"
        await _patch(
            client, chat_id, msg_id,
            f"<b>➕ ᴀᴅᴅ ɴᴇᴡ ᴘʟᴀɴ — sᴛᴇᴘ 2 / 3</b>\n\n"
            f"ᴘʟᴀɴ: <b>{raw}</b>\n\n"
            f"sᴇɴᴅ ᴛʜᴇ <b>ᴅᴜʀᴀᴛɪᴏɴ ᴠᴀʟᴜᴇ</b> ᴀs ᴀ ɴᴜᴍʙᴇʀ.\n"
            f"<i>ᴇxᴀᴍᴘʟᴇ:  1   |   30   |   12</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
        )
        raise StopPropagation

    # ── STEP: VALUE ──────────────────────────────────────────
    if step == "value":
        try:
            value = int(raw)
            if value <= 0:
                raise ValueError
        except ValueError:
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ sᴇɴᴅ ᴀ ᴘᴏsɪᴛɪᴠᴇ ᴡʜᴏʟᴇ ɴᴜᴍʙᴇʀ.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
            )
            raise StopPropagation
        draft["duration_value"] = value
        state["step"] = "unit"
        await _patch(
            client, chat_id, msg_id,
            f"<b>➕ ᴀᴅᴅ ɴᴇᴡ ᴘʟᴀɴ — sᴛᴇᴘ 2 / 3</b>\n\n"
            f"ᴘʟᴀɴ: <b>{draft['name']}</b>\n"
            f"ᴅᴜʀᴀᴛɪᴏɴ ᴠᴀʟᴜᴇ: <b>{value}</b>\n\n"
            f"ᴘɪᴄᴋ ᴀ <b>ᴅᴜʀᴀᴛɪᴏɴ ᴜɴɪᴛ</b>:",
            _unit_markup(),
        )
        raise StopPropagation

    # ── STEP: PRICE  →  SAVE ─────────────────────────────────
    if step == "price":
        if not raw:
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ ᴘʀɪᴄᴇ ᴄᴀɴɴᴏᴛ ʙᴇ ᴇᴍᴘᴛʏ.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
            )
            raise StopPropagation
        if len(raw) > 32:
            raw = raw[:32]
        draft["price"] = raw
        try:
            new_id = await add_plan(
                name           = draft["name"],
                tier           = draft.get("tier", "gold"),
                duration_value = draft["duration_value"],
                duration_unit  = draft["duration_unit"],
                price          = draft["price"],
            )
        except Exception as e:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                f"<b>❌ ᴄᴏᴜʟᴅ ɴᴏᴛ sᴀᴠᴇ ᴘʟᴀɴ:</b>\n<code>{e}</code>",
                _back_main(),
            )
            raise StopPropagation

        _pending.pop(uid, None)
        plan = await get_plan(new_id)
        await _patch(
            client, chat_id, msg_id,
            "<b>✅ ᴘʟᴀɴ sᴀᴠᴇᴅ!</b>\n\n" + format_plan_line(plan, with_id=True),
            InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ᴀᴅᴅ ᴀɴᴏᴛʜᴇʀ", callback_data="pst_add"),
                 InlineKeyboardButton("📋 ʟɪsᴛ ᴘʟᴀɴs", callback_data="pst_list")],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="pst_back")],
            ]),
        )
        raise StopPropagation

    # ── STEP: GIFT CHANNEL — receive channel id, verify bot is admin ─
    if step == "gift_channel":
        plan_id = draft.get("plan_id")
        plan = await get_plan(plan_id)
        if not plan:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ Plan no longer exists.</b>",
                _back_main(),
            )
            raise StopPropagation

        # parse channel id
        try:
            ch_id = int(raw)
        except ValueError:
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ ɪɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ.</b>\n\n"
                "sᴇɴᴅ ᴀ ɴᴜᴍᴇʀɪᴄ ᴄʜᴀɴɴᴇʟ ɪᴅ sᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ <code>-100</code>.",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
            )
            raise StopPropagation

        if not str(ch_id).startswith("-100"):
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴍᴜsᴛ sᴛᴀʀᴛ ᴡɪᴛʜ</b> <code>-100</code>.\n\n"
                "ғᴏʀᴡᴀʀᴅ ᴀ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ <b>@username_to_id_bot</b> "
                "ᴏʀ sɪᴍɪʟᴀʀ ᴛᴏ ғᴇᴛᴄʜ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ɪᴅ.",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
            )
            raise StopPropagation

        # show "verifying..." state
        await _patch(
            client, chat_id, msg_id,
            f"<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ — ᴠᴇʀɪғʏɪɴɢ…</b>\n\n"
            f"ᴘʟᴀɴ: <b>{plan.get('name','—')}</b>\n"
            f"ᴄʜᴀɴɴᴇʟ: <code>{ch_id}</code>\n\n"
            "ᴄʜᴇᴄᴋɪɴɢ ʙᴏᴛ ᴘᴇʀᴍɪssɪᴏɴs, ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ…",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
        )

        # actually verify
        try:
            chat = await client.get_chat(ch_id)
            channel_title = chat.title or str(ch_id)
            me = await client.get_me()
            member = await client.get_chat_member(ch_id, me.id)
            status = str(getattr(member, "status", "")).lower()
            if "administrator" not in status and "owner" not in status and "creator" not in status:
                raise PermissionError("not_admin")
            privs = getattr(member, "privileges", None)
            if not privs or not getattr(privs, "can_invite_users", False):
                raise PermissionError("no_invite")
        except PermissionError as pe:
            _pending.pop(uid, None)
            reason = (
                "ʙᴏᴛ ɪs ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ."
                if str(pe) == "not_admin"
                else "ʙᴏᴛ ɪs ᴀᴅᴍɪɴ ʙᴜᴛ ʟᴀᴄᴋs ᴛʜᴇ <b>ɪɴᴠɪᴛᴇ ᴜsᴇʀs ᴠɪᴀ ʟɪɴᴋ</b> ᴘᴇʀᴍɪssɪᴏɴ."
            )
            await _patch(
                client, chat_id, msg_id,
                "<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ — ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ғᴀɪʟᴇᴅ</b>\n\n"
                f"❌ {reason}\n\n"
                "ғɪx ɪᴛ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ғʀᴏᴍ ᴛʜᴇ ɢɪғᴛ ᴍᴇɴᴜ.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 ᴛʀʏ ᴀɢᴀɪɴ", callback_data=f"pst_gift_{plan_id}")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ",     callback_data="pst_back")],
                ]),
            )
            raise StopPropagation
        except Exception as e:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                "<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ — ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ғᴀɪʟᴇᴅ</b>\n\n"
                f"❌ ᴄᴏᴜʟᴅ ɴᴏᴛ ᴀᴄᴄᴇss ᴄʜᴀɴɴᴇʟ.\n<code>{str(e)[:200]}</code>\n\n"
                "ᴍᴀᴋᴇ sᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪs ᴀ ᴍᴇᴍʙᴇʀ ᴀɴᴅ ʏᴏᴜ sᴇɴᴛ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ɪᴅ.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 ᴛʀʏ ᴀɢᴀɪɴ", callback_data=f"pst_gift_{plan_id}")],
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ",     callback_data="pst_back")],
                ]),
            )
            raise StopPropagation

        # all good — save to plan
        try:
            await set_gift_channel(plan_id, ch_id, channel_title)
        except Exception as e:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                f"<b>❌ ᴄᴏᴜʟᴅ ɴᴏᴛ sᴀᴠᴇ ɢɪғᴛ ᴄʜᴀɴɴᴇʟ:</b>\n<code>{e}</code>",
                _back_main(),
            )
            raise StopPropagation

        _pending.pop(uid, None)
        await _patch(
            client, chat_id, msg_id,
            "<b>🎀 ɢɪғᴛ ᴄʜᴀɴɴᴇʟ — ʟɪɴᴋᴇᴅ!</b>\n\n"
            f"✅ ᴘʟᴀɴ: <b>{plan.get('name','—')}</b>\n"
            f"✅ ᴄʜᴀɴɴᴇʟ: <b>{channel_title}</b>\n"
            f"   <code>{ch_id}</code>\n\n"
            "ʙᴜʏᴇʀs ᴏғ ᴛʜɪs ᴘʟᴀɴ ᴡɪʟʟ ɴᴏᴡ ʀᴇᴄᴇɪᴠᴇ ᴀɴ ɪɴᴠɪᴛᴇ ʟɪɴᴋ "
            "ᴀɴᴅ ʙᴇ ᴀᴜᴛᴏ-ᴀᴘᴘʀᴏᴠᴇᴅ ɪɴᴛᴏ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴀғᴛᴇʀ ᴛʜᴇʏ ᴄʟɪᴄᴋ "
            "<b>ᴅᴏɴᴇ</b>. ᴛʜᴇʏ ᴡɪʟʟ ʙᴇ ʀᴇᴍᴏᴠᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴡʜᴇɴ "
            "ᴛʜᴇɪʀ ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀᴇs.",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🎀 ʟɪɴᴋ ᴀɴᴏᴛʜᴇʀ", callback_data="pst_gift_menu"),
                 InlineKeyboardButton("🔙 ʙᴀᴄᴋ",         callback_data="pst_back")],
            ]),
        )
        raise StopPropagation

    # ── STEP: GRANT — collect user_id, then apply ────────────
    if step == "grant_uid":
        try:
            target_id = int(raw)
        except ValueError:
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴜsᴇʀ_ɪᴅ.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="pst_back")]]),
            )
            raise StopPropagation

        plan = await get_plan(draft.get("plan_id"))
        if not plan:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ ᴘʟᴀɴ ɴᴏ ʟᴏɴɢᴇʀ ᴇxɪsᴛs.</b>",
                _back_main(),
            )
            raise StopPropagation

        try:
            value, unit = to_addpremium_unit(
                int(plan["duration_value"]),
                plan["duration_unit"],
            )
            expiration_time = await add_premium(
                target_id, value, unit, "gold",
            )
        except Exception as e:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                f"<b>❌ ᴄᴏᴜʟᴅ ɴᴏᴛ ɢʀᴀɴᴛ ᴘʟᴀɴ:</b>\n<code>{e}</code>",
                _back_main(),
            )
            raise StopPropagation

        _pending.pop(uid, None)

        # ── Build full manual receipt (no order_id, no txn_id) ──
        active_date = datetime.now(timezone("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p")
        unit_label  = _UNIT_LABELS_SMALLCAPS.get(plan.get("duration_unit", ""), plan.get("duration_unit", ""))
        plan_label  = f"{plan.get('name', '—')} · {plan.get('duration_value', '?')} {unit_label}"

        # Try to fetch the target user's name
        try:
            target_user = await client.get_users(target_id)
            full_name = (target_user.first_name or "") + (
                f" {target_user.last_name}" if target_user.last_name else ""
            )
            full_name = full_name.strip() or str(target_id)
            if getattr(target_user, "username", None):
                full_name = f"{full_name} (@{target_user.username})"
        except Exception:
            full_name = str(target_id)

        receipt = (
            "<b>🧾 ᴘʀᴇᴍɪᴜᴍ ʀᴇᴄᴇɪᴘᴛ — ᴍᴀɴᴜᴀʟʟʏ ɢʀᴀɴᴛᴇᴅ</b>\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
            f"👤 <b>ᴜsᴇʀ ɴᴀᴍᴇ:</b> {full_name}\n"
            f"🆔 <b>ᴜsᴇʀ ɪᴅ:</b> <code>{target_id}</code>\n"
            f"🥇 <b>ᴘʟᴀɴ ᴛʏᴘᴇ:</b> {plan_label}\n"
            f"📅 <b>ᴀᴄᴛɪᴠᴇ ᴅᴀᴛᴇ:</b> <code>{active_date}</code>\n"
            f"⏳ <b>ᴇxᴘɪʀᴇ ᴅᴀᴛᴇ:</b> <code>{expiration_time}</code>\n"
            f"🎁 <b>ɢʀᴀɴᴛᴇᴅ ʙʏ:</b> ᴀᴅᴍɪɴ\n\n"
            "<b>ᴘᴇʀᴋs ᴜɴʟᴏᴄᴋᴇᴅ:</b>\n"
            "  ✅ ғʀᴇᴇ ʟɪɴᴋ ʙʏᴘᴀss\n"
            "  ✅ ᴘʀᴏᴛᴇᴄᴛ-ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss\n"
            "  ✅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ʟɪɴᴋs\n\n"
            "<code>━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            "<i>✨ ᴇɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss! ᴋᴇᴇᴘ ᴛʜɪs ʀᴇᴄᴇɪᴘᴛ ғᴏʀ ʀᴇғᴇʀᴇɴᴄᴇ.</i>"
        )

        # Send the receipt to the target user (best-effort)
        try:
            await client.send_message(target_id, receipt, disable_web_page_preview=True)
        except Exception:
            pass

        # Confirm to the admin in the wizard window
        await _patch(
            client, chat_id, msg_id,
            "<b>✅ ᴘʟᴀɴ ɢʀᴀɴᴛᴇᴅ!</b>\n\n"
            f"ᴜsᴇʀ: <code>{target_id}</code>\n"
            f"ᴘʟᴀɴ: <b>{plan.get('name','—')}</b>\n"
            f"ᴇxᴘɪʀᴇs ᴏɴ: <b>{expiration_time}</b>\n\n"
            "<i>ʀᴇᴄᴇɪᴘᴛ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ.</i>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 ɢʀᴀɴᴛ ᴀɴᴏᴛʜᴇʀ", callback_data="pst_grant_menu"),
                 InlineKeyboardButton("🔙 ʙᴀᴄᴋ",          callback_data="pst_back")],
            ]),
        )
        raise StopPropagation
