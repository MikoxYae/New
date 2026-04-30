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
from helper_func import get_readable_time, normalize_support_link, get_support_url
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
            InlineKeyboardButton("👑 ᴀᴅᴍɪɴ",      callback_data="stg_admin"),
            InlineKeyboardButton("🚫 ʙᴀɴ ᴜsᴇʀs",  callback_data="stg_ban")
        ],
        [
            InlineKeyboardButton("👥 ᴜsᴇʀs",      callback_data="stg_users"),
            InlineKeyboardButton("📊 sᴛᴀᴛs",      callback_data="stg_stats")
        ],
        [
            InlineKeyboardButton("🧹 ᴅᴇʟʀᴇǫ",     callback_data="stg_delreq"),
            InlineKeyboardButton("📢 ғᴏʀᴄᴇ sᴜʙ",  callback_data="stg_fsub")
        ],
        [
            InlineKeyboardButton("🔄 ʀᴇǫᴜᴇsᴛ ᴍᴏᴅᴇ", callback_data="stg_reqmode"),
            InlineKeyboardButton("⏱ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ", callback_data="stg_autodel")
        ],
        [
            InlineKeyboardButton("🆓 ғʀᴇᴇ ʟɪɴᴋ",   callback_data="stg_freelink"),
            InlineKeyboardButton("🔐 ᴘʀᴏᴛᴇᴄᴛ",     callback_data="stg_protect")
        ],
        [
            InlineKeyboardButton("📝 ᴄᴀᴘᴛɪᴏɴ",     callback_data="stg_caption"),
            InlineKeyboardButton("🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ", callback_data="stg_maintenance")
        ],
        [
            InlineKeyboardButton("🆘 sᴜᴘᴘᴏʀᴛ",     callback_data="stg_support")
        ]
    ])


def _freelink_panel(limit: int, enabled: bool):
    """Render the Free Link settings panel (text + markup) for a given state."""
    if enabled:
        status_line = "<b>sᴛᴀᴛᴜs:</b> 🟢 ᴏɴ\n"
        mode_line   = "<b>ᴍᴏᴅᴇ:</b> ᴀғᴛᴇʀ ғʀᴇᴇ ʟɪɴᴋs, ᴘʀᴇᴍɪᴜᴍ ʀᴇǫᴜɪʀᴇᴅ\n"
        toggle_btn  = InlineKeyboardButton("🔴 ᴛᴜʀɴ ᴏғғ", callback_data="stg_fl_toggle")
    else:
        status_line = "<b>sᴛᴀᴛᴜs:</b> 🔴 ᴏғғ\n"
        mode_line   = "<b>ᴍᴏᴅᴇ:</b> ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss — ɴᴏ ᴅᴀɪʟʏ ʟɪᴍɪᴛ\n"
        toggle_btn  = InlineKeyboardButton("🟢 ᴛᴜʀɴ ᴏɴ",  callback_data="stg_fl_toggle")

    text = (
        "<b>🆓 ғʀᴇᴇ ʟɪɴᴋ sᴇᴛᴛɪɴɢs</b>\n\n"
        f"{status_line}"
        f"<b>ᴅᴀɪʟʏ ғʀᴇᴇ ʟɪɴᴋs:</b> <code>{limit}</code> ᴘᴇʀ ᴜsᴇʀ\n"
        f"{mode_line}\n"
        "<i>ᴛᴏɢɢʟᴇ ᴛʜᴇ sʏsᴛᴇᴍ ᴏʀ sᴇʟᴇᴄᴛ ᴛʜᴇ ᴅᴀɪʟʏ ғʀᴇᴇ ʟɪɴᴋ ʟɪᴍɪᴛ ʙᴇʟᴏᴡ:</i>"
    )
    markup = InlineKeyboardMarkup([
        [toggle_btn],
        [
            InlineKeyboardButton("5"  if limit != 5  else "✅ 5",  callback_data="stg_fl_5"),
            InlineKeyboardButton("10" if limit != 10 else "✅ 10", callback_data="stg_fl_10"),
            InlineKeyboardButton("15" if limit != 15 else "✅ 15", callback_data="stg_fl_15"),
            InlineKeyboardButton("20" if limit != 20 else "✅ 20", callback_data="stg_fl_20"),
        ],
        [InlineKeyboardButton("✏️ ᴄᴜsᴛᴏᴍ", callback_data="stg_fl_custom")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]
    ])
    return text, markup


def _admin_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ ᴀᴅᴅ",    callback_data="stg_admin_add"),
            InlineKeyboardButton("➖ ʀᴇᴍᴏᴠᴇ", callback_data="stg_admin_remove"),
            InlineKeyboardButton("📋 ʟɪsᴛ",   callback_data="stg_admin_list")
        ],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]
    ])


def _ban_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚫 ʙᴀɴ",    callback_data="stg_ban_add"),
            InlineKeyboardButton("✅ ᴜɴʙᴀɴ",  callback_data="stg_ban_remove"),
            InlineKeyboardButton("📋 ʟɪsᴛ",   callback_data="stg_ban_list")
        ],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]
    ])


def _fsub_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ ᴀᴅᴅ",    callback_data="stg_fsub_add"),
            InlineKeyboardButton("➖ ʀᴇᴍᴏᴠᴇ", callback_data="stg_fsub_remove"),
            InlineKeyboardButton("📋 ʟɪsᴛ",   callback_data="stg_fsub_list")
        ],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]
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
            "<b>⚙️ sᴇᴛᴛɪɴɢs ᴘᴀɴᴇʟ</b>\n\nsᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ᴛᴏ ᴍᴀɴᴀɢᴇ:",
            _main_markup()
        )

    # ══════════════════════════════════════════════════════════
    #  ADMIN PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_admin":
        _pending.pop(uid, None)
        await _edit(query, "<b>👑 ᴀᴅᴍɪɴ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ</b>\n\nᴄʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:", _admin_markup())

    elif data == "stg_admin_add":
        _pending[uid] = {"action": "admin_add", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>➕ ᴀᴅᴅ ᴀᴅᴍɪɴ</b>\n\n📤 sᴇɴᴅ ᴛʜᴇ <b>ᴜsᴇʀ ɪᴅ</b> ᴛᴏ ᴀᴅᴅ ᴀs ᴀᴅᴍɪɴ:",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="stg_admin")]])
        )

    elif data == "stg_admin_remove":
        _pending.pop(uid, None)
        admins = await db.get_all_admins()
        if not admins:
            await _edit(query, "<b>📋 ɴᴏ ᴀᴅᴍɪɴs ᴛᴏ ʀᴇᴍᴏᴠᴇ.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_admin")]]))
            return
        buttons = []
        for aid in admins:
            try:
                u = await client.get_users(aid)
                label = f"❌ {u.first_name} ({aid})"
            except Exception:
                label = f"❌ {aid}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"stg_deladmin_{aid}")])
        buttons.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_admin")])
        await _edit(query, "<b>➖ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ</b>\n\nᴛᴀᴘ ᴀɴ ᴀᴅᴍɪɴ ᴛᴏ ʀᴇᴍᴏᴠᴇ:", InlineKeyboardMarkup(buttons))

    elif data.startswith("stg_deladmin_"):
        _pending.pop(uid, None)
        aid = int(data.replace("stg_deladmin_", ""))
        await db.del_admin(aid)
        await _edit(query,
            f"<b>✅ ᴀᴅᴍɪɴ <code>{aid}</code> ʀᴇᴍᴏᴠᴇᴅ.</b>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_admin")]])
        )

    elif data == "stg_admin_list":
        _pending.pop(uid, None)
        admins = await db.get_all_admins()
        if not admins:
            text = "<b>📋 ᴀᴅᴍɪɴ ʟɪsᴛ ɪs ᴇᴍᴘᴛʏ.</b>"
        else:
            rows = "\n".join([f"• <code>{a}</code>" for a in admins])
            text = f"<b>👑 ᴀᴅᴍɪɴs ({len(admins)}):</b>\n\n{rows}"
        await _edit(query, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_admin")]]))

    # ══════════════════════════════════════════════════════════
    #  BAN PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_ban":
        _pending.pop(uid, None)
        await _edit(query, "<b>🚫 ʙᴀɴ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ</b>\n\nᴄʜᴏᴏsᴇ ᴀɴ ᴀᴄᴛɪᴏɴ:", _ban_markup())

    elif data == "stg_ban_add":
        _pending[uid] = {"action": "ban_add", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>🚫 ʙᴀɴ ᴜsᴇʀ</b>\n\n📤 sᴇɴᴅ ᴛʜᴇ <b>ᴜsᴇʀ ɪᴅ</b> ᴛᴏ ʙᴀɴ:",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="stg_ban")]])
        )

    elif data == "stg_ban_remove":
        _pending[uid] = {"action": "ban_remove", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>✅ ᴜɴʙᴀɴ ᴜsᴇʀ</b>\n\n📤 sᴇɴᴅ ᴛʜᴇ <b>ᴜsᴇʀ ɪᴅ</b> ᴛᴏ ᴜɴʙᴀɴ:",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="stg_ban")]])
        )

    elif data == "stg_ban_list":
        _pending.pop(uid, None)
        banned = await db.get_ban_users()
        if not banned:
            text = "<b>📋 ɴᴏ ʙᴀɴɴᴇᴅ ᴜsᴇʀs.</b>"
        else:
            rows = "\n".join([f"• <code>{u}</code>" for u in banned])
            text = f"<b>🚫 ʙᴀɴɴᴇᴅ ᴜsᴇʀs ({len(banned)}):</b>\n\n{rows}"
        await _edit(query, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_ban")]]))

    # ══════════════════════════════════════════════════════════
    #  USERS
    # ══════════════════════════════════════════════════════════

    elif data == "stg_users":
        _pending.pop(uid, None)
        users = await db.full_userbase()
        await _edit(query,
            f"<b>👥 ᴜsᴇʀs ɪɴғᴏ</b>\n\n<b>ᴛᴏᴛᴀʟ ᴜsᴇʀs ɪɴ ᴅʙ:</b> <code>{len(users)}</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]])
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
            f"<b>📊 ʙᴏᴛ & sʏsᴛᴇᴍ sᴛᴀᴛs</b>\n\n"
            f"<b>⏰ ᴜᴘᴛɪᴍᴇ:</b> <code>{uptime}</code>\n\n"
            f"<b>🧠 ʀᴀᴍ</b>\n"
            f"├ ᴛᴏᴛᴀʟ: <code>{round(ram.total  / 1024**3, 2)} GB</code>\n"
            f"├ ᴜsᴇᴅ:  <code>{round(ram.used   / 1024**3, 2)} GB ({ram.percent}%)</code>\n"
            f"└ ғʀᴇᴇ:  <code>{round(ram.available / 1024**3, 2)} GB</code>\n\n"
            f"<b>💾 ᴅɪsᴋ</b>\n"
            f"├ ᴛᴏᴛᴀʟ: <code>{round(disk.total / 1024**3, 2)} GB</code>\n"
            f"├ ᴜsᴇᴅ:  <code>{round(disk.used  / 1024**3, 2)} GB ({disk.percent}%)</code>\n"
            f"└ ғʀᴇᴇ:  <code>{round(disk.free  / 1024**3, 2)} GB</code>\n\n"
            f"<b>⚙️ ᴄᴘᴜ:</b> <code>{cpu}%</code>"
        )
        await _edit(query, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]]))

    elif data == "stg_delreq":
        _pending.pop(uid, None)
        channels = await db.show_channels()
        if not channels:
            await _edit(query,
                "<b>❌ ɴᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]])
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
        buttons.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")])
        await _edit(query,
            "<b>🧹 ᴅᴇʟᴇᴛᴇ ʀᴇǫᴜᴇsᴛ ᴄʟᴇᴀɴᴜᴘ</b>\n\nsᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇᴍᴏᴠᴇ ʟᴇғᴛᴏᴠᴇʀ ʀᴇǫᴜᴇsᴛ ᴜsᴇʀs:",
            InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("stg_delreq_clean_"):
        _pending.pop(uid, None)
        channel_id = int(data.split("stg_delreq_clean_")[1])
        channel_data = await db.rqst_fsub_Channel_data.find_one({'_id': channel_id})
        if not channel_data:
            await _edit(query,
                f"<b>ℹ️ ɴᴏ ʀᴇǫᴜᴇsᴛ ᴄʜᴀɴɴᴇʟ ғᴏᴜɴᴅ ғᴏʀ:</b> <code>{channel_id}</code>",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_delreq")]])
            )
            return

        user_ids = channel_data.get("user_ids", [])
        if not user_ids:
            await _edit(query,
                f"<b>✅ ɴᴏ ᴜsᴇʀs ᴛᴏ ᴘʀᴏᴄᴇss ғᴏʀ:</b> <code>{channel_id}</code>",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_delreq")]])
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
            f"<b>✅ ᴄʟᴇᴀɴᴜᴘ ᴅᴏɴᴇ ғᴏʀ ᴄʜᴀɴɴᴇʟ</b> <code>{channel_id}</code>\n\n"
            f"👤 ʀᴇᴍᴏᴠᴇᴅ (ʟᴇғᴛ ᴄʜᴀɴɴᴇʟ): <code>{left_users}</code>\n"
            f"🗑️ ʀᴇᴍᴏᴠᴇᴅ (ʟᴇғᴛᴏᴠᴇʀ): <code>{removed}</code>\n"
            f"✅ sᴛɪʟʟ ᴍᴇᴍʙᴇʀs: <code>{skipped}</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_delreq")]])
        )

    # ══════════════════════════════════════════════════════════
    #  FORCE SUB PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_fsub":
        _pending.pop(uid, None)
        await _edit(query,
            "<b>📢 ғᴏʀᴄᴇ sᴜʙ sᴇᴛᴛɪɴɢs</b>\n\nᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴄʜᴀɴɴᴇʟs:",
            _fsub_markup()
        )

    elif data == "stg_fsub_add":
        _pending[uid] = {"action": "fsub_add", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>➕ ᴀᴅᴅ ғᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ</b>\n\n"
            "📤 sᴇɴᴅ ᴛʜᴇ <b>ᴄʜᴀɴɴᴇʟ ɪᴅ</b> (ᴇ.ɢ. <code>-100xxxxxxxxxx</code>)\n\n"
            "<i>ᴛʜᴇ ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="stg_fsub")]])
        )

    elif data == "stg_fsub_remove":
        _pending.pop(uid, None)
        channels = await db.show_channels()
        if not channels:
            await query.answer("❌ ɴᴏ ᴄʜᴀɴɴᴇʟs ᴀᴅᴅᴇᴅ ʏᴇᴛ!", show_alert=True)
            return
        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                name = chat.title
            except Exception:
                name = str(ch_id)
            buttons.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"stg_fsub_del_{ch_id}")])
        buttons.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")])
        await _edit(query, "<b>➖ sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇᴍᴏᴠᴇ:</b>", InlineKeyboardMarkup(buttons))

    elif data.startswith("stg_fsub_del_"):
        _pending.pop(uid, None)
        ch_id = int(data.split("stg_fsub_del_")[1])
        await db.rem_channel(ch_id)
        await query.answer("✅ ʀᴇᴍᴏᴠᴇᴅ!", show_alert=True)
        channels = await db.show_channels()
        if not channels:
            await _edit(query,
                "<b>📢 ғᴏʀᴄᴇ sᴜʙ sᴇᴛᴛɪɴɢs</b>\n\nᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴄʜᴀɴɴᴇʟs:",
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
        buttons.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")])
        await _edit(query, "<b>➖ sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇᴍᴏᴠᴇ:</b>", InlineKeyboardMarkup(buttons))

    elif data == "stg_fsub_list":
        _pending.pop(uid, None)
        channels = await db.show_channels()
        if not channels:
            await _edit(query, "<b>❌ ɴᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ᴀᴅᴅᴇᴅ ʏᴇᴛ.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")]]))
            return
        text = "<b>📋 ғᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟs:</b>\n\n"
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                status = "🟢 Request" if mode == "on" else "🔴 Direct"
                text += f"• <b>{chat.title}</b> [{status}]\n  └ <code>{ch_id}</code>\n\n"
            except Exception:
                text += f"• ⚠️ <code>{ch_id}</code> — Unavailable\n\n"
        await _edit(query, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")]]))

    # ══════════════════════════════════════════════════════════
    #  REQUEST MODE PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_reqmode":
        _pending.pop(uid, None)
        channels = await db.show_channels()
        if not channels:
            await _edit(query,
                "<b>�� ɴᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.\nᴀᴅᴅ ᴄʜᴀɴɴᴇʟs ғɪʀsᴛ ᴠɪᴀ ғᴏʀᴄᴇ sᴜʙ.</b>",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]])
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
        buttons.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")])
        await _edit(query,
            "<b>🔄 ʀᴇǫᴜᴇsᴛ ᴍᴏᴅᴇ</b>\n\n"
            "<b>🟢 ᴏɴ</b>  → ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ʀᴇǫᴜɪʀᴇᴅ\n"
            "<b>🔴 ᴏғғ</b> → ᴅɪʀᴇᴄᴛ ᴊᴏɪɴ\n\n"
            "<i>ᴛᴀᴘ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ:</i>",
            InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("stg_rq_"):
        _pending.pop(uid, None)
        ch_id = int(data.split("stg_rq_")[1])
        current = await db.get_channel_mode(ch_id)
        new_mode = "off" if current == "on" else "on"
        await db.set_channel_mode(ch_id, new_mode)
        label = "🟢 Request Mode ON" if new_mode == "on" else "🔴 Direct Join"
        await query.answer(f"ᴛᴏɢɢʟᴇᴅ → {label}", show_alert=True)

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
        buttons.append([InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")])
        await _edit(query,
            "<b>🔄 ʀᴇǫᴜᴇsᴛ ᴍᴏᴅᴇ</b>\n\n"
            "<b>🟢 ᴏɴ</b>  → ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ʀᴇǫᴜɪʀᴇᴅ\n"
            "<b>🔴 ᴏғғ</b> → ᴅɪʀᴇᴄᴛ ᴊᴏɪɴ\n\n"
            "<i>ᴛᴀᴘ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ:</i>",
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
            f"<b>🔐 ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ</b>\n\n<b>ᴄᴜʀʀᴇɴᴛ:</b> <code>{status}</code>\n\n<i>ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴡɪʟʟ ᴀʟᴡᴀʏs ʀᴇᴄᴇɪᴠᴇ ғɪʟᴇs ᴡɪᴛʜ ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ ᴏғғ.</i>",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🟢 ᴛʀᴜᴇ", callback_data="stg_protect_true"),
                    InlineKeyboardButton("🔴 ғᴀʟsᴇ", callback_data="stg_protect_false")
                ],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]
            ])
        )

    elif data == "stg_protect_true":
        _pending.pop(uid, None)
        await db.set_protect_content(True)
        await _edit(query,
            "<b>✅ ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ sᴇᴛ ᴛᴏ:</b> <code>True</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_protect")]])
        )

    elif data == "stg_protect_false":
        _pending.pop(uid, None)
        await db.set_protect_content(False)
        await _edit(query,
            "<b>✅ ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ sᴇᴛ ᴛᴏ:</b> <code>False</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_protect")]])
        )

    elif data == "stg_caption":
        _pending.pop(uid, None)
        caption = await db.get_custom_caption()
        current = f"<code>{caption}</code>" if caption else "<code>Disabled</code>"
        await _edit(query,
            f"<b>📝 ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ</b>\n\n<b>ᴄᴜʀʀᴇɴᴛ:</b> {current}\n\n<i>ʏᴏᴜ ᴄᴀɴ ᴜsᴇ {{previouscaption}} ᴀɴᴅ {{filename}} ᴘʟᴀᴄᴇʜᴏʟᴅᴇʀs.</i>",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✏️ sᴇᴛ ᴄᴀᴘᴛɪᴏɴ", callback_data="stg_caption_set"),
                    InlineKeyboardButton("❌ ᴄʟᴇᴀʀ", callback_data="stg_caption_clear")
                ],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]
            ])
        )

    elif data == "stg_caption_set":
        _pending[uid] = {"action": "caption_set", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>📝 sᴇᴛ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ</b>\n\n📤 sᴇɴᴅ ᴛʜᴇ ᴄᴀᴘᴛɪᴏɴ ᴛᴇxᴛ ɴᴏᴡ.\n\nᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀᴄᴇʜᴏʟᴅᴇʀs:\n<code>{previouscaption}</code>\n<code>{filename}</code>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="stg_caption")]])
        )

    elif data == "stg_caption_clear":
        _pending.pop(uid, None)
        await db.set_custom_caption(None)
        await _edit(query,
            "<b>✅ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴄʟᴇᴀʀᴇᴅ.</b>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_caption")]])
        )

    # ══════════════════════════════════════════════════════════
    #  FREE LINK PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_freelink":
        _pending.pop(uid, None)
        limit   = await db.get_free_link_limit()
        enabled = await db.get_free_link_enabled()
        text, markup = _freelink_panel(limit, enabled)
        await _edit(query, text, markup)

    elif data == "stg_fl_toggle":
        _pending.pop(uid, None)
        new_state = not (await db.get_free_link_enabled())
        await db.set_free_link_enabled(new_state)
        await query.answer(
            f"✅ ғʀᴇᴇ ʟɪɴᴋ sʏsᴛᴇᴍ ᴛᴜʀɴᴇᴅ {'ᴏɴ' if new_state else 'ᴏғғ'}",
            show_alert=True
        )
        limit = await db.get_free_link_limit()
        text, markup = _freelink_panel(limit, new_state)
        await _edit(query, text, markup)

    elif data.startswith("stg_fl_") and data != "stg_fl_custom" and data != "stg_fl_toggle":
        _pending.pop(uid, None)
        try:
            new_limit = int(data.replace("stg_fl_", ""))
        except ValueError:
            await query.answer("ɪɴᴠᴀʟɪᴅ!", show_alert=True)
            return
        await db.set_free_link_limit(new_limit)
        await query.answer(f"✅ ғʀᴇᴇ ʟɪɴᴋ ʟɪᴍɪᴛ sᴇᴛ ᴛᴏ {new_limit}/ᴅᴀʏ", show_alert=True)
        enabled = await db.get_free_link_enabled()
        text, markup = _freelink_panel(new_limit, enabled)
        await _edit(query, text, markup)

    elif data == "stg_fl_custom":
        _pending[uid] = {"action": "freelink_custom", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>✏️ ᴄᴜsᴛᴏᴍ ғʀᴇᴇ ʟɪɴᴋ ʟɪᴍɪᴛ</b>\n\n"
            "📤 sᴇɴᴅ ᴀ <b>ɴᴜᴍʙᴇʀ</b> (ᴇ.ɢ. <code>25</code>) ᴀs ᴛʜᴇ ᴅᴀɪʟʏ ғʀᴇᴇ ʟɪɴᴋ ʟɪᴍɪᴛ:",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="stg_freelink")]])
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
            f"<b>⏱ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ</b>\n\n"
            f"<b>ᴄᴜʀʀᴇɴᴛ ᴛɪᴍᴇʀ:</b> {status}\n\n"
            "<i>ғɪʟᴇs sᴇɴᴛ ʙʏ ʙᴏᴛ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ ᴛʜᴇ sᴇᴛ ᴛɪᴍᴇ.</i>",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✏️ sᴇᴛ ᴛɪᴍᴇʀ", callback_data="stg_autodel_set"),
                    InlineKeyboardButton("❌ ᴅɪsᴀʙʟᴇ",   callback_data="stg_autodel_off")
                ],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]
            ])
        )

    elif data == "stg_autodel_set":
        _pending[uid] = {"action": "autodel_set", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>⏱ sᴇᴛ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ</b>\n\n"
            "📤 sᴇɴᴅ ᴛʜᴇ ᴛɪᴍᴇ ɪɴ <b>sᴇᴄᴏɴᴅs</b>\n"
            "(ᴇ.ɢ. <code>300</code> = 5 ᴍɪɴᴜᴛᴇs, <code>3600</code> = 1 ʜᴏᴜʀ)\n\n"
            "sᴇɴᴅ <code>0</code> ᴛᴏ ᴅɪsᴀʙʟᴇ.",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="stg_autodel")]])
        )

    elif data == "stg_autodel_off":
        _pending.pop(uid, None)
        await db.set_del_timer(0)
        await _edit(query,
            "<b>✅ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴅɪsᴀʙʟᴇᴅ</b>\n\nғɪʟᴇs ᴡɪʟʟ ɴᴏ ʟᴏɴɢᴇʀ ʙᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ.",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_autodel")]])
        )

    elif data == "stg_maintenance":
        _pending.pop(uid, None)
        is_on = await db.get_maintenance()
        status_text = "🔴 ON" if is_on else "🟢 OFF"
        toggle_label = "🟢 Turn OFF" if is_on else "🔴 Turn ON"
        toggle_data  = "stg_maintenance_off" if is_on else "stg_maintenance_on"
        await _edit(query,
            f"<b>🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ</b>\n\n"
            f"<b>sᴛᴀᴛᴜs:</b> {status_text}\n\n"
            f"<i>ᴡʜᴇɴ ᴏɴ — ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ.\n"
            f"ʀᴇɢᴜʟᴀʀ ᴜsᴇʀs ᴡɪʟʟ sᴇᴇ ᴀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴇssᴀɢᴇ.</i>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(toggle_label, callback_data=toggle_data)],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ",    callback_data="stg_back")]
            ])
        )

    elif data == "stg_maintenance_on":
        _pending.pop(uid, None)
        await db.set_maintenance(True)
        await _edit(query,
            "<b>🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ: 🔴 ᴏɴ</b>\n\n"
            "<i>ʙᴏᴛ ɪs ɴᴏᴡ ɪɴ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ. ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ɪᴛ.</i>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 ᴛᴜʀɴ ᴏғғ", callback_data="stg_maintenance_off")],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ",     callback_data="stg_maintenance")]
            ])
        )

    elif data == "stg_maintenance_off":
        _pending.pop(uid, None)
        await db.set_maintenance(False)
        await _edit(query,
            "<b>🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ: 🟢 ᴏғғ</b>\n\n"
            "<i>ʙᴏᴛ ɪs ʙᴀᴄᴋ ᴛᴏ ɴᴏʀᴍᴀʟ. ᴀʟʟ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ.</i>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🔴 ᴛᴜʀɴ ᴏɴ", callback_data="stg_maintenance_on")],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ",    callback_data="stg_maintenance")]
            ])
        )

    # ══════════════════════════════════════════════════════════
    #  SUPPORT LINK PANEL
    # ══════════════════════════════════════════════════════════

    elif data == "stg_support":
        _pending.pop(uid, None)
        current = await get_support_url()
        await _edit(query,
            "<b>🆘 sᴜᴘᴘᴏʀᴛ ʟɪɴᴋ</b>\n\n"
            f"<b>ᴄᴜʀʀᴇɴᴛ:</b> <a href=\"{current}\">{current}</a>\n\n"
            "<i>ᴛʜɪs ɪs ᴛʜᴇ ʟɪɴᴋ ᴜsᴇᴅ ʙʏ ᴀʟʟ <b>sᴜᴘᴘᴏʀᴛ</b> ʙᴜᴛᴛᴏɴs (ᴘᴀʏᴍᴇɴᴛ ʀᴇᴄᴇɪᴘᴛs, "
            "ᴇʀʀᴏʀ ᴍᴇssᴀɢᴇs, ᴇᴛᴄ.).</i>",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✏️ sᴇᴛ ʟɪɴᴋ", callback_data="stg_support_set"),
                    InlineKeyboardButton("❌ ʀᴇsᴇᴛ",     callback_data="stg_support_clear")
                ],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")]
            ])
        )

    elif data == "stg_support_set":
        _pending[uid] = {"action": "support_set", "msg_id": query.message.id, "chat_id": query.message.chat.id}
        await _edit(query,
            "<b>🆘 sᴇᴛ sᴜᴘᴘᴏʀᴛ ʟɪɴᴋ</b>\n\n"
            "📤 sᴇɴᴅ ᴀ ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ʟɪɴᴋ ɴᴏᴡ.\n\n"
            "<b>ᴀᴄᴄᴇᴘᴛᴇᴅ ғᴏʀᴍᴀᴛs:</b>\n"
            "• <code>https://t.me/Iam_addictive</code>\n"
            "• <code>t.me/Iam_addictive</code>\n"
            "• <code>@Iam_addictive</code>\n"
            "• <code>Iam_addictive</code>\n\n"
            "<i>ᴀɴʏ ᴏғ ᴛʜᴇ ᴀʙᴏᴠᴇ ɪs ᴀᴜᴛᴏ-ᴄᴏɴᴠᴇʀᴛᴇᴅ ɪɴᴛᴏ ᴀ ғᴜʟʟ <code>https://t.me/...</code> ʟɪɴᴋ.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="stg_support")]])
        )

    elif data == "stg_support_clear":
        _pending.pop(uid, None)
        await db.set_support_link(None)
        fallback = await get_support_url()
        await _edit(query,
            "<b>✅ sᴜᴘᴘᴏʀᴛ ʟɪɴᴋ ʀᴇsᴇᴛ.</b>\n\n"
            f"<b>ɴᴏᴡ ᴜsɪɴɢ ᴅᴇғᴀᴜʟᴛ:</b> <a href=\"{fallback}\">{fallback}</a>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_support")]])
        )

    raise StopPropagation


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
            await patch("<b>❌ ɪɴᴠᴀʟɪᴅ ɪᴅ. sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴜsᴇʀ ɪᴅ.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_admin")]]))
            raise StopPropagation

        await db.add_admin(target_id)
        await patch(
            f"<b>✅ ᴜsᴇʀ <code>{target_id}</code> ᴀᴅᴅᴇᴅ ᴀs ᴀᴅᴍɪɴ.</b>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ᴀᴅᴅ ᴀɴᴏᴛʜᴇʀ", callback_data="stg_admin_add"),
                 InlineKeyboardButton("🔙 ʙᴀᴄᴋ",        callback_data="stg_admin")]
            ])
        )

    # ── BAN ADD ──────────────────────────────────────────────
    elif action == "ban_add":
        try:
            target_id = int(raw)
        except ValueError:
            await patch("<b>❌ ɪɴᴠᴀʟɪᴅ ɪᴅ. sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴜsᴇʀ ɪᴅ.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_ban")]]))
            raise StopPropagation

        if target_id == OWNER_ID or await db.admin_exist(target_id):
            await patch("<b>⛔ ᴄᴀɴɴᴏᴛ ʙᴀɴ ᴀɴ ᴀᴅᴍɪɴ ᴏʀ ᴏᴡɴᴇʀ.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_ban")]]))
            raise StopPropagation

        await db.add_ban_user(target_id)
        await patch(
            f"<b>✅ ᴜsᴇʀ <code>{target_id}</code> ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ.</b>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🚫 ʙᴀɴ ᴀɴᴏᴛʜᴇʀ", callback_data="stg_ban_add"),
                 InlineKeyboardButton("🔙 ʙᴀᴄᴋ",        callback_data="stg_ban")]
            ])
        )

    # ── BAN REMOVE ───────────────────────────────────────────
    elif action == "ban_remove":
        try:
            target_id = int(raw)
        except ValueError:
            await patch("<b>❌ ɪɴᴠᴀʟɪᴅ ɪᴅ. sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴜsᴇʀ ɪᴅ.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_ban")]]))
            raise StopPropagation

        await db.del_ban_user(target_id)
        await patch(
            f"<b>✅ ᴜsᴇʀ <code>{target_id}</code> ʜᴀs ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ.</b>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ ᴜɴʙᴀɴ ᴀɴᴏᴛʜᴇʀ", callback_data="stg_ban_remove"),
                 InlineKeyboardButton("🔙 ʙᴀᴄᴋ",          callback_data="stg_ban")]
            ])
        )

    # ── FSUB ADD ─────────────────────────────────────────────
    elif action == "fsub_add":
        try:
            ch_id = int(raw)
        except ValueError:
            await patch("<b>❌ ɪɴᴠᴀʟɪᴅ ɪᴅ. sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴄʜᴀɴɴᴇʟ ɪᴅ.</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")]]))
            raise StopPropagation

        existing = await db.show_channels()
        if ch_id in existing:
            await patch(f"<b>⚠️ ᴄʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b> <code>{ch_id}</code>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")]]))
            raise StopPropagation

        try:
            chat = await client.get_chat(ch_id)
            if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                await patch("<b>❌ ᴏɴʟʏ ᴄʜᴀɴɴᴇʟs/sᴜᴘᴇʀɢʀᴏᴜᴘs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>",
                            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")]]))
                raise StopPropagation

            bot_member = await client.get_chat_member(chat.id, "me")
            if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await patch("<b>❌ ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>",
                            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")]]))
                raise StopPropagation

            await db.add_channel(ch_id)
            await patch(
                f"<b>✅ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b>\n\n"
                f"<b>ɴᴀᴍᴇ:</b> {chat.title}\n"
                f"<b>ɪᴅ:</b> <code>{ch_id}</code>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ᴀᴅᴅ ᴀɴᴏᴛʜᴇʀ", callback_data="stg_fsub_add"),
                     InlineKeyboardButton("🔙 ʙᴀᴄᴋ",        callback_data="stg_fsub")]
                ])
            )
        except StopPropagation:
            raise
        except Exception as e:
            await patch(f"<b>❌ ғᴀɪʟᴇᴅ:</b> <code>{e}</code>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_fsub")]]))

    # ── CUSTOM CAPTION SET ───────────────────────────────────
    elif action == "caption_set":
        caption = raw or None
        await db.set_custom_caption(caption)
        if caption:
            msg_txt = f"<b>✅ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ.</b>\n\n<code>{caption}</code>"
        else:
            msg_txt = "<b>✅ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴄʟᴇᴀʀᴇᴅ.</b>"

        await patch(msg_txt,
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ ᴄʜᴀɴɢᴇ", callback_data="stg_caption_set"),
                 InlineKeyboardButton("🔙 ʙᴀᴄᴋ",   callback_data="stg_caption")]
            ])
        )

    # ── AUTO DELETE SET ──────────────────────────────��───────
    elif action == "autodel_set":
        try:
            seconds = int(raw)
        except ValueError:
            await patch("<b>❌ ɪɴᴠᴀʟɪᴅ. sᴇɴᴅ ᴀ ɴᴜᴍʙᴇʀ (sᴇᴄᴏɴᴅs).</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_autodel")]]))
            raise StopPropagation

        await db.set_del_timer(seconds)
        if seconds == 0:
            msg_txt = "<b>✅ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴅɪsᴀʙʟᴇᴅ.</b>"
        else:
            mins = seconds // 60
            secs = seconds % 60
            readable = f"{mins}m {secs}s" if mins else f"{secs}s"
            msg_txt = f"<b>✅ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ sᴇᴛ ᴛᴏ <code>{seconds}s</code> ({readable}).</b>"

        await patch(msg_txt,
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ ᴄʜᴀɴɢᴇ", callback_data="stg_autodel_set"),
                 InlineKeyboardButton("🔙 ʙᴀᴄᴋ",   callback_data="stg_autodel")]
            ])
        )

    # ── SUPPORT LINK SET ─────────────────────────────────────
    elif action == "support_set":
        link = normalize_support_link(raw)
        if not link:
            await patch(
                "<b>❌ ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ.</b>\n\n"
                "sᴇɴᴅ ᴀ ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ᴀ <code>t.me</code> ʟɪɴᴋ.",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_support")]])
            )
            raise StopPropagation

        await db.set_support_link(link)
        await patch(
            f"<b>✅ sᴜᴘᴘᴏʀᴛ ʟɪɴᴋ ᴜᴘᴅᴀᴛᴇᴅ.</b>\n\n"
            f"<b>ɴᴇᴡ:</b> <a href=\"{link}\">{link}</a>",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ ᴄʜᴀɴɢᴇ", callback_data="stg_support_set"),
                 InlineKeyboardButton("🔙 ʙᴀᴄᴋ",   callback_data="stg_support")]
            ])
        )

    # ── FREE LINK CUSTOM SET ─────────────────────────────────
    elif action == "freelink_custom":
        try:
            new_limit = int(raw)
            if new_limit < 1:
                raise ValueError
        except ValueError:
            await patch("<b>❌ ɪɴᴠᴀʟɪᴅ. sᴇɴᴅ ᴀ ᴘᴏsɪᴛɪᴠᴇ ɴᴜᴍʙᴇʀ (ᴇ.ɢ. <code>25</code>).</b>",
                        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_freelink")]]))
            raise StopPropagation

        await db.set_free_link_limit(new_limit)
        enabled = await db.get_free_link_enabled()
        mode_txt = ("ᴀғᴛᴇʀ ғʀᴇᴇ ʟɪɴᴋs, ᴘʀᴇᴍɪᴜᴍ ʀᴇǫᴜɪʀᴇᴅ"
                    if enabled else "ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss — ɴᴏ ᴅᴀɪʟʏ ʟɪᴍɪᴛ")
        await patch(
            f"<b>✅ ғʀᴇᴇ ʟɪɴᴋ ʟɪᴍɪᴛ sᴇᴛ ᴛᴏ <code>{new_limit}</code>/ᴅᴀʏ.</b>\n\n"
            f"<b>sᴛᴀᴛᴜs:</b> {'🟢 ᴏɴ' if enabled else '🔴 ᴏғғ'}\n"
            f"<b>ᴍᴏᴅᴇ:</b> {mode_txt}",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_freelink")]
            ])
        )

    raise StopPropagation
