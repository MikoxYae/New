from pyrogram import Client, filters
from pyrogram.types import Message
from bot import Bot
from helper_func import admin
from plugins.settings_panel_cb import _main_markup, _main_text

SETTINGS_PIC = "https://graph.org/file/d18515f99d522b3ee4e6f-876aedcb4f5dde2d4e.jpg"


@Bot.on_message(filters.command('settings') & filters.private & admin)
async def settings_command(client: Client, message: Message):
    await message.reply_photo(
        photo=SETTINGS_PIC,
        caption=_main_text(1),
        reply_markup=_main_markup(1),
    )
