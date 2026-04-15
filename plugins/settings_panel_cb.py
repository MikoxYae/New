import asyncio
import psutil
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ChatType
from bot import Bot
from database.database import db


# ─── SETTINGS BACK ────────────────────────────────────────────────────────────

def settings_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Admin", callback_data="stg_admin"),
            InlineKeyboardButton("🚫 Ban Users", callback_data="stg_ban")
        ],
        [
            InlineKeyboardButton("👥 Users", callback_data="stg_users"),
            InlineKeyboardButton("📊 Stats", callback_data="stg_stats")
        ],
        [
            InlineKeyboardButton("📢 Force Sub", callback_data="stg_fsub"),
            InlineKeyboardButton("🔄 Request Mode", callback_data="stg_reqmode")
        ]
    ])


@Bot.on_callback_query(filters.regex(r"^stg_back$"))
async def stg_back_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "<b>⚙️ Settings Panel</b>\n\nSelect a category to manage:",
        reply_markup=settings_markup()
    )


# ─── USERS ────────────────────────────────────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^stg_users$"))
async def stg_users_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    users = await db.full_userbase()
    count = len(users)
    await query.message.edit_text(
        f"<b>👥 Users Info</b>\n\n"
        f"<b>Total Users in DB:</b> <code>{count}</code>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
        ])
    )


# ─── STATS ────────────────────────────────────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^stg_stats$"))
async def stg_stats_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    cpu = psutil.cpu_percent(interval=0.5)

    ram_total = round(ram.total / (1024 ** 3), 2)
    ram_used = round(ram.used / (1024 ** 3), 2)
    ram_free = round(ram.available / (1024 ** 3), 2)
    ram_percent = ram.percent

    disk_total = round(disk.total / (1024 ** 3), 2)
    disk_used = round(disk.used / (1024 ** 3), 2)
    disk_free = round(disk.free / (1024 ** 3), 2)
    disk_percent = disk.percent

    await query.message.edit_text(
        f"<b>📊 System Stats</b>\n\n"
        f"<b>🧠 RAM</b>\n"
        f"├ Total: <code>{ram_total} GB</code>\n"
        f"├ Used: <code>{ram_used} GB ({ram_percent}%)</code>\n"
        f"└ Free: <code>{ram_free} GB</code>\n\n"
        f"<b>💾 Disk</b>\n"
        f"├ Total: <code>{disk_total} GB</code>\n"
        f"├ Used: <code>{disk_used} GB ({disk_percent}%)</code>\n"
        f"└ Free: <code>{disk_free} GB</code>\n\n"
        f"<b>⚙️ CPU Usage:</b> <code>{cpu}%</code>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
        ])
    )


# ─── FORCE SUB PANEL ──────────────────────────────────────────────────────────

def fsub_panel_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add", callback_data="stg_fsub_add"),
            InlineKeyboardButton("➖ Remove", callback_data="stg_fsub_remove"),
            InlineKeyboardButton("📋 List", callback_data="stg_fsub_list")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
    ])


@Bot.on_callback_query(filters.regex(r"^stg_fsub$"))
async def stg_fsub_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "<b>📢 Force Sub Settings</b>\n\nManage your force subscription channels:",
        reply_markup=fsub_panel_markup()
    )


# ─── FORCE SUB: ADD ───────────────────────────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^stg_fsub_add$"))
async def stg_fsub_add_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    msg = await query.message.edit_text(
        "<b>➕ Add Force Sub Channel</b>\n\n"
        "Send the <b>Channel ID</b> (e.g. <code>-100xxxxxxxxxx</code>)\n\n"
        "<i>Send /cancel to go back.</i>"
    )
    try:
        response = await client.listen(query.from_user.id, timeout=60)
    except asyncio.TimeoutError:
        await msg.edit(
            "<b>⏰ Timeout! No input received.</b>",
            reply_markup=fsub_panel_markup()
        )
        return

    if response.text and response.text.strip() == "/cancel":
        try:
            await response.delete()
        except Exception:
            pass
        await msg.edit(
            "<b>📢 Force Sub Settings</b>\n\nManage your force subscription channels:",
            reply_markup=fsub_panel_markup()
        )
        return

    try:
        await response.delete()
    except Exception:
        pass

    try:
        chat_id = int(response.text.strip())
    except (ValueError, AttributeError):
        await msg.edit(
            "<b>❌ Invalid ID! Please send a valid numeric Channel ID.</b>",
            reply_markup=fsub_panel_markup()
        )
        return

    all_chats = await db.show_channels()
    if chat_id in all_chats:
        await msg.edit(
            f"<b>⚠️ Channel already exists:</b> <code>{chat_id}</code>",
            reply_markup=fsub_panel_markup()
        )
        return

    try:
        chat = await client.get_chat(chat_id)
        if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
            await msg.edit(
                "<b>❌ Only channels/supergroups are allowed.</b>",
                reply_markup=fsub_panel_markup()
            )
            return

        bot_member = await client.get_chat_member(chat.id, "me")
        if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await msg.edit(
                "<b>❌ Bot must be an admin in that channel/group.</b>",
                reply_markup=fsub_panel_markup()
            )
            return

        await db.add_channel(chat_id)
        await msg.edit(
            f"<b>✅ Added Successfully!</b>\n\n"
            f"<b>Name:</b> {chat.title}\n"
            f"<b>ID:</b> <code>{chat_id}</code>",
            reply_markup=fsub_panel_markup()
        )

    except Exception as e:
        await msg.edit(
            f"<b>❌ Failed to add channel:</b> <code>{chat_id}</code>\n\n<i>{e}</i>",
            reply_markup=fsub_panel_markup()
        )


# ─── FORCE SUB: REMOVE ────────────────────────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^stg_fsub_remove$"))
async def stg_fsub_remove_cb(client: Bot, query: CallbackQuery):
    await query.answer()
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
    await query.message.edit_text(
        "<b>➖ Select a channel to remove:</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Bot.on_callback_query(filters.regex(r"^stg_fsub_del_-?\d+$"))
async def stg_fsub_del_cb(client: Bot, query: CallbackQuery):
    ch_id = int(query.data.split("stg_fsub_del_")[1])
    await db.rem_channel(ch_id)
    await query.answer("✅ Removed!", show_alert=True)

    channels = await db.show_channels()
    if not channels:
        await query.message.edit_text(
            "<b>📢 Force Sub Settings</b>\n\nManage your force subscription channels:",
            reply_markup=fsub_panel_markup()
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
    await query.message.edit_text(
        "<b>➖ Select a channel to remove:</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ─── FORCE SUB: LIST ──────────────────────────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^stg_fsub_list$"))
async def stg_fsub_list_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    channels = await db.show_channels()
    if not channels:
        await query.message.edit_text(
            "<b>❌ No force-sub channels added yet.</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]
            ])
        )
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

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="stg_fsub")]
        ]),
        disable_web_page_preview=True
    )


# ─── REQUEST MODE ─────────────────────────────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^stg_reqmode$"))
async def stg_reqmode_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    channels = await db.show_channels()
    if not channels:
        await query.message.edit_text(
            "<b>❌ No force-sub channels found.\nAdd channels first via Force Sub.</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
            ])
        )
        return

    buttons = []
    for ch_id in channels:
        try:
            chat = await client.get_chat(ch_id)
            mode = await db.get_channel_mode(ch_id)
            status = "🟢 ON" if mode == "on" else "🔴 OFF"
            buttons.append([InlineKeyboardButton(
                f"{status} — {chat.title}",
                callback_data=f"stg_rq_toggle_{ch_id}"
            )])
        except Exception:
            buttons.append([InlineKeyboardButton(
                f"⚠️ {ch_id}",
                callback_data=f"stg_rq_toggle_{ch_id}"
            )])

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_back")])
    await query.message.edit_text(
        "<b>🔄 Request Mode</b>\n\n"
        "<b>🟢 ON</b>  → Users must send a join request (Request Mode)\n"
        "<b>🔴 OFF</b> → Users join directly (Direct Join)\n\n"
        "<i>Click a channel to toggle its mode:</i>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Bot.on_callback_query(filters.regex(r"^stg_rq_toggle_-?\d+$"))
async def stg_rq_toggle_cb(client: Bot, query: CallbackQuery):
    ch_id = int(query.data.split("stg_rq_toggle_")[1])
    current = await db.get_channel_mode(ch_id)
    new_mode = "off" if current == "on" else "on"
    await db.set_channel_mode(ch_id, new_mode)

    label = "🟢 Request Mode ON" if new_mode == "on" else "🔴 Direct Join (OFF)"
    await query.answer(f"Toggled → {label}", show_alert=True)

    channels = await db.show_channels()
    buttons = []
    for cid in channels:
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ON" if mode == "on" else "🔴 OFF"
            buttons.append([InlineKeyboardButton(
                f"{status} — {chat.title}",
                callback_data=f"stg_rq_toggle_{cid}"
            )])
        except Exception:
            buttons.append([InlineKeyboardButton(
                f"⚠️ {cid}",
                callback_data=f"stg_rq_toggle_{cid}"
            )])

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_back")])
    await query.message.edit_text(
        "<b>🔄 Request Mode</b>\n\n"
        "<b>🟢 ON</b>  → Users must send a join request (Request Mode)\n"
        "<b>🔴 OFF</b> → Users join directly (Direct Join)\n\n"
        "<i>Click a channel to toggle its mode:</i>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
