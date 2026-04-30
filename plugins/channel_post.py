import asyncio
from pyrogram import filters, Client, StopPropagation
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from pyrogram.errors import FloodWait
from asyncio import TimeoutError

from bot import Bot
from config import *
from helper_func import encode, admin, get_message_id
from database.db_stats import log_activity


# ─────────────────────────────────────────────────────────────────────────────
#  /custom_batch state
#
#  _in_custom_batch  : set of admin user-ids currently inside a batch session
#  _batch_queues     : per-user asyncio.Queue that the high-priority capture
#                      handler pushes incoming messages into. The custom_batch
#                      coroutine then pulls from this queue instead of using
#                      `client.ask` (which leaks messages to other handlers and
#                      caused the double-copy + junk-STOP-link bugs).
# ─────────────────────────────────────────────────────────────────────────────
_in_custom_batch: set = set()
_batch_queues: dict = {}


def not_in_batch_filter(_, __, message: Message) -> bool:
    if message.from_user is None:
        return True
    return message.from_user.id not in _in_custom_batch


def in_batch_filter(_, __, message: Message) -> bool:
    if message.from_user is None:
        return False
    return message.from_user.id in _in_custom_batch


not_in_batch = filters.create(not_in_batch_filter)
in_batch = filters.create(in_batch_filter)


# ─────────────────────────────────────────────────────────────────────────────
#  Commands the channel_post catch-all must NOT swallow.
# ─────────────────────────────────────────────────────────────────────────────
_EXCLUDED_COMMANDS = [
    # core / help
    "start", "commands", "help", "about",
    # broadcasts
    "broadcast", "dbroadcast", "pbroadcast",
    # batching / link gen
    "batch", "custom_batch", "genlink",
    # premium admin
    "addpremium", "premium_users", "remove_premium", "myplan",
    # settings + monitoring
    "settings", "peakhours", "weeklyreport", "cleanstats",
    "start_premium_monitoring",
    # admin orders panel (v1.2)
    "id", "ord", "amount", "stats", "checkorder", "forceverify",
]


# ═══════════════════════════════════════════════════════════════════════════════
#   HIGH-PRIORITY capture handler for messages while admin is inside
#   /custom_batch.  Runs in group=-5 (before any normal-group handler), pushes
#   the message into the per-user queue and then halts propagation so that
#   channel_post (group 0) can NEVER see the same message a second time.
#
#   This is what kills the two reported bugs:
#     1. "media goes into DB twice"  – previously channel_post ALSO copied the
#        same media after `client.ask` returned it.
#     2. "STOP also generates a junk encoded link" – previously the STOP text
#        message slipped through to channel_post (race in the discard timing
#        of _in_custom_batch) and got copied + encoded.
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.private & admin & in_batch, group=-5)
async def _capture_batch_messages(client: Client, message: Message):
    uid = message.from_user.id
    q = _batch_queues.get(uid)
    if q is not None:
        try:
            q.put_nowait(message)
        except Exception:
            pass
    # STOP propagation so no other handler in any later group runs for this
    # message. This is the critical line that prevents channel_post from
    # making a second db_channel copy.
    raise StopPropagation


# ═══════════════════════════════════════════════════════════════════════════════
#   Catch-all admin upload  ->  store in db_channel and return share link
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(
    filters.private
    & admin
    & not_in_batch
    & ~filters.command(_EXCLUDED_COMMANDS)
)
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>", quote=True)
    try:
        post_message = await message.copy(
            chat_id=client.db_channel.id, disable_notification=True
        )
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(
            chat_id=client.db_channel.id, disable_notification=True
        )
    except Exception as e:
        print(f"channel_post copy failed: {e}")
        await reply_text.edit_text("<b>sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ!</b>")
        return

    converted_id = post_message.id * abs(client.db_channel.id)
    base64_string = await encode(f"get-{converted_id}")
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


# ═══════════════════════════════════════════════════════════════════════════════
#   /batch  -  range link
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.private & admin & filters.command("batch"))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(
                text="<b>ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..\n\nᴏʀ sᴇɴᴅ ᴛʜᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ʟɪɴᴋ</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
            )
        except Exception:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        await first_message.reply(
            "<b>❌ ᴇʀʀᴏʀ\n\nᴛʜɪs ғᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴏʀ ᴛʜɪs ʟɪɴᴋ ɪs ɴᴏᴛ ᴛᴀᴋᴇɴ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ</b>",
            quote=True,
        )

    while True:
        try:
            second_message = await client.ask(
                text="<b>ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..\nᴏʀ sᴇɴᴅ ᴛʜᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ʟɪɴᴋ</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
            )
        except Exception:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        await second_message.reply(
            "<b>❌ ᴇʀʀᴏʀ\n\nᴛʜɪs ғᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴏʀ ᴛʜɪs ʟɪɴᴋ ɪs ɴᴏᴛ ᴛᴀᴋᴇɴ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ</b>",
            quote=True,
        )

    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    custom_message = (
        f"{link}\n\n"
        f"<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ: <a href=\"https://t.me/Base_Angle\">ᴀɴɢʟᴇ ʙᴀsᴇ</a>\n\n"
        f"ɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"
    )
    await second_message.reply_text(
        custom_message, quote=True, disable_web_page_preview=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
#   /genlink  -  single message link
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.private & admin & filters.command("genlink"))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(
                text="<b>ғᴏʀᴡᴀʀᴅ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴛʜᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ (ᴡɪᴛʜ ǫᴜᴏᴛᴇs)..\nᴏʀ sᴇɴᴅ ᴛʜᴇ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ʟɪɴᴋ</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
            )
        except Exception:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        await channel_message.reply(
            "<b>❌ ᴇʀʀᴏʀ\n\nᴛʜɪs ғᴏʀᴡᴀʀᴅᴇᴅ ᴘᴏsᴛ ɪs ɴᴏᴛ ғʀᴏᴍ ᴍʏ ᴅʙ ᴄʜᴀɴɴᴇʟ ᴏʀ ᴛʜɪs ʟɪɴᴋ ɪs ɴᴏᴛ ᴛᴀᴋᴇɴ ғʀᴏᴍ ᴅʙ ᴄʜᴀɴɴᴇʟ</b>",
            quote=True,
        )

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"

    custom_message = (
        f"{link}\n\n"
        f"<b>𝗠ᴜsᴛ 𝗝ᴏɪɴ: <a href=\"https://t.me/Base_Angle\">ᴀɴɢʟᴇ ʙᴀsᴇ</a>\n\n"
        f"ɢɪᴠᴇ sᴏᴍᴇ ʟᴏᴠᴇ ᴛᴏ ᴜs, ʜɪᴛ ᴛʜᴇ ʀᴇᴀᴄᴛɪᴏɴ! 🔥💫⚡</b>"
    )
    await channel_message.reply_text(
        custom_message, quote=True, disable_web_page_preview=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
#   /custom_batch  -  collect messages then build a range link.
#
#   Uses the per-user queue fed by `_capture_batch_messages` (group=-5) so
#   that:
#     • messages are processed exactly once (no double-copy to db_channel)
#     • the STOP control message never reaches channel_post (no junk link)
#     • a 5-minute idle timeout still ends an abandoned session
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    uid = message.from_user.id
    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["STOP"]], resize_keyboard=True)

    # set up the queue BEFORE we mark the user "in batch" so that the very
    # first captured message has somewhere to land.
    q: asyncio.Queue = asyncio.Queue()
    _batch_queues[uid] = q
    _in_custom_batch.add(uid)

    await message.reply(
        "<b>sᴇɴᴅ ᴀʟʟ ᴍᴇssᴀɢᴇs ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɪɴᴄʟᴜᴅᴇ ɪɴ ʙᴀᴛᴄʜ.\n\nᴘʀᴇss sᴛᴏᴘ ᴡʜᴇɴ ʏᴏᴜ'ʀᴇ ᴅᴏɴᴇ.</b>",
        reply_markup=STOP_KEYBOARD,
    )

    try:
        while True:
            try:
                user_msg: Message = await asyncio.wait_for(q.get(), timeout=300)
            except asyncio.TimeoutError:
                break

            # STOP control – never copy to db_channel, just end the loop.
            if user_msg.text and user_msg.text.strip().upper() == "STOP":
                break

            try:
                sent = await user_msg.copy(
                    client.db_channel.id, disable_notification=True
                )
                collected.append(sent.id)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                try:
                    sent = await user_msg.copy(
                        client.db_channel.id, disable_notification=True
                    )
                    collected.append(sent.id)
                except Exception as e2:
                    await message.reply(
                        f"<b>❌ ғᴀɪʟᴇᴅ ᴛᴏ sᴛᴏʀᴇ ᴀ ᴍᴇssᴀɢᴇ:</b>\n<code>{e2}</code>"
                    )
                    continue
            except Exception as e:
                await message.reply(
                    f"<b>❌ ғᴀɪʟᴇᴅ ᴛᴏ sᴛᴏʀᴇ ᴀ ᴍᴇssᴀɢᴇ:</b>\n<code>{e}</code>"
                )
                continue
    finally:
        # IMPORTANT: discard from set FIRST so any genuinely-late uploads after
        # STOP fall through to channel_post normally (not silently swallowed).
        _in_custom_batch.discard(uid)
        _batch_queues.pop(uid, None)

    await message.reply(
        "<b>✅ ʙᴀᴛᴄʜ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ᴄᴏᴍᴘʟᴇᴛᴇ.</b>",
        reply_markup=ReplyKeyboardRemove(),
    )

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
    await message.reply(custom_message, disable_web_page_preview=True)
