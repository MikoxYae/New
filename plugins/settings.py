from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from helper_func import admin

SETTINGS_PIC = "https://graph.org/file/d18515f99d522b3ee4e6f-876aedcb4f5dde2d4e.jpg"


@Bot.on_message(filters.command('settings') & filters.private & admin)
async def settings_command(client: Client, message: Message):
    await message.reply_photo(
        photo=SETTINGS_PIC,
        caption="<b>⚙️ Settings Panel</b>\n\nSelect a category to manage:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👑 Admin",        callback_data="stg_admin"),
                InlineKeyboardButton("🚫 Ban Users",    callback_data="stg_ban")
            ],
            [
                InlineKeyboardButton("👥 Users",        callback_data="stg_users"),
                InlineKeyboardButton("📊 Stats",        callback_data="stg_stats")
            ],
            [
                InlineKeyboardButton("🔢 Count",        callback_data="stg_count"),
                InlineKeyboardButton("🧹 DelReq",       callback_data="stg_delreq")
            ],
            [
                InlineKeyboardButton("📢 Force Sub",    callback_data="stg_fsub"),
                InlineKeyboardButton("🔄 Request Mode", callback_data="stg_reqmode")
            ],
            [
                InlineKeyboardButton("⏱ Auto Delete",  callback_data="stg_autodel"),
                InlineKeyboardButton("🔗 Shortner",     callback_data="stg_shortner")
            ],
            [
                InlineKeyboardButton("🔐 Protect",      callback_data="stg_protect"),
                InlineKeyboardButton("📝 Caption",      callback_data="stg_caption")
            ],
            [
                InlineKeyboardButton("🛡 Anti Bypass",  callback_data="stg_antibypass")
            ]
        ])
    )
