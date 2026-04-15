from aiohttp import web
from plugins import web_server
import asyncio
import pyromod.listen

# ── Pyromod 1.5 KeyError fix ───────────────────────────────────────────────────
# pyromod 1.5 never seeds self.listeners with enum keys so every incoming message
# crashes with KeyError.  Patch BOTH source files once at startup.
import os as _os, re as _re

def _patch_pyromod():
    # Patch 1 – client.py: use .get() so a missing key returns []
    _p1 = "/usr/local/lib/python3.10/dist-packages/pyromod/listen/client.py"
    if _os.path.exists(_p1):
        _src = open(_p1).read()
        _fixed = _re.sub(
            r'for listener in self\.listeners\[listener_type\]:',
            'for listener in self.listeners.get(listener_type, []):',
            _src
        )
        if _fixed != _src:
            open(_p1, "w").write(_fixed)

    # Patch 2 – message_handler.py: wrap the whole check in try/except KeyError
    _p2 = "/usr/local/lib/python3.10/dist-packages/pyromod/listen/message_handler.py"
    if _os.path.exists(_p2):
        _src = open(_p2).read()
        # Wrap check_if_has_matching_listener body
        _BAD  = "        listener = client.get_listener_matching_with_data(data, ListenerTypes.MESSAGE)"
        _GOOD = (
            "        try:\n"
            "            listener = client.get_listener_matching_with_data(data, ListenerTypes.MESSAGE)\n"
            "        except (KeyError, Exception):\n"
            "            return"
        )
        if _BAD in _src and _GOOD.replace("\n", "\n") not in _src:
            open(_p2, "w").write(_src.replace(_BAD, _GOOD))

_patch_pyromod()
# ───────────────────────────────────────────────────────────────────────────────
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
import pytz
from datetime import datetime
from config import *
from database.db_premium import *
from database.database import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

logging.getLogger("apscheduler").setLevel(logging.WARNING)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(remove_expired_users, "interval", seconds=10)

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
        # Seed pyromod listeners dict so no KeyError on first message
        try:
            from pyromod.listen import ListenerTypes as _LT
            for _lt in _LT:
                if _lt not in self.listeners:
                    self.listeners[_lt] = []
        except Exception:
            pass
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
