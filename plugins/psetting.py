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

from bot import Bot
from helper_func import admin
from database.db_plans import (
    add_plan, list_plans, delete_plan, get_plan,
    format_plan_line, format_plans_block,
    ALLOWED_UNITS, ALLOWED_TIERS, to_addpremium_unit,
)
from database.db_premium import add_premium

PSETTING_PIC = "https://graph.org/file/d18515f99d522b3ee4e6f-876aedcb4f5dde2d4e.jpg"

# user_id -> { step, draft, msg_id, chat_id }
_pending: dict = {}


# ═══════════════════════════════════════════════════════════════
#  MARKUP HELPERS
# ═══════════════════════════════════════════════════════════════

def _main_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 List Plans",  callback_data="pst_list"),
            InlineKeyboardButton("➕ Add Plan",    callback_data="pst_add"),
        ],
        [
            InlineKeyboardButton("🗑 Delete Plan", callback_data="pst_del_menu"),
            InlineKeyboardButton("🎁 Grant",       callback_data="pst_grant_menu"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="pst_close")],
    ])


def _back_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="pst_back")]])


def _tier_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🥇 Gold",     callback_data="pst_tier_gold"),
            InlineKeyboardButton("💎 Platinum", callback_data="pst_tier_platinum"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="pst_back")],
    ])


def _unit_markup():
    rows = []
    units = list(ALLOWED_UNITS.items())
    for i in range(0, len(units), 3):
        rows.append([
            InlineKeyboardButton(label, callback_data=f"pst_unit_{code}")
            for code, label in units[i:i + 3]
        ])
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data="pst_back")])
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
        "<b>💎 Premium Plan Manager</b>\n"
        "─────────────────────\n\n"
        "<b>📋 List Plans</b> — see all configured plans\n"
        "<b>➕ Add Plan</b> — create a new plan (name, tier, duration, price)\n"
        "<b>🗑 Delete Plan</b> — remove an existing plan\n"
        "<b>🎁 Grant</b> — apply a plan to a specific user\n\n"
        "<i>Tip: users can run /plans to see your available offers.</i>"
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
        "<b>💎 Available Premium Plans</b>\n"
        "─────────────────────\n\n"
        + format_plans_block(plans, with_id=False)
    )
    if plans:
        text += (
            "\n\n<i>Contact the owner to purchase a plan.</i>"
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
            "draft": {},
            "msg_id":  query.message.id,
            "chat_id": query.message.chat.id,
        }
        return await _edit(
            query,
            "<b>➕ Add New Plan — Step 1 / 4</b>\n\n"
            "Send the <b>plan name</b> as a message.\n"
            "<i>Example:  Gold 1 Month</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pst_back")]]),
        )

    # ── ADD PLAN — TIER PICK ─────────────────────────────────
    if data.startswith("pst_tier_"):
        st = _pending.get(uid)
        if not st or st.get("step") != "tier":
            return
        tier = data.split("_", 2)[2]
        if tier not in ALLOWED_TIERS:
            return
        st["draft"]["tier"] = tier
        st["step"] = "value"
        return await _edit(
            query,
            f"<b>➕ Add New Plan — Step 3 / 4</b>\n\n"
            f"Plan: <b>{st['draft']['name']}</b>\n"
            f"Tier: <b>{tier.capitalize()}</b>\n\n"
            f"Send the <b>duration value</b> as a number.\n"
            f"<i>Example:  1   |   30   |   12</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pst_back")]]),
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
            f"<b>➕ Add New Plan — Step 4 / 4</b>\n\n"
            f"Plan: <b>{st['draft']['name']}</b>\n"
            f"Tier: <b>{st['draft']['tier'].capitalize()}</b>\n"
            f"Duration: <b>{st['draft']['duration_value']} "
            f"{ALLOWED_UNITS[unit]}</b>\n\n"
            f"Send the <b>price</b> as a message.\n"
            f"<i>Example:  ₹49   |   $5   |   Free</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pst_back")]]),
        )

    # ── DELETE MENU ──────────────────────────────────────────
    if data == "pst_del_menu":
        plans = await list_plans()
        if not plans:
            return await _edit(
                query,
                "<b>🗑 Delete Plan</b>\n\nNo plans to delete.",
                _back_main(),
            )
        rows = []
        for p in plans:
            label = f"❌ {p.get('name','—')} ({p.get('tier','gold').capitalize()})"
            rows.append([InlineKeyboardButton(label, callback_data=f"pst_del_{p['_id']}")])
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="pst_back")])
        return await _edit(
            query,
            "<b>🗑 Delete Plan</b>\n\nTap a plan to delete it.",
            InlineKeyboardMarkup(rows),
        )

    if data.startswith("pst_del_"):
        plan_id = data.split("_", 2)[2]
        ok = await delete_plan(plan_id)
        msg = "✅ Plan deleted." if ok else "❌ Plan not found."
        plans = await list_plans()
        rows = []
        for p in plans:
            label = f"❌ {p.get('name','—')} ({p.get('tier','gold').capitalize()})"
            rows.append([InlineKeyboardButton(label, callback_data=f"pst_del_{p['_id']}")])
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="pst_back")])
        return await _edit(
            query,
            f"<b>🗑 Delete Plan</b>\n\n{msg}",
            InlineKeyboardMarkup(rows) if plans else _back_main(),
        )

    # ── GRANT MENU ───────────────────────────────────────────
    if data == "pst_grant_menu":
        plans = await list_plans()
        if not plans:
            return await _edit(
                query,
                "<b>🎁 Grant Plan</b>\n\nNo plans configured. Add one first.",
                _back_main(),
            )
        rows = []
        for p in plans:
            label = f"🎁 {p.get('name','—')} ({p.get('tier','gold').capitalize()})"
            rows.append([InlineKeyboardButton(label, callback_data=f"pst_grant_{p['_id']}")])
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="pst_back")])
        return await _edit(
            query,
            "<b>🎁 Grant Plan</b>\n\nPick a plan to grant to a user.",
            InlineKeyboardMarkup(rows),
        )

    if data.startswith("pst_grant_"):
        plan_id = data.split("_", 2)[2]
        plan = await get_plan(plan_id)
        if not plan:
            return await _edit(query, "<b>❌ Plan not found.</b>", _back_main())
        _pending[uid] = {
            "step":   "grant_uid",
            "draft":  {"plan_id": plan_id},
            "msg_id":  query.message.id,
            "chat_id": query.message.chat.id,
        }
        return await _edit(
            query,
            "<b>🎁 Grant Plan</b>\n\n"
            f"Plan: {format_plan_line(plan)}\n\n"
            "Send the <b>user_id</b> to grant this plan to.",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pst_back")]]),
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

    # ── STEP: NAME ───────────────────────────────────────────
    if step == "name":
        if not raw:
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ Name cannot be empty. Try again.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pst_back")]]),
            )
            raise StopPropagation
        if len(raw) > 64:
            raw = raw[:64]
        draft["name"] = raw
        state["step"] = "tier"
        await _patch(
            client, chat_id, msg_id,
            f"<b>➕ Add New Plan — Step 2 / 4</b>\n\n"
            f"Plan: <b>{raw}</b>\n\n"
            f"Pick a <b>tier</b>:",
            _tier_markup(),
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
                "<b>❌ Send a positive whole number.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pst_back")]]),
            )
            raise StopPropagation
        draft["duration_value"] = value
        state["step"] = "unit"
        await _patch(
            client, chat_id, msg_id,
            f"<b>➕ Add New Plan — Step 3 / 4</b>\n\n"
            f"Plan: <b>{draft['name']}</b>\n"
            f"Tier: <b>{draft['tier'].capitalize()}</b>\n"
            f"Duration value: <b>{value}</b>\n\n"
            f"Pick a <b>duration unit</b>:",
            _unit_markup(),
        )
        raise StopPropagation

    # ── STEP: PRICE  →  SAVE ─────────────────────────────────
    if step == "price":
        if not raw:
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ Price cannot be empty.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pst_back")]]),
            )
            raise StopPropagation
        if len(raw) > 32:
            raw = raw[:32]
        draft["price"] = raw
        try:
            new_id = await add_plan(
                name           = draft["name"],
                tier           = draft["tier"],
                duration_value = draft["duration_value"],
                duration_unit  = draft["duration_unit"],
                price          = draft["price"],
            )
        except Exception as e:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                f"<b>❌ Could not save plan:</b>\n<code>{e}</code>",
                _back_main(),
            )
            raise StopPropagation

        _pending.pop(uid, None)
        plan = await get_plan(new_id)
        await _patch(
            client, chat_id, msg_id,
            "<b>✅ Plan saved!</b>\n\n" + format_plan_line(plan, with_id=True),
            InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Another", callback_data="pst_add"),
                 InlineKeyboardButton("📋 List Plans", callback_data="pst_list")],
                [InlineKeyboardButton("🔙 Back", callback_data="pst_back")],
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
                "<b>❌ Send a valid numeric user_id.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="pst_back")]]),
            )
            raise StopPropagation

        plan = await get_plan(draft.get("plan_id"))
        if not plan:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                "<b>❌ Plan no longer exists.</b>",
                _back_main(),
            )
            raise StopPropagation

        try:
            value, unit = to_addpremium_unit(
                int(plan["duration_value"]),
                plan["duration_unit"],
            )
            expiration_time = await add_premium(
                target_id, value, unit, plan.get("tier", "gold"),
            )
        except Exception as e:
            _pending.pop(uid, None)
            await _patch(
                client, chat_id, msg_id,
                f"<b>❌ Could not grant plan:</b>\n<code>{e}</code>",
                _back_main(),
            )
            raise StopPropagation

        _pending.pop(uid, None)
        tier = plan.get("tier", "gold")
        emoji = "🥇" if tier == "gold" else "💎"
        # try to notify the user
        try:
            await client.send_message(
                target_id,
                f"{emoji} <b>{tier.capitalize()} Premium Activated!</b>\n\n"
                f"Plan: <b>{plan.get('name','—')}</b>\n"
                f"Expires on: <b>{expiration_time}</b>",
            )
        except Exception:
            pass

        await _patch(
            client, chat_id, msg_id,
            "<b>✅ Plan granted!</b>\n\n"
            f"User: <code>{target_id}</code>\n"
            f"Plan: <b>{plan.get('name','—')}</b> "
            f"({tier.capitalize()})\n"
            f"Expires on: <b>{expiration_time}</b>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Grant Another", callback_data="pst_grant_menu"),
                 InlineKeyboardButton("🔙 Back",          callback_data="pst_back")],
            ]),
        )
        raise StopPropagation
