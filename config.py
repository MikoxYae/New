import os
from os import environ,getenv
import logging
from logging.handlers import RotatingFileHandler

#------------------------------------------------------------------------------------------------------------------------------------------------
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8417356865:AAHV1GEeeT7Gq9tVNrANRv-hiFD1OV8gwrA")
APP_ID = int(os.environ.get("APP_ID", "28614709")) #Your API ID from my.telegram.org
API_HASH = os.environ.get("API_HASH", "f36fd2ee6e3d3a17c4d244ff6dc1bac8") #Your API Hash from my.telegram.org
#------------------------------------------------------------------------------------------------------------------------------------------------
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003249797203")) #Your db channel Id
OWNER = os.environ.get("OWNER", "Yae_N_Miko") # Owner username without @
OWNER_ID = int(os.environ.get("OWNER_ID", "8136381258")) # Owner id
#------------------------------------------------------------------------------------------------------------------------------------------------
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://Angle:Aloksingh@angle.be47a1n.mongodb.net/?appName=Angle")
DB_NAME = os.environ.get("DATABASE_NAME", "Angle")
PORT = os.environ.get("PORT", "4537")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))
#------------------------------------------------------------------------------------------------------------------------------------------------
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", None)
#------------------------------------------------------------------------------------------------------------------------------------------------
START_PIC = os.environ.get("START_PIC", "https://graph.org/file/c3298a2f4d623e7f204c1-882cbd3ff41094cb41.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://graph.org/file/c3298a2f4d623e7f204c1-882cbd3ff41094cb41.jpg")
PREMIUM_PIC = os.environ.get("PREMIUM_PIC", "https://graph.org/file/c3298a2f4d623e7f204c1-882cbd3ff41094cb41.jpg")
#------------------------------------------------------------------------------------------------------------------------------------------------
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "linkshortify.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "d568956721f5beb08837393f7e8efbccffeb1902")
VERIFY_EXPIRE = int(os.environ.get('VERIFY_EXPIRE', "43200"))
TUT_VID = os.environ.get("TUT_VID","https://t.me/How_To_Take_Tokens/12")
ANTI_BYPASS_ENABLED = True if os.environ.get("ANTI_BYPASS_ENABLED", "True") == "True" else False
ANTI_BYPASS_MIN_WAIT = int(os.environ.get("ANTI_BYPASS_MIN_WAIT", "8"))
ANTI_BYPASS_BLOCK_SCORE = int(os.environ.get("ANTI_BYPASS_BLOCK_SCORE", "70"))
WEB_VERIFY_BASE_URL = os.environ.get("WEB_VERIFY_BASE_URL", " https://believes-contacting-assessment-editorial.trycloudflare.com").rstrip("/")
if not WEB_VERIFY_BASE_URL:
    _public_host = (
        os.environ.get("RENDER_EXTERNAL_HOSTNAME") or
        os.environ.get("KOYEB_PUBLIC_DOMAIN") or
        os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    )
    WEB_VERIFY_BASE_URL = f"https://{_public_host}" if _public_host else ""
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

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
