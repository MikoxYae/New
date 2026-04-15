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


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def _shortner_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 Add Shortner", callback_data="srt_url"),
            InlineKeyboardButton("🔑 Api",           callback_data="srt_api")
        ],
        [
            InlineKeyboardButton("🎬 Tutorial Video", callback_data="srt_tut"),
            InlineKeyboardButton("⏱ Token Expire",   callback_data="srt_expire")
        ],
        [InlineKeyboardButton("💾 Save Change",      callback_data="srt_save")],
        [InlineKeyboardButton("🔙 Back",             callback_data="stg_back")]
    ])


def _build_panel_text(draft: dict) -> str:
    url    = draft.get("url")    or "<i>not set</i>"
    api    = draft.get("api")    or "<i>not set</i>"
    expire = draft.get("expire") or "<i>not set</i>"
    tut    = draft.get("tut_vid") or "<i>not set</i>"
    return (
        "<b>🔗 Shortner Settings</b>\n\n"
        f"<b>🌐 URL:</b> <code>{url}</code>\n"
        f"<b>🔑 API:</b> <code>{api}</code>\n"
        f"<b>⏱ Token Expire:</b> <code>{expire}</code> seconds\n"
        f"<b>🎬 Tutorial Video:</b> <code>{tut}</code>\n\n"
        "<i>Edit a field then press <b>Save Change</b> to apply.</i>"
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
        await query.answer("⛔ Only Owner can manage Shortner settings!", show_alert=True)
        return

    await query.answer()

    # ── Show panel ────────────────────────────────────────────
    if data == "srt_show":
        await _show_shortner_panel(query, uid)

    # ── Prompt for URL ────────────────────────────────────────
    elif data == "srt_url":
        _shortner_pending[uid] = "srt_url"
        try:
            await query.message.edit_caption(
                caption=(
                    "<b>🌐 Enter Shortner Website URL</b>\n\n"
                    "<i>Example:</i> <code>linkshortify.com</code>"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>🌐 Enter Shortner Website URL</b>\n\n"
                "<i>Example:</i> <code>linkshortify.com</code>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )

    # ── Prompt for API ────────────────────────────────────────
    elif data == "srt_api":
        _shortner_pending[uid] = "srt_api"
        try:
            await query.message.edit_caption(
                caption="<b>🔑 Enter Shortner API Key:</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>🔑 Enter Shortner API Key:</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )

    # ── Prompt for Tutorial Video ──────────────────────────────
    elif data == "srt_tut":
        _shortner_pending[uid] = "srt_tut"
        try:
            await query.message.edit_caption(
                caption=(
                    "<b>🎬 Enter Tutorial Video Link</b>\n\n"
                    "<i>Example:</i> <code>https://t.me/channel/12</code>"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>🎬 Enter Tutorial Video Link</b>\n\n"
                "<i>Example:</i> <code>https://t.me/channel/12</code>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )

    # ── Prompt for Token Expire ───────────────────────────────
    elif data == "srt_expire":
        _shortner_pending[uid] = "srt_expire"
        try:
            await query.message.edit_caption(
                caption=(
                    "<b>⏱ Enter Token Expire Time (in seconds)</b>\n\n"
                    "<i>Example:</i> <code>60</code> = 60 seconds"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>⏱ Enter Token Expire Time (in seconds)</b>\n\n"
                "<i>Example:</i> <code>60</code> = 60 seconds",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )

    # ── Save all settings ─────────────────────────────────────
    elif data == "srt_save":
        draft = _shortner_draft.get(uid)
        if not draft:
            await query.answer("⚠️ Nothing to save. Open settings first.", show_alert=True)
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
                    "<b>✅ Shortner Settings Saved Successfully!</b>\n\n"
                    f"<b>🌐 URL:</b> <code>{draft.get('url') or 'not set'}</code>\n"
                    f"<b>🔑 API:</b> <code>{draft.get('api') or 'not set'}</code>\n"
                    f"<b>⏱ Token Expire:</b> <code>{draft.get('expire', '60')}</code> seconds\n"
                    f"<b>🎬 Tutorial:</b> <code>{draft.get('tut_vid') or 'not set'}</code>"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="stg_back")
                ]])
            )
        except Exception:
            await query.message.edit_text(
                "<b>✅ Shortner Settings Saved Successfully!</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="stg_back")
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
                "<b>❌ Invalid! Please enter a number (seconds).</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="srt_show")
                ]])
            )
            raise StopPropagation
    else:
        raise StopPropagation

    draft = _shortner_draft[uid]
    await message.reply(
        f"{note}\n\n{_build_panel_text(draft)}",
        reply_markup=_shortner_markup()
    )
    raise StopPropagation
