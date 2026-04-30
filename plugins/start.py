import asyncio
import os
import sys
import re
import time
from datetime import datetime
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from database.db_premium import *

# Fallback: if BAN_SUPPORT is not configured, point to OWNER's profile so the
# "Contact Support" button is always a valid URL.
if not BAN_SUPPORT or str(BAN_SUPPORT).strip().lower() in ("none", ""):
    BAN_SUPPORT = f"https://t.me/{OWNER}" if OWNER else "https://t.me/"
else:
    BAN_SUPPORT = str(BAN_SUPPORT)


@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    id = message.from_user.id
    tier = await get_premium_tier(id)

    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except Exception as ex:
            print(f"add_user failed for {user_id}: {ex}")

    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        # Prefer the admin-configured support link; fall back to BAN_SUPPORT.
        _ban_support = await get_support_url(BAN_SUPPORT)
        return await message.reply_text(
            "<b>⛔️ ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.</b>\n\n"
            "<i>ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ɪғ ʏᴏᴜ ᴛʜɪɴᴋ ᴛʜɪs ɪs ᴀ ᴍɪsᴛᴀᴋᴇ.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ", url=_ban_support)]]
            )
        )

    # Maintenance mode check — block non-admins
    if await db.get_maintenance():
        admins = await db.get_all_admins()
        if user_id not in admins and user_id != OWNER_ID:
            return await message.reply_text(
                "<b>🔧 ʙᴏᴛ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ.</b>\n\n"
                "<i>ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.</i>"
            )

    FILE_AUTO_DELETE = await db.get_del_timer()

    text = message.text
    if len(text) > 7:
        is_admin = await db.admin_exist(id)

        # ── Access gate: free daily link count → premium after limit ─────────────
        # If the Free Link system is OFF, skip the gate entirely — everyone
        # gets unrestricted access to content.
        free_link_enabled = await db.get_free_link_enabled()
        if free_link_enabled and tier is None and id != OWNER_ID and not is_admin:
            free_limit = await db.get_free_link_limit()
            daily_count = await db.get_user_daily_links(id)

            if daily_count < free_limit:
                # Free link available — increment count and allow through
                await db.increment_user_daily_links(id)
            else:
                # Free links exhausted — premium required
                return await message.reply_photo(
                    photo=PREMIUM_PIC,
                    caption=(
                        f"<b>🔒 ʏᴏᴜʀ {free_limit} ғʀᴇᴇ ᴅᴀɪʟʏ ʟɪɴᴋs ʜᴀᴠᴇ ʙᴇᴇɴ ᴜsᴇᴅ!</b>\n\n"
                        f"<b>ᴅᴀɪʟʏ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ. ᴄᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏᴍᴏʀʀᴏᴡ ғᴏʀ {free_limit} ᴍᴏʀᴇ ғʀᴇᴇ ʟɪɴᴋs.</b>\n\n"
                        f"<b>ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ ғᴏʀ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss ᴡɪᴛʜ ɴᴏ ᴅᴀɪʟʏ ʀᴇsᴛʀɪᴄᴛɪᴏɴs!</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("• ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", callback_data="premium")]
                    ])
                )

        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return

        string = await decode(base64_string)
        argument = string.split("-")

        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return

        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return

        temp_msg = await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("<b>sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ!</b>")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        # Defensive: even though get_messages already filters out empty
        # messages, double-check here so a single bad message can never
        # spam the log with "Empty messages cannot be copied." warnings.
        messages = [m for m in messages if m and not getattr(m, "empty", False)]

        if not messages:
            return await message.reply_text(
                "<b>⚠️ ᴛʜᴇsᴇ ғɪʟᴇs ᴀʀᴇ ɴᴏ ʟᴏɴɢᴇʀ ᴀᴠᴀɪʟᴀʙʟᴇ. ᴘʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ.</b>"
            )

        yaemiko_msgs = []
        custom_caption = await db.get_custom_caption()
        protect_content = False if tier == "gold" else await db.get_protect_content()
        for msg in messages:
            # Skip any message that slipped through as empty / deleted.
            if not msg or getattr(msg, "empty", False):
                continue

            caption = (custom_caption.format(previouscaption="" if not msg.caption else msg.caption.html,
                                             filename=msg.document.file_name) if bool(custom_caption) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=protect_content)
                if copied_msg:
                    yaemiko_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML,
                                                reply_markup=reply_markup, protect_content=protect_content)
                    if copied_msg:
                        yaemiko_msgs.append(copied_msg)
                except Exception as e2:
                    print(f"Failed to send message after FloodWait: {e2}")
            except Exception as e:
                print(f"Failed to send message: {e}")
                pass

        if FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"<b>ᴛʜɪs ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ  {get_exp_time(FILE_AUTO_DELETE)}. ᴘʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs ᴅᴇʟᴇᴛᴇᴅ.</b>"
            )

            await asyncio.sleep(FILE_AUTO_DELETE)

            for snt_msg in yaemiko_msgs:    
                if snt_msg:
                    try:    
                        await snt_msg.delete()  
                    except Exception as e:
                        print(f"Error deleting message {snt_msg.id}: {e}")

            try:
                reload_url = (
                    f"https://t.me/{client.username}?start={message.command[1]}"
                    if message.command and len(message.command) > 1
                    else None
                )
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)]]
                ) if reload_url else None

                await notification_msg.edit(
                    "<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error updating notification with 'Get File Again' button: {e}")
    else:
        reply_markup = InlineKeyboardMarkup(
    [
        
        [
            InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="about"),
            InlineKeyboardButton("ʜᴇʟᴘ", callback_data="help")
        ]
    ]
)

        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup
            ) 

        return

chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    temp = await message.reply("<b><i>ᴄʜᴇᴄᴋɪɴɢ sᴜʙsᴄʀɪᴘᴛɪᴏɴ...</i></b>")

    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        all_channels = await db.show_channels()
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)

            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                try:
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    if mode == "on":
                        link = await db.get_request_link(chat_id)
                        try:
                            if not link:
                                invite = await client.create_chat_invite_link(
                                    chat_id=chat_id,
                                    creates_join_request=True
                                )
                                link = invite.invite_link
                                await db.set_request_link(chat_id, link)
                        except Exception:
                            if not link:
                                link = data.invite_link or await client.export_chat_invite_link(chat_id)

                    else:
                        # Direct join link
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            try:
                                link = data.invite_link or await client.export_chat_invite_link(chat_id)
                            except Exception:
                                invite = await client.create_chat_invite_link(chat_id=chat_id)
                                link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b>{'! ' * count}</b>")

                except Exception as e:
                    print(f"Error with chat {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>! ᴇʀʀᴏʀ, ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @ʀᴏʜɪᴛ_1888</i></b>\n"
                        f"<blockquote expandable><b>ʀᴇᴀsᴏɴ:</b> {e}</blockquote>"
                    )

        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ ᴛʀʏ ᴀɢᴀɪɴ',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except IndexError:
            pass

        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        print(f"Error in not_joined: {e}")
        await temp.edit(f"<b>ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {e}</b>")

    await temp.delete()


#=====================================================================================##
