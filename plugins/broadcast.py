import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__, StopPropagation
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatMemberUpdated, ChatPermissions, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, InviteHashEmpty, ChatAdminRequired, PeerIdInvalid, UserIsBlocked, InputUserDeactivated
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from pytz import timezone

REPLY_ERROR = "<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴀs ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇssᴀɢᴇ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ sᴘᴀᴄᴇs.</b>"
WAIT_MSG = "<b>ᴡᴏʀᴋɪɴɢ....</b>"


@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="close")]])
    await message.reply(text=CMD_TXT, reply_markup=reply_markup, quote=True)


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

        pls_wait = await message.reply("<b><i>ʙʀᴏᴀᴅᴄᴀsᴛ ᴘʀᴏᴄᴇssɪɴɢ....</i></b>")
        for chat_id in query:
            try:
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

        status = (
            f"<b><u>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>\n\n"
            f"<b>ᴛᴏᴛᴀʟ ᴜsᴇʀs:</b> <code>{total}</code>\n"
            f"<b>sᴜᴄᴄᴇssғᴜʟ:</b> <code>{successful}</code>\n"
            f"<b>ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs:</b> <code>{blocked}</code>\n"
            f"<b>ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs:</b> <code>{deleted}</code>\n"
            f"<b>ᴜɴsᴜᴄᴄᴇssғᴜʟ:</b> <code>{unsuccessful}</code>"
        )
        return await pls_wait.edit(status)
    else:
        msg = await message.reply("<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ᴀɴᴅ ᴘɪɴ ɪᴛ.</b>")
        await asyncio.sleep(8)
        await msg.delete()


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

        pls_wait = await message.reply("<b><i>ʙʀᴏᴀᴅᴄᴀsᴛ ᴘʀᴏᴄᴇssɪɴɢ....</i></b>")
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
            total += 1

        status = (
            f"<b><u>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>\n\n"
            f"<b>ᴛᴏᴛᴀʟ ᴜsᴇʀs:</b> <code>{total}</code>\n"
            f"<b>sᴜᴄᴄᴇssғᴜʟ:</b> <code>{successful}</code>\n"
            f"<b>ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs:</b> <code>{blocked}</code>\n"
            f"<b>ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs:</b> <code>{deleted}</code>\n"
            f"<b>ᴜɴsᴜᴄᴄᴇssғᴜʟ:</b> <code>{unsuccessful}</code>"
        )
        return await pls_wait.edit(status)
    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()


@Bot.on_message(filters.private & filters.command('dbroadcast') & admin)
async def delete_broadcast(client: Bot, message: Message):
    if message.reply_to_message:
        try:
            duration = int(message.command[1])
        except (IndexError, ValueError):
            await message.reply(
                f"<b>ᴘʟᴇᴀsᴇ ᴜsᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b>\n"
                f"<b>ᴜsᴀɢᴇ:</b> /dbroadcast {{duration}}"
            )
            return

        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<b><i>ʙʀᴏᴀᴅᴄᴀsᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴘʀᴏᴄᴇssɪɴɢ....</i></b>")
        for chat_id in query:
            try:
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
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
            total += 1

        status = (
            f"<b><u>ʙʀᴏᴀᴅᴄᴀsᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>\n\n"
            f"<b>ᴛᴏᴛᴀʟ ᴜsᴇʀs:</b> <code>{total}</code>\n"
            f"<b>sᴜᴄᴄᴇssғᴜʟ:</b> <code>{successful}</code>\n"
            f"<b>ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs:</b> <code>{blocked}</code>\n"
            f"<b>ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs:</b> <code>{deleted}</code>\n"
            f"<b>ᴜɴsᴜᴄᴄᴇssғᴜʟ:</b> <code>{unsuccessful}</code>"
        )
        return await pls_wait.edit(status)
    else:
        msg = await message.reply("<b>ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ.</b>")
        await asyncio.sleep(8)
        await msg.delete()
