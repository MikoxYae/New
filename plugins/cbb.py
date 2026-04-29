from pyrogram import Client, filters
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *


# ═══════════════════════════════════════════════════════════════════════════════
#   General callback handler  (premium-purchase flow lives in plugins/premium_auto.py)
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^(help|about|start|close)$"))
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data

    # ── ʜᴇʟᴘ ─────────────────────────────────────────────────────────────────
    if data == "help":
        await query.message.edit_text(
            text=HELP_TXT.format(
                first=query.from_user.first_name,
                last=query.from_user.last_name,
                username=None if not query.from_user.username else '@' + query.from_user.username,
                mention=query.from_user.mention,
                id=query.from_user.id
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                 InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data='close')]
            ])
        )

    # ── ᴀʙᴏᴜᴛ ────────────────────────────────────────────────────────────────
    elif data == "about":
        await query.message.edit_text(
            text=ABOUT_TXT.format(
                first=query.from_user.first_name,
                last=query.from_user.last_name,
                username=None if not query.from_user.username else '@' + query.from_user.username,
                mention=query.from_user.mention,
                id=query.from_user.id
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                 InlineKeyboardButton('ᴄʟᴏꜱᴇ', callback_data='close')]
            ])
        )

    # ── sᴛᴀʀᴛ ────────────────────────────────────────────────────────────────
    elif data == "start":
        await query.message.edit_text(
            text=START_MSG.format(
                first=query.from_user.first_name,
                last=query.from_user.last_name,
                username=None if not query.from_user.username else '@' + query.from_user.username,
                mention=query.from_user.mention,
                id=query.from_user.id
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʜᴇʟᴘ", callback_data='help'),
                 InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data='about')]
            ])
        )

    # ── ᴄʟᴏsᴇ ────────────────────────────────────────────────────────────────
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#   Force-sub channel mode toggle  (used by settings panel)
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^(rfs_ch_|rfs_toggle_|fsub_back)"))
async def fsub_cb(client: Bot, query: CallbackQuery):
    data = query.data

    if data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
            new_mode = "off" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(
                    f"ʀᴇǫ ᴍᴏᴅᴇ {'ᴏғғ' if mode == 'on' else 'ᴏɴ'}",
                    callback_data=f"rfs_toggle_{cid}_{new_mode}"
                )],
                [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
            ]
            await query.message.edit_text(
                f"<b>ᴄʜᴀɴɴᴇʟ:</b> {chat.title}\n<b>ᴄᴜʀʀᴇɴᴛ ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:</b> {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            await query.answer("ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴄʜᴀɴɴᴇʟ ɪɴғᴏ", show_alert=True)

    elif data.startswith("rfs_toggle_"):
        parts = data.split("_")
        cid = int(parts[2])
        action = parts[3]
        mode = "on" if action == "on" else "off"
        await db.set_channel_mode(cid, mode)
        await query.answer(f"ғᴏʀᴄᴇ-sᴜʙ sᴇᴛ ᴛᴏ {'ᴏɴ' if mode == 'on' else 'ᴏғғ'}")
        chat = await client.get_chat(cid)
        status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
        new_mode = "off" if mode == "on" else "on"
        buttons = [
            [InlineKeyboardButton(
                f"ʀᴇǫ ᴍᴏᴅᴇ {'ᴏғғ' if mode == 'on' else 'ᴏɴ'}",
                callback_data=f"rfs_toggle_{cid}_{new_mode}"
            )],
            [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
        ]
        await query.message.edit_text(
            f"<b>ᴄʜᴀɴɴᴇʟ:</b> {chat.title}\n<b>ᴄᴜʀʀᴇɴᴛ ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:</b> {status}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "fsub_back":
        channels = await db.show_channels()
        buttons = []
        for cid in channels:
            try:
                chat = await client.get_chat(cid)
                mode = await db.get_channel_mode(cid)
                status_icon = "🟢" if mode == "on" else "🔴"
                buttons.append([InlineKeyboardButton(
                    f"{status_icon} {chat.title}", callback_data=f"rfs_ch_{cid}"
                )])
            except Exception:
                continue
        await query.message.edit_text(
            "<b>sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ɪᴛs ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
