import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from pyrogram.errors import FloodWait
from asyncio import TimeoutError

from bot import Bot
from config import *
from helper_func import encode, admin, get_message_id

@Bot.on_message(filters.private & admin & ~filters.command(['start', 'commands','users','broadcast','batch', 'custom_batch', 'genlink','stats', 'dlt_time', 'check_dlt_time', 'dbroadcast', 'ban', 'unban', 'banlist', 'addchnl', 'delchnl', 'listchnl', 'fsub_mode', 'pbroadcast', 'add_admin', 'deladmin', 'admins', 'addpremium', 'premium_users', 'remove_premium', 'myplan', 'count', 'delreq', 'add_super_premium', 'remove_super_premium', 'super_premium_users', 'my_super_plan']))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote = True)
    try:
        post_message = await message.copy(chat_id = client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id = client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went Wrong..!")
        return
    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    # Updated message format with custom text
    custom_message = f"{link}\n\n<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ:  <a href=\"https://t.me/+S95mGGbWHFRmNjM1\"> 𝗛ᴇᴀᴠᴇɴ 𝗕ᴀsᴇ</a> \n\nɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"

    await reply_text.edit(custom_message, disable_web_page_preview = True)

    if not DISABLE_CHANNEL_BUTTON:
        await post_message.edit_reply_markup(None)


@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(text = "Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue

    while True:
        try:
            second_message = await client.ask(text = "Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue


    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    
    # Updated message format with custom text
    custom_message = f"{link}\n\n<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ:  <a href=\"https://t.me/+S95mGGbWHFRmNjM1\"> 𝗛ᴇᴀᴠᴇɴ 𝗕ᴀsᴇ</a> \n\nɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"
    
    await second_message.reply_text(custom_message, quote=True)


@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(text = "Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote = True)
            continue

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    
    # Updated message format with custom text
    custom_message = f"{link}\n\n<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ:  <a href=\"https://t.me/+S95mGGbWHFRmNjM1\"> 𝗛ᴇᴀᴠᴇɴ 𝗕ᴀsᴇ</a> \n\nɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"
    
    await channel_message.reply_text(custom_message, quote=True)


@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["STOP"]], resize_keyboard=True)

    await message.reply("Send all messages you want to include in batch.\n\nPress STOP when you're done.", reply_markup=STOP_KEYBOARD)

    while True:
        try:
            user_msg = await client.ask(
                chat_id=message.chat.id,
                text="Waiting for files/messages...\nPress STOP to finish.",
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
            await message.reply(f"❌ Failed to store a message:\n<code>{e}</code>")
            continue

    await message.reply("✅ Batch collection complete.", reply_markup=ReplyKeyboardRemove())

    if not collected:
        await message.reply("❌ No messages were added to batch.")
        return

    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    # Updated message format with custom text
    custom_message = f"<b>Here is your custom batch link:</b>\n\n{link}\n\n<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ:  <a href=\"https://t.me/+S95mGGbWHFRmNjM1\"> 𝗛ᴇᴀᴠᴇɴ 𝗕ᴀsᴇ</a> \n\nɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"

    await message.reply(custom_message)
