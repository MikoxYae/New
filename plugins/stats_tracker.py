from pyrogram import filters
from pyrogram.types import Message
from bot import Bot
from helper_func import admin
from database.db_stats import (
    log_activity, get_peak_hours_today, get_peak_hours_week,
    get_daily_breakdown_week, cleanup_old_logs, DAYS
)

BAR_WIDTH = 20

def make_bar(count, max_count):
    if max_count == 0:
        return ''
    filled = round((count / max_count) * BAR_WIDTH)
    return '█' * filled + '░' * (BAR_WIDTH - filled)


# ── Auto-log every private message ───────────────────────────────────────────
@Bot.on_message(filters.private & ~filters.service, group=-3)
async def track_activity(client: Bot, message: Message):
    if message.from_user:
        try:
            await log_activity(message.from_user.id)
        except Exception:
            pass


# ── /peakhours — Today's hourly activity ─────────────────────────────────────
@Bot.on_message(filters.command('peakhours') & filters.private & admin)
async def peak_hours_today(client: Bot, message: Message):
    hourly = await get_peak_hours_today()
    if not hourly:
        return await message.reply('<b>ɴᴏ ᴀᴄᴛɪᴠɪᴛʏ ᴅᴀᴛᴀ ғᴏʀ ᴛᴏᴅᴀʏ ʏᴇᴛ.</b>')

    max_count = max(hourly.values())
    peak_hour = max(hourly, key=hourly.get)
    total = sum(hourly.values())

    lines = ['<b>📊 ᴘᴇᴀᴋ ʜᴏᴜʀs — ᴛᴏᴅᴀʏ (ɪsᴛ)</b>', '']
    for h in range(24):
        count = hourly.get(h, 0)
        bar = make_bar(count, max_count)
        marker = ' 🔥' if h == peak_hour else ''
        lines.append(f'<code>{h:02d}:00</code> {bar} {count}{marker}')

    lines += ['', f'<b>ᴛᴏᴛᴀʟ ɪɴᴛᴇʀᴀᴄᴛɪᴏɴs:</b> {total}',
              f'<b>ᴘᴇᴀᴋ ʜᴏᴜʀ:</b> {peak_hour:02d}:00 — {hourly[peak_hour]} ɪɴᴛᴇʀᴀᴄᴛɪᴏɴs']
    await message.reply('\n'.join(lines))


# ── /weeklyreport — Last 7 days hourly + daily breakdown ─────────────────────
@Bot.on_message(filters.command('weeklyreport') & filters.private & admin)
async def weekly_report(client: Bot, message: Message):
    hourly = await get_peak_hours_week()
    daily  = await get_daily_breakdown_week()

    if not hourly and not daily:
        return await message.reply('<b>ɴᴏ ᴀᴄᴛɪᴠɪᴛʏ ᴅᴀᴛᴀ ғᴏʀ ᴛʜᴇ ᴘᴀsᴛ 7 ᴅᴀʏs ʏᴇᴛ.</b>')

    total = sum(hourly.values())
    max_h = max(hourly.values()) if hourly else 1
    peak_hour = max(hourly, key=hourly.get) if hourly else None

    max_d = max(daily.values()) if daily else 1
    peak_day = max(daily, key=daily.get) if daily else None

    lines = ['<b>📊 ᴡᴇᴇᴋʟʏ ʀᴇᴘᴏʀᴛ — ʟᴀsᴛ 7 ᴅᴀʏs (ɪsᴛ)</b>', '', '<b>ʜᴏᴜʀʟʏ ʙʀᴇᴀᴋᴅᴏᴡɴ:</b>']
    for h in range(24):
        count = hourly.get(h, 0)
        bar = make_bar(count, max_h)
        marker = ' 🔥' if h == peak_hour else ''
        lines.append(f'<code>{h:02d}:00</code> {bar} {count}{marker}')

    lines += ['', '<b>ᴅᴀɪʟʏ ʙʀᴇᴀᴋᴅᴏᴡɴ:</b>']
    for d in range(7):
        count = daily.get(d, 0)
        bar = make_bar(count, max_d)
        marker = ' 🔥' if d == peak_day else ''
        lines.append(f'<code>{DAYS[d][:3]}</code>  {bar} {count}{marker}')

    lines += [
        '',
        f'<b>ᴛᴏᴛᴀʟ ɪɴᴛᴇʀᴀᴄᴛɪᴏɴs (7ᴅ):</b> {total}',
        f'<b>ᴘᴇᴀᴋ ʜᴏᴜʀ:</b> {peak_hour:02d}:00 ɪsᴛ' if peak_hour is not None else '',
        f'<b>ʙᴜsɪᴇsᴛ ᴅᴀʏ:</b> {DAYS[peak_day]}' if peak_day is not None else '',
    ]
    await message.reply('\n'.join(l for l in lines if l is not None))


# ── /cleanstats — Remove logs older than 30 days ─────────────────────────────
@Bot.on_message(filters.command('cleanstats') & filters.private & admin)
async def clean_stats(client: Bot, message: Message):
    deleted = await cleanup_old_logs(days=30)
    await message.reply(f'<b>🗑 ᴄʟᴇᴀɴᴇᴅ {deleted} ᴏʟᴅ ᴀᴄᴛɪᴠɪᴛʏ ʟᴏɢ ᴇɴᴛʀɪᴇs.</b>')