from aiohttp import web
from plugins import web_server
import asyncio
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
import pytz
from datetime import datetime
from config import *
from database.db_premium import *
from database.database import *
from database.premium_database import remove_expired_super_premium_users
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

logging.getLogger("apscheduler").setLevel(logging.WARNING)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(remove_expired_users, "interval", seconds=10)
scheduler.add_job(remove_expired_super_premium_users, "interval", seconds=30)

async def daily_reset_task():
    try:
        await db.reset_all_verify_counts()
    except Exception:
        pass  

scheduler.add_job(daily_reset_task, "cron", hour=0, minute=0)

name ="""
 BY Yae X Miko
"""

def get_indian_time():
    """Returns the current time in IST."""
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        scheduler.start()
        usr_bot_me = await self.get_me()
        self.uptime = get_indian_time()

        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id = db_channel.id, text = "Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"Make Sure bot is Admin in DB Channel, and Double check the CHANNEL_ID Value, Current Value {CHANNEL_ID}")
            self.LOGGER(__name__).info("\nBot Stopped.")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Running..!\n\nYae Miko")
        self.LOGGER(__name__).info(f"""       


  𝗥𝗨𝗡𝗡𝗜𝗡𝗚 𝗕𝗢𝗧
 
                                          """)

        self.set_parse_mode(ParseMode.HTML)
        self.username = usr_bot_me.username
        self.LOGGER(__name__).info(f"Bot Running..!")   

        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

        try: await self.send_message(OWNER_ID, text = f"<b>𝗠𝗔𝗦𝗧𝗘𝗥 𝗬𝗢𝗨𝗥 𝗕𝗢𝗧 𝗜𝗦 𝗕𝗔𝗖𝗞 𝗢𝗡𝗟𝗜𝗡𝗘.</b>")
        except: pass

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")

    def run(self):
        """Run the bot."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start())
        self.LOGGER(__name__).info("Bot is now running.")
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.LOGGER(__name__).info("Shutting down...")
        finally:
            loop.run_until_complete(self.stop())
