import os
from os import environ,getenv
import logging
from logging.handlers import RotatingFileHandler

#------------------------------------------------------------------------------------------------------------------------------------------------
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8095711612:AAF5GAs3wkyFwvptkRNQJKHTRJP8Vp6bcUE")
APP_ID = int(os.environ.get("APP_ID", "27704224"))
API_HASH = os.environ.get("API_HASH", "c2e33826d757fe113bc154fcfabc987d")
#------------------------------------------------------------------------------------------------------------------------------------------------
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002729018369"))
OWNER = os.environ.get("OWNER", "Yae_X_Miko")
OWNER_ID = int(os.environ.get("OWNER_ID", "8108281129"))
#------------------------------------------------------------------------------------------------------------------------------------------------
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://Angel:aloksingh@angel.4qdpllb.mongodb.net/?retryWrites=true&w=majority&appName=Angel")
DB_NAME = os.environ.get("DATABASE_NAME", "Angle")
PORT = os.environ.get("PORT", "1011")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))
#------------------------------------------------------------------------------------------------------------------------------------------------
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", None)
#------------------------------------------------------------------------------------------------------------------------------------------------
START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/a6aa096874ef37dfb7924-8fc85569d0fb5fa66c.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://telegra.ph/file/a6aa096874ef37dfb7924-8fc85569d0fb5fa66c.jpg")
PREMIUM_PIC = os.environ.get("PREMIUM_PIC", "https://graph.org/file/9eaf27dbab4ba6d729111-553004f7a5a2a2ab86.jpg")
#------------------------------------------------------------------------------------------------------------------------------------------------
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "linkshortify.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "d568956721f5beb08837393f7e8efbccffeb1902")
VERIFY_EXPIRE = int(os.environ.get('VERIFY_EXPIRE', "43200"))
TUT_VID = os.environ.get("TUT_VID","https://t.me/Download_By_Miko/4")
#------------------------------------------------------------------------------------------------------------------------------------------------
SUPER_PREMIUM_ENABLED = os.environ.get("SUPER_PREMIUM_ENABLED", "True") == "True"
SUPER_PREMIUM_PROTECT_CONTENT = os.environ.get("SUPER_PREMIUM_PROTECT_CONTENT", "False") == "True"
#------------------------------------------------------------------------------------------------------------------------------------------------
HELP_TXT = "<b>ɪ ᴀᴍ ᴊᴜsᴛ ғɪʟᴇ sʜᴀʀɪɴɢ ʙᴏᴛ. ɴᴏᴛʜɪɴɢ ʜᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ɢᴏ ʙᴀᴄᴋ.\nɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴘᴀɪᴅ ʙᴏᴛ ʜᴏsᴛɪɴɢ ʏᴏᴜ ᴄᴀɴ ᴅᴍ ᴍᴇ ʜᴇʀᴇ @Yae_X_Miko</b>"
ABOUT_TXT = "<b>◈ ᴄʀᴇᴀᴛᴏʀ: <a href=https://t.me/Yae_X_Miko>『𝚈𝚊𝚎 𝙼𝚒𝚔𝚘』❋𝄗⃝🦋 ⌞𝚆𝚊𝚛𝚕𝚘𝚛𝚍𝚜⌝ ㊋</a></b>"#--------------------------------------------
START_MSG = os.environ.get("START_MESSAGE", "<b>ʜᴇʟʟᴏ {first}\n\nɪ ᴀᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ, ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ.</b>")
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "ʜᴇʟʟᴏ {first}\n\n<b>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b>")
#------------------------------------------------------------------------------------------------------------------------------------------------
CMD_TXT = """<blockquote><b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>

<b>›› /dlt_time :</b> sᴇᴛ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /check_dlt_time :</b> ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /dbroadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏᴄᴜᴍᴇɴᴛ / ᴠɪᴅᴇᴏ
<b>›› /ban :</b> ʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /unban :</b> ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /banlist :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀs
<b>›› /addchnl :</b> ᴀᴅᴅ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /delchnl :</b> ʀᴇᴍᴏᴠᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /listchnl :</b> ᴠɪᴇᴡ ᴀᴅᴅᴇᴅ ᴄʜᴀɴɴᴇʟs
<b>›› /fsub_mode :</b> ᴛᴏɢɢʟᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴍᴏᴅᴇ
<b>›› /pbroadcast :</b> sᴇɴᴅ ᴘʜᴏᴛᴏ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀs
<b>›› /add_admin :</b> ᴀᴅᴅ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /deladmin :</b> ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /admins :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ᴀᴅᴍɪɴs
<b>›› /addpremium :</b> ᴀᴅᴅ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ
<b>›› /premium_users :</b> ʟɪsᴛ ᴀʟʟ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀs
<b>›› /remove_premium :</b> ʀᴇᴍᴏᴠᴇ ᴘʀᴇᴍɪᴜᴍ ꜰʀᴏᴍ ᴀ ᴜꜱᴇʀ
<b>›› /myplan :</b> ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ sᴛᴀᴛᴜs
<b>›› /count :</b> ᴄᴏᴜɴᴛ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴs
<b>›› /delreq :</b> Rᴇᴍᴏᴠᴇᴅ ʟᴇғᴛᴏᴠᴇʀ ɴᴏɴ-ʀᴇǫᴜᴇsᴛ ᴜsᴇʀs
<b>›› /add_super_premium :</b> ᴀᴅᴅ sᴜᴘᴇʀ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ
<b>›› /remove_super_premium :</b> ʀᴇᴍᴏᴠᴇ sᴜᴘᴇʀ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ
<b>›› /super_premium_users :</b> ʟɪsᴛ sᴜᴘᴇʀ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs
<b>›› /my_super_plan :</b> ᴄʜᴇᴄᴋ sᴜᴘᴇʀ ᴘʀᴇᴍɪᴜᴍ sᴛᴀᴛᴜs"""
#------------------------------------------------------------------------------------------------------------------------------------------------
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "True") == "True" else False
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'
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
