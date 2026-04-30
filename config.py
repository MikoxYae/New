import os
from os import environ,getenv
import logging
from logging.handlers import RotatingFileHandler

#------------------------------------------------------------------------------------------------------------------------------------------------
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8717980062:AAHDlzk2k33i1V5f5udR7kKRAfRcbzW8m_k")
APP_ID = int(os.environ.get("APP_ID", "28614709")) #Your API ID from my.telegram.org
API_HASH = os.environ.get("API_HASH", "f36fd2ee6e3d3a17c4d244ff6dc1bac8") #Your API Hash from my.telegram.org
#------------------------------------------------------------------------------------------------------------------------------------------------
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003855391616")) #Your db channel Id
OWNER = os.environ.get("OWNER", "Anythingbutnew56") # Owner username without @
OWNER_ID = int(os.environ.get("OWNER_ID", "8229041976")) # Owner id
#------------------------------------------------------------------------------------------------------------------------------------------------
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://Payal:Aloksingh@payal.jv2kwch.mongodb.net/?appName=Payal")
DB_NAME = os.environ.get("DATABASE_NAME", "Angle")
PORT = os.environ.get("PORT", "4447")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))
#------------------------------------------------------------------------------------------------------------------------------------------------
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", None)
#------------------------------------------------------------------------------------------------------------------------------------------------
START_PIC = os.environ.get("START_PIC", "https://graph.org/file/c3298a2f4d623e7f204c1-882cbd3ff41094cb41.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://graph.org/file/c3298a2f4d623e7f204c1-882cbd3ff41094cb41.jpg")
PREMIUM_PIC = os.environ.get("PREMIUM_PIC", "https://graph.org/file/c3298a2f4d623e7f204c1-882cbd3ff41094cb41.jpg")
#------------------------------------------------------------------------------------------------------------------------------------------------
ABOUT_TXT = ""
HELP_TXT = ""
START_MSG = os.environ.get("START_MESSAGE", "<b>ʜᴇʟʟᴏ {first}\n\nɪ ᴀᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ, ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ.</b>")
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "ʜᴇʟʟᴏ {first}\n\n<b>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b>")
#------------------------------------------------------------------------------------------------------------------------------------------------
CMD_TXT = """

> <b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b>

<b>›› /batch :</b> ᴄʀᴇᴀᴛᴇ ʙᴀᴛᴄʜ ғɪʟᴇ ʟɪɴᴋ
<b>›› /genlink :</b> ᴄʀᴇᴀᴛᴇ sɪɴɢʟᴇ ғɪʟᴇ ʟɪɴᴋ
<b>›› /custom_batch :</b> ᴄʀᴇᴀᴛᴇ ᴄᴜsᴛᴏᴍ ʙᴀᴛᴄʜ ʟɪɴᴋ
<b>›› /broadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs
<b>›› /dbroadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏᴄᴜᴍᴇɴᴛ / ᴠɪᴅᴇᴏ
<b>›› /pbroadcast :</b> sᴇɴᴅ ᴘʜᴏᴛᴏ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀs
<b>›› /addpremium :</b> ᴀᴅᴅ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ
<b>›› /premium_users :</b> ʟɪsᴛ ᴀʟʟ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs
<b>›› /remove_premium :</b> ʀᴇᴍᴏᴠᴇ ᴘʀᴇᴍɪᴜᴍ ғʀᴏᴍ ᴀ ᴜsᴇʀ
<b>›› /myplan :</b> ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ sᴛᴀᴛᴜs
<b>›› /plans :</b> sʜᴏᴡ ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs
<b>›› /psetting :</b> ᴍᴀɴᴀɢᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs (ᴀᴅᴅ / ᴇᴅɪᴛ / ɢʀᴀɴᴛ)
<b>›› /commands :</b> sʜᴏᴡ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ʟɪsᴛ
<b>›› /settings :</b> ᴏᴘᴇɴ sᴇᴛᴛɪɴɢs ᴘᴀɴᴇʟ
<b>›› /peakhours :</b> ᴛᴏᴅᴀʏ's ᴘᴇᴀᴋ ᴀᴄᴛɪᴠɪᴛʏ ʜᴏᴜʀs
<b>›› /weeklyreport :</b> ʟᴀsᴛ 7 ᴅᴀʏs ᴀᴄᴛɪᴠɪᴛʏ ʀᴇᴘᴏʀᴛ
<b>›› /cleanstats :</b> ᴄʟᴇᴀɴ ᴏʟᴅ ᴀᴄᴛɪᴠɪᴛʏ ʟᴏɢs"""
#------------------------------------------------------------------------------------------------------------------------------------------------
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "True") == "True" else False
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'
#------------------------------------------------------------------------------------------------------------------------------------------------
# FLOOD PROTECTION
FLOOD_LIMIT = int(os.environ.get("FLOOD_LIMIT", "5")) # max msgs in window
FLOOD_WINDOW = int(os.environ.get("FLOOD_WINDOW", "5")) # seconds (sliding window)
FLOOD_BLOCK_DURATION= int(os.environ.get("FLOOD_BLOCK_DURATION", "30")) # seconds user is blocked
# STATS / PEAK HOURS TRACKER
STATS_ENABLED = True if os.environ.get("STATS_ENABLED", "True") == "True" else False
#------------------------------------------------------------------------------------------------------------------------------------------------
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "ʙᴀᴋᴋᴀ ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ꜱᴇɴᴘᴀɪ!!"
#------------------------------------------------------------------------------------------------------------------------------------------------

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
# Silence the noisy "Empty messages cannot be copied." warning that fires
# when a DB-channel message has been deleted. We already filter empty
# messages in helper_func.get_messages and plugins/start.py; this just
# keeps the log clean if any future call site forgets to.
logging.getLogger("pyrogram.types.messages_and_media.message").setLevel(logging.ERROR)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
