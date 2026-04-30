from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from helper_func import admin

SETTINGS_PIC = "https://graph.org/file/d18515f99d522b3ee4e6f-876aedcb4f5dde2d4e.jpg"


@Bot.on_message(filters.command('settings') & filters.private & admin)
async def settings_command(client: Client, message: Message):
    await message.reply_photo(
        photo=SETTINGS_PIC,
        caption="<b>⚙️ sᴇᴛᴛɪɴɢs ᴘᴀɴᴇʟ</b>\n\nsᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ᴛᴏ ᴍᴀɴᴀɢᴇ:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👑 ᴀᴅᴍɪɴ",        callback_data="stg_admin"),
                InlineKeyboardButton("🚫 ʙᴀɴ ᴜsᴇʀs",    callback_data="stg_ban")
            ],
            [
                InlineKeyboardButton("👥 ᴜsᴇʀs",        callback_data="stg_users"),
                InlineKeyboardButton("📊 sᴛᴀᴛs",        callback_data="stg_stats")
            ],
            [
                InlineKeyboardButton("🧹 ᴅᴇʟʀᴇǫ",       callback_data="stg_delreq"),
                InlineKeyboardButton("📢 ғᴏʀᴄᴇ sᴜʙ",    callback_data="stg_fsub")
            ],
            [
                InlineKeyboardButton("🔄 ʀᴇǫᴜᴇsᴛ ᴍᴏᴅᴇ", callback_data="stg_reqmode"),
                InlineKeyboardButton("⏱ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ",  callback_data="stg_autodel")
            ],
            [
                InlineKeyboardButton("🆓 ғʀᴇᴇ ʟɪɴᴋ",    callback_data="stg_freelink"),
                InlineKeyboardButton("🔐 ᴘʀᴏᴛᴇᴄᴛ",      callback_data="stg_protect")
            ],
            [
                InlineKeyboardButton("📝 ᴄᴀᴘᴛɪᴏɴ",      callback_data="stg_caption"),
                InlineKeyboardButton("🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ",  callback_data="stg_maintenance")
            ]
        ])
    )
