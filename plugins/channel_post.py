import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from pyrogram.errors import FloodWait
from asyncio import TimeoutError

from bot import Bot
from config import *
from helper_func import encode, admin, get_message_id
from database.db_stats import log_activity

_in_custom_batch: set = set()


def not_in_batch_filter(_, __, message: Message) -> bool:
    if message.from_user is None:
        return True
    return message.from_user.id not in _in_custom_batch


not_in_batch = filters.create(not_in_batch_filter)


@Bot.on_message(filters.private & admin & ~filters.command([
    'start', 'commands', 'broadcast', 'batch', 'custom_batch', 'genlink',
    'dbroadcast', 'pbroadcast', 'addpremium', 'premium_users', 'remove_premium',
    'myplan', 'settings', 'peakhours', 'weeklyreport', 'cleanstats', 'start_premium_monitoring'
]))
async def channel_post(client: Client, message: Message):
    if message.from_user and message.from_user.id in _in_custom_batch:
        return
    reply_text = await message.reply_text("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>", quote=True)
    try:
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("<b>sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ!</b>")
        return
    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    custom_message = (
        f"{link}\n\n"
        f"<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ: <a href=\"https://t.me/Base_Angle\">ᴀɴɢʟᴇ ʙᴀsᴇ</a>\n\n"
        f"ɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"
    )
    await reply_text.edit(custom_message, disable_web_page_preview=True)

    try:
        await log_activity(message.from_user.id)
    except Exception:
        pass

    if not DISABLE_CHANNEL_BUTTON:
        try:
            await post_message.edit_reply_markup(None)
        except Exception:
            pass


@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(
                text="<b>ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..\n\nᴏʀ sᴇɴᴅ ᴛʜᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ʟɪɴᴋ</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply(
                "<b>❌ ᴇʀʀᴏʀ\n\nᴛʜɪs ғᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴏʀ ᴛʜɪs ʟɪɴᴋ ɪs ɴᴏᴛ ᴛᴀᴋᴇɴ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ</b>",
                quote=True
            )
            continue

    while True:
        try:
            second_message = await client.ask(
                text="<b>ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..\nᴏʀ sᴇɴᴅ ᴛʜᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ʟɪɴᴋ</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply(
                "<b>❌ ᴇʀʀᴏʀ\n\nᴛʜɪs ғᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴏʀ ᴛʜɪs ʟɪɴᴋ ɪs ɴᴏᴛ ᴛᴀᴋᴇɴ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ</b>",
                quote=True
            )
            continue

    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    custom_message = (
        f"{link}\n\n"
        f"<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ: <a href=\"https://t.me/Base_Angle\">ᴀɴɢʟᴇ ʙᴀsᴇ</a>\n\n"
        f"ɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"
    )
    await second_message.reply_text(custom_message, quote=True)


@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(
                text="<b>ғᴏʀᴡᴀʀᴅ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴛʜᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..\nᴏʀ sᴇɴᴅ ᴛʜᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ʟɪɴᴋ</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply(
                "<b>❌ ᴇʀʀᴏʀ\n\nᴛʜɪs ғᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴏʀ ᴛʜɪs ʟɪɴᴋ ɪs ɴᴏᴛ ᴛᴀᴋᴇɴ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ</b>",
                quote=True
            )
            continue

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"

    custom_message = (
        f"{link}\n\n"
        f"<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ: <a href=\"https://t.me/Base_Angle\">ᴀɴɢʟᴇ ʙᴀsᴇ</a>\n\n"
        f"ɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"
    )
    await channel_message.reply_text(custom_message, quote=True)


@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    uid = message.from_user.id
    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["STOP"]], resize_keyboard=True)

    _in_custom_batch.add(uid)
    await message.reply(
        "<b>sᴇɴᴅ ᴀʟʟ ᴍᴇssᴀɢᴇs ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɪɴᴄʟᴜᴅᴇ ɪɴ ʙᴀᴛᴄʜ.\n\nᴘʀᴇss sᴛᴏᴘ ᴡʜᴇɴ ʏᴏᴜ'ʀᴇ ᴅᴏɴᴇ.</b>",
        reply_markup=STOP_KEYBOARD
    )

    try:
        while True:
            try:
                user_msg = await client.ask(
                    chat_id=message.chat.id,
                    text="<b>ᴡᴀɪᴛɪɴɢ ғᴏʀ ғɪʟᴇs / ᴍᴇssᴀɢᴇs...\nᴘʀᴇss sᴛᴏᴘ ᴛᴏ ғɪɴɪsʜ.</b>",
                    timeout=60
                )
            except asyncio.TimeoutError:
                break

            if user_msg.text and user_msg.text.strip().upper() == "STOP":
                break

            try:
                sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
                collected.append(sent.id)
            except Exception as e:
                await message.reply(f"<b>❌ ғᴀɪʟᴇᴅ ᴛᴏ sᴛᴏʀᴇ ᴀ ᴍᴇssᴀɢᴇ:</b>\n<code>{e}</code>")
                continue
    finally:
        _in_custom_batch.discard(uid)

    await message.reply("<b>✅ ʙᴀᴛᴄʜ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ᴄᴏᴍᴘʟᴇᴛᴇ.</b>", reply_markup=ReplyKeyboardRemove())

    if not collected:
        await message.reply("<b>❌ ɴᴏ ᴍᴇssᴀɢᴇs ᴡᴇʀᴇ ᴀᴅᴅᴇᴅ ᴛᴏ ʙᴀᴛᴄʜ.</b>")
        return

    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    custom_message = (
        f"<b>ʜᴇʀᴇ ɪs ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ ʙᴀᴛᴄʜ ʟɪɴᴋ:</b>\n\n{link}\n\n"
        f"<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ: <a href=\"https://t.me/Base_Angle\">ᴀɴɢʟᴇ ʙᴀsᴇ</a>\n\n"
        f"ɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"
    )
    await message.reply(custom_message)
