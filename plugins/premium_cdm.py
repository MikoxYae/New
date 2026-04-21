"""
Replace your existing plugins/premium_cdm.py with this file.

Changes vs the original:
  • When /addpremium runs, a styled PAYMENT RECEIPT image is generated and:
      1. sent to the user (DM)
      2. sent to OWNER_ID (so you keep a copy)
  • Same receipt image is sent on auto-renewal failures? No — only on activation.
  • Receipt also goes out from the payment-screenshot flow (cbb.py) by reusing
    the same generate_receipt() function. (See cbb_patch.py if you want that.)

Drop receipt_generator.py into the same plugins/ folder.
"""

import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from pytz import timezone

from bot import Bot
from config import OWNER_ID
from helper_func import admin
from database.db_premium import (
    add_premium, remove_premium, check_user_plan, collection,
)
from plugins.receipt_generator import generate_receipt, format_ist, random_receipt_id

monitoring_started = False
IST = timezone("Asia/Kolkata")


# ──────────────────────────────────────────────────────────────────────────────
def _premium_label(tier: str) -> str:
    tier = (tier or "gold").lower()
    if tier == "platinum":
        return "Platinum Premium"
    return "Gold Premium"


def _plan_label(time_value: int, time_unit: str) -> str:
    unit_map = {"s": "SEC", "m": "MIN", "h": "HOUR", "d": "DAY", "y": "YEAR"}
    unit = unit_map.get(time_unit.lower(), time_unit.upper())
    if time_value > 1 and not unit.endswith("S"):
        unit += "S"
    return f"{time_value} {unit}"


async def _send_receipt(client, user_id: int, name: str, tier: str,
                        time_value: int, time_unit: str, expiration_str: str):
    """Render the receipt PNG and DM it to the user + owner."""
    try:
        # Parse the expiration timestamp the DB returned
        try:
            exp_dt = datetime.fromisoformat(expiration_str).astimezone(IST)
            expires_pretty = format_ist(exp_dt)
        except Exception:
            expires_pretty = str(expiration_str)

        rid = random_receipt_id()
        issued = datetime.now(IST)

        bio = generate_receipt(
            name=name or "User",
            user_id=user_id,
            premium=_premium_label(tier),
            plan=_plan_label(time_value, time_unit),
            expires=expires_pretty,
            issued_at=issued,
            receipt_id=rid,
            status="PAID",
            brand="Angle Baby",
        )
        png_bytes = bio.getvalue()

        user_caption = (
            f"<b>🧾 Payment Receipt</b>\n\n"
            f"<b>Receipt ID:</b> <code>{rid}</code>\n"
            f"<b>Plan:</b> {_plan_label(time_value, time_unit)}\n"
            f"<b>Premium:</b> {_premium_label(tier)}\n"
            f"<b>Expires:</b> {expires_pretty}\n\n"
            f"<i>Save this receipt for your records.</i>"
        )
        owner_caption = (
            f"<b>🧾 Receipt Issued</b>\n\n"
            f"<b>User:</b> <code>{user_id}</code> ({name})\n"
            f"<b>Receipt ID:</b> <code>{rid}</code>\n"
            f"<b>Plan:</b> {_plan_label(time_value, time_unit)}\n"
            f"<b>Premium:</b> {_premium_label(tier)}\n"
            f"<b>Expires:</b> {expires_pretty}"
        )

        # Send to user
        try:
            from io import BytesIO
            await client.send_photo(
                chat_id=user_id,
                photo=BytesIO(png_bytes),
                caption=user_caption,
            )
        except Exception as e:
            print(f"[receipt] failed to DM user {user_id}: {e}")

        # Send to owner
        try:
            from io import BytesIO
            await client.send_photo(
                chat_id=OWNER_ID,
                photo=BytesIO(png_bytes),
                caption=owner_caption,
            )
        except Exception as e:
            print(f"[receipt] failed to DM owner: {e}")

    except Exception as e:
        print(f"[receipt] generation error for {user_id}: {e}")


# ──────────────────────────────────────────────────────────────────────────────
@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id
    status_message = await check_user_plan(user_id)
    await message.reply(status_message)


@Bot.on_message(filters.command('addpremium') & filters.private & admin)
async def add_premium_user_command(client: Client, msg: Message):
    if len(msg.command) not in (4, 5):
        await msg.reply_text(
            "<b>Usage:</b> /addpremium user_id time_value time_unit tier\n\n"
            "<b>Tiers:</b>\n"
            "🥇 gold — Token bypass + Protect Content bypass\n"
            "💎 platinum — Token bypass + Protect Content bypass + Force Sub bypass\n\n"
            "<b>Time Units:</b> s | m | h | d | y\n\n"
            "<b>Examples:</b>\n"
            "/addpremium 123456789 1 d gold\n"
            "/addpremium 123456789 1 d platinum"
        )
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()
        tier = msg.command[4].lower() if len(msg.command) == 5 else "gold"

        if tier not in ("gold", "platinum"):
            return await msg.reply_text("Invalid tier. Use: gold or platinum")

        expiration_time = await add_premium(user_id, time_value, time_unit, tier)
        tier_emoji = "🥇" if tier == "gold" else "💎"
        perks = (
            "Token bypass\nProtect Content bypass"
            if tier == "gold"
            else "Token bypass\nProtect Content bypass\nForce Subscribe bypass"
        )

        # Owner ack
        await msg.reply_text(
            f"User {user_id} added as {tier_emoji} {tier.capitalize()} Premium "
            f"for {time_value}{time_unit}.\nExpiration: {expiration_time}"
        )

        # Activation message to user
        try:
            await client.send_message(
                chat_id=user_id,
                text=(
                    f"{tier_emoji} <b>{tier.capitalize()} Premium Activated!</b>\n\n"
                    f"Duration: <b>{time_value}{time_unit}</b>\n"
                    f"Expires on: <b>{expiration_time}</b>\n\n"
                    f"<b>Your perks:</b>\n{perks}"
                ),
            )
        except Exception as e:
            print(f"[addpremium] activation msg failed for {user_id}: {e}")

        # ── NEW: send receipt to user + owner ──────────────────────────────
        try:
            user_info = await client.get_users(user_id)
            full_name = (
                f"{user_info.first_name or ''} {user_info.last_name or ''}".strip()
                or user_info.username or str(user_id)
            )
        except Exception:
            full_name = str(user_id)

        await _send_receipt(
            client, user_id, full_name, tier, time_value, time_unit, expiration_time
        )

        asyncio.create_task(monitor_premium_expiry(client, user_id))

    except ValueError:
        await msg.reply_text("Invalid input. Ensure user ID and time value are numbers.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {str(e)}")


@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("Usage: /remove_premium user_id")
        return
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"User {user_id} has been removed from premium.")
    except ValueError:
        await msg.reply_text("user_id must be an integer.")


@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    premium_users_cursor = collection.find({})
    premium_user_list = ["<b>Active Premium Users:</b>"]
    current_time = datetime.now(IST)

    async for user in premium_users_cursor:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]
        tier = user.get("tier", "gold")
        tier_emoji = "🥇" if tier == "gold" else "💎"

        try:
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(IST)
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
                f"{tier_emoji} <b>{tier.capitalize()}</b>\n"
                f"UserID: <code>{user_id}</code>\n"
                f"User: @{username} | {mention}\n"
                f"Expiry: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"UserID: <code>{user_id}</code> | Error: {str(e)}"
            )

    if len(premium_user_list) == 1:
        await message.reply_text("No active premium users found.")
    else:
        await message.reply_text("\n\n".join(premium_user_list))


async def monitor_premium_expiry(client, user_id):
    reminder_24h_sent = False
    final_reminder_sent = False

    while True:
        try:
            user = await collection.find_one({"user_id": user_id})
            if not user:
                break

            expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(IST)
            current_time = datetime.now(IST)
            time_remaining = expiration_time - current_time
            tier = user.get("tier", "gold")
            tier_emoji = "🥇" if tier == "gold" else "💎"

            if time_remaining.total_seconds() <= 0:
                await remove_premium(user_id)
                try:
                    await client.send_message(
                        user_id,
                        f"{tier_emoji} <b>{tier.capitalize()} Premium Expired!</b>\n\n"
                        "Your premium access has been automatically removed.\n\n"
                        "Renew premium to continue enjoying your perks."
                    )
                except Exception:
                    pass
                break

            if not reminder_24h_sent and time_remaining <= timedelta(days=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                try:
                    await client.send_message(
                        user_id,
                        f"<b>⏰ {tier_emoji} {tier.capitalize()} Premium Expiry Reminder</b>\n\n"
                        f"Your premium expires in less than 24 hours!\n"
                        f"<b>Expires on:</b> {formatted_time}\n\n"
                        "Renew now to keep your perks."
                    )
                    reminder_24h_sent = True
                except Exception as e:
                    print(f"Failed to send 24h reminder to {user_id}: {e}")

            if not final_reminder_sent and time_remaining <= timedelta(hours=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                try:
                    await client.send_message(
                        user_id,
                        f"<b>🚨 {tier_emoji} Final Reminder — {tier.capitalize()} Premium</b>\n\n"
                        f"Your premium expires in less than 1 hour!\n"
                        f"<b>Expires at:</b> {formatted_time}\n\n"
                        "This is your last reminder. Renew now!"
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
    current_time = datetime.now(IST)
    try:
        async for user in collection.find({}):
            try:
                expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(IST)
                if expiration_time <= current_time:
                    await remove_premium(user["user_id"])
                else:
                    asyncio.create_task(monitor_premium_expiry(client, user["user_id"]))
            except Exception as e:
                print(f"Error processing premium user {user.get('user_id')}: {e}")
    except Exception as e:
        print(f"Error accessing premium users collection: {e}")
    print("Automatic premium monitoring started.")


@Bot.on_message(filters.command('start_premium_monitoring') & filters.private & admin)
async def start_monitoring_existing_users(client: Client, message: Message):
    await auto_start_monitoring(client)
    await message.reply("Started monitoring all existing premium users for expiry reminders.")
