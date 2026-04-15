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

BAN_SUPPORT = f"{BAN_SUPPORT}"
TUT_VID = f"{TUT_VID}"

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    id = message.from_user.id
    is_premium = await is_premium_user(id)

    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    if not await is_subscribed(client, user_id):
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

    FILE_AUTO_DELETE = await db.get_del_timer()

    text = message.text
    if len(text) > 7:
        verify_status = await db.get_verify_status(id)

        if SHORTLINK_URL or SHORTLINK_API:
            if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
                await db.update_verify_status(user_id, is_verified=False)

            if "verify_" in message.text:
                _, token = message.text.split("_", 1)
                if verify_status['verify_token'] != token:
                    return await message.reply_photo(
                        photo=PREMIUM_PIC,
                        caption="<b>⚠️ 𝖨𝗇𝗏𝖺𝗅𝗂𝖽 𝗍𝗈𝗄𝖾𝗇. 𝖯𝗅𝖾𝖺𝗌𝖾 /start 𝖺𝗀𝖺𝗂𝗇.</b>"
                    )

                await db.update_verify_status(id, is_verified=True, verified_time=time.time())
                current = await db.get_verify_count(id)
                await db.set_verify_count(id, current + 1)
                return await message.reply_photo(
                    photo=PREMIUM_PIC,
                    caption=f"<b>✅ 𝗧𝗼𝗸𝗲𝗻 𝘃𝗲𝗿𝗶𝗳𝗶𝗲𝗱! Vᴀʟɪᴅ ғᴏʀ {get_exp_time(VERIFY_EXPIRE)}</b>"
                )

            if not verify_status['is_verified'] and not is_premium:
                token = ''.join(random.choices(rohit.ascii_letters + rohit.digits, k=10))
                await db.update_verify_status(id, verify_token=token, link="")
                link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{client.username}?start=verify_{token}')
                btn = [
                    [InlineKeyboardButton("• ᴏᴘᴇɴ ʟɪɴᴋ •", url=link),
                     InlineKeyboardButton("• ᴛᴜᴛᴏʀɪᴀʟ •", url=TUT_VID)],
                    [InlineKeyboardButton("• ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", callback_data="premium")]
                ]
                return await message.reply_photo(
                    photo=PREMIUM_PIC,
                    caption=(
                        f"<b>𝗬𝗼𝘂𝗿 𝘁𝗼𝗸𝗲𝗻 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝗿𝗲𝗳𝗿𝗲𝘀𝗵 𝘆𝗼𝘂𝗿 𝘁𝗼𝗸𝗲𝗻 𝘁𝗼 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗲..</b>\n\n"
                        f"<b>Tᴏᴋᴇɴ Tɪᴍᴇᴏᴜᴛ:</b> {get_exp_time(VERIFY_EXPIRE)}\n\n"
                        f"<b>ᴡʜᴀᴛ ɪs ᴛʜᴇ ᴛᴏᴋᴇɴ??</b>\n\n"
                        f"<b>ᴛʜɪs ɪs ᴀɴ ᴀᴅs ᴛᴏᴋᴇɴ. ᴘᴀssɪɴɢ ᴏɴᴇ ᴀᴅ ᴀʟʟᴏᴡs ʏᴏᴜ ᴛᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ ғᴏʀ {get_exp_time(VERIFY_EXPIRE)} ᴀғᴛᴇʀ ᴛʜᴇ ᴛᴏᴋᴇɴ ɢᴇᴛs ᴇxᴘɪʀᴇᴅ ᴀɢᴀɪɴ ᴛʜᴇ ᴀᴅ ᴛᴏᴋᴇɴ ɪs ʀᴇǫᴜɪʀᴇᴅ.</b>\n\n"
                        f"<blockquote><b>ᴛᴏ ᴀᴠᴏɪᴅᴇ ᴛᴏᴋᴇɴ ᴛᴀᴋᴇ ᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ.</b></blockquote>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn)
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

        temp_msg = await message.reply("<b>Please wait...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong!")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        yaemiko_msgs = []
        for msg in messages:
            caption = (CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, 
                                             filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                yaemiko_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
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
            InlineKeyboardButton("𝗔𝗯𝗼𝘂𝘁", callback_data="about"),
            InlineKeyboardButton("𝗛𝗲𝗹𝗽", callback_data="help")
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
    temp = await message.reply("<b><i>Checking Subscription...</i></b>")

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
                        # Join request link — sirf request send karna kaafi hai
                        try:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                creates_join_request=True
                            )
                            link = invite.invite_link
                        except Exception:
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
        await temp.edit(f"An error occurred: {e}")

    await temp.delete()


#=====================================================================================##
