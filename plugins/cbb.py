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

    # ── Help ──────────────────────────────────────────────────────────────────
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

    # ── About ─────────────────────────────────────────────────────────────────
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

    # ── Start ─────────────────────────────────────────────────────────────────
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

    # ── Premium tier selection ────────────────────────────────────────────────
    elif data == "premium":
        await query.message.delete()
        text = (
            f"<b>Hello {query.from_user.first_name}!</b>\n\n"
            f"Choose a premium tier that suits you:\n\n"
            f"🥇 <b>Gold Premium</b>\n"
            f"  ✅ Token Bypass — No shortner required\n"
            f"  ✅ Free Link Limit Bypass — Unlimited daily links\n"
            f"  ✅ Protected Content Bypass — Save & forward freely\n\n"
            f"💎 <b>Platinum Premium</b>\n"
            f"  ✅ Everything in Gold, plus:\n"
            f"  ✅ Force Subscribe Bypass — Access without joining channels\n\n"
            f"Select a tier below to see plans and pricing."
        )
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_PIC,
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🥇 Gold", callback_data="gold_premium"),
                    InlineKeyboardButton("💎 Platinum", callback_data="platinum_premium")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="start"),
                    InlineKeyboardButton("🔒 Close", callback_data="close")
                ]
            ])
        )

    # ── Gold plan selection ───────────────────────────────────────────────────
    elif data == "gold_premium":
        await query.message.delete()
        text = (
            f"<b>🥇 Gold Premium</b>\n\n"
            f"<b>Benefits:</b>\n"
            f"  ✅ Token Bypass — No shortner token required\n"
            f"  ✅ Free Link Limit Bypass — Unlimited daily links\n"
            f"  ✅ Protected Content Bypass — Save & forward freely\n\n"
            f"<b>Select a plan to proceed with payment:</b>"
        )
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_PIC,
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        f"14 Days — ₹{GOLD_PREMIUM_PRICES['14days']}",
                        callback_data="gold_14days"
                    ),
                    InlineKeyboardButton(
                        f"1 Month — ₹{GOLD_PREMIUM_PRICES['1month']}",
                        callback_data="gold_1month"
                    )
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="premium"),
                    InlineKeyboardButton("🔒 Close", callback_data="close")
                ]
            ])
        )

    # ── Platinum plan selection ───────────────────────────────────────────────
    elif data == "platinum_premium":
        await query.message.delete()
        text = (
            f"<b>💎 Platinum Premium</b>\n\n"
            f"<b>Benefits:</b>\n"
            f"  ✅ Token Bypass — No shortner token required\n"
            f"  ✅ Free Link Limit Bypass — Unlimited daily links\n"
            f"  ✅ Protected Content Bypass — Save & forward freely\n"
            f"  ✅ Force Subscribe Bypass — Access without joining channels\n\n"
            f"<b>Select a plan to proceed with payment:</b>"
        )
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_PIC,
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        f"14 Days — ₹{PLATINUM_PREMIUM_PRICES['14days']}",
                        callback_data="plat_14days"
                    ),
                    InlineKeyboardButton(
                        f"1 Month — ₹{PLATINUM_PREMIUM_PRICES['1month']}",
                        callback_data="plat_1month"
                    )
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="premium"),
                    InlineKeyboardButton("🔒 Close", callback_data="close")
                ]
            ])
        )

    # ── Gold payment QR ───────────────────────────────────────────────────────
    elif data.startswith("gold_"):
        plan_duration = data.replace("gold_", "")
        amount = GOLD_PREMIUM_PRICES.get(plan_duration, 0)

        user_payment_info[query.from_user.id] = {
            "tier": "gold",
            "plan_type": "Gold Premium",
            "duration": plan_duration,
            "amount": amount
        }

        qr_code = generate_upi_qr(amount, "Gold_Premium", plan_duration)
        duration_label = plan_duration.replace("days", " Days").replace("month", " Month").title()

        payment_text = (
            f"<b>💳 Gold Premium Payment</b>\n\n"
            f"<b>Plan:</b> {duration_label}\n"
            f"<b>Amount:</b> ₹{amount}\n\n"
            f"<b>📱 Instructions:</b>\n"
            f"1. Scan the QR code with any UPI app.\n"
            f"2. Pay the exact amount: <b>₹{amount}</b>\n"
            f"3. Click <b>I Have Paid</b> and send your payment screenshot.\n"
            f"4. Your Gold Premium will be activated once the owner verifies.\n\n"
            f"⚠️ <b>Note:</b> Payments made after 11:00 PM may be activated the next morning."
        )

        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=qr_code,
            caption=payment_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ I Have Paid", callback_data="payment_done"),
                    InlineKeyboardButton("🔙 Back", callback_data="gold_premium")
                ]
            ])
        )

    # ── Platinum payment QR ───────────────────────────────────────────────────
    elif data.startswith("plat_"):
        plan_duration = data.replace("plat_", "")
        amount = PLATINUM_PREMIUM_PRICES.get(plan_duration, 0)

        user_payment_info[query.from_user.id] = {
            "tier": "platinum",
            "plan_type": "Platinum Premium",
            "duration": plan_duration,
            "amount": amount
        }

        qr_code = generate_upi_qr(amount, "Platinum_Premium", plan_duration)
        duration_label = plan_duration.replace("days", " Days").replace("month", " Month").title()

        payment_text = (
            f"<b>💳 Platinum Premium Payment</b>\n\n"
            f"<b>Plan:</b> {duration_label}\n"
            f"<b>Amount:</b> ₹{amount}\n\n"
            f"<b>📱 Instructions:</b>\n"
            f"1. Scan the QR code with any UPI app.\n"
            f"2. Pay the exact amount: <b>₹{amount}</b>\n"
            f"3. Click <b>I Have Paid</b> and send your payment screenshot.\n"
            f"4. Your Platinum Premium will be activated once the owner verifies.\n\n"
            f"⚠️ <b>Note:</b> Payments made after 11:00 PM may be activated the next morning."
        )

        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=qr_code,
            caption=payment_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ I Have Paid", callback_data="payment_done"),
                    InlineKeyboardButton("🔙 Back", callback_data="platinum_premium")
                ]
            ])
        )

    # ── Payment done confirmation ─────────────────────────────────────────────
    elif data == "payment_done":
        first_name = query.from_user.first_name
        last_name = query.from_user.last_name or ""
        await client.send_message(
            chat_id=query.message.chat.id,
            text=(
                f"Hello {first_name} {last_name}, please send your payment screenshot "
                f"for verification. Your premium will be activated once the owner verifies it!"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("👤 Owner", url="https://t.me/Iam_addictive"),
                    InlineKeyboardButton("📢 Channel", url="https://t.me/+sSi9iWidSjg1Y2Ex")
                ]
            ])
        )

    # ── Close ─────────────────────────────────────────────────────────────────
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass

    # ── Force-sub channel mode toggle ─────────────────────────────────────────
    elif data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
            new_mode = "ᴏғғ" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(
                    f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}",
                    callback_data=f"rfs_toggle_{cid}_{new_mode}"
                )],
                [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
            ]
            await query.message.edit_text(
                f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            await query.answer("Failed to fetch channel info", show_alert=True)

    elif data.startswith("rfs_toggle_"):
        parts = data.split("_")
        cid = int(parts[2])
        action = parts[3]
        mode = "on" if action == "on" else "off"
        await db.set_channel_mode(cid, mode)
        await query.answer(f"Force-Sub set to {'ON' if mode == 'on' else 'OFF'}")
        chat = await client.get_chat(cid)
        status = "🟢 ON" if mode == "on" else "🔴 OFF"
        new_mode = "off" if mode == "on" else "on"
        buttons = [
            [InlineKeyboardButton(
                f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}",
                callback_data=f"rfs_toggle_{cid}_{new_mode}"
            )],
            [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
        ]
        await query.message.edit_text(
            f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
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
            "sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ɪᴛs ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:",
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
    duration_label = info["duration"].replace("days", " Days").replace("month", " Month").title()

    # Build the exact /addpremium command for the owner
    if info["duration"] == "14days":
        cmd = f"/addpremium {user_id} 14 d {tier}"
    elif info["duration"] == "1month":
        cmd = f"/addpremium {user_id} 30 d {tier}"
    else:
        cmd = f"/addpremium {user_id} 14 d {tier}"

    caption = (
        f"<b>💳 New Payment Screenshot</b>\n\n"
        f"<b>User:</b> {message.from_user.mention}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n"
        f"<b>Username:</b> @{message.from_user.username or 'None'}\n"
        f"<b>Tier:</b> {tier_emoji} {tier.capitalize()} Premium\n"
        f"<b>Plan:</b> {duration_label}\n"
        f"<b>Amount:</b> ₹{info['amount']}\n\n"
        f"<b>Activate command:</b>\n"
        f"<code>{cmd}</code>"
    )

    await client.send_photo(
        chat_id=OWNER_ID,
        photo=message.photo.file_id,
        caption=caption
    )

    await message.reply_text(
        f"{tier_emoji} <b>Your payment screenshot has been sent to the owner for verification.</b>\n\n"
        f"<b>Your {tier.capitalize()} Premium will be activated soon!</b>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👤 Owner", url="https://t.me/Yae_N_Miko"),
                InlineKeyboardButton("📢 Channel", url="https://t.me/+vDWmV0TcGJE3ZmIx")
            ]
        ])
    )

    del user_payment_info[user_id]
