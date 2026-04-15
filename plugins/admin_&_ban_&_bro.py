import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatMemberUpdated, ChatPermissions, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, InviteHashEmpty, ChatAdminRequired, PeerIdInvalid, UserIsBlocked, InputUserDeactivated
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from pytz import timezone

#=====================================================================================##

REPLY_ERROR = "<code>Use this command as a reply to any telegram message without any spaces.</code>"

WAIT_MSG = "<b>Working....</b>"

#=====================================================================================##

@Bot.on_message(filters.command('stats') & admin)
async def stats(bot: Bot, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    time = get_readable_time(delta.seconds)
    await message.reply(BOT_STATS_TEXT.format(uptime=time))

#=====================================================================================##

@Bot.on_message(filters.command('users') & filters.private & admin)
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await db.full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

#=====================================================================================##

#AUTO-DELETE

@Bot.on_message(filters.private & filters.command('dlt_time') & admin)
async def set_delete_time(client: Bot, message: Message):
    try:
        duration = int(message.command[1])

        await db.set_del_timer(duration)

        await message.reply(f"<b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ <blockquote>{duration} sᴇᴄᴏɴᴅs.</blockquote></b>")

    except (IndexError, ValueError):
        await message.reply("<b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b> Usage: /dlt_time {duration}")

@Bot.on_message(filters.private & filters.command('check_dlt_time') & admin)
async def check_delete_time(client: Bot, message: Message):
    duration = await db.get_del_timer()

    await message.reply(f"<b><blockquote>Cᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ ɪs sᴇᴛ ᴛᴏ {duration}sᴇᴄᴏɴᴅs.</blockquote></b>")

#=====================================================================================##

@Bot.on_message(filters.command("count") & filters.private & admin)
async def total_verify_count_cmd(client, message: Message):
    total = await db.get_total_verify_count()
    await message.reply_text(f"Tᴏᴛᴀʟ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴋᴇɴs ᴛᴏᴅᴀʏ: <b>{total}</b>")

#=====================================================================================##

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):        
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data = "close")]])
    await message.reply(text=CMD_TXT, reply_markup = reply_markup, quote= True)

#=====================================================================================##

# BROADCAST COMMANDS

@Bot.on_message(filters.private & filters.command('pbroadcast') & admin)
async def send_pin_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")
        for chat_id in query:
            try:
                # Send and pin the message
                sent_msg = await broadcast_msg.copy(chat_id)
                await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_msg = await broadcast_msg.copy(chat_id)
                await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except Exception as e:
                print(f"Failed to send or pin message to {chat_id}: {e}")
                unsuccessful += 1
            total += 1

        status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply("Reply to a message to broadcast and pin it.")
        await asyncio.sleep(8)
        await msg.delete()

#=====================================================================================##

@Bot.on_message(filters.private & filters.command('broadcast') & admin)
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ...</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

#=====================================================================================##

@Bot.on_message(filters.private & filters.command('dbroadcast') & admin)
async def delete_broadcast(client: Bot, message: Message):
    if message.reply_to_message:
        try:
            duration = int(message.command[1])  # Get the duration in seconds
        except (IndexError, ValueError):
            await message.reply("<b>Pʟᴇᴀsᴇ ᴜsᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b> Usᴀɢᴇ: /dbroadcast {duration}")
            return

        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcast with auto-delete processing....</i>")
        for chat_id in query:
            try:
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)  # Wait for the specified duration
                await sent_msg.delete()  # Delete the message after the duration
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴡɪᴛʜ Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ...</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply("Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ ᴡɪᴛʜ Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ.")
        await asyncio.sleep(8)
        await msg.delete()

#=====================================================================================##

#BAN-USER-SYSTEM
@Bot.on_message(filters.private & filters.command('ban') & admin)
async def add_banuser(client: Client, message: Message):        
    pro = await message.reply("⏳ <i>Pʀᴏᴄᴇssɪɴɢ ʀᴇǫᴜᴇsᴛ...</i>", quote=True)
    banuser_ids = await db.get_ban_users()
    banusers = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]])

    if not banusers:
        return await pro.edit(
            "<b>❗ Yᴏᴜ ᴍᴜsᴛ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ IDs ᴛᴏ ʙᴀɴ.</b>\n\n"
            "<b>📌 Usᴀɢᴇ:</b>\n"
            "<code>/ban [user_id]</code> — Ban one or more users by ID.",
            reply_markup=reply_markup
        )

    report, success_count = "", 0
    for uid in banusers:
        try:
            uid_int = int(uid)
        except:
            report += f"⚠️ Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code>\n"
            continue

        if uid_int in await db.get_all_admins() or uid_int == OWNER_ID:
            report += f"⛔ Sᴋɪᴘᴘᴇᴅ ᴀᴅᴍɪɴ/ᴏᴡɴᴇʀ ID: <code>{uid_int}</code>\n"
            continue

        if uid_int in banuser_ids:
            report += f"⚠️ Aʟʀᴇᴀᴅʏ : <code>{uid_int}</code>\n"
            continue

        if len(str(uid_int)) == 10:
            await db.add_ban_user(uid_int)
            report += f"✅ Bᴀɴɴᴇᴅ: <code>{uid_int}</code>\n"
            success_count += 1
        else:
            report += f"⚠️ Invalid Telegram ID length: <code>{uid_int}</code>\n"

    if success_count:
        await pro.edit(f"<b>✅ Bᴀɴɴᴇᴅ Usᴇʀs Uᴘᴅᴀᴛᴇᴅ:</b>\n\n{report}", reply_markup=reply_markup)
    else:
        await pro.edit(f"<b>❌ Nᴏ ᴜsᴇʀs ᴡᴇʀᴇ ʙᴀɴɴᴇᴅ.</b>\n\n{report}", reply_markup=reply_markup)

@Bot.on_message(filters.private & filters.command('unban') & admin)
async def delete_banuser(client: Client, message: Message):        
    pro = await message.reply("⏳ <i>Pʀᴏᴄᴇssɪɴɢ ʀᴇǫᴜᴇsᴛ...</i>", quote=True)
    banuser_ids = await db.get_ban_users()
    banusers = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]])

    if not banusers:
        return await pro.edit(
            "<b>❗ Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ IDs ᴛᴏ ᴜɴʙᴀɴ.</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/unban [user_id]</code> — Unban specific user(s)\n"
            "<code>/unban all</code> — Remove all banned users",
            reply_markup=reply_markup
        )

    if banusers[0].lower() == "all":
        if not banuser_ids:
            return await pro.edit("<b>✅ NO ᴜsᴇʀs ɪɴ ᴛʜᴇ ʙᴀɴ ʟɪsᴛ.</b>", reply_markup=reply_markup)
        for uid in banuser_ids:
            await db.del_ban_user(uid)
        listed = "\n".join([f"✅ Uɴʙᴀɴɴᴇᴅ: <code>{uid}</code>" for uid in banuser_ids])
        return await pro.edit(f"<b>🚫 Cʟᴇᴀʀᴇᴅ Bᴀɴ Lɪsᴛ:</b>\n\n{listed}", reply_markup=reply_markup)

    report = ""
    for uid in banusers:
        try:
            uid_int = int(uid)
        except:
            report += f"⚠️ Iɴᴀᴠʟɪᴅ ID: <code>{uid}</code>\n"
            continue

        if uid_int in banuser_ids:
            await db.del_ban_user(uid_int)
            report += f"✅ Uɴʙᴀɴɴᴇᴅ: <code>{uid_int}</code>\n"
        else:
            report += f"⚠️ Nᴏᴛ ɪɴ ʙᴀɴ ʟɪsᴛ: <code>{uid_int}</code>\n"

    await pro.edit(f"<b>🚫 Uɴʙᴀɴ Rᴇᴘᴏʀᴛ:</b>\n\n{report}", reply_markup=reply_markup)

@Bot.on_message(filters.private & filters.command('banlist') & admin)
async def get_banuser_list(client: Client, message: Message):        
    banuser_ids = await db.get_ban_users()
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]])

    if not banuser_ids:
        return await message.reply("<b>✅ Nᴏ ᴜsᴇʀs ᴀʀᴇ ᴄᴜʀʀᴇɴᴛʟʏ ʙᴀɴɴᴇᴅ.</b>", reply_markup=reply_markup)

    listed = "\n".join([f"• <code>{uid}</code>" for uid in banuser_ids])
    await message.reply(f"<b>🚫 Bᴀɴɴᴇᴅ Usᴇʀs ({len(banuser_ids)}):</b>\n\n{listed}", reply_markup=reply_markup)

#=====================================================================================##

# ADMIN MANAGEMENT

@Bot.on_message(filters.private & filters.command('add_admin') & admin)
async def add_admin_user(client: Client, message: Message):
    admins = message.text.split()[1:]
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]])

    if not admins:
        return await message.reply(
            "<b>❗ Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ IDs ᴛᴏ ᴀᴅᴅ ᴀs ᴀᴅᴍɪɴs.</b>\n\n"
            "<b>📌 Usᴀɢᴇ:</b>\n"
            "<code>/add_admin [user_id]</code>",
            reply_markup=reply_markup
        )

    report = ""
    for uid in admins:
        try:
            uid_int = int(uid)
            if await db.admin_exist(uid_int):
                report += f"⚠️ Aʟʀᴇᴀᴅʏ ᴀᴅᴍɪɴ: <code>{uid_int}</code>\n"
            else:
                await db.add_admin(uid_int)
                report += f"✅ Aᴅᴅᴇᴅ ᴀᴅᴍɪɴ: <code>{uid_int}</code>\n"
        except ValueError:
            report += f"⚠️ Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code>\n"

    await message.reply(f"<b>👑 Aᴅᴍɪɴ Uᴘᴅᴀᴛᴇ Rᴇᴘᴏʀᴛ:</b>\n\n{report}", reply_markup=reply_markup)

@Bot.on_message(filters.private & filters.command('deladmin') & admin)
async def del_admin_user(client: Client, message: Message):
    admins = message.text.split()[1:]
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]])

    if not admins:
        return await message.reply(
            "<b>❗ Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ IDs ᴛᴏ ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ᴀᴅᴍɪɴs.</b>\n\n"
            "<b>📌 Usᴀɢᴇ:</b>\n"
            "<code>/deladmin [user_id]</code>",
            reply_markup=reply_markup
        )

    report = ""
    for uid in admins:
        try:
            uid_int = int(uid)
            if uid_int == OWNER_ID:
                report += f"⛔ Cᴀɴɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴏᴡɴᴇʀ: <code>{uid_int}</code>\n"
            elif await db.admin_exist(uid_int):
                await db.del_admin(uid_int)
                report += f"✅ Rᴇᴍᴏᴠᴇᴅ ᴀᴅᴍɪɴ: <code>{uid_int}</code>\n"
            else:
                report += f"⚠️ Nᴏᴛ ᴀɴ ᴀᴅᴍɪɴ: <code>{uid_int}</code>\n"
        except ValueError:
            report += f"⚠️ Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code>\n"

    await message.reply(f"<b>👑 Aᴅᴍɪɴ Rᴇᴍᴏᴠᴀʟ Rᴇᴘᴏʀᴛ:</b>\n\n{report}", reply_markup=reply_markup)

@Bot.on_message(filters.private & filters.command('admins') & admin)
async def get_admin_list(client: Client, message: Message):
    admin_ids = await db.get_all_admins()
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]])

    if not admin_ids:
        return await message.reply("<b>✅ Nᴏ ᴀᴅᴍɪɴs ғᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ.</b>", reply_markup=reply_markup)

    admin_list = [f"• <code>{OWNER_ID}</code> (Owner)"]
    admin_list.extend([f"• <code>{uid}</code>" for uid in admin_ids])
    
    listed = "\n".join(admin_list)
    await message.reply(f"<b>👑 Aᴅᴍɪɴs ({len(admin_list)}):</b>\n\n{listed}", reply_markup=reply_markup)


# =====================================================================================##
# SETTINGS PANEL CALLBACKS
# =====================================================================================##

@Bot.on_callback_query(filters.regex(r"^stg_"))
async def settings_cb(client: Bot, query: CallbackQuery):
    data = query.data

    async def edit(caption, markup):
        try:
            await query.message.edit_caption(caption=caption, reply_markup=markup)
        except Exception:
            pass

    BACK_ADMIN = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_admin")]])
    BACK_BAN   = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="stg_ban")]])
    MAIN_MARKUP = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Admin", callback_data="stg_admin"),
            InlineKeyboardButton("🚫 Ban Users", callback_data="stg_ban")
        ]
    ])
    ADMIN_MARKUP = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add", callback_data="stg_admin_add"),
            InlineKeyboardButton("➖ Remove", callback_data="stg_admin_remove"),
            InlineKeyboardButton("📋 List", callback_data="stg_admin_list")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
    ])
    BAN_MARKUP = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add", callback_data="stg_ban_add"),
            InlineKeyboardButton("➖ Remove", callback_data="stg_ban_remove"),
            InlineKeyboardButton("📋 List", callback_data="stg_ban_list")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
    ])

    # ── MAIN BACK ──────────────────────────────────────────────────
    if data == "stg_back":
        await edit(
            "<b>⚙️ Settings Panel</b>\n\nSelect a category to manage:",
            MAIN_MARKUP
        )

    # ── ADMIN SUBMENU ──────────────────────────────────────────────
    elif data == "stg_admin":
        await edit("<b>👑 Admin Management</b>\n\nChoose an action:", ADMIN_MARKUP)

    elif data == "stg_admin_add":
        await edit(
            "<b>➕ Add Admin</b>\n\n📤 Send the <b>User ID</b> of the user to add as admin:\n\n<i>You have 60 seconds.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_admin")]])
        )
        try:
            resp = await client.ask(
                chat_id=query.message.chat.id,
                text="",
                filters=filters.text & filters.private,
                timeout=60
            )
            try:
                admin_id = int(resp.text.strip())
            except ValueError:
                await resp.delete()
                await edit("<b>❌ Invalid ID. Must be a numeric User ID.</b>", BACK_ADMIN)
                return
            await db.add_admin(admin_id)
            await resp.delete()
            await edit(
                f"<b>✅ User <code>{admin_id}</code> added as Admin successfully.</b>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Another", callback_data="stg_admin_add"),
                     InlineKeyboardButton("🔙 Back", callback_data="stg_admin")]
                ])
            )
        except Exception:
            await edit("<b>⏰ Timed out. No input received.</b>", BACK_ADMIN)

    elif data == "stg_admin_remove":
        admins = await db.get_all_admins()
        if not admins:
            await edit("<b>📋 No admins found to remove.</b>", BACK_ADMIN)
            return
        buttons = []
        for aid in admins:
            try:
                user = await client.get_users(aid)
                label = f"❌ {user.first_name} ({aid})"
            except Exception:
                label = f"❌ {aid}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"stg_deladmin_{aid}")])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="stg_admin")])
        await edit("<b>➖ Remove Admin</b>\n\nTap an admin to remove them:", InlineKeyboardMarkup(buttons))

    elif data.startswith("stg_deladmin_"):
        aid = int(data.replace("stg_deladmin_", ""))
        await db.del_admin(aid)
        await edit(
            f"<b>✅ Admin <code>{aid}</code> has been removed.</b>",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data="stg_admin")]])
        )

    elif data == "stg_admin_list":
        admins = await db.get_all_admins()
        if not admins:
            text = "<b>📋 Admin List is empty.</b>"
        else:
            lines = "\n".join([f"• <code>{aid}</code>" for aid in admins])
            text = f"<b>📋 Admins ({len(admins)}):</b>\n\n{lines}"
        await edit(text, BACK_ADMIN)

    # ── BAN SUBMENU ────────────────────────────────────────────────
    elif data == "stg_ban":
        await edit("<b>🚫 Ban Management</b>\n\nChoose an action:", BAN_MARKUP)

    elif data == "stg_ban_add":
        await edit(
            "<b>🚫 Ban User</b>\n\n📤 Send the <b>User ID</b> to ban:\n\n<i>You have 60 seconds.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_ban")]])
        )
        try:
            resp = await client.ask(
                chat_id=query.message.chat.id,
                text="",
                filters=filters.text & filters.private,
                timeout=60
            )
            try:
                uid = int(resp.text.strip())
            except ValueError:
                await resp.delete()
                await edit("<b>❌ Invalid ID. Must be a numeric User ID.</b>", BACK_BAN)
                return
            if uid == OWNER_ID or uid in await db.get_all_admins():
                await resp.delete()
                await edit("<b>⛔ Cannot ban an admin or owner.</b>", BACK_BAN)
                return
            await db.add_ban_user(uid)
            await resp.delete()
            await edit(
                f"<b>✅ User <code>{uid}</code> has been banned.</b>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Ban Another", callback_data="stg_ban_add"),
                     InlineKeyboardButton("🔙 Back", callback_data="stg_ban")]
                ])
            )
        except Exception:
            await edit("<b>⏰ Timed out. No input received.</b>", BACK_BAN)

    elif data == "stg_ban_remove":
        await edit(
            "<b>➖ Unban User</b>\n\n📤 Send the <b>User ID</b> to unban:\n\n<i>You have 60 seconds.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="stg_ban")]])
        )
        try:
            resp = await client.ask(
                chat_id=query.message.chat.id,
                text="",
                filters=filters.text & filters.private,
                timeout=60
            )
            try:
                uid = int(resp.text.strip())
            except ValueError:
                await resp.delete()
                await edit("<b>❌ Invalid ID. Must be a numeric User ID.</b>", BACK_BAN)
                return
            await db.del_ban_user(uid)
            await resp.delete()
            await edit(
                f"<b>✅ User <code>{uid}</code> has been unbanned.</b>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("➖ Unban Another", callback_data="stg_ban_remove"),
                     InlineKeyboardButton("🔙 Back", callback_data="stg_ban")]
                ])
            )
        except Exception:
            await edit("<b>⏰ Timed out. No input received.</b>", BACK_BAN)

    elif data == "stg_ban_list":
        banned = await db.get_ban_users()
        if not banned:
            text = "<b>📋 No banned users.</b>"
        else:
            lines = "\n".join([f"• <code>{uid}</code>" for uid in banned])
            text = f"<b>🚫 Banned Users ({len(banned)}):</b>\n\n{lines}"
        await edit(text, BACK_BAN)
