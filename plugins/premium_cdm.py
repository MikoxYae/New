import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import *
from helper_func import admin
from database.premium_database import *
from database.db_premium import *
from pytz import timezone
from datetime import datetime, timedelta

# Global variables to track monitoring status
monitoring_started = False

# Command to check premium plan
@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id  # Get user ID from the message

    # Get the premium status of the user
    status_message = await check_user_plan(user_id)

    # Send the response message to the user
    await message.reply(status_message)

# Command to add premium user
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
        time_unit = msg.command[3].lower()  # supports: s, m, h, d, y

        # Call add_premium function
        expiration_time = await add_premium(user_id, time_value, time_unit)

        # Notify the admin
        await msg.reply_text(
            f"✅ User `{user_id}` added as a premium user for {time_value} {time_unit}.\n"
            f"Expiration Time: `{expiration_time}`"
        )

        # Notify the user
        await client.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Premium Activated!\n\n"
                f"You have received premium access for `{time_value} {time_unit}`.\n"
                f"Expires on: `{expiration_time}`"
            ),
        )

        # Start monitoring this user for reminders
        asyncio.create_task(monitor_premium_expiry(client, user_id))

    except ValueError:
        await msg.reply_text("❌ Invalid input. Please ensure user ID and time value are numbers.")
    except Exception as e:
        await msg.reply_text(f"⚠️ An error occurred: `{str(e)}`")


# Command to remove premium user
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


# Command to list active premium users
@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    # Define IST timezone
    ist = timezone("Asia/Kolkata")

    # Retrieve all users from the collection
    premium_users_cursor = collection.find({})
    premium_user_list = ['Active Premium Users in database:']
    current_time = datetime.now(ist)  # Get current time in IST

    # Use async for to iterate over the async cursor
    async for user in premium_users_cursor:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        try:
            # Convert expiration_timestamp to a timezone-aware datetime object in IST
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)

            # Calculate remaining time
            remaining_time = expiration_time - current_time

            if remaining_time.total_seconds() <= 0:
                # Remove expired users from the database
                await collection.delete_one({"user_id": user_id})
                continue  # Skip to the next user if this one is expired

            # If not expired, retrieve user info
            user_info = await client.get_users(user_id)
            username = user_info.username if user_info.username else "No Username"
            first_name = user_info.first_name
            mention=user_info.mention

            # Calculate days, hours, minutes, seconds left
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            # Add user details to the list
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

    if len(premium_user_list) == 1:  # No active users found
        await message.reply_text("I found 0 active premium users in my DB")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)

# Super Premium Commands

@Bot.on_message(filters.command('my_super_plan') & filters.private)
async def check_super_plan(client: Client, message: Message):
    user_id = message.from_user.id
    status_message = await check_super_premium_plan(user_id)
    await message.reply(status_message)

@Bot.on_message(filters.command('add_super_premium') & filters.private & admin)
async def add_super_premium_user_command(client, msg):
    if len(msg.command) != 4:
        await msg.reply_text(
            "Usage: /add_super_premium <user_id> <time_value> <time_unit>\n\n"
            "Time Units:\n"
            "s - seconds\n"
            "m - minutes\n"
            "h - hours\n"
            "d - days\n"
            "y - years\n\n"
            "Examples:\n"
            "/add_super_premium 123456789 30 m → 30 minutes\n"
            "/add_super_premium 123456789 2 h → 2 hours\n"
            "/add_super_premium 123456789 1 d → 1 day\n"
            "/add_super_premium 123456789 1 y → 1 year"
        )
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()

        expiration_time = await add_super_premium(user_id, time_value, time_unit)

        await msg.reply_text(
            f"✅ User `{user_id}` added as a super premium user for {time_value} {time_unit}.\n"
            f"Expiration Time: `{expiration_time}`"
        )

        try:
            await client.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 Super Premium Activated!\n\n"
                    f"You have received super premium access for `{time_value} {time_unit}`.\n"
                    f"Expires on: `{expiration_time}`\n\n"
                    f"Benefits:\n"
                    f"• No token verification required\n"
                    f"• Files can be forwarded (if enabled by admin)"
                ),
            )
        except:
            pass

        # Start monitoring this user for super premium reminders
        asyncio.create_task(monitor_super_premium_expiry(client, user_id))

    except ValueError:
        await msg.reply_text("❌ Invalid input. Please ensure user ID and time value are numbers.")
    except Exception as e:
        await msg.reply_text(f"⚠️ An error occurred: `{str(e)}`")

@Bot.on_message(filters.command('remove_super_premium') & filters.private & admin)
async def remove_super_premium_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("Usage: /remove_super_premium user_id")
        return
    try:
        user_id = int(msg.command[1])
        await remove_super_premium(user_id)
        await msg.reply_text(f"User {user_id} has been removed from super premium.")
        
        try:
            await client.send_message(
                chat_id=user_id,
                text="Your super premium access has been revoked."
            )
        except:
            pass
            
    except ValueError:
        await msg.reply_text("User ID must be an integer.")

@Bot.on_message(filters.command('super_premium_users') & filters.private & admin)
async def list_super_premium_users_command(client, message):
    ist = timezone("Asia/Kolkata")
    super_premium_users_cursor = super_premium_collection.find({})
    super_premium_user_list = ['Active Super Premium Users in database:']
    current_time = datetime.now(ist)

    async for user in super_premium_users_cursor:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        try:
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
            remaining_time = expiration_time - current_time

            if remaining_time.total_seconds() <= 0:
                await super_premium_collection.delete_one({"user_id": user_id})
                continue

            user_info = await client.get_users(user_id)
            username = user_info.username if user_info.username else "No Username"
            first_name = user_info.first_name
            mention = user_info.mention

            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            super_premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"User: @{username}\n"
                f"Name: {mention}\n"
                f"Expiry: {expiry_info}"
            )
        except Exception as e:
            super_premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"Error: Unable to fetch user details ({str(e)})"
            )

    if len(super_premium_user_list) == 1:
        await message.reply_text("I found 0 active super premium users in my DB")
    else:
        await message.reply_text("\n\n".join(super_premium_user_list), parse_mode=None)

# Premium Expiry Monitor Functions

async def monitor_premium_expiry(client, user_id):
    """Monitor a premium user for expiry reminders"""
    ist = timezone("Asia/Kolkata")
    reminder_24h_sent = False
    final_reminder_sent = False
    
    while True:
        try:
            # Check if user still has premium
            user = await collection.find_one({"user_id": user_id})
            if not user:
                break  # User no longer has premium
            
            expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
            current_time = datetime.now(ist)
            time_remaining = expiration_time - current_time
            
            # If expired, stop monitoring
            if time_remaining.total_seconds() <= 0:
                break
            
            # Send 24-hour reminder
            if not reminder_24h_sent and time_remaining <= timedelta(days=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                message = (
                    f"<b>⏰ Premium Expiry Reminder</b>\n\n"
                    f"<b>Your premium access will expire in less than 24 hours!</b>\n\n"
                    f"<b>Expires on: {formatted_time}</b>\n\n"
                    f"<b>Renew your premium to continue enjoying uninterrupted access.</b>"
                )
                
                try:
                    await client.send_message(user_id, message)
                    reminder_24h_sent = True
                    print(f"Sent 24h premium reminder to user {user_id}")
                except Exception as e:
                    print(f"Failed to send 24h premium reminder to {user_id}: {e}")
            
            # Send final reminder (1 hour before expiry)
            if not final_reminder_sent and time_remaining <= timedelta(hours=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                message = (
                    f"<b>🚨 Final Premium Reminder</b>\n\n"
                    f"<b>Your premium access will expire in less than 1 hour!</b>\n\n"
                    f"<b>Expires at: {formatted_time}</b>\n\n"
                    f"<b>This is your final reminder to renew premium access.</b>"
                )
                
                try:
                    await client.send_message(user_id, message)
                    final_reminder_sent = True
                    print(f"Sent final premium reminder to user {user_id}")
                except Exception as e:
                    print(f"Failed to send final premium reminder to {user_id}: {e}")
            
            # Both reminders sent, stop monitoring
            if reminder_24h_sent and final_reminder_sent:
                break
            
            # Wait 10 minutes before next check
            await asyncio.sleep(600)
            
        except Exception as e:
            print(f"Error monitoring premium expiry for user {user_id}: {e}")
            await asyncio.sleep(600)

async def monitor_super_premium_expiry(client, user_id):
    """Monitor a super premium user for expiry reminders"""
    ist = timezone("Asia/Kolkata")
    reminder_24h_sent = False
    final_reminder_sent = False
    
    while True:
        try:
            # Check if user still has super premium
            user = await super_premium_collection.find_one({"user_id": user_id})
            if not user:
                break  # User no longer has super premium
            
            expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
            current_time = datetime.now(ist)
            time_remaining = expiration_time - current_time
            
            # If expired, stop monitoring
            if time_remaining.total_seconds() <= 0:
                break
            
            # Send 24-hour reminder
            if not reminder_24h_sent and time_remaining <= timedelta(days=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                message = (
                    f"<b>⏰ Super Premium Expiry Reminder</b>\n\n"
                    f"<b>Your super premium access will expire in less than 24 hours!</b>\n\n"
                    f"<b>Expires on: {formatted_time}</b>\n\n"
                    f"<b>Renew your super premium to continue enjoying uninterrupted access.</b>"
                )
                
                try:
                    await client.send_message(user_id, message)
                    reminder_24h_sent = True
                    print(f"Sent 24h super premium reminder to user {user_id}")
                except Exception as e:
                    print(f"Failed to send 24h super premium reminder to {user_id}: {e}")
            
            # Send final reminder (1 hour before expiry)
            if not final_reminder_sent and time_remaining <= timedelta(hours=1):
                formatted_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S IST')
                message = (
                    f"<b>🚨 Final Super Premium Reminder</b>\n\n"
                    f"<b>Your super premium access will expire in less than 1 hour!</b>\n\n"
                    f"<b>Expires at: {formatted_time}</b>\n\n"
                    f"<b>This is your final reminder to renew super premium access.</b>"
                )
                
                try:
                    await client.send_message(user_id, message)
                    final_reminder_sent = True
                    print(f"Sent final super premium reminder to user {user_id}")
                except Exception as e:
                    print(f"Failed to send final super premium reminder to {user_id}: {e}")
            
            # Both reminders sent, stop monitoring
            if reminder_24h_sent and final_reminder_sent:
                break
            
            # Wait 10 minutes before next check
            await asyncio.sleep(600)
            
        except Exception as e:
            print(f"Error monitoring super premium expiry for user {user_id}: {e}")
            await asyncio.sleep(600)

# Auto-start monitoring for existing premium users
async def auto_start_monitoring(client):
    """Automatically start monitoring all existing premium users"""
    global monitoring_started
    
    if monitoring_started:
        return
    
    monitoring_started = True
    print("🔄 Starting automatic premium monitoring...")
    
    ist = timezone("Asia/Kolkata")
    current_time = datetime.now(ist)
    
    # Monitor regular premium users
    try:
        async for user in collection.find({}):
            try:
                expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
                if expiration_time > current_time:  # Only monitor active users
                    asyncio.create_task(monitor_premium_expiry(client, user["user_id"]))
                    print(f"Started monitoring premium user: {user['user_id']}")
            except Exception as e:
                print(f"Error starting monitoring for premium user {user.get('user_id')}: {e}")
    except Exception as e:
        print(f"Error accessing premium users collection: {e}")
    
    # Monitor super premium users
    try:
        async for user in super_premium_collection.find({}):
            try:
                expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
                if expiration_time > current_time:  # Only monitor active users
                    asyncio.create_task(monitor_super_premium_expiry(client, user["user_id"]))
                    print(f"Started monitoring super premium user: {user['user_id']}")
            except Exception as e:
                print(f"Error starting monitoring for super premium user {user.get('user_id')}: {e}")
    except Exception as e:
        print(f"Error accessing super premium users collection: {e}")
    
    print("✅ Automatic premium monitoring started successfully!")

# Manual command to start monitoring (for admin use)
@Bot.on_message(filters.command('start_premium_monitoring') & filters.private & admin)
async def start_monitoring_existing_users(client: Client, message: Message):
    """Start monitoring all existing premium users"""
    await auto_start_monitoring(client)
    await message.reply("✅ Started monitoring all existing premium and super premium users for expiry reminders.")

# COMMENTED OUT: Auto-trigger monitoring when bot starts
# This was interfering with the /start command, so it's commented out
# If you want automatic monitoring, use /start_premium_monitoring command instead

# @Bot.on_message(filters.private)
# async def trigger_auto_monitoring(client: Client, message: Message):
#     """Automatically start monitoring when bot receives any message"""
#     global monitoring_started
#     
#     if not monitoring_started:
#         asyncio.create_task(auto_start_monitoring(client))
