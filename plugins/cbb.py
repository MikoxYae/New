from pyrogram import Client, filters
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *
import qrcode
from io import BytesIO

UPI_ID = "7348433876@mbk"

GOLD_PREMIUM_PRICES = {
    "14days": 89,
    "1month": 170
}

PLATINUM_PREMIUM_PRICES = {
    "14days": 149,
    "1month": 270
}

user_payment_info = {}


def generate_upi_qr(amount, plan_type, duration):
    upi_string = f"upi://pay?pa={UPI_ID}&pn=Premium&am={amount}&cu=INR&tn={plan_type}_{duration}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    bio.name = 'qr.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio


@Bot.on_callback_query(filters.regex(
    r"^(help|about|start|premium|gold_premium|gold_|platinum_premium|plat_|payment_done|close)"
))
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data

    # ── ʜᴇʟᴘ ─────────────────────────────────────────────────────────────────
    if data == "help":
        await query.message.edit_text(
            text=HELP_TXT.format(
                first=query.from_user.first_name,
                last=query.from_user.last_name,
                username=None if not query.from_user.username else '@' + query.from_user.username,
                mention=query.from_user.mention,
                id=query.from_user.id
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                 InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data='close')]
            ])
        )

    # ── ᴀʙᴏᴜᴛ ────────────────────────────────────────────────────────────────
    elif data == "about":
        await query.message.edit_text(
            text=ABOUT_TXT.format(
                first=query.from_user.first_name,
                last=query.from_user.last_name,
                username=None if not query.from_user.username else '@' + query.from_user.username,
                mention=query.from_user.mention,
                id=query.from_user.id
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                 InlineKeyboardButton('ᴄʟᴏꜱᴇ', callback_data='close')]
            ])
        )

    # ── sᴛᴀʀᴛ ────────────────────────────────────────────────────────────────
    elif data == "start":
        await query.message.edit_text(
            text=START_MSG.format(
                first=query.from_user.first_name,
                last=query.from_user.last_name,
                username=None if not query.from_user.username else '@' + query.from_user.username,
                mention=query.from_user.mention,
                id=query.from_user.id
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʜᴇʟᴘ", callback_data='help'),
                 InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data='about')]
            ])
        )

    # ── ᴘʀᴇᴍɪᴜᴍ ᴛɪᴇʀ sᴇʟᴇᴄᴛɪᴏɴ ─────────────────────────────────────────────
    elif data == "premium":
        await query.message.delete()
        text = (
            f"<b>ʜᴇʟʟᴏ {query.from_user.first_name}!</b>\n\n"
            f"<b>ᴄʜᴏᴏsᴇ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴛɪᴇʀ ᴛʜᴀᴛ sᴜɪᴛs ʏᴏᴜ:</b>\n\n"
            f"🥇 <b>ɢᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ</b>\n"
            f"  ✅ <b>ᴛᴏᴋᴇɴ ʙʏᴘᴀss</b> — ɴᴏ sʜᴏʀᴛɴᴇʀ ʀᴇǫᴜɪʀᴇᴅ\n"
            f"  ✅ <b>ғʀᴇᴇ ʟɪɴᴋ ʟɪᴍɪᴛ ʙʏᴘᴀss</b> — ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ʟɪɴᴋs\n"
            f"  ✅ <b>ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss</b> — sᴀᴠᴇ & ғᴏʀᴡᴀʀᴅ ғʀᴇᴇʟʏ\n\n"
            f"💎 <b>ᴘʟᴀᴛɪɴᴜᴍ ᴘʀᴇᴍɪᴜᴍ</b>\n"
            f"  ✅ <b>ᴇᴠᴇʀʏᴛʜɪɴɢ ɪɴ ɢᴏʟᴅ, ᴘʟᴜs:</b>\n"
            f"  ✅ <b>ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ʙʏᴘᴀss</b> — ᴀᴄᴄᴇss ᴡɪᴛʜᴏᴜᴛ ᴊᴏɪɴɪɴɢ ᴄʜᴀɴɴᴇʟs\n\n"
            f"<b>sᴇʟᴇᴄᴛ ᴀ ᴛɪᴇʀ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴇ ᴘʟᴀɴs ᴀɴᴅ ᴘʀɪᴄɪɴɢ.</b>"
        )
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_PIC,
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🥇 ɢᴏʟᴅ", callback_data="gold_premium"),
                    InlineKeyboardButton("💎 ᴘʟᴀᴛɪɴᴜᴍ", callback_data="platinum_premium")
                ],
                [
                    InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="start"),
                    InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="close")
                ]
            ])
        )

    # ── ɢᴏʟᴅ ᴘʟᴀɴ sᴇʟᴇᴄᴛɪᴏɴ ─────────────────────────────────────────────────
    elif data == "gold_premium":
        await query.message.delete()
        text = (
            f"<b>🥇 ɢᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ</b>\n\n"
            f"<b>ʙᴇɴᴇғɪᴛs:</b>\n"
            f"  ✅ <b>ᴛᴏᴋᴇɴ ʙʏᴘᴀss</b> — ɴᴏ sʜᴏʀᴛɴᴇʀ ᴛᴏᴋᴇɴ ʀᴇǫᴜɪʀᴇᴅ\n"
            f"  ✅ <b>ғʀᴇᴇ ʟɪɴᴋ ʟɪᴍɪᴛ ʙʏᴘᴀss</b> — ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ʟɪɴᴋs\n"
            f"  ✅ <b>ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss</b> — sᴀᴠᴇ & ғᴏʀᴡᴀʀᴅ ғʀᴇᴇʟʏ\n\n"
            f"<b>sᴇʟᴇᴄᴛ ᴀ ᴘʟᴀɴ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ ᴡɪᴛʜ ᴘᴀʏᴍᴇɴᴛ:</b>"
        )
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_PIC,
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        f"14 ᴅᴀʏs — ₹{GOLD_PREMIUM_PRICES['14days']}",
                        callback_data="gold_14days"
                    ),
                    InlineKeyboardButton(
                        f"1 ᴍᴏɴᴛʜ — ₹{GOLD_PREMIUM_PRICES['1month']}",
                        callback_data="gold_1month"
                    )
                ],
                [
                    InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="premium"),
                    InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="close")
                ]
            ])
        )

    # ── ᴘʟᴀᴛɪɴᴜᴍ ᴘʟᴀɴ sᴇʟᴇᴄᴛɪᴏɴ ──────────────────────────────────────────────
    elif data == "platinum_premium":
        await query.message.delete()
        text = (
            f"<b>💎 ᴘʟᴀᴛɪɴᴜᴍ ᴘʀᴇᴍɪᴜᴍ</b>\n\n"
            f"<b>ʙᴇɴᴇғɪᴛs:</b>\n"
            f"  ✅ <b>ᴛᴏᴋᴇɴ ʙʏᴘᴀss</b> — ɴᴏ sʜᴏʀᴛɴᴇʀ ᴛᴏᴋᴇɴ ʀᴇǫᴜɪʀᴇᴅ\n"
            f"  ✅ <b>ғʀᴇᴇ ʟɪɴᴋ ʟɪᴍɪᴛ ʙʏᴘᴀss</b> — ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ʟɪɴᴋs\n"
            f"  ✅ <b>ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ ʙʏᴘᴀss</b> — sᴀᴠᴇ & ғᴏʀᴡᴀʀᴅ ғʀᴇᴇʟʏ\n"
            f"  ✅ <b>ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ʙʏᴘᴀss</b> — ᴀᴄᴄᴇss ᴡɪᴛʜᴏᴜᴛ ᴊᴏɪɴɪɴɢ ᴄʜᴀɴɴᴇʟs\n\n"
            f"<b>sᴇʟᴇᴄᴛ ᴀ ᴘʟᴀɴ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ ᴡɪᴛʜ ᴘᴀʏᴍᴇɴᴛ:</b>"
        )
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_PIC,
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        f"14 ᴅᴀʏs — ₹{PLATINUM_PREMIUM_PRICES['14days']}",
                        callback_data="plat_14days"
                    ),
                    InlineKeyboardButton(
                        f"1 ᴍᴏɴᴛʜ — ₹{PLATINUM_PREMIUM_PRICES['1month']}",
                        callback_data="plat_1month"
                    )
                ],
                [
                    InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="premium"),
                    InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="close")
                ]
            ])
        )

    # ── ɢᴏʟᴅ ᴘᴀʏᴍᴇɴᴛ ǫʀ ──────────────────────────────────────────────────────
    elif data.startswith("gold_"):
        plan_duration = data.replace("gold_", "")
        amount = GOLD_PREMIUM_PRICES.get(plan_duration, 0)

        user_payment_info[query.from_user.id] = {
            "tier": "gold",
            "plan_type": "ɢᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ",
            "duration": plan_duration,
            "amount": amount
        }

        qr_code = generate_upi_qr(amount, "Gold_Premium", plan_duration)
        duration_label = "14 ᴅᴀʏs" if plan_duration == "14days" else "1 ᴍᴏɴᴛʜ"

        payment_text = (
            f"<b>💳 ɢᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ ᴘᴀʏᴍᴇɴᴛ</b>\n\n"
            f"<b>ᴘʟᴀɴ:</b> {duration_label}\n"
            f"<b>ᴀᴍᴏᴜɴᴛ:</b> ₹{amount}\n\n"
            f"<b>📱 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:</b>\n"
            f"1. sᴄᴀɴ ᴛʜᴇ ǫʀ ᴄᴏᴅᴇ ᴡɪᴛʜ ᴀɴʏ ᴜᴘɪ ᴀᴘᴘ.\n"
            f"2. ᴘᴀʏ ᴛʜᴇ ᴇxᴀᴄᴛ ᴀᴍᴏᴜɴᴛ: <b>₹{amount}</b>\n"
            f"3. ᴄʟɪᴄᴋ <b>ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ</b> ᴀɴᴅ sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ.\n"
            f"4. ʏᴏᴜʀ 🥇 ɢᴏʟᴅ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴏɴᴄᴇ ᴛʜᴇ ᴏᴡɴᴇʀ ᴠᴇʀɪғɪᴇs.\n\n"
            f"⚠️ <b>ɴᴏᴛᴇ:</b> ᴘᴀʏᴍᴇɴᴛs ᴍᴀᴅᴇ ᴀғᴛᴇʀ 11:00 ᴘᴍ ᴍᴀʏ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴛʜᴇ ɴᴇxᴛ ᴍᴏʀɴɪɴɢ."
        )

        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=qr_code,
            caption=payment_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ", callback_data="payment_done"),
                    InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="gold_premium")
                ]
            ])
        )

    # ── ᴘʟᴀᴛɪɴᴜᴍ ᴘᴀʏᴍᴇɴᴛ ǫʀ ───────────────────────────────────────────────────
    elif data.startswith("plat_"):
        plan_duration = data.replace("plat_", "")
        amount = PLATINUM_PREMIUM_PRICES.get(plan_duration, 0)

        user_payment_info[query.from_user.id] = {
            "tier": "platinum",
            "plan_type": "ᴘʟᴀᴛɪɴᴜᴍ ᴘʀᴇᴍɪᴜᴍ",
            "duration": plan_duration,
            "amount": amount
        }

        qr_code = generate_upi_qr(amount, "Platinum_Premium", plan_duration)
        duration_label = "14 ᴅᴀʏs" if plan_duration == "14days" else "1 ᴍᴏɴᴛʜ"

        payment_text = (
            f"<b>💳 ᴘʟᴀᴛɪɴᴜᴍ ᴘʀᴇᴍɪᴜᴍ ᴘᴀʏᴍᴇɴᴛ</b>\n\n"
            f"<b>ᴘʟᴀɴ:</b> {duration_label}\n"
            f"<b>ᴀᴍᴏᴜɴᴛ:</b> ₹{amount}\n\n"
            f"<b>📱 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:</b>\n"
            f"1. sᴄᴀɴ ᴛʜᴇ ǫʀ ᴄᴏᴅᴇ ᴡɪᴛʜ ᴀɴʏ ᴜᴘɪ ᴀᴘᴘ.\n"
            f"2. ᴘᴀʏ ᴛʜᴇ ᴇxᴀᴄᴛ ᴀᴍᴏᴜɴᴛ: <b>₹{amount}</b>\n"
            f"3. ᴄʟɪᴄᴋ <b>ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ</b> ᴀɴᴅ sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ.\n"
            f"4. ʏᴏᴜʀ 💎 ᴘʟᴀᴛɪɴᴜᴍ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴏɴᴄᴇ ᴛʜᴇ ᴏᴡɴᴇʀ ᴠᴇʀɪғɪᴇs.\n\n"
            f"⚠️ <b>ɴᴏᴛᴇ:</b> ᴘᴀʏᴍᴇɴᴛs ᴍᴀᴅᴇ ᴀғᴛᴇʀ 11:00 ᴘᴍ ᴍᴀʏ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴛʜᴇ ɴᴇxᴛ ᴍᴏʀɴɪɴɢ."
        )

        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=qr_code,
            caption=payment_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ", callback_data="payment_done"),
                    InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="platinum_premium")
                ]
            ])
        )

    # ── ᴘᴀʏᴍᴇɴᴛ ᴅᴏɴᴇ ᴄᴏɴғɪʀᴍᴀᴛɪᴏɴ ──────────────────────────────────────────────
    elif data == "payment_done":
        first_name = query.from_user.first_name
        last_name = query.from_user.last_name or ""
        await client.send_message(
            chat_id=query.message.chat.id,
            text=(
                f"<b>ʜᴇʟʟᴏ {first_name} {last_name}!</b>\n\n"
                f"<b>ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ғᴏʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ.</b>\n"
                f"<b>ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴏɴᴄᴇ ᴛʜᴇ ᴏᴡɴᴇʀ ᴠᴇʀɪғɪᴇs ɪᴛ!</b>"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", url="https://t.me/Iam_addictive"),
                    InlineKeyboardButton("📢 ᴄʜᴀɴɴᴇʟ", url="https://t.me/+sSi9iWidSjg1Y2Ex")
                ]
            ])
        )

    # ── ᴄʟᴏsᴇ ────────────────────────────────────────────────────────────────
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass

    # ── ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟ ᴍᴏᴅᴇ ᴛᴏɢɢʟᴇ ───────────────────────────────────────
    elif data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
            new_mode = "ᴏғғ" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(
                    f"ʀᴇǫ ᴍᴏᴅᴇ {'ᴏғғ' if mode == 'on' else 'ᴏɴ'}",
                    callback_data=f"rfs_toggle_{cid}_{new_mode}"
                )],
                [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
            ]
            await query.message.edit_text(
                f"<b>ᴄʜᴀɴɴᴇʟ:</b> {chat.title}\n<b>ᴄᴜʀʀᴇɴᴛ ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:</b> {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            await query.answer("ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴄʜᴀɴɴᴇʟ ɪɴғᴏ", show_alert=True)

    elif data.startswith("rfs_toggle_"):
        parts = data.split("_")
        cid = int(parts[2])
        action = parts[3]
        mode = "on" if action == "on" else "off"
        await db.set_channel_mode(cid, mode)
        await query.answer(f"ғᴏʀᴄᴇ-sᴜʙ sᴇᴛ ᴛᴏ {'ᴏɴ' if mode == 'on' else 'ᴏғғ'}")
        chat = await client.get_chat(cid)
        status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
        new_mode = "off" if mode == "on" else "on"
        buttons = [
            [InlineKeyboardButton(
                f"ʀᴇǫ ᴍᴏᴅᴇ {'ᴏғғ' if mode == 'on' else 'ᴏɴ'}",
                callback_data=f"rfs_toggle_{cid}_{new_mode}"
            )],
            [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
        ]
        await query.message.edit_text(
            f"<b>ᴄʜᴀɴɴᴇʟ:</b> {chat.title}\n<b>ᴄᴜʀʀᴇɴᴛ ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:</b> {status}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "fsub_back":
        channels = await db.show_channels()
        buttons = []
        for cid in channels:
            try:
                chat = await client.get_chat(cid)
                mode = await db.get_channel_mode(cid)
                status_icon = "🟢" if mode == "on" else "🔴"
                buttons.append([InlineKeyboardButton(
                    f"{status_icon} {chat.title}", callback_data=f"rfs_ch_{cid}"
                )])
            except Exception:
                continue
        await query.message.edit_text(
            "<b>sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ɪᴛs ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@Bot.on_message(filters.private & filters.photo)
async def forward_payment_screenshot(client: Bot, message: Message):
    user_id = message.from_user.id

    if user_id not in user_payment_info:
        return

    info = user_payment_info[user_id]
    tier = info.get("tier", "gold")
    tier_emoji = "🥇" if tier == "gold" else "💎"
    duration_label = "14 ᴅᴀʏs" if info["duration"] == "14days" else "1 ᴍᴏɴᴛʜ"

    if info["duration"] == "14days":
        cmd = f"/addpremium {user_id} 14 d {tier}"
    elif info["duration"] == "1month":
        cmd = f"/addpremium {user_id} 30 d {tier}"
    else:
        cmd = f"/addpremium {user_id} 14 d {tier}"

    caption = (
        f"<b>💳 ɴᴇᴡ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ</b>\n\n"
        f"<b>ᴜsᴇʀ:</b> {message.from_user.mention}\n"
        f"<b>ᴜsᴇʀ ɪᴅ:</b> <code>{user_id}</code>\n"
        f"<b>ᴜsᴇʀɴᴀᴍᴇ:</b> @{message.from_user.username or 'None'}\n"
        f"<b>ᴛɪᴇʀ:</b> {tier_emoji} {tier.capitalize()} ᴘʀᴇᴍɪᴜᴍ\n"
        f"<b>ᴘʟᴀɴ:</b> {duration_label}\n"
        f"<b>ᴀᴍᴏᴜɴᴛ:</b> ₹{info['amount']}\n\n"
        f"<b>ᴀᴄᴛɪᴠᴀᴛᴇ ᴄᴏᴍᴍᴀɴᴅ:</b>\n"
        f"<code>{cmd}</code>"
    )

    await client.send_photo(
        chat_id=OWNER_ID,
        photo=message.photo.file_id,
        caption=caption
    )

    await message.reply_text(
        f"{tier_emoji} <b>ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ᴛʜᴇ ᴏᴡɴᴇʀ ғᴏʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ.</b>\n\n"
        f"<b>ʏᴏᴜʀ {tier.capitalize()} ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ sᴏᴏɴ!</b>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", url="https://t.me/Yae_N_Miko"),
                InlineKeyboardButton("📢 ᴄʜᴀɴɴᴇʟ", url="https://t.me/+vDWmV0TcGJE3ZmIx")
            ]
        ])
    )

    del user_payment_info[user_id]
