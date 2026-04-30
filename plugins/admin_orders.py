"""
═══════════════════════════════════════════════════════════════════════════════
  ADMIN ORDERS PANEL  —  /id  /ord  /amount  /stats  /checkorder  /forceverify
  Reads from MongoDB `pending_orders` collection (filled by premium_auto.py).
  Owner-only. Pure read-only except /forceverify (recovery for failed
  auto-verifications when Sellgram says success but our DB says pending).
═══════════════════════════════════════════════════════════════════════════════
"""
import asyncio
import io
from datetime import datetime, timedelta

import aiohttp
import motor.motor_asyncio
from pytz import timezone

from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from bot import Bot
from config import DB_URI, DB_NAME, OWNER_ID
from database.db_premium import add_premium
from plugins.premium_cdm import monitor_premium_expiry


# ═══════════════════════════════════════════════════════════════════════════════
#   Sellgram (mirrors premium_auto.py — kept independent to avoid circular import)
# ═══════════════════════════════════════════════════════════════════════════════
SELLGRAM_API_BASE = "https://ptapi.sellgram.in"
SELLGRAM_API_KEY = "8Mv3zQgQZNVCdU4iBaAFvtu8"

PLAN_LABELS = {"1h": "1ʜ", "1d": "1ᴅ", "7d": "7ᴅ", "30d": "30ᴅ"}
PLAN_AMOUNTS = {"1h": 1, "1d": 10, "7d": 50, "30d": 150}

PER_PAGE = 10
IST = timezone("Asia/Kolkata")
UTC = timezone("UTC")

# Independent client (premium_auto.py owns its own — same DB, same collection)
_mongo = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
_db = _mongo[DB_NAME]
_orders = _db["pending_orders"]


# ═══════════════════════════════════════════════════════════════════════════════
#   Date helpers
# ═══════════════════════════════════════════════════════════════════════════════
def _parse_date(arg):
    if not arg or arg.lower() == "today":
        return datetime.now(IST).date()
    if arg.lower() == "yesterday":
        return (datetime.now(IST) - timedelta(days=1)).date()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y"):
        try:
            return datetime.strptime(arg, fmt).date()
        except ValueError:
            continue
    return None


def _date_window(d):
    """Return (start_iso, end_iso) — naive UTC ISO strings matching the DB format."""
    start_ist = IST.localize(datetime.combine(d, datetime.min.time()))
    end_ist = start_ist + timedelta(days=1)
    s = start_ist.astimezone(UTC).replace(tzinfo=None).isoformat()
    e = end_ist.astimezone(UTC).replace(tzinfo=None).isoformat()
    return s, e


def _fmt_date_human(d):
    return d.strftime("%d %b %Y")


def _fmt_date_short(d):
    return d.strftime("%Y%m%d")


def _parse_short(s):
    return datetime.strptime(s, "%Y%m%d").date()


def _fmt_time_ist(iso_str):
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = UTC.localize(dt)
        return dt.astimezone(IST).strftime("%I:%M %p")
    except Exception:
        return "—"


# ═══════════════════════════════════════════════════════════════════════════════
#   Mongo helpers
# ═══════════════════════════════════════════════════════════════════════════════
async def _fetch_orders_for_date(d):
    s, e = _date_window(d)
    cursor = _orders.find(
        {"status": "paid", "paid_at": {"$gte": s, "$lt": e}}
    ).sort("paid_at", 1)
    return [doc async for doc in cursor]


async def _sellgram(order_id):
    url = f"{SELLGRAM_API_BASE}/status/{order_id}?api_key={SELLGRAM_API_KEY}"
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url) as r:
            return await r.json(content_type=None)


# ═══════════════════════════════════════════════════════════════════════════════
#   /id  —  paginated successful orders for a date
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.command("id") & filters.private & filters.user(OWNER_ID))
async def id_cmd(client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else None
    d = _parse_date(arg)
    if not d:
        return await message.reply(
            "<b>❌ ʙᴀᴅ ᴅᴀᴛᴇ.</b>\n"
            "<b>ᴜsᴇ:</b> <code>/id</code>, <code>/id today</code>, "
            "<code>/id yesterday</code>, ᴏʀ <code>/id DD-MM-YYYY</code>"
        )
    await _render_id_page(client, message, d, page=1, edit=False)


def _id_page_kb(date_short, page, total_pages):
    rows = []
    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀️ ᴘʀᴇᴠ", callback_data=f"aord_id_{date_short}_{page-1}"))
        nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="aord_noop"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("ɴᴇxᴛ ▶️", callback_data=f"aord_id_{date_short}_{page+1}"))
        rows.append(nav)
    rows.append([
        InlineKeyboardButton("📄 ᴇxᴘᴏʀᴛ ᴀʟʟ", callback_data=f"aord_exp_{date_short}"),
        InlineKeyboardButton("💰 ᴀᴍᴏᴜɴᴛ",     callback_data=f"aord_amt_{date_short}"),
    ])
    rows.append([
        InlineKeyboardButton("🔄 ʀᴇғʀᴇsʜ", callback_data=f"aord_id_{date_short}_{page}"),
        InlineKeyboardButton("✖️ ᴄʟᴏsᴇ",  callback_data="aord_close"),
    ])
    return InlineKeyboardMarkup(rows)


async def _render_id_page(client, src, d, page, edit):
    orders = await _fetch_orders_for_date(d)
    total = len(orders)
    total_amount = sum(o.get("amount", 0) for o in orders)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))
    chunk = orders[(page - 1) * PER_PAGE : page * PER_PAGE]

    head = (
        f"<b>📋 ᴏʀᴅᴇʀ ɪᴅs — {_fmt_date_human(d)}</b>\n"
        f"<b>ᴏʀᴅᴇʀs:</b> {total}  •  <b>ᴀᴍᴏᴜɴᴛ:</b> ₹{total_amount}\n"
        f"<b>ᴘᴀɢᴇ:</b> {page}/{total_pages}\n"
        f"────────────────────"
    )

    if not chunk:
        text = head + "\n\n<i>ɴᴏ ᴏʀᴅᴇʀs ғᴏᴜɴᴅ ғᴏʀ ᴛʜɪs ᴅᴀᴛᴇ.</i>"
    else:
        lines = []
        start_i = (page - 1) * PER_PAGE + 1
        for i, o in enumerate(chunk, start=start_i):
            plan_lbl = PLAN_LABELS.get(o.get("plan_id", ""), o.get("plan_id", "-"))
            lines.append(
                f"\n{i}. <code>{o.get('order_id', '?')}</code>\n"
                f"   <b>USER:</b> <code>{o.get('user_id', '?')}</code>  •  "
                f"Gold {plan_lbl}  •  ₹{o.get('amount', 0)}  •  {_fmt_time_ist(o.get('paid_at'))}\n"
                f"   <b>TXN:</b> <code>{o.get('txn_id') or '—'}</code>"
            )
        text = head + "".join(lines)

    kb = _id_page_kb(_fmt_date_short(d), page, total_pages)
    if edit:
        try:
            await src.message.edit(text, reply_markup=kb, disable_web_page_preview=True)
        except Exception:
            pass
    else:
        await src.reply(text, reply_markup=kb, disable_web_page_preview=True, quote=True)


# ═══════════════════════════════════════════════════════════════════════════════
#   /ord  —  plain serial-wise list of just order IDs
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.command("ord") & filters.private & filters.user(OWNER_ID))
async def ord_cmd(client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else None
    d = _parse_date(arg)
    if not d:
        return await message.reply("<b>❌ ʙᴀᴅ ᴅᴀᴛᴇ.</b>")
    orders = await _fetch_orders_for_date(d)
    head = (
        f"<b>🧾 ᴏʀᴅᴇʀ ɪᴅs (ᴘʟᴀɪɴ) — {_fmt_date_human(d)}</b>\n"
        f"<b>ᴄᴏᴜɴᴛ:</b> {len(orders)}\n"
        f"────────────────────\n"
    )
    if not orders:
        return await message.reply(head + "<i>ɴᴏ ᴏʀᴅᴇʀs.</i>")
    body_lines = [f"{i+1}. <code>{o.get('order_id','?')}</code>" for i, o in enumerate(orders)]
    text = head + "\n".join(body_lines)
    if len(text) <= 4000:
        await message.reply(text, disable_web_page_preview=True)
    else:
        buf = io.BytesIO("\n".join(o.get("order_id", "?") for o in orders).encode())
        buf.name = f"orders-{_fmt_date_short(d)}.txt"
        await message.reply_document(buf, caption=head)


# ═══════════════════════════════════════════════════════════════════════════════
#   /amount  —  per-plan income breakdown
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.command("amount") & filters.private & filters.user(OWNER_ID))
async def amount_cmd(client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else None
    d = _parse_date(arg)
    if not d:
        return await message.reply("<b>❌ ʙᴀᴅ ᴅᴀᴛᴇ.</b>")
    await _send_amount(client, message, d, edit=False)


async def _send_amount(client, src, d, edit):
    orders = await _fetch_orders_for_date(d)
    by_plan = {}
    for o in orders:
        pid = o.get("plan_id", "?")
        slot = by_plan.setdefault(pid, {"count": 0, "amount": 0})
        slot["count"] += 1
        slot["amount"] += o.get("amount", 0)

    head = f"<b>💰 ᴀᴍᴏᴜɴᴛ ʙʀᴇᴀᴋᴅᴏᴡɴ — {_fmt_date_human(d)}</b>\n────────────────────\n"
    if not orders:
        text = head + "<i>ɴᴏ ᴏʀᴅᴇʀs.</i>"
    else:
        lines = ["<b>ɢᴏʟᴅ:</b>"]
        for pid in ("1h", "1d", "7d", "30d"):
            if pid in by_plan:
                stats = by_plan[pid]
                lines.append(
                    f"  {PLAN_LABELS[pid]} (₹{PLAN_AMOUNTS[pid]})  ×  {stats['count']}  =  ₹{stats['amount']}"
                )
        for pid, stats in by_plan.items():
            if pid not in PLAN_LABELS:
                lines.append(f"  {pid}  ×  {stats['count']}  =  ₹{stats['amount']}")
        total_amt = sum(s["amount"] for s in by_plan.values())
        total_cnt = sum(s["count"] for s in by_plan.values())
        lines.append("  ─────────────")
        lines.append(f"  <b>ɢᴏʟᴅ ᴛᴏᴛᴀʟ:</b>  ₹{total_amt}")
        lines.append("")
        lines.append(f"<b>ɢʀᴀɴᴅ ᴛᴏᴛᴀʟ:</b>  ₹{total_amt}")
        lines.append(f"<b>ᴏʀᴅᴇʀs:</b>       {total_cnt}")
        text = head + "\n".join(lines)

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("📋 ᴏʀᴅᴇʀ ɪᴅs", callback_data=f"aord_id_{_fmt_date_short(d)}_1"),
        InlineKeyboardButton("✖️ ᴄʟᴏsᴇ",   callback_data="aord_close"),
    ]])

    if edit:
        try:
            await src.message.edit(text, reply_markup=kb)
        except Exception:
            pass
    else:
        await src.reply(text, reply_markup=kb, quote=True)


# ═══════════════════════════════════════════════════════════════════════════════
#   /stats  —  lifetime dashboard
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
async def stats_cmd(client, message: Message):
    paid = [o async for o in _orders.find({"status": "paid"})]
    total_orders = len(paid)
    total_revenue = sum(o.get("amount", 0) for o in paid)
    active_users = len({o.get("user_id") for o in paid if o.get("user_id") is not None})

    plan_count = {}
    for o in paid:
        pid = o.get("plan_id", "?")
        plan_count[pid] = plan_count.get(pid, 0) + 1
    top_plan = max(plan_count.items(), key=lambda kv: kv[1]) if plan_count else (None, 0)

    by_day = {}
    for o in paid:
        try:
            dt = datetime.fromisoformat(o["paid_at"])
            if dt.tzinfo is None:
                dt = UTC.localize(dt)
            day = dt.astimezone(IST).date()
        except Exception:
            continue
        by_day[day] = by_day.get(day, 0) + o.get("amount", 0)
    best_day = max(by_day.items(), key=lambda kv: kv[1]) if by_day else (None, 0)

    plan_label = PLAN_LABELS.get(top_plan[0], top_plan[0]) if top_plan[0] else "—"
    plan_price = PLAN_AMOUNTS.get(top_plan[0], 0) if top_plan[0] else 0
    best_str = f"{best_day[0].strftime('%d-%m-%Y')}  (₹{best_day[1]})" if best_day[0] else "—"

    text = (
        f"<b>📊 ʟɪғᴇᴛɪᴍᴇ ᴅᴀsʜʙᴏᴀʀᴅ</b>\n"
        f"────────────────────\n"
        f"<b>ᴛᴏᴛᴀʟ ᴏʀᴅᴇʀs:</b>        <code>{total_orders}</code>\n"
        f"<b>ᴛᴏᴛᴀʟ ʀᴇᴠᴇɴᴜᴇ:</b>      <code>₹{total_revenue}</code>\n"
        f"<b>ᴀᴄᴛɪᴠᴇ ᴜsᴇʀs:</b>        <code>{active_users}</code>\n"
        f"<b>ᴛᴏᴘ-sᴇʟʟɪɴɢ ᴘʟᴀɴ:</b>   <code>{plan_label} (₹{plan_price})  ×  {top_plan[1]}</code>\n"
        f"<b>ʙᴇsᴛ-ᴘᴇʀғᴏʀᴍɪɴɢ ᴅᴀʏ:</b> <code>{best_str}</code>"
    )
    await message.reply(text)


# ═══════════════════════════════════════════════════════════════════════════════
#   /checkorder <order_id>  —  read-only debug
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.command("checkorder") & filters.private & filters.user(OWNER_ID))
async def checkorder_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<b>ᴜsᴇ:</b> <code>/checkorder &lt;order_id&gt;</code>")
    oid = message.command[1].strip()

    db_doc = await _orders.find_one({"order_id": oid})
    api_resp, api_err = None, None
    try:
        api_resp = await _sellgram(oid)
    except Exception as e:
        api_err = str(e)

    lines = [f"<b>🔍 ᴄʜᴇᴄᴋ ᴏʀᴅᴇʀ — </b><code>{oid}</code>", "", "<b>ᴅʙ:</b>"]
    if not db_doc:
        lines.append("  <i>ɴᴏᴛ ғᴏᴜɴᴅ.</i>")
    else:
        lines += [
            f"  <b>status:</b>  <code>{db_doc.get('status')}</code>",
            f"  <b>user_id:</b> <code>{db_doc.get('user_id')}</code>",
            f"  <b>amount:</b>  <code>₹{db_doc.get('amount')}</code>",
            f"  <b>plan:</b>    <code>{db_doc.get('plan_id')}</code>",
            f"  <b>created:</b> <code>{db_doc.get('created_at')}</code>",
            f"  <b>paid_at:</b> <code>{db_doc.get('paid_at') or '—'}</code>",
            f"  <b>txn_id:</b>  <code>{db_doc.get('txn_id') or '—'}</code>",
        ]

    lines += ["", "<b>sᴇʟʟɢʀᴀᴍ:</b>"]
    if api_err:
        lines.append(f"  <i>ᴀᴘɪ ᴇʀʀᴏʀ:</i> <code>{api_err}</code>")
    elif api_resp and api_resp.get("success"):
        d = api_resp.get("data") or {}
        lines += [
            f"  <b>status:</b>  <code>{d.get('status')}</code>",
            f"  <b>amount:</b>  <code>₹{d.get('amount')}</code>",
            f"  <b>txn_id:</b>  <code>{d.get('txn_id')}</code>",
            f"  <b>bank:</b>    <code>{d.get('bank_txn_id')}</code>",
            f"  <b>mode:</b>    <code>{d.get('payment_mode')}</code>",
            f"  <b>paid_on:</b> <code>{d.get('txn_date')}</code>",
        ]
    else:
        msg = (api_resp or {}).get("message") or "ᴜɴᴋɴᴏᴡɴ"
        lines.append(f"  <i>{msg}</i>")

    if (
        db_doc and db_doc.get("status") != "paid"
        and api_resp and api_resp.get("success")
        and (api_resp.get("data") or {}).get("status") == "TXN_SUCCESS"
    ):
        lines += ["", f"<b>⚠️ ᴍɪsᴍᴀᴛᴄʜ —</b> ᴜsᴇ <code>/forceverify {oid}</code> ᴛᴏ ʀᴇᴄᴏɴᴄɪʟᴇ."]

    await message.reply("\n".join(lines))


# ═══════════════════════════════════════════════════════════════════════════════
#   /forceverify <order_id>  —  recovery
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_message(filters.command("forceverify") & filters.private & filters.user(OWNER_ID))
async def forceverify_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<b>ᴜsᴇ:</b> <code>/forceverify &lt;order_id&gt;</code>")
    oid = message.command[1].strip()

    progress = await message.reply(f"<b>🔧 ғᴏʀᴄᴇ ᴠᴇʀɪғʏɪɴɢ</b> <code>{oid}</code> …")

    order = await _orders.find_one({"order_id": oid})
    if not order:
        return await progress.edit("<b>❌ ᴏʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴅʙ.</b>")

    try:
        api = await _sellgram(oid)
    except Exception as e:
        return await progress.edit(f"<b>❌ ᴀᴘɪ ᴇʀʀᴏʀ:</b> <code>{e}</code>")

    if not (api and api.get("success")):
        return await progress.edit(
            f"<b>❌ sᴇʟʟɢʀᴀᴍ:</b> <i>{(api or {}).get('message', 'unknown')}</i>"
        )

    data = api.get("data") or {}
    if data.get("status") != "TXN_SUCCESS":
        return await progress.edit(
            f"<b>❌ sᴇʟʟɢʀᴀᴍ sᴛᴀᴛᴜs:</b> <code>{data.get('status')}</code>\n"
            f"<i>{data.get('resp_msg', '')}</i>"
        )

    paid_amt = float(data.get("amount") or 0)
    expected = float(order.get("amount") or 0)
    if paid_amt + 0.01 < expected:
        return await progress.edit(
            f"<b>❌ ᴀᴍᴏᴜɴᴛ ᴍɪsᴍᴀᴛᴄʜ.</b> ᴘᴀɪᴅ ₹{paid_amt} ʙᴜᴛ ᴇxᴘᴇᴄᴛᴇᴅ ₹{expected}."
        )

    user_id = order["user_id"]

    if order.get("status") == "paid":
        return await progress.edit(
            f"<b>ℹ️ ᴀʟʀᴇᴀᴅʏ ᴘᴀɪᴅ.</b>\n\n"
            f"<b>ᴏʀᴅᴇʀ:</b> <code>{oid}</code>\n"
            f"<b>ᴜsᴇʀ:</b>  <code>{user_id}</code>\n"
            f"<b>ᴘᴀɪᴅ ᴀᴛ:</b> <code>{order.get('paid_at')}</code>"
        )

    expiration_time = await add_premium(
        user_id,
        int(order["time_value"]),
        order["time_unit"],
        "gold",
    )

    await _orders.update_one(
        {"order_id": oid},
        {"$set": {
            "status": "paid",
            "txn_id": data.get("txn_id"),
            "paid_at": datetime.utcnow().isoformat(),
            "force_verified": True,
        }},
    )

    asyncio.create_task(monitor_premium_expiry(client, user_id))

    user_notified = True
    try:
        await client.send_message(
            chat_id=user_id,
            text=(
                f"<b>✅ ᴘᴀʏᴍᴇɴᴛ ᴠᴇʀɪғɪᴇᴅ — ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!</b>\n\n"
                f"<b>ᴏʀᴅᴇʀ ɪᴅ:</b> <code>{oid}</code>\n"
                f"<b>ᴀᴍᴏᴜɴᴛ:</b> ₹{order['amount']}\n"
                f"<b>ᴅᴜʀᴀᴛɪᴏɴ:</b> {order['time_value']}{order['time_unit']}\n"
                f"<b>ᴇxᴘɪʀᴇs ᴏɴ:</b> {expiration_time}\n\n"
                f"<i>ᴇɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss! 🎉</i>"
            ),
        )
    except Exception:
        user_notified = False

    await progress.edit(
        f"<b>🔧 ғᴏʀᴄᴇ ᴠᴇʀɪғɪᴇᴅ</b> <code>{oid}</code>\n\n"
        f"✅ sᴇʟʟɢʀᴀᴍ ᴄᴏɴғɪʀᴍs sᴜᴄᴄᴇss\n"
        f"✅ ᴀᴍᴏᴜɴᴛ ᴍᴀᴛᴄʜᴇs (₹{order['amount']})\n"
        f"✅ ᴅʙ ᴜᴘᴅᴀᴛᴇᴅ → <code>paid</code>\n"
        f"✅ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ (gold, {order['time_value']}{order['time_unit']})\n"
        f"{'✅' if user_notified else '⚠️'} ʀᴇᴄᴇɪᴘᴛ "
        f"{'sᴇɴᴛ' if user_notified else 'ʙʟᴏᴄᴋᴇᴅ'} ᴛᴏ <code>{user_id}</code>\n"
        f"✅ ᴀᴘᴘᴇᴀʀs ɪɴ /id, /ord, /amount"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#   Callbacks
# ═══════════════════════════════════════════════════════════════════════════════
@Bot.on_callback_query(filters.regex(r"^aord_id_(\d{8})_(\d+)$"))
async def cb_id_page(client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ.", show_alert=True)
    date_short = query.matches[0].group(1)
    page = int(query.matches[0].group(2))
    d = _parse_short(date_short)
    await _render_id_page(client, query, d, page, edit=True)
    try:
        await query.answer()
    except Exception:
        pass


@Bot.on_callback_query(filters.regex(r"^aord_amt_(\d{8})$"))
async def cb_amt(client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ.", show_alert=True)
    d = _parse_short(query.matches[0].group(1))
    await _send_amount(client, query, d, edit=True)
    try:
        await query.answer()
    except Exception:
        pass


@Bot.on_callback_query(filters.regex(r"^aord_exp_(\d{8})$"))
async def cb_exp(client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ.", show_alert=True)
    d = _parse_short(query.matches[0].group(1))
    orders = await _fetch_orders_for_date(d)
    if not orders:
        return await query.answer("ɴᴏ ᴏʀᴅᴇʀs.", show_alert=True)
    total_amt = sum(o.get("amount", 0) for o in orders)
    lines = [
        f"# ORDERS — {_fmt_date_human(d)}",
        f"# count={len(orders)} amount=Rs{total_amt}",
        "",
    ]
    for i, o in enumerate(orders, start=1):
        lines.append(
            f"{i}. {o.get('order_id','?')}  user={o.get('user_id','?')}  "
            f"plan={o.get('plan_id','?')}  amount=Rs{o.get('amount',0)}  "
            f"paid_at={o.get('paid_at')}  txn={o.get('txn_id')}"
        )
    buf = io.BytesIO("\n".join(lines).encode())
    buf.name = f"orders-{_fmt_date_short(d)}.txt"
    await query.message.reply_document(
        buf,
        caption=f"<b>ᴇxᴘᴏʀᴛ — {_fmt_date_human(d)}</b>  •  {len(orders)} ᴏʀᴅᴇʀs  •  ₹{total_amt}",
    )
    try:
        await query.answer("ᴇxᴘᴏʀᴛᴇᴅ ✓")
    except Exception:
        pass


@Bot.on_callback_query(filters.regex(r"^aord_close$"))
async def cb_close(client, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception:
        pass
    try:
        await query.answer()
    except Exception:
        pass


@Bot.on_callback_query(filters.regex(r"^aord_noop$"))
async def cb_noop(client, query: CallbackQuery):
    try:
        await query.answer()
    except Exception:
        pass
