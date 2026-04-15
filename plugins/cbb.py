from pyrogram import Client, filters
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *
import qrcode
from io import BytesIO

UPI_ID = "7348433876@mbk"

NORMAL_PREMIUM_PRICES = {
    "14days": 89,
    "1month": 170
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

@Bot.on_callback_query(filters.regex(r"^(help|about|start|premium|normal_premium|normal_|payment_done|close)"))
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data

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
        
    elif data == "premium":
        await query.message.delete()
        premium_text = (
            f"ʜᴇʟʟᴏ {query.from_user.first_name} {query.from_user.last_name}\n\n"
            f"ʜᴇʀᴇ ʏᴏᴜ ᴄᴀɴ ʙᴜʏ ᴏᴜʀ ɴᴏʀᴍᴀʟ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀꜱʜɪᴘ ᴏꜰ sᴇʟᴇᴄᴛᴇᴅ ʙᴏᴛ. ᴄʟɪᴄᴋ ᴏɴ ɴᴏʀᴍᴀʟ ᴘʀᴇᴍɪᴜᴍ ᴛᴏ sᴛᴀʀᴛ ʙᴜʏɪɴɢ.\n\n"
            f"<b>𝗪𝗵𝗮𝘁 𝗬𝗼𝘂 𝗚𝗲𝘁 𝗜𝗻 𝗡𝗼𝗿𝗺𝗮𝗹 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗠𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽.</b>\n\n"
            f"• ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛᴏ ᴛᴀᴋᴇ ᴛᴏᴋᴇɴ.\n"
            f"• ʏᴏᴜʀ ғᴏʀᴡᴀʀᴅ ᴏᴘᴛɪᴏɴ ᴡɪʟʟ ʙᴇ ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ [ᴍᴇᴀɴs ʏᴏᴜ ᴄᴀɴ'ᴛ sᴀᴠᴇ ғɪʟᴇs ɪɴ ʏᴏᴜʀ ɢᴀʟʟᴇʀʏ ᴏʀ ɪɴ ᴏᴛʜᴇʀ ᴄʜᴀɴɴᴇʟ ɢʀᴏᴜᴘs]."
        )
        
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_PIC,
            caption=premium_text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Normal Premium", callback_data="normal_premium")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="start"),
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ]
            )
        )

    elif data == "normal_premium":
        await query.message.delete()
        normal_premium_text = (
            f"<b>𝗪𝗵𝗮𝘁 𝗬𝗼𝘂 𝗚𝗲𝘁 𝗜𝗻 𝗡𝗼𝗿𝗺𝗮𝗹 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗠𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽.</b>\n\n"
            f"• ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛᴏ ᴛᴀᴋᴇ ᴛᴏᴋᴇɴ.\n"
            f"• ʏᴏᴜʀ ғᴏʀᴡᴀʀᴅ ᴏᴘᴛɪᴏɴ ᴡɪʟʟ ʙᴇ ɴᴏᴛ ᴇɴᴀʙʟᴇᴅ [ᴍᴇᴀɴs ʏᴏᴜ ᴄᴀɴ'ᴛ sᴀᴠᴇ ғɪʟᴇs ɪɴ ʏᴏᴜʀ ɢᴀʟʟᴇʀʏ ᴏʀ ɪɴ ᴏᴛʜᴇʀ ᴄʜᴀɴɴᴇʟ ɢʀᴏᴜᴘs].\n"
            f"• ᴘʟᴇᴀsᴇ sᴇʟᴇᴄᴛ ᴘʟᴀɴ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ"
        )
        
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_PIC,
            caption=normal_premium_text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("14 Days - ₹89", callback_data="normal_14days"),
                        InlineKeyboardButton("1 Month - ₹170", callback_data="normal_1month")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="premium"),
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ]
            )
        )

    elif data.startswith("normal_"):
        plan_duration = data.replace("normal_", "")
        amount = NORMAL_PREMIUM_PRICES.get(plan_duration, 0)
        
        user_payment_info[query.from_user.id] = {
            "plan_type": "Normal Premium",
            "duration": plan_duration,
            "amount": amount
        }
        
        qr_code = generate_upi_qr(amount, "Normal_Premium", plan_duration)
        
        payment_text = (
            f"<b>💳 Normal Premium Payment</b>\n\n"
            f"<b>Plan:</b> {plan_duration.replace('days', ' Days').replace('month', ' Month').title()}\n"
            f"<b>Amount:</b> ₹{amount}\n\n"
            f"<b>📱 ɪɴsᴛʀᴜᴄᴛɪᴏɴs:</b>\n"
            f"1. sᴄᴀɴ ᴛʜᴇ ϙʀ ᴄᴏᴅᴇ ᴡɪᴛʜ ᴀɴʏ ᴜᴘɪ ᴀᴘᴘ.\n"
            f"2. ᴘᴀʏ ᴛʜᴇ ᴇxᴀᴄᴛ ᴀᴍᴏᴜɴᴛ : ₹{amount}\n"
            f"3. ᴄʟɪᴄᴋ ᴏɴ ɪ ʜᴀᴠᴇ ᴘᴀɪᴅ ᴛʜᴇɴ sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ɪɴ ʙᴏᴛ ᴛᴏ sᴇɴᴅ ᴛʜᴇᴍ ᴛᴏ ᴏᴡɴᴇʀ.\n"
            f"4. ʏᴏᴜ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ sᴏᴏɴ ᴏɴᴄᴇ ᴏᴡɴᴇʀ ᴡɪʟʟ ᴄᴀᴍᴇ ᴏɴʟɪɴᴇ.\n\n"
            f"⚠️ <b>ᴡᴀʀɴɪɴɢ:</b> ɪғ ᴘᴀʏᴍᴇɴᴛ ɪs ᴍᴀᴅᴇ ᴀғᴛᴇʀ 11:00 ᴘᴍ (ᴀᴛ ɴɪɢʜᴛ) ᴛʜᴇɴ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ᴅᴇᴘᴇɴᴅs ᴏɴ ᴏᴡɴᴇʀ ᴀᴠᴀɪʟᴀʙɪʟɪᴛʏ (ɪғ ᴏᴡɴᴇʀ ᴏɴʟɪɴᴇ ᴛʜᴇɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴇ. ɪғ ᴏᴡɴᴇʀ ɪs ɴᴏᴛ ᴀᴄᴛɪᴠᴇ ᴛʜᴇɴ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴇ ɪɴ ᴍᴏʀɴɪɴɢ)."
        )
        
        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=qr_code,
            caption=payment_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ I Have Paid", callback_data="payment_done"),
                    InlineKeyboardButton("🔙 Back", callback_data="normal_premium")
                ]
            ])
        )

    elif data == "payment_done":
        first_name = query.from_user.first_name
        last_name = query.from_user.last_name or ""
        
        await client.send_message(
            chat_id=query.message.chat.id,
            text=f"ʜᴇʟʟᴏ {first_name} {last_name} ᴘʟᴇᴀsᴇ sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ғᴏʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ. ᴏɴᴄᴇ ʏᴏᴜ ᴀʀᴇ ᴠᴇʀɪғɪᴇᴅ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴇ sᴏᴏɴ!",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("👤 Owner", url="https://t.me/Iam_addictive"),
                    InlineKeyboardButton("📢 Channel", url="https://t.me/+sSi9iWidSjg1Y2Ex")
                ]
            ])
        )

    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

    elif data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
            new_mode = "ᴏғғ" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
                [InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data="fsub_back")]
            ]
            await query.message.edit_text(
                f"Channel: {chat.title}\nCurrent Force-Sub Mode: {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            await query.answer("Failed to fetch channel info", show_alert=True)

    elif data.startswith("rfs_toggle_"):
        cid, action = data.split("_")[2:]
        cid = int(cid)
        mode = "on" if action == "on" else "off"

        await db.set_channel_mode(cid, mode)
        await query.answer(f"Force-Sub set to {'ON' if mode == 'on' else 'OFF'}")

        chat = await client.get_chat(cid)
        status = "🟢 ON" if mode == "on" else "🔴 OFF"
        new_mode = "off" if mode == "on" else "on"
        buttons = [
            [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'OFF' if mode == 'on' else 'ON'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
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
                status = "🟢" if mode == "on" else "🔴"
                buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"rfs_ch_{cid}")])
            except:
                continue

        await query.message.edit_text(
            "sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ɪᴛs ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@Bot.on_message(filters.private & filters.photo)
async def forward_payment_screenshot(client: Bot, message: Message):
    user_id = message.from_user.id
    
    if user_id in user_payment_info:
        payment_info = user_payment_info[user_id]
        
        caption = (
            f"<b>💳 New Payment Screenshot</b>\n\n"
            f"<b>User:</b> {message.from_user.mention}\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Username:</b> @{message.from_user.username or 'None'}\n"
            f"<b>Plan Type:</b> {payment_info['plan_type']}\n"
            f"<b>Duration:</b> {payment_info['duration'].replace('days', ' Days').replace('month', ' Month').title()}\n"
            f"<b>Amount:</b> ₹{payment_info['amount']}\n\n"
            f"<b>Use the command to activate:</b>\n"
        )
        
        if payment_info['duration'] == "14days":
            caption += f"<code>/addpremium {user_id} 14 d</code>"
        elif payment_info['duration'] == "1month":
            caption += f"<code>/addpremium {user_id} 30 d</code>"
        
        await client.send_photo(
            chat_id=OWNER_ID,
            photo=message.photo.file_id,
            caption=caption
        )
        
        await message.reply_text(
            "<b>✅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ᴏᴡɴᴇʀ ғᴏʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ.</b>\n\n"
            "<b>ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ sᴏᴏɴ!</b>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("👤 Owner", url="https://t.me/Yae_N_Miko"),
                    InlineKeyboardButton("📢 Channel", url="https://t.me/+vDWmV0TcGJE3ZmIx")
                ]
            ])
        )
        
        del user_payment_info[user_id]
