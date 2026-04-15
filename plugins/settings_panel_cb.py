import asyncio
import psutil
from datetime import datetime
from pyrogram import filters, StopPropagation
from pyrogram.types import (
    CallbackQuery, Message,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from bot import Bot
from config import OWNER_ID
from helper_func import get_readable_time
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
            InlineKeyboardButton("🔢 Count",      callback_data="stg_count"),
            InlineKeyboardButton("🧹 DelReq",     callback_data="stg_delreq")
        ],
        [
            InlineKeyboardButton("📢 Force Sub",  callback_data="stg_fsub"),
            InlineKeyboardButton("🔄 Request Mode", callback_data="stg_reqmode")
        ],
        [
            InlineKeyboardButton("⏱ Auto Delete", callback_data="stg_autodel")
        ],
        [
            InlineKeyboardButton("🔐 Protect", callback_data="stg_protect"),
            InlineKeyboardButton("📝 Caption", callback_data="stg_caption")
        ],
        [
            InlineKeyboardButton("🛡 Anti Bypass", callback_data="stg_antibypass")
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
    # ═���════════════════════════════════════════════════════════

    elif data == "stg_stats":
        _pending.pop(uid, None)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu  = psutil.cpu_percent(interval=0.5)
        now = datetime.now(client.uptime.tzinfo) if getattr(client.uptime, "tzinfo", None) else datetime.now()
        uptime = get_readable_time(int((now - client.uptime).total_seconds()))

        text = (
            f"<b>📊 Bot & System Stats</b>\n\n"
            f"<b>⏰ Uptime:</b> <code>{uptime}</code>\n\n"
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

    elif data == "stg_count":
        _pending.pop(uid, None)
        total = await db.get_total_verify_count()
        await _edit(query,
            f"<b>🔢 Verification Count</b>\n\n<b>Total verified tokens today:</b> <code>{total}</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_back")]])
        )

    elif data == "stg_delreq":
        _pending.pop(uid, None)
        channels = await db.show_channels()
        if not channels:
            await _edit(query,
                "<b>❌ No force-sub channels found.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_back")]])
            )
            return
        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                name = chat.title
            except Exception:
                name = str(ch_id)
            buttons.append([InlineKeyboardButton(f"🧹 {name}", callback_data=f"stg_delreq_clean_{ch_id}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_back")])
        await _edit(query,
            "<b>🧹 Delete Request Cleanup</b>\n\nSelect a channel to remove leftover request users:",
            InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("stg_delreq_clean_"):
        _pending.pop(uid, None)
        channel_id = int(data.split("stg_delreq_clean_")[1])
        channel_data = await db.rqst_fsub_Channel_data.find_one({'_id': channel_id})
        if not channel_data:
            await _edit(query,
                f"<b>ℹ️ No request channel found for:</b> <code>{channel_id}</code>",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_delreq")]])
            )
            return

        user_ids = channel_data.get("user_ids", [])
        if not user_ids:
            await _edit(query,
                f"<b>✅ No users to process for:</b> <code>{channel_id}</code>",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_delreq")]])
            )
            return

        removed = 0
        skipped = 0
        left_users = 0

        for user_id in user_ids:
            try:
                member = await client.get_chat_member(channel_id, user_id)
                if member.status in (
                    ChatMemberStatus.MEMBER,
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.OWNER
                ):
                    skipped += 1
                    continue
                await db.del_req_user(channel_id, user_id)
                left_users += 1
            except UserNotParticipant:
                await db.del_req_user(channel_id, user_id)
                left_users += 1
            except Exception as e:
                print(f"[!] Error checking user {user_id}: {e}")
                skipped += 1

        for user_id in user_ids:
            if not await db.req_user_exist(channel_id, user_id):
                await db.del_req_user(channel_id, user_id)
                removed += 1

        await _edit(query,
            f"<b>✅ Cleanup done for channel</b> <code>{channel_id}</code>\n\n"
            f"👤 Removed (left channel): <code>{left_users}</code>\n"
            f"🗑️ Removed (leftover): <code>{removed}</code>\n"
            f"✅ Still members: <code>{skipped}</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_delreq")]])
        )

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
                "<b>�� No force-sub channels found.\nAdd channels first via Force Sub.</b>",
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


    # ══════════════════════════════════════════════════════════
    #  CONTENT SETTINGS
    # ══════════════════════════════════════════════════════════

    elif data == "stg_protect":
        _pending.pop(uid, None)
        enabled = await db.get_protect_content()
        status = "🟢 True" if enabled else "🔴 False"
        await _edit(query,
            f"<b>🔐 Protect Content</b>\n\n<b>Current:</b> <code>{status}</code>\n\n<i>Premium users will always receive files with protect content OFF.</i>",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🟢 True", callback_data="stg_protect_true"),
                    InlineKeyboardButton("🔴 False", callback_data="stg_protect_false")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
            ])
        )

    elif data == "stg_protect_true":
        _pending.pop(uid, None)
        await db.set_protect_content(True)
        await _edit(query,
            "<b>✅ Protect Content set to:</b> <code>True</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_protect")]])
        )

    elif data == "stg_protect_false":
        _pending.pop(uid, None)
        await db.set_protect_content(False)
        await _edit(query,
            "<b>✅ Protect Content set to:</b> <code>False</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_protect")]])
        )

    elif data == "stg_caption":
        _pending.pop(uid, None)
        caption = await db.get_custom_caption()
        current = f"<code>{caption}</code>" if caption else "<code>Disabled</code>"
        await _edit(query,
            f"<b>📝 Custom Caption</b>\n\n<b>Current:</b> {current}\n\n<i>You can use {{previouscaption}} and {{filename}} placeholders.</i>",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✏️ Set Caption", callback_data="stg_caption_set"),
                    InlineKeyboardButton("❌ Clear", callback_data="stg_caption_clear")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
            ])
        )

    elif data == "stg_caption_set":
        _pending[uid] = {"action": "caption_set", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>📝 Set Custom Caption</b>\n\n📤 Send the caption text now.\n\nAvailable placeholders:\n<code>{previouscaption}</code>\n<code>{filename}</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_caption")]])
        )

    elif data == "stg_caption_clear":
        _pending.pop(uid, None)
        await db.set_custom_caption(None)
        await _edit(query,
            "<b>✅ Custom Caption cleared.</b>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_caption")]])
        )

    elif data == "stg_antibypass":
        _pending.pop(uid, None)
        enabled = await db.get_anti_bypass()
        status = "🟢 ON" if enabled else "🔴 OFF"
        await _edit(query,
            f"<b>🛡 Anti Bypass</b>\n\n<b>Current:</b> <code>{status}</code>\n\n<i>Default is ON. It checks suspicious browser/server requests, repeated attempts, and too-fast verification.</i>",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🟢 ON", callback_data="stg_antibypass_on"),
                    InlineKeyboardButton("🔴 OFF", callback_data="stg_antibypass_off")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
            ])
        )

    elif data == "stg_antibypass_on":
        _pending.pop(uid, None)
        await db.set_anti_bypass(True)
        await _edit(query,
            "<b>✅ Anti Bypass set to:</b> <code>ON</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_antibypass")]])
        )

    elif data == "stg_antibypass_off":
        _pending.pop(uid, None)
        await db.set_anti_bypass(False)
        await _edit(query,
            "<b>✅ Anti Bypass set to:</b> <code>OFF</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_antibypass")]])
        )

    # ══════════════════════════════════════════════════════════
    #  AUTO DELETE PANEL
    # ═══════════════════════════════════════════════════��══════

    elif data == "stg_autodel":
        _pending.pop(uid, None)
        current = await db.get_del_timer()
        try:
            val = int(current)
        except Exception:
            val = 0
        status = f"<code>{val}s</code>" if val > 0 else "<code>Disabled</code>"
        await _edit(query,
            f"<b>⏱ Auto Delete</b>\n\n"
            f"<b>Current Timer:</b> {status}\n\n"
            "<i>Files sent by bot will be auto-deleted after the set time.</i>",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✏️ Set Timer", callback_data="stg_autodel_set"),
                    InlineKeyboardButton("❌ Disable",   callback_data="stg_autodel_off")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
            ])
        )

    elif data == "stg_autodel_set":
        _pending[uid] = {"action": "autodel_set", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>⏱ Set Auto Delete Timer</b>\n\n"
            "📤 Send the time in <b>seconds</b>\n"
            "(e.g. <code>300</code> = 5 minutes, <code>3600</code> = 1 hour)\n\n"
            "Send <code>0</code> to disable.",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_autodel")]])
        )

    elif data == "stg_autodel_off":
        _pending.pop(uid, None)
        await db.set_del_timer(0)
        await _edit(query,
            "<b>✅ Auto Delete Disabled</b>\n\nFiles will no longer be auto-deleted.",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_autodel")]])
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

    # ── CUSTOM CAPTION SET ───────────────────────────────────
    elif action == "caption_set":
        caption = raw or None
        await db.set_custom_caption(caption)
        if caption:
            msg_txt = f"<b>✅ Custom Caption updated.</b>\n\n<code>{caption}</code>"
        else:
            msg_txt = "<b>✅ Custom Caption cleared.</b>"

        await patch(msg_txt,
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Change", callback_data="stg_caption_set"),
                 InlineKeyboardButton("🔙 Back",   callback_data="stg_caption")]
            ])
        )

    # ── AUTO DELETE SET ──────────────────────────────��───────
    elif action == "autodel_set":
        try:
            seconds = int(raw)
        except ValueError:
            await patch("<b>❌ Invalid. Send a number (seconds).</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_autodel")]]))
            raise StopPropagation

        await db.set_del_timer(seconds)
        if seconds == 0:
            msg_txt = "<b>✅ Auto Delete Disabled.</b>"
        else:
            mins = seconds // 60
            secs = seconds % 60
            readable = f"{mins}m {secs}s" if mins else f"{secs}s"
            msg_txt = f"<b>✅ Auto Delete set to <code>{seconds}s</code> ({readable}).</b>"

        await patch(msg_txt,
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Change", callback_data="stg_autodel_set"),
                 InlineKeyboardButton("🔙 Back",   callback_data="stg_autodel")]
            ])
        )


    raise StopPropagation
