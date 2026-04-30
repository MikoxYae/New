#  ─────────────────────────────────────────────
#   Premium Plans store  (used by /psetting + /plans)
#   By Yae X Miko
#  ─────────────────────────────────────────────

import asyncio
import motor.motor_asyncio
from datetime import datetime
from pytz import timezone
from bson import ObjectId
from config import DB_URI, DB_NAME

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]
plans_col = database["premium-plans"]
gifts_col = database["gift_grants"]

# Allowed duration units and their display labels
ALLOWED_UNITS = {
    "m":   "Minutes",
    "h":   "Hours",
    "d":   "Days",
    "w":   "Weeks",
    "mon": "Months",
    "y":   "Years",
}

ALLOWED_TIERS = ("gold",)


def _unit_label(unit: str) -> str:
    return ALLOWED_UNITS.get(unit.lower(), unit)


def _tier_emoji(tier: str) -> str:
    # Single tier supported (gold). Kept for backward compatibility.
    return "🥇"


# ─────────────────────────────────────────────
#  Convert a (value, unit) plan duration into
#  the (value, unit) pair accepted by
#  database.db_premium.add_premium  ('s','m','h','d','y')
# ─────────────────────────────────────────────
def to_addpremium_unit(value: int, unit: str):
    unit = unit.lower()
    if unit in ("s", "m", "h", "d", "y"):
        return value, unit
    if unit == "w":
        return value * 7, "d"
    if unit == "mon":
        return value * 30, "d"
    raise ValueError(f"Unknown unit: {unit}")


# ─────────────────────────────────────────────
#  CRUD
# ─────────────────────────────────────────────
async def add_plan(name: str, tier: str, duration_value: int,
                   duration_unit: str, price: str) -> str:
    tier = "gold"  # only gold tier supported
    duration_unit = duration_unit.lower()
    if tier not in ALLOWED_TIERS:
        raise ValueError("Invalid tier. Only 'gold' is supported.")
    if duration_unit not in ALLOWED_UNITS:
        raise ValueError("Invalid duration unit.")
    if duration_value <= 0:
        raise ValueError("Duration value must be > 0.")

    ist = timezone("Asia/Kolkata")
    doc = {
        "name":           name.strip(),
        "tier":           tier,
        "duration_value": int(duration_value),
        "duration_unit":  duration_unit,
        "price":          str(price).strip(),
        "created_at":     datetime.now(ist).isoformat(),
    }
    res = await plans_col.insert_one(doc)
    return str(res.inserted_id)


async def get_plan(plan_id: str):
    try:
        return await plans_col.find_one({"_id": ObjectId(plan_id)})
    except Exception:
        return None


async def list_plans():
    out = []
    cursor = plans_col.find({}).sort("created_at", 1)
    async for p in cursor:
        out.append(p)
    return out


async def delete_plan(plan_id: str) -> bool:
    try:
        res = await plans_col.delete_one({"_id": ObjectId(plan_id)})
        return res.deleted_count > 0
    except Exception:
        return False


async def update_plan(plan_id: str, **fields) -> bool:
    if not fields:
        return False
    try:
        res = await plans_col.update_one(
            {"_id": ObjectId(plan_id)},
            {"$set": fields},
        )
        return res.modified_count > 0
    except Exception:
        return False


# ─────────────────────────────────────────────
#  Pretty formatter (for /plans + admin list)
# ─────────────────────────────────────────────
def format_plan_line(plan: dict, with_id: bool = False) -> str:
    tier = plan.get("tier", "gold")
    head = f"{_tier_emoji(tier)} <b>{plan.get('name','—')}</b>  "
    head += f"<i>({tier.capitalize()})</i>"
    body = (
        f"\n   💰 Price: <b>{plan.get('price','—')}</b>"
        f"\n   ⏳ Duration: <b>{plan.get('duration_value','?')} "
        f"{_unit_label(plan.get('duration_unit',''))}</b>"
    )
    if with_id:
        body += f"\n   🆔 <code>{plan.get('_id')}</code>"
    return head + body


def format_plans_block(plans: list, with_id: bool = False) -> str:
    if not plans:
        return "<b>No premium plans available yet.</b>"
    return "\n\n".join(format_plan_line(p, with_id=with_id) for p in plans)


# ─────────────────────────────────────────────
#  Gift channel — link / unlink a Telegram
#  channel to a plan so buyers are auto-added.
# ─────────────────────────────────────────────
async def set_gift_channel(plan_id: str, channel_id: int, channel_title: str) -> bool:
    return await update_plan(
        plan_id,
        gift_channel_id=int(channel_id),
        gift_channel_title=str(channel_title),
    )


async def clear_gift_channel(plan_id: str) -> bool:
    try:
        res = await plans_col.update_one(
            {"_id": ObjectId(plan_id)},
            {"$unset": {"gift_channel_id": "", "gift_channel_title": ""}},
        )
        return res.modified_count > 0
    except Exception:
        return False


# ─────────────────────────────────────────────
#  Gift grants  —  per-user record of which
#  gift channels they currently have access to,
#  and when that access expires (mirrors the
#  premium expiry).
# ─────────────────────────────────────────────
async def grant_gift(user_id: int,
                     channel_id: int,
                     channel_title: str,
                     plan_id: str,
                     expires_at: str,
                     order_id: str = None) -> str:
    ist = timezone("Asia/Kolkata")
    doc = {
        "user_id":       int(user_id),
        "channel_id":    int(channel_id),
        "channel_title": str(channel_title),
        "plan_id":       str(plan_id),
        "order_id":      order_id,
        "granted_at":    datetime.now(ist).isoformat(),
        "expires_at":    expires_at,
        "status":        "active",
    }
    res = await gifts_col.insert_one(doc)
    return str(res.inserted_id)


async def list_active_gifts_for_user(user_id: int) -> list:
    out = []
    cursor = gifts_col.find({"user_id": int(user_id), "status": "active"})
    async for g in cursor:
        out.append(g)
    return out


async def mark_gift_revoked(grant_oid) -> bool:
    try:
        res = await gifts_col.update_one(
            {"_id": grant_oid},
            {"$set": {"status": "revoked",
                      "revoked_at": datetime.now(timezone("Asia/Kolkata")).isoformat()}},
        )
        return res.modified_count > 0
    except Exception:
        return False


async def revoke_user_gifts(client, user_id: int) -> int:
    """
    Remove `user_id` from every gift channel they currently hold an
    active grant for, and mark those grants revoked.

    Uses ban -> unban so the user is kicked but can rejoin if they
    purchase the plan again later. Errors per-channel are swallowed
    (e.g. user already left, bot lost admin) so one bad channel
    doesn't block the rest.

    Returns the number of channels the user was removed from.
    """
    grants = await list_active_gifts_for_user(user_id)
    removed = 0
    for g in grants:
        ch_id = g.get("channel_id")
        if not ch_id:
            await mark_gift_revoked(g["_id"])
            continue
        try:
            await client.ban_chat_member(ch_id, int(user_id))
            await asyncio.sleep(0.4)
            try:
                await client.unban_chat_member(ch_id, int(user_id))
            except Exception:
                pass
            removed += 1
        except Exception:
            pass
        await mark_gift_revoked(g["_id"])
    return removed
