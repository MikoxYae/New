import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, ChatMemberUpdated
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from bot import Bot
from config import *
from helper_func import admin
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


# ─── DELREQ COMMAND ───────────────────────────────────────────────────────────

@Bot.on_message(filters.command('delreq') & filters.private & admin)
async def delete_requested_users(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("⚠️ Usage: <code>/delreq &lt;channel_id&gt;</code>", quote=True)

    try:
        channel_id = int(message.command[1])
    except ValueError:
        return await message.reply("❌ Invalid channel ID.", quote=True)

    channel_data = await db.rqst_fsub_Channel_data.find_one({'_id': channel_id})
    if not channel_data:
        return await message.reply("ℹ️ No request channel found for this ID.", quote=True)

    user_ids = channel_data.get("user_ids", [])
    if not user_ids:
        return await message.reply("✅ No users to process.", quote=True)

    removed = 0
    skipped = 0
    left_users = 0

    for user_id in user_ids:
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER
            ):
                skipped += 1
                continue
            else:
                await db.del_req_user(channel_id, user_id)
                left_users += 1
        except UserNotParticipant:
            await db.del_req_user(channel_id, user_id)
            left_users += 1
        except Exception as e:
            print(f"[!] Error checking user {user_id}: {e}")
            skipped += 1

    for user_id in user_ids:
        if not await db.req_user_exist(channel_id, user_id):
            await db.del_req_user(channel_id, user_id)
            removed += 1

    await message.reply(
        f"✅ Cleanup done for channel <code>{channel_id}</code>\n\n"
        f"👤 Removed (left channel): <code>{left_users}</code>\n"
        f"🗑️ Removed (leftover): <code>{removed}</code>\n"
        f"✅ Still members: <code>{skipped}</code>",
        quote=True
    )
