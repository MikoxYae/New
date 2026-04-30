import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import Bot
from helper_func import admin
from database.db_premium import *
from database.db_plans import revoke_user_gifts
from pytz import timezone
from datetime import datetime, timedelta
from .receipt_image import build_receipt_image

monitoring_started = False

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id
    status_message = await check_user_plan(user_id)
    await message.reply(status_message)


_UNIT_LABELS = {"s": "sᴇᴄᴏɴᴅs", "m": "ᴍɪɴᴜᴛᴇs", "h": "ʜᴏᴜʀs", "d": "ᴅᴀʏs", "y": "ʏᴇᴀʀs"}


@Bot.on_message(filters.command('addpremium') & filters.private & admin)
async def add_premium_user_command(client, msg):
    if len(msg.command) != 4:
        await msg.reply_text(
            "<b>ᴜsᴀɢᴇ:</b> <code>/addpremium user_id time_value time_unit</code>\n\n"
            "<b>ᴘʟᴀɴ:</b> 🥇 ɢᴏʟᴅ (ᴏɴʟʏ ᴛɪᴇʀ)\n"
            "<b>ᴘᴇʀᴋs:</b> ғʀᴇᴇ ʟɪɴᴋ ʙʏᴘᴀss + ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss\n\n"
            "<b>ᴛɪᴍᴇ ᴜɴɪᴛs:</b> <code>s</code> | <code>m</code> | <code>h</code> | <code>d</code> | <code>y</code>\n\n"
            "<b>ᴇxᴀᴍᴘʟᴇs:</b>\n"
            "<code>/addpremium 123456789 1 d</code>\n"
            "<code>/addpremium 123456789 30 d</code>"
        )
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()

        expiration_time = await add_premium(user_id, time_value, time_unit, "gold")

        # Pretty duration
        unit_label = _UNIT_LABELS.get(time_unit, time_unit)
        duration_str = f"{time_value} {unit_label}"

        # Active date (now, IST)
        ist = timezone("Asia/Kolkata")
        active_str = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %p IST')

        # Admin confirmation
        await msg.reply_text(
            f"<b>✅ ᴘʀᴇᴍɪᴜᴍ ɢʀᴀɴᴛᴇᴅ — ᴍᴀɴᴜᴀʟ ᴀᴅᴅ</b>\n\n"
            f"<b>ᴜsᴇʀ:</b> <code>{user_id}</code>\n"
            f"<b>ᴘʟᴀɴ:</b> 🥇 ɢᴏʟᴅ\n"
            f"<b>ᴅᴜʀᴀᴛɪᴏɴ:</b> <code>{duration_str}</code>\n"
            f"<b>ᴇxᴘɪʀᴇs:</b> <code>{expiration_time}</code>\n\n"
            f"<i>ʀᴇᴄᴇɪᴘᴛ sᴇɴᴛ ᴛᴏ ᴜsᴇʀ.</i>"
        )

        # User receipt — same template as auto receipt, BUT
        # no order_id / txn_id / amount (this is a manual grant).
        try:
            user_info = await client.get_users(user_id)
            user_name = user_info.first_name or "—"
            if user_info.last_name:
                user_name = f"{user_name} {user_info.last_name}"
        except Exception:
            user_name = "—"

        # Build PNG receipt and deliver as a downloadable document.
        receipt_img = build_receipt_image(
            title="PREMIUM RECEIPT",
            subtitle="MANUALLY GRANTED",
            user_name=user_name,
            user_id=user_id,
            plan_type=f"GOLD ({duration_str})",
            active_date=active_str,
            expire_date=str(expiration_time),
            granted_by="ADMIN",
        )
        receipt_img.name = f"receipt_{user_id}.png"

        receipt_caption = (
            "<b>🧾 ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ — ʀᴇᴄᴇɪᴘᴛ</b>\n\n"
            f"🥇 <b>ᴘʟᴀɴ:</b> ɢᴏʟᴅ ({duration_str})\n"
            f"⏳ <b>ᴇxᴘɪʀᴇs:</b> <code>{expiration_time}</code>\n\n"
            "<b>ʏᴏᴜʀ ᴘᴇʀᴋs:</b>\n"
            "✅ ғʀᴇᴇ ʟɪɴᴋ ʙʏᴘᴀss\n"
            "✅ ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss\n\n"
            "<i>🎉 ᴇɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss! ᴋᴇᴇᴘ ᴛʜᴇ ʀᴇᴄᴇɪᴘᴛ ғᴏʀ ʏᴏᴜʀ ʀᴇᴄᴏʀᴅs.</i>"
        )

        try:
            await client.send_document(
                chat_id=user_id,
                document=receipt_img,
                file_name=receipt_img.name,
                caption=receipt_caption,
            )
        except Exception as e:
            await msg.reply_text(
                f"<b>⚠️ ᴄᴏᴜʟᴅ ɴᴏᴛ ᴅᴍ ᴜsᴇʀ:</b> <code>{e}</code>"
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
                f"🥇 <b>ɢᴏʟᴅ</b>\n"
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
                        f"🥇 <b>ɢᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀᴇᴅ!</b>\n\n"
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
                        f"<b>⏰ 🥇 ɢᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀʏ ʀᴇᴍɪɴᴅᴇʀ</b>\n\n"
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
                        f"<b>🚨 🥇 ғɪɴᴀʟ ʀᴇᴍɪɴᴅᴇʀ — ɢᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ</b>\n\n"
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
