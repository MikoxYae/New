import psutil
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from database.database import db


@Bot.on_callback_query(filters.regex(r"^stg_users$"))
async def stg_users_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    users = await db.full_userbase()
    count = len(users)
    await query.message.edit_text(
        f"<b>👥 Users Info</b>\n\n"
        f"<b>Total Users in DB:</b> <code>{count}</code>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
        ])
    )


@Bot.on_callback_query(filters.regex(r"^stg_stats$"))
async def stg_stats_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    cpu = psutil.cpu_percent(interval=0.5)

    ram_total = round(ram.total / (1024 ** 3), 2)
    ram_used = round(ram.used / (1024 ** 3), 2)
    ram_free = round(ram.available / (1024 ** 3), 2)
    ram_percent = ram.percent

    disk_total = round(disk.total / (1024 ** 3), 2)
    disk_used = round(disk.used / (1024 ** 3), 2)
    disk_free = round(disk.free / (1024 ** 3), 2)
    disk_percent = disk.percent

    await query.message.edit_text(
        f"<b>📊 System Stats</b>\n\n"
        f"<b>🧠 RAM</b>\n"
        f"├ Total: <code>{ram_total} GB</code>\n"
        f"├ Used: <code>{ram_used} GB ({ram_percent}%)</code>\n"
        f"└ Free: <code>{ram_free} GB</code>\n\n"
        f"<b>💾 Disk</b>\n"
        f"├ Total: <code>{disk_total} GB</code>\n"
        f"├ Used: <code>{disk_used} GB ({disk_percent}%)</code>\n"
        f"└ Free: <code>{disk_free} GB</code>\n\n"
        f"<b>⚙️ CPU Usage:</b> <code>{cpu}%</code>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="stg_back")]
        ])
    )


@Bot.on_callback_query(filters.regex(r"^stg_back$"))
async def stg_back_cb(client: Bot, query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "<b>⚙️ Settings Panel</b>\n\nSelect a category to manage:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👑 Admin", callback_data="stg_admin"),
                InlineKeyboardButton("🚫 Ban Users", callback_data="stg_ban")
            ],
            [
                InlineKeyboardButton("👥 Users", callback_data="stg_users"),
                InlineKeyboardButton("📊 Stats", callback_data="stg_stats")
            ]
        ])
    )
