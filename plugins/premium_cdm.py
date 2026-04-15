import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import Bot
from helper_func import admin
from database.db_premium import *
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
    if len(msg.command) != 4:
        await msg.reply_text(
            "Usage: /addpremium <user_id> <time_value> <time_unit>\n\n"
            "Time Units:\n"
            "s - seconds\n"
            "m - minutes\n"
            "h - hours\n"
            "d - days\n"
            "y - years\n\n"
            "Examples:\n"
            "/addpremium 123456789 30 m → 30 minutes\n"
            "/addpremium 123456789 2 h → 2 hours\n"
            "/addpremium 123456789 1 d → 1 day\n"
            "/addpremium 123456789 1 y → 1 year"
        )
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()
        expiration_time = await add_premium(user_id, time_value, time_unit)

        await msg.reply_text(
            f"✅ User `{user_id}` added as a premium user for {time_value} {time_unit}.\n"
            f"Expiration Time: `{expiration_time}`"
        )

        await client.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Premium Activated!\n\n"
                f"You have received premium access for `{time_value} {time_unit}`.\n"
                f"Expires on: `{expiration_time}`"
            ),
        )

        asyncio.create_task(monitor_premium_expiry(client, user_id))

    except ValueError:
        await msg.reply_text("❌ Invalid input. Please ensure user ID and time value are numbers.")
    except Exception as e:
        await msg.reply_text(f"⚠️ An error occurred: `{str(e)}`")

@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("useage: /remove_premium user_id ")
        return
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"User {user_id} has been removed.")
    except ValueError:
        await msg.reply_text("user_id must be an integer or not available in database.")

@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    ist = timezone("Asia/Kolkata")
    premium_users_cursor = collection.find({})
    premium_user_list = ['Active Premium Users in database:']
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
            username = user_info.username if user_info.username else "No Username"
            mention = user_info.mention
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"User: @{username}\n"
                f"Name: {mention}\n"
                f"Expiry: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"Error: Unable to fetch user details ({str(e)})"
            )

    if len(premium_user_list) == 1:
        await message.reply_text("I found 0 active premium users in my DB")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)


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

            # ── AUTO REMOVE on expiry ─────────────────────────────
            if time_remaining.total_seconds() <= 0:
                await remove_premium(user_id)
                try:
                    await client.send_message(
                        user_id,
                        "<b>❌ Premium Expired!</b>\n\n"
                        "Your premium access has been automatically removed.\n\n"
                        "💳 <b>Renew premium to continue enjoying uninterrupted access!</b>"
                    )
                except Exception:
                    pass
                break

            # ── 24h reminder ──────────────────────────────────────
            if not reminder_24h_sent and time_remaining <= timedelta(days=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                try:
                    await client.send_message(
                        user_id,
                        f"<b>⏰ Premium Expiry Reminder</b>\n\n"
                        f"Your premium access will expire in less than 24 hours!\n\n"
                        f"<b>Expires on:</b> {formatted_time}\n\n"
                        f"Renew your premium to continue enjoying uninterrupted access."
                    )
                    reminder_24h_sent = True
                except Exception as e:
                    print(f"Failed to send 24h reminder to {user_id}: {e}")

            # ── Final 1h reminder ─────────────────────────────────
            if not final_reminder_sent and time_remaining <= timedelta(hours=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                try:
                    await client.send_message(
                        user_id,
                        f"<b>🚨 Final Premium Reminder</b>\n\n"
                        f"Your premium access will expire in less than 1 hour!\n\n"
                        f"<b>Expires at:</b> {formatted_time}\n\n"
                        f"This is your final reminder to renew premium access."
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
    print("🔄 Starting automatic premium monitoring...")

    ist = timezone("Asia/Kolkata")
    current_time = datetime.now(ist)

    try:
        async for user in collection.find({}):
            try:
                expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
                # Auto-remove already expired users on startup
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

    print("✅ Automatic premium monitoring started successfully!")


@Bot.on_message(filters.command('start_premium_monitoring') & filters.private & admin)
async def start_monitoring_existing_users(client: Client, message: Message):
    await auto_start_monitoring(client)
    await message.reply("✅ Started monitoring all existing premium users for expiry reminders.")
