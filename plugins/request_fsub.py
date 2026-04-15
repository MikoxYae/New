from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated
from bot import Bot
from database.database import db


# ─── CHAT MEMBER UPDATED (handles users leaving/kicked) ──────────────────────

@Bot.on_chat_member_updated()
async def handle_Chatmembers(client, chat_member_updated: ChatMemberUpdated):
    chat_id = chat_member_updated.chat.id

    if await db.reqChannel_exist(chat_id):
        old_member = chat_member_updated.old_chat_member

        if not old_member:
            return

        if old_member.status == ChatMemberStatus.MEMBER:
            user_id = old_member.user.id

            if await db.req_user_exist(chat_id, user_id):
                await db.del_req_user(chat_id, user_id)


# ─── JOIN REQUEST HANDLER ─────────────────────────────────────────────────────

@Bot.on_chat_join_request()
async def handle_join_request(client, chat_join_request):
    chat_id = chat_join_request.chat.id
    user_id = chat_join_request.from_user.id

    channel_exists = await db.reqChannel_exist(chat_id)

    if channel_exists:
        if not await db.req_user_exist(chat_id, user_id):
            await db.req_user(chat_id, user_id)
