import motor.motor_asyncio
  from config import DB_URI, DB_NAME
  from pytz import timezone
  from datetime import datetime, timedelta

  dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
  database = dbclient[DB_NAME]
  collection = database['premium-users']

  # Check if the user is a premium user (any tier)
  async def is_premium_user(user_id):
      return await get_premium_tier(user_id) is not None

  # Get premium tier: returns 'gold', 'platinum', or None if not premium / expired
  async def get_premium_tier(user_id):
      ist = timezone("Asia/Kolkata")
      user = await collection.find_one({"user_id": user_id})
      if not user:
          return None
      try:
          expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
          if expiration_time <= datetime.now(ist):
              return None
      except Exception:
          return None
      return user.get("tier", "gold")

  # Remove premium user
  async def remove_premium(user_id):
      await collection.delete_one({"user_id": user_id})

  # Remove expired users
  async def remove_expired_users():
      ist = timezone("Asia/Kolkata")
      current_time = datetime.now(ist)
      async for user in collection.find({}):
          expiration = user.get("expiration_timestamp")
          if not expiration:
              continue
          try:
              expiration_time = datetime.fromisoformat(expiration).astimezone(ist)
              if expiration_time <= current_time:
                  await collection.delete_one({"user_id": user["user_id"]})
          except Exception as e:
              print(f"Error removing user {user.get('user_id')}: {e}")

  # List active premium users
  async def list_premium_users():
      ist = timezone("Asia/Kolkata")
      premium_users = collection.find({})
      premium_user_list = []
      async for user in premium_users:
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
              tier = user.get("tier", "gold")
              premium_user_list.append(
                  f"UserID: {user_id} | Tier: {tier.capitalize()} - Expiry: {expiry_info} (Expires at {formatted_expiry_time})"
              )
      return premium_user_list

  # Add premium user with tier (gold / platinum)
  async def add_premium(user_id, time_value, time_unit, tier="gold"):
      time_unit = time_unit.lower()
      tier = tier.lower()
      if tier not in ("gold", "platinum"):
          raise ValueError("Invalid tier. Use 'gold' or 'platinum'.")

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

      premium_data = {
          "user_id": user_id,
          "expiration_timestamp": expiration_time.isoformat(),
          "tier": tier,
          "reminder_24h_sent": False,
          "final_reminder_sent": False
      }

      await collection.update_one(
          {"user_id": user_id},
          {"$set": premium_data},
          upsert=True
      )

      return expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST')

  # Check if a user has an active premium plan
  async def check_user_plan(user_id):
      ist = timezone("Asia/Kolkata")
      user = await collection.find_one({"user_id": user_id})
      if user:
          expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
          remaining_time = expiration_time - datetime.now(ist)
          if remaining_time.total_seconds() > 0:
              days, hours, minutes, seconds = (
                  remaining_time.days,
                  remaining_time.seconds // 3600,
                  (remaining_time.seconds // 60) % 60,
                  remaining_time.seconds % 60,
              )
              tier = user.get("tier", "gold")
              tier_emoji = "🥇" if tier == "gold" else "💎"
              return (
                  f"{tier_emoji} <b>{tier.capitalize()} Premium Active</b>\n"
                  f"Time left: <b>{days}d {hours}h {minutes}m {seconds}s</b>"
              )
          else:
              return "Your premium plan has expired."
      else:
          return "You do not have a premium plan."

  # Get users expiring in 24 hours who haven't received 24h reminder
  async def get_users_expiring_24h():
      ist = timezone("Asia/Kolkata")
      current_time = datetime.now(ist)
      users_to_remind = []
      async for user in collection.find({"reminder_24h_sent": {"$ne": True}}):
          expiration_timestamp = user.get("expiration_timestamp")
          if not expiration_timestamp:
              continue
          try:
              expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
              time_remaining = expiration_time - current_time
              if timedelta(0) < time_remaining <= timedelta(hours=24):
                  users_to_remind.append({"user_id": user["user_id"], "expiration_time": expiration_time})
          except Exception as e:
              print(f"Error checking user {user.get('user_id')}: {e}")
      return users_to_remind

  # Get users expiring in 5 minutes who haven't received final reminder
  async def get_users_expiring_1min():
      ist = timezone("Asia/Kolkata")
      current_time = datetime.now(ist)
      users_to_remind = []
      async for user in collection.find({"final_reminder_sent": {"$ne": True}}):
          expiration_timestamp = user.get("expiration_timestamp")
          if not expiration_timestamp:
              continue
          try:
              expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
              time_remaining = expiration_time - current_time
              if timedelta(0) < time_remaining <= timedelta(minutes=5):
                  users_to_remind.append({"user_id": user["user_id"], "expiration_time": expiration_time})
          except Exception as e:
              print(f"Error checking user {user.get('user_id')}: {e}")
      return users_to_remind

  # Mark 24h reminder as sent
  async def mark_24h_reminder_sent(user_id):
      await collection.update_one({"user_id": user_id}, {"$set": {"reminder_24h_sent": True}})

  # Mark final reminder as sent
  async def mark_final_reminder_sent(user_id):
      await collection.update_one({"user_id": user_id}, {"$set": {"final_reminder_sent": True}})
  