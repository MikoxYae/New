import time
import asyncio
from pyrogram import filters
from pyrogram.types import Message
from bot import Bot
from config import FLOOD_LIMIT, FLOOD_WINDOW, FLOOD_BLOCK_DURATION

_flood: dict = {}


def _check(user_id: int):
    now = time.time()
    d = _flood.get(user_id)
    if not d:
        _flood[user_id] = {'count': 1, 'first_ts': now, 'warned': False, 'blocked_until': 0.0}
        return False, False
    if now < d['blocked_until']:
        return True, False
    if now - d['first_ts'] > FLOOD_WINDOW:
        _flood[user_id] = {'count': 1, 'first_ts': now, 'warned': False, 'blocked_until': 0.0}
        return False, False
    d['count'] += 1
    if d['count'] > FLOOD_LIMIT:
        is_new = not d['warned']
        d['warned'] = True
        d['blocked_until'] = now + FLOOD_BLOCK_DURATION
        return True, is_new
    return False, False


@Bot.on_message(filters.private & ~filters.service, group=-2)
async def flood_guard(client: Bot, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return
    blocked, is_new = _check(user_id)
    if blocked:
        if is_new:
            try:
                warn = await message.reply(
                    f'<b>⚠️ sʟᴏᴡ ᴅᴏᴡɴ!</b>\n\n'
                    f'<b>ʏᴏᴜ ᴀʀᴇ sᴇɴᴅɪɴɢ ᴍᴇssᴀɢᴇs ᴛᴏᴏ ғᴀsᴛ.</b>\n'
                    f'<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ <b>{FLOOD_BLOCK_DURATION} sᴇᴄᴏɴᴅs</b> ʙᴇғᴏʀᴇ ᴛʀʏɪɴɢ ᴀɢᴀɪɴ.</b>'
                )
                await asyncio.sleep(FLOOD_BLOCK_DURATION)
                try:
                    await warn.delete()
                except Exception:
                    pass
            except Exception:
                pass
        message.stop_propagation()
