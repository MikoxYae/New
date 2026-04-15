import asyncio
import psutil
from pyrogram import filters
from pyrogram.types import (
    CallbackQuery, Message,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import StopPropagation
from bot import Bot
from config import OWNER_ID
from database.database import db


# ═══════════════════════════════════════════════════════════════
#  PENDING STATE  (for text-input flows)
# ═══════════════════════════════════════════════════════════════

_pending: dict = {}   # user_id -> { action, msg_id, chat_id }


# ═══════════════════════════════════════════════════════════════
#  MARKUP HELPERS
# ═══════════════════════════════════════════════════════════════

def _main_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Admin",      callback_data="stg_admin"),
            InlineKeyboardButton("🚫 Ban Users",  callback_data="stg_ban")
        ],
        [
            InlineKeyboardButton("👥 Users",      callback_data="stg_users"),
            InlineKeyboardButton("📊 Stats",      callback_data="stg_stats")
        ],
        [
            InlineKeyboardButton("📢 Force Sub",  callback_data="stg_fsub"),
            InlineKeyboardButton("🔄 Request Mode", callback_data="stg_reqmode")
        ]
    ])


def _admin_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add",    callback_data="stg_admin_add"),
            InlineKeyboardButton("➖ Remove", callback_data="stg_admin_remove"),
            InlineKeyboardButton("📋 List",   callback_data="stg_admin_list")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
    ])


def _ban_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚫 Ban",    callback_data="stg_ban_add"),
            InlineKeyboardButton("✅ Unban",  callback_data="stg_ban_remove"),
            InlineKeyboardButton("📋 List",   callback_data="stg_ban_list")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
    ])


def _fsub_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add",    callback_data="stg_fsub_add"),
            InlineKeyboardButton("➖ Remove", callback_data="stg_fsub_remove"),
            InlineKeyboardButton("📋 List",   callback_data="stg_fsub_list")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
    ])


async def _edit(query: CallbackQuery, caption: str, markup):
    """Edit caption if photo message, else edit text."""
    try:
        await query.message.edit_caption(caption=caption, reply_markup=markup)
    except Exception:
        try:
            await query.message.edit_text(caption, reply_markup=markup)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
#  MAIN SETTINGS CALLBACK ROUTER
# ═══════════════════════════════════════════════════════════════

@Bot.on_callback_query(filters.regex(r"^stg_"))
async def settings_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    data = query.data
    uid  = query.from_user.id

    # ── BACK TO MAIN ──────────────────────────────────────────
    if data == "stg_back":
        _pending.pop(uid, None)
        await _edit(query,
            "<b>⚙️ Settings Panel</b>\n\nSelect a category to manage:",
            _main_markup()
        )

    # ══════════════════════════════════════════════════════════
    #  ADMIN PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_admin":
        _pending.pop(uid, None)
        await _edit(query, "<b>👑 Admin Management</b>\n\nChoose an action:", _admin_markup())

    elif data == "stg_admin_add":
        _pending[uid] = {"action": "admin_add", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>➕ Add Admin</b>\n\n📤 Send the <b>User ID</b> to add as admin:",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_admin")]])
        )

    elif data == "stg_admin_remove":
        _pending.pop(uid, None)
        admins = await db.get_all_admins()
        if not admins:
            await _edit(query, "<b>📋 No admins to remove.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_admin")]]))
            return
        buttons = []
        for aid in admins:
            try:
                u = await client.get_users(aid)
                label = f"❌ {u.first_name} ({aid})"
            except Exception:
                label = f"❌ {aid}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"stg_deladmin_{aid}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_admin")])
        await _edit(query, "<b>➖ Remove Admin</b>\n\nTap an admin to remove:", InlineKeyboardMarkup(buttons))

    elif data.startswith("stg_deladmin_"):
        _pending.pop(uid, None)
        aid = int(data.replace("stg_deladmin_", ""))
        await db.del_admin(aid)
        await _edit(query,
            f"<b>✅ Admin <code>{aid}</code> removed.</b>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_admin")]])
        )

    elif data == "stg_admin_list":
        _pending.pop(uid, None)
        admins = await db.get_all_admins()
        if not admins:
            text = "<b>📋 Admin list is empty.</b>"
        else:
            rows = "\n".join([f"• <code>{a}</code>" for a in admins])
            text = f"<b>👑 Admins ({len(admins)}):</b>\n\n{rows}"
        await _edit(query, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_admin")]]))

    # ══════════════════════════════════════════════════════════
    #  BAN PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_ban":
        _pending.pop(uid, None)
        await _edit(query, "<b>🚫 Ban Management</b>\n\nChoose an action:", _ban_markup())

    elif data == "stg_ban_add":
        _pending[uid] = {"action": "ban_add", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>🚫 Ban User</b>\n\n📤 Send the <b>User ID</b> to ban:",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_ban")]])
        )

    elif data == "stg_ban_remove":
        _pending[uid] = {"action": "ban_remove", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>✅ Unban User</b>\n\n📤 Send the <b>User ID</b> to unban:",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_ban")]])
        )

    elif data == "stg_ban_list":
        _pending.pop(uid, None)
        banned = await db.get_ban_users()
        if not banned:
            text = "<b>📋 No banned users.</b>"
        else:
            rows = "\n".join([f"• <code>{u}</code>" for u in banned])
            text = f"<b>🚫 Banned Users ({len(banned)}):</b>\n\n{rows}"
        await _edit(query, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_ban")]]))

    # ══════════════════════════════════════════════════════════
    #  USERS
    # ══════════════════════════════════════════════════════════

    elif data == "stg_users":
        _pending.pop(uid, None)
        users = await db.full_userbase()
        await _edit(query,
            f"<b>👥 Users Info</b>\n\n<b>Total Users in DB:</b> <code>{len(users)}</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_back")]])
        )

    # ══════════════════════════════════════════════════════════
    #  STATS
    # ══════════════════════════════════════════════════════════

    elif data == "stg_stats":
        _pending.pop(uid, None)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu  = psutil.cpu_percent(interval=0.5)

        text = (
            f"<b>📊 System Stats</b>\n\n"
            f"<b>🧠 RAM</b>\n"
            f"├ Total: <code>{round(ram.total  / 1024**3, 2)} GB</code>\n"
            f"├ Used:  <code>{round(ram.used   / 1024**3, 2)} GB ({ram.percent}%)</code>\n"
            f"└ Free:  <code>{round(ram.available / 1024**3, 2)} GB</code>\n\n"
            f"<b>💾 Disk</b>\n"
            f"├ Total: <code>{round(disk.total / 1024**3, 2)} GB</code>\n"
            f"├ Used:  <code>{round(disk.used  / 1024**3, 2)} GB ({disk.percent}%)</code>\n"
            f"└ Free:  <code>{round(disk.free  / 1024**3, 2)} GB</code>\n\n"
            f"<b>⚙️ CPU:</b> <code>{cpu}%</code>"
        )
        await _edit(query, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_back")]]))

    # ══════════════════════════════════════════════════════════
    #  FORCE SUB PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_fsub":
        _pending.pop(uid, None)
        await _edit(query,
            "<b>📢 Force Sub Settings</b>\n\nManage your force subscription channels:",
            _fsub_markup()
        )

    elif data == "stg_fsub_add":
        _pending[uid] = {"action": "fsub_add", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>➕ Add Force Sub Channel</b>\n\n"
            "📤 Send the <b>Channel ID</b> (e.g. <code>-100xxxxxxxxxx</code>)\n\n"
            "<i>The bot must be admin in that channel.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_fsub")]])
        )

    elif data == "stg_fsub_remove":
        _pending.pop(uid, None)
        channels = await db.show_channels()
        if not channels:
            await query.answer("❌ No channels added yet!", show_alert=True)
            return
        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                name = chat.title
            except Exception:
                name = str(ch_id)
            buttons.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"stg_fsub_del_{ch_id}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")])
        await _edit(query, "<b>➖ Select a channel to remove:</b>", InlineKeyboardMarkup(buttons))

    elif data.startswith("stg_fsub_del_"):
        _pending.pop(uid, None)
        ch_id = int(data.split("stg_fsub_del_")[1])
        await db.rem_channel(ch_id)
        await query.answer("✅ Removed!", show_alert=True)
        channels = await db.show_channels()
        if not channels:
            await _edit(query,
                "<b>📢 Force Sub Settings</b>\n\nManage your force subscription channels:",
                _fsub_markup()
            )
            return
        buttons = []
        for cid in channels:
            try:
                chat = await client.get_chat(cid)
                name = chat.title
            except Exception:
                name = str(cid)
            buttons.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"stg_fsub_del_{cid}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")])
        await _edit(query, "<b>➖ Select a channel to remove:</b>", InlineKeyboardMarkup(buttons))

    elif data == "stg_fsub_list":
        _pending.pop(uid, None)
        channels = await db.show_channels()
        if not channels:
            await _edit(query, "<b>❌ No force-sub channels added yet.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]]))
            return
        text = "<b>📋 Force Sub Channels:</b>\n\n"
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                status = "🟢 Request" if mode == "on" else "🔴 Direct"
                text += f"• <b>{chat.title}</b> [{status}]\n  └ <code>{ch_id}</code>\n\n"
            except Exception:
                text += f"• ⚠️ <code>{ch_id}</code> — Unavailable\n\n"
        await _edit(query, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]]))

    # ══════════════════════════════════════════════════════════
    #  REQUEST MODE PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_reqmode":
        _pending.pop(uid, None)
        channels = await db.show_channels()
        if not channels:
            await _edit(query,
                "<b>❌ No force-sub channels found.\nAdd channels first via Force Sub.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_back")]])
            )
            return
        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                status = "🟢 ON" if mode == "on" else "🔴 OFF"
                buttons.append([InlineKeyboardButton(f"{status} — {chat.title}", callback_data=f"stg_rq_{ch_id}")])
            except Exception:
                buttons.append([InlineKeyboardButton(f"⚠️ {ch_id}", callback_data=f"stg_rq_{ch_id}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_back")])
        await _edit(query,
            "<b>🔄 Request Mode</b>\n\n"
            "<b>🟢 ON</b>  → Join request required\n"
            "<b>🔴 OFF</b> → Direct join\n\n"
            "<i>Tap a channel to toggle:</i>",
            InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("stg_rq_"):
        _pending.pop(uid, None)
        ch_id = int(data.split("stg_rq_")[1])
        current = await db.get_channel_mode(ch_id)
        new_mode = "off" if current == "on" else "on"
        await db.set_channel_mode(ch_id, new_mode)
        label = "🟢 Request Mode ON" if new_mode == "on" else "🔴 Direct Join"
        await query.answer(f"Toggled → {label}", show_alert=True)

        channels = await db.show_channels()
        buttons = []
        for cid in channels:
            try:
                chat = await client.get_chat(cid)
                mode = await db.get_channel_mode(cid)
                status = "🟢 ON" if mode == "on" else "🔴 OFF"
                buttons.append([InlineKeyboardButton(f"{status} — {chat.title}", callback_data=f"stg_rq_{cid}")])
            except Exception:
                buttons.append([InlineKeyboardButton(f"⚠️ {cid}", callback_data=f"stg_rq_{cid}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_back")])
        await _edit(query,
            "<b>🔄 Request Mode</b>\n\n"
            "<b>🟢 ON</b>  → Join request required\n"
            "<b>🔴 OFF</b> → Direct join\n\n"
            "<i>Tap a channel to toggle:</i>",
            InlineKeyboardMarkup(buttons)
        )


# ═══════════════════════════════════════════════════════════════
#  TEXT INPUT HANDLER  (for admin_add, ban_add, ban_remove, fsub_add)
# ═══════════════════════════════════════════════════════════════

@Bot.on_message(
    filters.private & filters.text &
    filters.create(lambda _, __, m: m.from_user and m.from_user.id in _pending),
    group=-1
)
async def handle_settings_input(client: Bot, message: Message):
    uid   = message.from_user.id
    state = _pending.pop(uid, None)
    if not state:
        return

    raw     = message.text.strip() if message.text else ""
    chat_id = state["chat_id"]
    msg_id  = state["msg_id"]
    action  = state["action"]

    async def patch(caption, markup):
        try:
            await client.edit_message_caption(chat_id, msg_id, caption=caption, reply_markup=markup)
        except Exception:
            try:
                await client.edit_message_text(chat_id, msg_id, caption, reply_markup=markup)
            except Exception:
                pass

    await message.delete()

    # ── ADMIN ADD ────────────────────────────────────────────
    if action == "admin_add":
        try:
            target_id = int(raw)
        except ValueError:
            await patch("<b>❌ Invalid ID. Send a valid numeric User ID.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_admin")]]))
            raise StopPropagation

        await db.add_admin(target_id)
        await patch(
            f"<b>✅ User <code>{target_id}</code> added as Admin.</b>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Another", callback_data="stg_admin_add"),
                 InlineKeyboardButton("🔙 Back",        callback_data="stg_admin")]
            ])
        )

    # ── BAN ADD ──────────────────────────────────────────────
    elif action == "ban_add":
        try:
            target_id = int(raw)
        except ValueError:
            await patch("<b>❌ Invalid ID. Send a valid numeric User ID.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_ban")]]))
            raise StopPropagation

        if target_id == OWNER_ID or await db.admin_exist(target_id):
            await patch("<b>⛔ Cannot ban an admin or owner.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_ban")]]))
            raise StopPropagation

        await db.add_ban_user(target_id)
        await patch(
            f"<b>✅ User <code>{target_id}</code> has been banned.</b>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🚫 Ban Another", callback_data="stg_ban_add"),
                 InlineKeyboardButton("🔙 Back",        callback_data="stg_ban")]
            ])
        )

    # ── BAN REMOVE ───────────────────────────────────────────
    elif action == "ban_remove":
        try:
            target_id = int(raw)
        except ValueError:
            await patch("<b>❌ Invalid ID. Send a valid numeric User ID.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_ban")]]))
            raise StopPropagation

        await db.del_ban_user(target_id)
        await patch(
            f"<b>✅ User <code>{target_id}</code> has been unbanned.</b>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Unban Another", callback_data="stg_ban_remove"),
                 InlineKeyboardButton("🔙 Back",          callback_data="stg_ban")]
            ])
        )

    # ── FSUB ADD ─────────────────────────────────────────────
    elif action == "fsub_add":
        try:
            ch_id = int(raw)
        except ValueError:
            await patch("<b>❌ Invalid ID. Send a valid numeric Channel ID.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]]))
            raise StopPropagation

        existing = await db.show_channels()
        if ch_id in existing:
            await patch(f"<b>⚠️ Channel already exists:</b> <code>{ch_id}</code>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]]))
            raise StopPropagation

        try:
            chat = await client.get_chat(ch_id)
            if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                await patch("<b>❌ Only channels/supergroups are allowed.</b>",
                            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]]))
                raise StopPropagation

            bot_member = await client.get_chat_member(chat.id, "me")
            if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await patch("<b>❌ Bot must be admin in that channel.</b>",
                            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]]))
                raise StopPropagation

            await db.add_channel(ch_id)
            await patch(
                f"<b>✅ Added Successfully!</b>\n\n"
                f"<b>Name:</b> {chat.title}\n"
                f"<b>ID:</b> <code>{ch_id}</code>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Another", callback_data="stg_fsub_add"),
                     InlineKeyboardButton("🔙 Back",        callback_data="stg_fsub")]
                ])
            )
        except StopPropagation:
            raise
        except Exception as e:
            await patch(f"<b>❌ Failed:</b> <code>{e}</code>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]]))

    raise StopPropagation
