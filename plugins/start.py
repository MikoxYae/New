import asyncio
import os
import random
import sys
import re
import string 
import string as rohit
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
import config as _cfg

BAN_SUPPORT = f"{BAN_SUPPORT}"

def _is_valid_btn_url(u):
    if not u or not isinstance(u, str):
        return False
    u = u.strip()
    if not u:
        return False
    return bool(re.match(r'^(https?://|tg://|t\\.me/|telegram\\.me/|telegram\\.dog/)', u, re.IGNORECASE))



@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    id = message.from_user.id
    tier = await get_premium_tier(id)

    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    if not await is_subscribed(client, user_id) and tier != "platinum":
        return await not_joined(client, message)

    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>⛔️ You are Bᴀɴɴᴇᴅ from using this bot.</b>\n\n"
            "<i>Contact support if you think this is a mistake.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
            )
        )

    # Maintenance mode check — block non-admins
    if await db.get_maintenance():
        admins = await db.get_all_admins()
        if user_id not in admins and user_id != OWNER_ID:
            return await message.reply_text(
                "<b>🔧 Bot is currently under maintenance.</b>\n\n"
                "<i>Please try again later.</i>"
            )

    FILE_AUTO_DELETE = await db.get_del_timer()

    text = message.text
    if len(text) > 7:
        verify_status = await db.get_verify_status(id)
        is_admin = await db.admin_exist(id)
        shortner_enabled = await db.get_shortner_enabled()

        # ── Handle verify_ token confirmation (shortner must be on + configured) ──
        if _cfg.SHORTLINK_URL or _cfg.SHORTLINK_API:
            if verify_status['is_verified'] and _cfg.VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
                await db.update_verify_status(user_id, is_verified=False)
                verify_status = await db.get_verify_status(id)

            if "verify_" in message.text:
                _, token = message.text.split("_", 1)
                if verify_status['verify_token'] != token:
                    return await message.reply_photo(
                        photo=PREMIUM_PIC,
                        caption="<b>⚠️ 𝖨𝗇𝗏𝖺𝗅𝗂𝖽 𝗍𝗈𝗄𝖾𝗇. 𝖯𝗅𝖾𝖺𝗌𝖾 /start 𝖺𝗀𝖺𝗂𝗇.</b>"
                    )
                # Security: web human verification must be completed before token is accepted
                if not verify_status.get('web_passed'):
                    return await message.reply_photo(
                        photo=PREMIUM_PIC,
                        caption="<b>⚠️ Please open the verification link and complete human verification first.</b>"
                    )
                await db.update_verify_status(id, is_verified=True, verified_time=time.time())
                current = await db.get_verify_count(id)
                await db.set_verify_count(id, current + 1)
                return await message.reply_photo(
                    photo=PREMIUM_PIC,
                    caption=f"<b>✅ 𝗧𝗼𝗸𝗲𝗻 𝘃𝗲𝗿𝗶𝗳𝗶𝗲𝗱! Vᴀʟɪᴅ ғᴏʀ {get_exp_time(_cfg.VERIFY_EXPIRE)}</b>"
                )

        # ── Access gate: free link count → token or premium ──────────────────────
        if tier is None and id != OWNER_ID and not is_admin:
            free_limit = await db.get_free_link_limit()
            daily_count = await db.get_user_daily_links(id)

            if daily_count < free_limit:
                # Free link available — increment count and allow through
                await db.increment_user_daily_links(id)
            else:
                # Free links exhausted
                if shortner_enabled and (_cfg.SHORTLINK_URL or _cfg.SHORTLINK_API):
                    # Mode: Shortner ON — require token after free limit
                    if not verify_status['is_verified']:
                        token = ''.join(random.choices(rohit.ascii_letters + rohit.digits, k=10))
                        direct_tg_link = f'https://telegram.dog/{client.username}?start=verify_{token}'
                        shortlink = await get_shortlink(_cfg.SHORTLINK_URL, _cfg.SHORTLINK_API, direct_tg_link)
                        await db.update_verify_status(id, verify_token=token, link=shortlink, created_at=time.time())
                        if await db.get_anti_bypass() and WEB_VERIFY_BASE_URL:
                            btn_url = get_verify_link(WEB_VERIFY_BASE_URL, id, token, client.username)
                        else:
                            btn_url = shortlink

                        # Validate URLs to avoid Telegram BUTTON_URL_INVALID (400) errors
                        if not _is_valid_btn_url(btn_url):
                            print(f"[start] Invalid verify btn_url={btn_url!r}; aborting token flow")
                            return await message.reply_photo(
                                photo=PREMIUM_PIC,
                                caption=(
                                    "<b>⚠️ Unable to generate your verification link right now.</b>\n\n"
                                    "<i>Please try again in a moment, or contact support.</i>"
                                ),
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("• ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", callback_data="premium")]
                                ])
                            )

                        first_row = [InlineKeyboardButton("• ᴏᴘᴇɴ ʟɪɴᴋ •", url=btn_url)]
                        if _is_valid_btn_url(getattr(_cfg, "TUT_VID", None)):
                            first_row.append(InlineKeyboardButton("• ᴛᴜᴛᴏʀɪᴀʟ •", url=_cfg.TUT_VID))
                        btn = [
                            first_row,
                            [InlineKeyboardButton("• ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", callback_data="premium")]
                        ]
                        return await message.reply_photo(
                            photo=PREMIUM_PIC,
                            caption=(
                                f"<b>🔒 Your {free_limit} free daily links have been used!</b>\n\n"
                                f"<b>Please refresh your token to continue using the bot.</b>\n\n"
                                f"<b>Token Timeout:</b> {get_exp_time(_cfg.VERIFY_EXPIRE)}\n\n"
                                f"<b>This is an ads token. Passing one ad allows you to use the bot until the next day.</b>\n\n"
                                f"<blockquote><b>To skip the token, get our Premium for unlimited access.</b></blockquote>"
                            ),
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                else:
                    # Mode: Shortner OFF — require premium after free limit
                    return await message.reply_photo(
                        photo=PREMIUM_PIC,
                        caption=(
                            f"<b>🔒 Your {free_limit} free daily links have been used!</b>\n\n"
                            f"<b>Daily limit reached. Come back tomorrow for {free_limit} more free links.</b>\n\n"
                            f"<b>Get Premium for unlimited access with no daily restrictions!</b>"
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

        yaemiko_msgs = []
        custom_caption = await db.get_custom_caption()
        protect_content = False if tier in ("gold", "platinum") else await db.get_protect_content()
        for msg in messages:
            caption = (custom_caption.format(previouscaption="" if not msg.caption else msg.caption.html,
                                             filename=msg.document.file_name) if bool(custom_caption) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=protect_content)
                yaemiko_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=protect_content)
                yaemiko_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")
                pass

        if FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"<b>Tʜɪs Fɪʟᴇ ᴡɪʟʟ ʙᴇ Dᴇʟᴇᴛᴇᴅ ɪɴ  {get_exp_time(FILE_AUTO_DELETE)}. Pʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs Dᴇʟᴇᴛᴇᴅ.</b>"
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
                            except:
                                invite = await client.create_chat_invite_link(chat_id=chat_id)
                                link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b>{'! ' * count}</b>")

                except Exception as e:
                    print(f"Error with chat {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @rohit_1888</i></b>\n"
                        f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
                    )

        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
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
