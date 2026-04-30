import base64
import re
import asyncio
import time
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import *
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from database.database import *

async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id       
        return any([user_id == OWNER_ID, await db.admin_exist(user_id)])
    except Exception as e:
        print(f"! Exception in check_admin: {e}")
        return False

async def is_subscribed(client, user_id):
    channel_ids = await db.show_channels()

    if not channel_ids:
        return True

    if user_id == OWNER_ID:
        return True

    for cid in channel_ids:
        if not await is_sub(client, user_id, cid):
            return False

    return True

async def is_sub(client, user_id, channel_id):
    mode = await db.get_channel_mode(channel_id)

    # Request Mode ON: just sending a join request is enough for access
    if mode == "on":
        if await db.req_user_exist(channel_id, user_id):
            return True

    # Normal check: verify actual membership
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status
        return status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        }

    except UserNotParticipant:
        return False

    except Exception as e:
        print(f"[!] Error in is_sub(): {e}")
        return False

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, message_ids):
    """Fetch DB-channel messages by id.

    Pyrogram returns a stub `Message` with `.empty=True` for ids that no
    longer exist (deleted from the DB channel). Calling `.copy()` on those
    spams the log with `Empty messages cannot be copied.` warnings and
    returns `None`, which downstream code can mishandle. We filter them
    out (and any `None`s) right here so every caller only sees real
    messages.
    """
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except Exception as ex:
            print(f"[!] get_messages error: {ex}")
            msgs = []
        total_messages += len(temb_ids)
        # Drop None and empty/deleted-message stubs so callers never try to
        # copy them (which would log "Empty messages cannot be copied.").
        for m in msgs:
            if m is None:
                continue
            if getattr(m, "empty", False):
                continue
            messages.append(m)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t\.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
        return 0
    else:
        return 0

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

def get_exp_time(seconds):
    periods = [('days', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)} {period_name}'
    return result

subscribed = filters.create(is_subscribed)
admin = filters.create(check_admin)


# ──────────────────────────────────────────────────────────────────
#  SUPPORT LINK HELPERS
# ──────────────────────────────────────────────────────────────────
#
#  Admin can paste any of the following in /settings → Support:
#      https://t.me/Iam_addictive
#      http://t.me/Iam_addictive
#      t.me/Iam_addictive
#      @Iam_addictive
#      Iam_addictive
#  …and the bot stores a canonical `https://t.me/<handle>` URL.
#  For invite/joinchat/+phone style links we keep the URL as-is.

_TG_URL_RE = re.compile(r'^https?://(?:t\.me|telegram\.me|telegram\.dog)/', re.IGNORECASE)
_BARE_TME_RE = re.compile(r'^(?:t\.me|telegram\.me|telegram\.dog)/', re.IGNORECASE)
_USERNAME_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]{3,31}$')


def normalize_support_link(raw: str):
    """Convert any of the accepted user inputs into a canonical t.me URL.

    Returns None if the input cannot be normalized.
    """
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None

    # Already a full http(s) telegram URL → keep as-is.
    if _TG_URL_RE.match(s):
        return s

    # bare t.me/... → just add scheme
    if _BARE_TME_RE.match(s):
        return "https://" + s

    # Strip leading @
    if s.startswith("@"):
        s = s[1:]

    # Bare valid username
    if _USERNAME_RE.match(s):
        return f"https://t.me/{s}"

    # Anything else (e.g. invite hash / +phone) — wrap as t.me/<value>
    # so the admin can still paste joinchat hashes like  joinchat/AAA…
    cleaned = s.lstrip("/")
    if cleaned:
        return f"https://t.me/{cleaned}"
    return None


async def get_support_url(default: str = "https://t.me/Iam_addictive") -> str:
    """Return the admin-configured support URL, or the fallback default."""
    try:
        url = await db.get_support_link()
    except Exception:
        url = None
    if url and isinstance(url, str) and url.strip():
        return url.strip()
    return default


# ──────────────────────────────────────────────────────────────────
#  MEDIA BUTTONS HELPERS
# ──────────────────────────────────────────────────────────────────
#
#  Admin can configure unlimited inline buttons from /settings → Media
#  Buttons. Every button is rendered on its own row (1 button per row)
#  and attached to every file the bot delivers via /start <encoded>
#  (covers /genlink, /batch and /custom_batch — they all flow through
#  the same delivery path in plugins/start.py).

# Loose URL validation — accepts http(s), tg://, and bare t.me links.
_URL_RE = re.compile(
    r'^(?:https?://|tg://)\S+$|^(?:t\.me|telegram\.me|telegram\.dog)/\S+$',
    re.IGNORECASE,
)


def normalize_button_url(raw: str):
    """Validate and canonicalise a button URL.

    Returns the cleaned URL string, or None if the input is unusable.
    Bare ``t.me/...`` links get an ``https://`` scheme prepended so
    Telegram accepts them as inline-button URLs.
    """
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if not _URL_RE.match(s):
        return None
    if s.lower().startswith(("http://", "https://", "tg://")):
        return s
    # bare t.me/... → add scheme
    return "https://" + s


async def build_media_buttons_markup():
    """Return an InlineKeyboardMarkup of admin-configured media buttons,
    or None when no buttons are configured. One button per row.
    """
    try:
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = await db.get_media_buttons()
    except Exception as e:
        print(f"[!] build_media_buttons_markup error: {e}")
        return None
    if not buttons:
        return None
    rows = []
    for b in buttons:
        name = (b.get("name") or "").strip()
        url = (b.get("url") or "").strip()
        if not name or not url:
            continue
        rows.append([InlineKeyboardButton(name, url=url)])
    if not rows:
        return None
    return InlineKeyboardMarkup(rows)


def merge_inline_markups(*markups):
    """Combine several InlineKeyboardMarkup objects into one (rows stacked).

    None entries are ignored. Returns None if everything was None.
    """
    from pyrogram.types import InlineKeyboardMarkup
    rows = []
    for mk in markups:
        if mk is None:
            continue
        try:
            for row in mk.inline_keyboard:
                rows.append(list(row))
        except Exception:
            continue
    if not rows:
        return None
    return InlineKeyboardMarkup(rows)
