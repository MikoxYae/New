import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import Bot
from helper_func import admin
from database.db_premium import *
from database.db_plans import revoke_user_gifts
from pytz import timezone
from datetime import datetime, timedelta

monitoring_started = False

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id
    status_message = await check_user_plan(user_id)
    await message.reply(status_message)


@Bot.on_message(filters.command('addpremium') & filters.private & admin)
async def add_premium_user_command(client, msg):
    if len(msg.command) not in (4, 5):
        await msg.reply_text(
            "<b>ᴜsᴀɢᴇ:</b> /ᴀᴅᴅᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ_ɪᴅ ᴛɪᴍᴇ_ᴠᴀʟᴜᴇ ᴛɪᴍᴇ_ᴜɴɪᴛ ᴛɪᴇʀ\n\n"
            "<b>ᴛɪᴇʀs:</b>\n"
            "🥇 ɢᴏʟᴅ — ᴛᴏᴋᴇɴ ʙʏᴘᴀss + ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss\n"
            "💎 ᴘʟᴀᴛɪɴᴜᴍ — ᴛᴏᴋᴇɴ ʙʏᴘᴀss + ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss + ғᴏʀᴄᴇ sᴜʙ ʙʏᴘᴀss\n\n"
            "<b>ᴛɪᴍᴇ ᴜɴɪᴛs:</b> s | ᴍ | ʜ | ᴅ | ʏ\n\n"
            "<b>ᴇxᴀᴍᴘʟᴇs:</b>\n"
            "/ᴀᴅᴅᴘʀᴇᴍɪᴜᴍ 123456789 1 ᴅ ɢᴏʟᴅ\n"
            "/ᴀᴅᴅᴘʀᴇᴍɪᴜᴍ 123456789 1 ᴅ ᴘʟᴀᴛɪɴᴜᴍ\n"
            "(ᴅᴇғᴀᴜʟᴛ ᴛɪᴇʀ ɪs ɢᴏʟᴅ ɪғ ɴᴏᴛ sᴘᴇᴄɪғɪᴇᴅ)"
        )
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()
        tier = msg.command[4].lower() if len(msg.command) == 5 else "gold"

        if tier not in ("gold", "platinum"):
            return await msg.reply_text("<b>ɪɴᴠᴀʟɪᴅ ᴛɪᴇʀ. ᴜsᴇ:</b> <code>gold</code> <b>ᴏʀ</b> <code>platinum</code>")

        expiration_time = await add_premium(user_id, time_value, time_unit, tier)
        tier_emoji = "🥇" if tier == "gold" else "💎"
        perks = (
            "ᴛᴏᴋᴇɴ ʙʏᴘᴀss\nᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss"
            if tier == "gold"
            else "ᴛᴏᴋᴇɴ ʙʏᴘᴀss\nᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss\nғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ʙʏᴘᴀss"
        )

        await msg.reply_text(
            f"<b>ᴜsᴇʀ</b> <code>{user_id}</code> <b>ᴀᴅᴅᴇᴅ ᴀs</b> {tier_emoji} <b>{tier.capitalize()} ᴘʀᴇᴍɪᴜᴍ ғᴏʀ</b> <code>{time_value}{time_unit}</code><b>.\nᴇxᴘɪʀᴀᴛɪᴏɴ:</b> <code>{expiration_time}</code>"
        )

        await client.send_message(
            chat_id=user_id,
            text=(
                f"{tier_emoji} <b>{tier.capitalize()} ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!</b>\n\n"
                f"ᴅᴜʀᴀᴛɪᴏɴ: <b>{time_value}{time_unit}</b>\n"
                f"ᴇxᴘɪʀᴇs ᴏɴ: <b>{expiration_time}</b>\n\n"
                f"<b>ʏᴏᴜʀ ᴘᴇʀᴋs:</b>\n{perks}"
            ),
        )

        asyncio.create_task(monitor_premium_expiry(client, user_id))

    except ValueError:
        await msg.reply_text("<b>ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ. ᴇɴsᴜʀᴇ ᴜsᴇʀ ɪᴅ ᴀɴᴅ ᴛɪᴍᴇ ᴠᴀʟᴜᴇ ᴀʀᴇ ɴᴜᴍʙᴇʀs.</b>")
    except Exception as e:
        await msg.reply_text(f"<b>ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ:</b> <code>{str(e)}</code>")


@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("<b>ᴜsᴀɢᴇ:</b> <code>/remove_premium user_id</code>")
        return
    try:
        user_id = int(msg.command[1])
        # kick from any gift channels first (before grants get orphaned)
        gift_count = 0
        try:
            gift_count = await revoke_user_gifts(client, user_id)
        except Exception:
            pass
        await remove_premium(user_id)
        extra = (
            f"\n<b>ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ:</b> <code>{gift_count}</code> ɢɪғᴛ ᴄʜᴀɴɴᴇʟ(s)."
            if gift_count else ""
        )
        await msg.reply_text(
            f"<b>ᴜsᴇʀ</b> <code>{user_id}</code> <b>ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ.</b>{extra}"
        )
    except ValueError:
        await msg.reply_text("<b>ᴜsᴇʀ_ɪᴅ ᴍᴜsᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.</b>")


@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    ist = timezone("Asia/Kolkata")
    premium_users_cursor = collection.find({})
    premium_user_list = ["<b>ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs:</b>"]
    current_time = datetime.now(ist)

    async for user in premium_users_cursor:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]
        tier = user.get("tier", "gold")
        tier_emoji = "🥇" if tier == "gold" else "💎"

        try:
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
            remaining_time = expiration_time - current_time

            if remaining_time.total_seconds() <= 0:
                await remove_premium(user_id)
                continue

            user_info = await client.get_users(user_id)
            username = user_info.username if user_info.username else "ɴᴏ ᴜsᴇʀɴᴀᴍᴇ"
            mention = user_info.mention
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            premium_user_list.append(
                f"{tier_emoji} <b>{tier.capitalize()}</b>\n"
                f"ᴜsᴇʀɪᴅ: <code>{user_id}</code>\n"
                f"ᴜsᴇʀ: @{username} | {mention}\n"
                f"ᴇxᴘɪʀʏ: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"<b>ᴜsᴇʀɪᴅ:</b> <code>{user_id}</code> | <b>ᴇʀʀᴏʀ:</b> <code>{str(e)}</code>"
            )

    if len(premium_user_list) == 1:
        await message.reply_text("<b>ɴᴏ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ғᴏᴜɴᴅ.</b>")
    else:
        await message.reply_text("\n\n".join(premium_user_list))


async def monitor_premium_expiry(client, user_id):
    ist = timezone("Asia/Kolkata")
    reminder_24h_sent = False
    final_reminder_sent = False

    while True:
        try:
            user = await collection.find_one({"user_id": user_id})
            if not user:
                break

            expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
            current_time = datetime.now(ist)
            time_remaining = expiration_time - current_time
            tier = user.get("tier", "gold")
            tier_emoji = "🥇" if tier == "gold" else "💎"

            # Auto remove on expiry
            if time_remaining.total_seconds() <= 0:
                # kick from any gift channels first
                gift_count = 0
                try:
                    gift_count = await revoke_user_gifts(client, user_id)
                except Exception as e:
                    print(f"Failed revoking gifts for {user_id}: {e}")
                await remove_premium(user_id)
                try:
                    extra = (
                        f"\n\n🎀 <b>ɢɪғᴛ ᴄʜᴀɴɴᴇʟ(s) ʀᴇᴍᴏᴠᴇᴅ:</b> <code>{gift_count}</code>"
                        if gift_count else ""
                    )
                    await client.send_message(
                        user_id,
                        f"{tier_emoji} <b>{tier.capitalize()} ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀᴇᴅ!</b>\n\n"
                        "ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ʜᴀs ʙᴇᴇɴ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʀᴇᴍᴏᴠᴇᴅ."
                        f"{extra}\n\n"
                        "ʀᴇɴᴇᴡ ᴘʀᴇᴍɪᴜᴍ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ᴇɴᴊᴏʏɪɴɢ ʏᴏᴜʀ ᴘᴇʀᴋs."
                    )
                except Exception:
                    pass
                break

            # 24h reminder
            if not reminder_24h_sent and time_remaining <= timedelta(days=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                try:
                    await client.send_message(
                        user_id,
                        f"<b>⏰ {tier_emoji} {tier.capitalize()} ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀʏ ʀᴇᴍɪɴᴅᴇʀ</b>\n\n"
                        f"ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀᴇs ɪɴ ʟᴇss ᴛʜᴀɴ 24 ʜᴏᴜʀs!\n"
                        f"<b>ᴇxᴘɪʀᴇs ᴏɴ:</b> {formatted_time}\n\n"
                        "ʀᴇɴᴇᴡ ɴᴏᴡ ᴛᴏ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴘᴇʀᴋs."
                    )
                    reminder_24h_sent = True
                except Exception as e:
                    print(f"Failed to send 24h reminder to {user_id}: {e}")

            # Final 1h reminder
            if not final_reminder_sent and time_remaining <= timedelta(hours=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                try:
                    await client.send_message(
                        user_id,
                        f"<b>🚨 {tier_emoji} ғɪɴᴀʟ ʀᴇᴍɪɴᴅᴇʀ — {tier.capitalize()} ᴘʀᴇᴍɪᴜᴍ</b>\n\n"
                        f"ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀᴇs ɪɴ ʟᴇss ᴛʜᴀɴ 1 ʜᴏᴜʀ!\n"
                        f"<b>ᴇxᴘɪʀᴇs ᴀᴛ:</b> {formatted_time}\n\n"
                        "ᴛʜɪs ɪs ʏᴏᴜʀ ʟᴀsᴛ ʀᴇᴍɪɴᴅᴇʀ. ʀᴇɴᴇᴡ ɴᴏᴡ!"
                    )
                    final_reminder_sent = True
                except Exception as e:
                    print(f"Failed to send final reminder to {user_id}: {e}")

            await asyncio.sleep(60)

        except Exception as e:
            print(f"Error monitoring premium expiry for user {user_id}: {e}")
            await asyncio.sleep(60)


async def auto_start_monitoring(client):
    global monitoring_started
    if monitoring_started:
        return

    monitoring_started = True
    print("Starting automatic premium monitoring...")

    ist = timezone("Asia/Kolkata")
    current_time = datetime.now(ist)

    try:
        async for user in collection.find({}):
            try:
                expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
                if expiration_time <= current_time:
                    await remove_premium(user["user_id"])
                    print(f"Auto-removed expired premium user: {user['user_id']}")
                else:
                    asyncio.create_task(monitor_premium_expiry(client, user["user_id"]))
                    print(f"Started monitoring premium user: {user['user_id']}")
            except Exception as e:
                print(f"Error processing premium user {user.get('user_id')}: {e}")
    except Exception as e:
        print(f"Error accessing premium users collection: {e}")

    print("Automatic premium monitoring started.")


@Bot.on_message(filters.command('start_premium_monitoring') & filters.private & admin)
async def start_monitoring_existing_users(client: Client, message: Message):
    await auto_start_monitoring(client)
    await message.reply("<b>sᴛᴀʀᴛᴇᴅ ᴍᴏɴɪᴛᴏʀɪɴɢ ᴀʟʟ ᴇxɪsᴛɪɴɢ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ғᴏʀ ᴇxᴘɪʀʏ ʀᴇᴍɪɴᴅᴇʀs.</b>")
