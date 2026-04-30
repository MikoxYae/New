import asyncio
from pyrogram import filters, StopPropagation
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import OWNER_ID
from database.database import db
import config as _cfg

# ═══════════════════════════════════════════════════════════════
#  SHORTNER SETTINGS  (Owner Only)
# ═══════════════════════════════════════════════════════════════

_shortner_draft: dict = {}   # user_id -> {url, api, expire, tut_vid}
_shortner_pending: dict = {} # user_id -> action string
_shortner_msg: dict = {}     # user_id -> original settings Message to edit


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def _shortner_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 ᴀᴅᴅ sʜᴏʀᴛɴᴇʀ", callback_data="srt_url"),
            InlineKeyboardButton("🔑 ᴀᴘɪ",           callback_data="srt_api")
        ],
        [
            InlineKeyboardButton("🎬 ᴛᴜᴛᴏʀɪᴀʟ ᴠɪᴅᴇᴏ", callback_data="srt_tut"),
            InlineKeyboardButton("⏱ ᴛᴏᴋᴇɴ ᴇxᴘɪʀᴇ",   callback_data="srt_expire")
        ],
        [InlineKeyboardButton("💾 sᴀᴠᴇ ᴄʜᴀɴɢᴇ",      callback_data="srt_save")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ",             callback_data="stg_back")]
    ])


def _build_panel_text(draft: dict) -> str:
    url    = draft.get("url")    or "<i>ɴᴏᴛ sᴇᴛ</i>"
    api    = draft.get("api")    or "<i>ɴᴏᴛ sᴇᴛ</i>"
    expire = draft.get("expire") or "<i>ɴᴏᴛ sᴇᴛ</i>"
    tut    = draft.get("tut_vid") or "<i>ɴᴏᴛ sᴇᴛ</i>"
    return (
        "<b>🔗 sʜᴏʀᴛɴᴇʀ sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<b>🌐 ᴜʀʟ:</b> <code>{url}</code>\n"
        f"<b>🔑 ᴀᴘɪ:</b> <code>{api}</code>\n"
        f"<b>⏱ ᴛᴏᴋᴇɴ ᴇxᴘɪʀᴇ:</b> <code>{expire}</code> sᴇᴄᴏɴᴅs\n"
        f"<b>🎬 ᴛᴜᴛᴏʀɪᴀʟ ᴠɪᴅᴇᴏ:</b> <code>{tut}</code>\n\n"
        "<i>ᴇᴅɪᴛ ᴀ ғɪᴇʟᴅ ᴛʜᴇɴ ᴘʀᴇss <b>sᴀᴠᴇ ᴄʜᴀɴɢᴇ</b> ᴛᴏ ᴀᴘᴘʟʏ.</i>"
    )


async def _show_shortner_panel(query: CallbackQuery, uid: int):
    """Load DB settings into draft and display the shortner panel."""
    settings = await db.get_shortner_settings()
    _shortner_draft[uid] = {
        "url":     settings.get("url",     _cfg.SHORTLINK_URL  or ""),
        "api":     settings.get("api",     _cfg.SHORTLINK_API  or ""),
        "expire":  str(settings.get("expire", _cfg.VERIFY_EXPIRE or 60)),
        "tut_vid": settings.get("tut_vid", _cfg.TUT_VID         or ""),
    }
    draft = _shortner_draft[uid]
    try:
        await query.message.edit_caption(
            caption=_build_panel_text(draft),
            reply_markup=_shortner_markup()
        )
    except Exception:
        try:
            await query.message.edit_text(
                _build_panel_text(draft),
                reply_markup=_shortner_markup()
            )
        except Exception:
            pass


@Bot.on_callback_query(filters.regex(r"^srt_"))
async def shortner_cb(client: Bot, query: CallbackQuery):
    uid  = query.from_user.id
    data = query.data

    if not _is_owner(uid):
        await query.answer("⛔ ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴍᴀɴᴀɢᴇ sʜᴏʀᴛɴᴇʀ sᴇᴛᴛɪɴɢs!", show_alert=True)
        return

    await query.answer()

    # ── Show panel ────────────────────────────────────────────
    if data == "srt_show":
        await _show_shortner_panel(query, uid)

    # ── Prompt for URL ────────────────────────────────────────
    elif data == "srt_url":
        _shortner_pending[uid] = "srt_url"
        _shortner_msg[uid] = query.message
        try:
            await query.message.edit_caption(
                caption=(
                    "<b>🌐 ᴇɴᴛᴇʀ sʜᴏʀᴛɴᴇʀ ᴡᴇʙsɪᴛᴇ ᴜʀʟ</b>\n\n"
                    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>linkshortify.com</code>"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>🌐 ᴇɴᴛᴇʀ sʜᴏʀᴛɴᴇʀ ᴡᴇʙsɪᴛᴇ ᴜʀʟ</b>\n\n"
                "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>linkshortify.com</code>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )

    # ── Prompt for API ────────────────────────────────────────
    elif data == "srt_api":
        _shortner_pending[uid] = "srt_api"
        _shortner_msg[uid] = query.message
        try:
            await query.message.edit_caption(
                caption="<b>🔑 ᴇɴᴛᴇʀ sʜᴏʀᴛɴᴇʀ ᴀᴘɪ ᴋᴇʏ:</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>🔑 ᴇɴᴛᴇʀ sʜᴏʀᴛɴᴇʀ ᴀᴘɪ ᴋᴇʏ:</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )

    # ── Prompt for Tutorial Video ──────────────────────────────
    elif data == "srt_tut":
        _shortner_pending[uid] = "srt_tut"
        _shortner_msg[uid] = query.message
        try:
            await query.message.edit_caption(
                caption=(
                    "<b>🎬 ᴇɴᴛᴇʀ ᴛᴜᴛᴏʀɪᴀʟ ᴠɪᴅᴇᴏ ʟɪɴᴋ</b>\n\n"
                    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>https://t.me/channel/12</code>"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>🎬 ᴇɴᴛᴇʀ ᴛᴜᴛᴏʀɪᴀʟ ᴠɪᴅᴇᴏ ʟɪɴᴋ</b>\n\n"
                "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>https://t.me/channel/12</code>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )

    # ── Prompt for Token Expire ───────────────────────────────
    elif data == "srt_expire":
        _shortner_pending[uid] = "srt_expire"
        _shortner_msg[uid] = query.message
        try:
            await query.message.edit_caption(
                caption=(
                    "<b>⏱ ᴇɴᴛᴇʀ ᴛᴏᴋᴇɴ ᴇxᴘɪʀᴇ ᴛɪᴍᴇ (ɪɴ sᴇᴄᴏɴᴅs)</b>\n\n"
                    "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>60</code> = 60 sᴇᴄᴏɴᴅs"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>⏱ ᴇɴᴛᴇʀ ᴛᴏᴋᴇɴ ᴇxᴘɪʀᴇ ᴛɪᴍᴇ (ɪɴ sᴇᴄᴏɴᴅs)</b>\n\n"
                "<i>ᴇxᴀᴍᴘʟᴇ:</i> <code>60</code> = 60 sᴇᴄᴏɴᴅs",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )

    # ── Save all settings ─────────────────────────────────────
    elif data == "srt_save":
        draft = _shortner_draft.get(uid)
        if not draft:
            await query.answer("⚠️ ɴᴏᴛʜɪɴɢ ᴛᴏ sᴀᴠᴇ. ᴏᴘᴇɴ sᴇᴛᴛɪɴɢs ғɪʀsᴛ.", show_alert=True)
            return

        await db.save_shortner_settings(draft)

        # Apply to running config immediately
        if draft.get("url"):
            _cfg.SHORTLINK_URL = draft["url"]
        if draft.get("api"):
            _cfg.SHORTLINK_API = draft["api"]
        if draft.get("tut_vid"):
            _cfg.TUT_VID = draft["tut_vid"]
        if draft.get("expire"):
            try:
                _cfg.VERIFY_EXPIRE = int(draft["expire"])
            except ValueError:
                pass

        _shortner_draft.pop(uid, None)
        _shortner_pending.pop(uid, None)

        try:
            await query.message.edit_caption(
                caption=(
                    "<b>✅ sʜᴏʀᴛɴᴇʀ sᴇᴛᴛɪɴɢs sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b>\n\n"
                    f"<b>🌐 ᴜʀʟ:</b> <code>{draft.get('url') or 'not set'}</code>\n"
                    f"<b>🔑 ᴀᴘɪ:</b> <code>{draft.get('api') or 'not set'}</code>\n"
                    f"<b>⏱ ᴛᴏᴋᴇɴ ᴇxᴘɪʀᴇ:</b> <code>{draft.get('expire', '60')}</code> sᴇᴄᴏɴᴅs\n"
                    f"<b>🎬 ᴛᴜᴛᴏʀɪᴀʟ:</b> <code>{draft.get('tut_vid') or 'not set'}</code>"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>✅ sʜᴏʀᴛɴᴇʀ sᴇᴛᴛɪɴɢs sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="stg_back")
                ]])
            )

    raise StopPropagation


# ═══════════════════════════════════════════════════════════════
#  TEXT INPUT HANDLER  (owner typing values)
# ═══════════════════════════════════════════════════════════════

@Bot.on_message(filters.private & filters.text & filters.create(
    lambda _, __, m: m.from_user and m.from_user.id in _shortner_pending
), group=-1)
async def shortner_text_handler(client: Bot, message: Message):
    uid    = message.from_user.id
    action = _shortner_pending.pop(uid, None)

    if not action or not _is_owner(uid):
        return

    text = message.text.strip()

    # Ensure draft exists
    if uid not in _shortner_draft:
        settings = await db.get_shortner_settings()
        _shortner_draft[uid] = {
            "url":     settings.get("url",     _cfg.SHORTLINK_URL  or ""),
            "api":     settings.get("api",     _cfg.SHORTLINK_API  or ""),
            "expire":  str(settings.get("expire", _cfg.VERIFY_EXPIRE or 60)),
            "tut_vid": settings.get("tut_vid", _cfg.TUT_VID         or ""),
        }

    if action == "srt_url":
        _shortner_draft[uid]["url"] = text
        note = f"✅ Shortner URL set to: <code>{text}</code>"
    elif action == "srt_api":
        _shortner_draft[uid]["api"] = text
        note = "✅ API Key updated."
    elif action == "srt_tut":
        _shortner_draft[uid]["tut_vid"] = text
        note = f"✅ Tutorial Video set to: <code>{text}</code>"
    elif action == "srt_expire":
        try:
            int(text)
            _shortner_draft[uid]["expire"] = text
            note = f"✅ Token Expire set to: <code>{text}</code> seconds"
        except ValueError:
            _shortner_pending[uid] = action  # restore pending
            await message.reply(
                "<b>❌ ɪɴᴠᴀʟɪᴅ! ᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ɴᴜᴍʙᴇʀ (sᴇᴄᴏɴᴅs).</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="srt_show")
                ]])
            )
            raise StopPropagation
    else:
        raise StopPropagation

    draft = _shortner_draft[uid]

    # Delete the user's typed message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    # Edit the original settings message instead of sending a new one
    orig_msg = _shortner_msg.get(uid)
    if orig_msg:
        try:
            await orig_msg.edit_caption(
                caption=f"{note}\n\n{_build_panel_text(draft)}",
                reply_markup=_shortner_markup()
            )
        except Exception:
            try:
                await orig_msg.edit_text(
                    f"{note}\n\n{_build_panel_text(draft)}",
                    reply_markup=_shortner_markup()
                )
            except Exception:
                pass
    else:
        await message.reply(
            f"{note}\n\n{_build_panel_text(draft)}",
            reply_markup=_shortner_markup()
        )
    raise StopPropagation
