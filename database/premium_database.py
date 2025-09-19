import motor.motor_asyncio
from config import DB_URI, DB_NAME
from pytz import timezone
from datetime import datetime, timedelta

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]
super_premium_collection = database['super-premium-users']

async def is_super_premium_user(user_id):
    user = await super_premium_collection.find_one({"user_id": user_id})
    return user is not None

async def remove_super_premium(user_id):
    await super_premium_collection.delete_one({"user_id": user_id})

async def remove_expired_super_premium_users():
    ist = timezone("Asia/Kolkata")
    current_time = datetime.now(ist)

    async for user in super_premium_collection.find({}):
        expiration = user.get("expiration_timestamp")
        if not expiration:
            continue

        try:
            expiration_time = datetime.fromisoformat(expiration).astimezone(ist)
            if expiration_time <= current_time:
                await super_premium_collection.delete_one({"user_id": user["user_id"]})
        except Exception as e:
            print(f"Error removing super premium user {user.get('user_id')}: {e}")

async def list_super_premium_users():
    ist = timezone("Asia/Kolkata")
    super_premium_users = super_premium_collection.find({})
    super_premium_user_list = []

    async for user in super_premium_users:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
        remaining_time = expiration_time - datetime.now(ist)

        if remaining_time.total_seconds() > 0:
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )

            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"
            formatted_expiry_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST')
            super_premium_user_list.append(f"UserID: {user_id} - Expiry: {expiry_info} (Expires at {formatted_expiry_time})")

    return super_premium_user_list

async def add_super_premium(user_id, time_value, time_unit):
    time_unit = time_unit.lower()
    ist = timezone("Asia/Kolkata")
    now = datetime.now(ist)
    
    if time_unit == 's':
        expiration_time = now + timedelta(seconds=time_value)
    elif time_unit == 'm':
        expiration_time = now + timedelta(minutes=time_value)
    elif time_unit == 'h':
        expiration_time = now + timedelta(hours=time_value)
    elif time_unit == 'd':
        expiration_time = now + timedelta(days=time_value)
    elif time_unit == 'y':
        expiration_time = now + timedelta(days=365 * time_value)
    else:
        raise ValueError("Invalid time unit. Use 's', 'm', 'h', 'd', or 'y'.")

    super_premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_time.isoformat(),
        "reminder_24h_sent": False,
        "final_reminder_sent": False
    }

    await super_premium_collection.update_one(
        {"user_id": user_id},
        {"$set": super_premium_data},
        upsert=True
    )

    formatted_expiration = expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST')
    return formatted_expiration

async def check_super_premium_plan(user_id):
    user = await super_premium_collection.find_one({"user_id": user_id})
    if user:
        expiration_timestamp = user["expiration_timestamp"]
        expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(timezone("Asia/Kolkata"))
        
        remaining_time = expiration_time - datetime.now(timezone("Asia/Kolkata"))
        
        if remaining_time.total_seconds() > 0:
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            validity_info = f"Your super premium plan is active. {days}d {hours}h {minutes}m {seconds}s left."
            return validity_info
        else:
            return "Your super premium plan has expired."
    else:
        return "You do not have a super premium plan."

# Get super premium users expiring in 24 hours who haven't received 24h reminder
async def get_super_users_expiring_24h():
    ist = timezone("Asia/Kolkata")
    current_time = datetime.now(ist)
    
    users_to_remind = []
    async for user in super_premium_collection.find({"reminder_24h_sent": {"$ne": True}}):
        expiration_timestamp = user.get("expiration_timestamp")
        if not expiration_timestamp:
            continue
            
        try:
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
            time_remaining = expiration_time - current_time
            
            # Check if expires within 24 hours and hasn't expired yet
            if timedelta(0) < time_remaining <= timedelta(hours=24):
                users_to_remind.append({
                    "user_id": user["user_id"],
                    "expiration_time": expiration_time
                })
        except Exception as e:
            print(f"Error checking super premium user {user.get('user_id')}: {e}")
    
    return users_to_remind

# Get super premium users expiring in 5 minutes who haven't received final reminder (changed from 1 minute to 5 minutes)
async def get_super_users_expiring_1min():
    ist = timezone("Asia/Kolkata")
    current_time = datetime.now(ist)
    
    users_to_remind = []
    async for user in super_premium_collection.find({"final_reminder_sent": {"$ne": True}}):
        expiration_timestamp = user.get("expiration_timestamp")
        if not expiration_timestamp:
            continue
            
        try:
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
            time_remaining = expiration_time - current_time
            
            # Check if expires within 5 minutes and hasn't expired yet (increased window)
            if timedelta(0) < time_remaining <= timedelta(minutes=5):
                users_to_remind.append({
                    "user_id": user["user_id"],
                    "expiration_time": expiration_time
                })
                print(f"Found super premium user {user['user_id']} expiring in {time_remaining}")
        except Exception as e:
            print(f"Error checking super premium user {user.get('user_id')}: {e}")
    
    return users_to_remind

# Mark 24h reminder as sent for super premium
async def mark_super_24h_reminder_sent(user_id):
    await super_premium_collection.update_one(
        {"user_id": user_id},
        {"$set": {"reminder_24h_sent": True}}
    )

# Mark final reminder as sent for super premium
async def mark_super_final_reminder_sent(user_id):
    await super_premium_collection.update_one(
        {"user_id": user_id},
        {"$set": {"final_reminder_sent": True}}
    )
